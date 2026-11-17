import json
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, inspect, text
from sqlalchemy.exc import IntegrityError

from ai_service import (
    GitHubProjectDraft,
    ModelRefusalError,
    ProviderUnavailableError,
    SessionNotFoundError,
    extract_project_details,
    get_github_draft,
    refine_github_session,
    start_github_session,
)
from github_service import (
    GitHubUnavailableError,
    RepositoryNotFoundError,
    fetch_repository_readme,
)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///portfolio.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

PROJECTS_SEED_FILE = Path(__file__).with_name("projects_seed.json")
SEEDED_AUTHOR_NAME = "Jake Mikruk"


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    projects = db.relationship("Project", backref="author")


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.String(500), nullable=False, default="")
    summary = db.Column(db.String(500), nullable=False, default="")
    technologies = db.Column(db.String(500), nullable=False, default="")
    difficulty = db.Column(db.String(20), nullable=False, default="")
    likes = db.Column(db.Integer, default=0)
    author_id = db.Column(db.Integer, db.ForeignKey("author.id"), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "summary": self.summary,
            "technologies": self.technologies,
            "difficulty": self.difficulty,
            "likes": self.likes,
            "author": self.author.name,
        }


def init_seed_data():
    if db.session.query(Project.id).first() is not None:
        return

    author = Author.query.filter_by(name=SEEDED_AUTHOR_NAME).first()
    if author is None:
        author = Author(name=SEEDED_AUTHOR_NAME)
        db.session.add(author)
        db.session.flush()

    with PROJECTS_SEED_FILE.open("r", encoding="utf-8") as seed_file:
        seed_projects = json.load(seed_file)

    db.session.add_all([
        Project(
            id=project["id"],
            title=project["title"],
            description=project.get("description", ""),
            summary=project.get("summary", ""),
            technologies=project.get("technologies", ""),
            likes=project.get("likes", 0),
            author=author,
        )
        for project in seed_projects
    ])
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()


def migrate_project_difficulty():
    project_columns = {
        column["name"] for column in inspect(db.engine).get_columns("project")
    }
    if "difficulty" not in project_columns:
        db.session.execute(
            text(
                "ALTER TABLE project "
                "ADD COLUMN difficulty VARCHAR(20) NOT NULL DEFAULT ''"
            )
        )
        db.session.commit()


with app.app_context():
    db.create_all()
    migrate_project_difficulty()
    init_seed_data()


@app.route("/")
def index():
    projects = Project.query.order_by(Project.id).all()
    return render_template("index.html", projects=projects)


@app.route("/api/projects", methods=["GET"])
def get_projects():
    projects = Project.query.order_by(Project.id).all()
    return jsonify([project.to_dict() for project in projects]), 200


@app.route("/api/projects/<int:project_id>/upvote", methods=["POST"])
def upvote_project(project_id):
    project = db.session.get(Project, project_id)
    if project is None:
        return jsonify({"error": "Project not found"}), 404

    project.likes += 1
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Unable to update project"}), 400
    return jsonify({"id": project_id, "likes": project.likes})


@app.route("/api/projects", methods=["POST"])
def create_project():
    data = request.get_json(silent=True)
    title = data.get("title") if isinstance(data, dict) else None
    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "A non-empty title is required"}), 400

    title = title.strip()
    author = Author.query.filter_by(name=SEEDED_AUTHOR_NAME).first()
    if author is None:
        return jsonify({"error": "Seeded author not found"}), 400

    next_id = db.session.query(func.coalesce(func.max(Project.id), 0)).scalar() + 1
    project = Project(
        id=next_id,
        title=title,
        description="",
        summary="",
        technologies="",
        likes=0,
        author=author,
    )
    db.session.add(project)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A project with that title already exists"}), 400
    return jsonify(project.to_dict()), 201


@app.route("/api/projects/smart", methods=["POST"])
def smart_create_project():
    data = request.get_json(silent=True)
    notes = data.get("notes") if isinstance(data, dict) else None
    if not isinstance(notes, str) or len(notes.strip()) < 20:
        return jsonify({"error": "At least 20 characters of notes are required"}), 400

    try:
        details = extract_project_details(notes.strip())
    except ModelRefusalError as error:
        return jsonify({"error": str(error)}), 422
    except ProviderUnavailableError as error:
        return jsonify({"error": str(error)}), 503

    author = Author.query.filter_by(name=SEEDED_AUTHOR_NAME).first()
    if author is None:
        return jsonify({"error": "Seeded author not found"}), 400

    next_id = db.session.query(func.coalesce(func.max(Project.id), 0)).scalar() + 1
    project = Project(
        id=next_id,
        title=details.title.strip(),
        description="",
        summary=details.summary.strip(),
        technologies=", ".join(technology.strip() for technology in details.technologies),
        likes=0,
        author=author,
    )
    db.session.add(project)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A project with that title already exists"}), 400
    return jsonify(project.to_dict()), 201


@app.route("/api/projects/git-start", methods=["POST"])
def start_github_import():
    data = request.get_json(silent=True)
    owner = data.get("owner") if isinstance(data, dict) else None
    repository = data.get("repo") if isinstance(data, dict) else None
    if (
        not isinstance(owner, str)
        or not owner.strip()
        or not isinstance(repository, str)
        or not repository.strip()
    ):
        return jsonify({"error": "A repository owner and name are required"}), 400

    try:
        readme = fetch_repository_readme(owner.strip(), repository.strip())
    except RepositoryNotFoundError as error:
        return jsonify({"error": str(error)}), 404
    except GitHubUnavailableError as error:
        return jsonify({"error": str(error)}), 503

    if len(readme.strip()) < 20:
        return jsonify(
            {"error": "The repository README must have at least 20 characters"}
        ), 400

    try:
        session_id, draft = start_github_session(readme)
    except ModelRefusalError as error:
        return jsonify({"error": str(error)}), 422
    except ProviderUnavailableError as error:
        return jsonify({"error": str(error)}), 503

    return jsonify({"session_id": session_id, "draft": draft.model_dump()}), 201


@app.route("/api/projects/git-refine", methods=["POST"])
def refine_github_import():
    data = request.get_json(silent=True)
    session_id = data.get("session_id") if isinstance(data, dict) else None
    feedback = data.get("feedback") if isinstance(data, dict) else None
    if not isinstance(session_id, str) or not session_id:
        return jsonify({"error": "A session_id is required"}), 400
    try:
        get_github_draft(session_id)
    except SessionNotFoundError as error:
        return jsonify({"error": str(error)}), 404
    if not isinstance(feedback, str):
        return jsonify({"error": "Feedback must be a string"}), 400

    try:
        draft = refine_github_session(session_id, feedback)
    except SessionNotFoundError as error:
        return jsonify({"error": str(error)}), 404
    except ModelRefusalError as error:
        return jsonify({"error": str(error)}), 422
    except ProviderUnavailableError as error:
        return jsonify({"error": str(error)}), 503
    return jsonify(draft.model_dump()), 200


@app.route("/api/projects/git-commit", methods=["POST"])
def commit_github_import():
    data = request.get_json(silent=True)
    session_id = data.get("session_id") if isinstance(data, dict) else None
    if not isinstance(session_id, str) or not session_id:
        return jsonify({"error": "A session_id is required"}), 400
    try:
        draft: GitHubProjectDraft = get_github_draft(session_id)
    except SessionNotFoundError as error:
        return jsonify({"error": str(error)}), 404

    title = draft.title.strip()
    summary = draft.summary.strip()
    technologies = ", ".join(
        technology.strip() for technology in draft.technologies
    )
    if (
        not title
        or len(title) > 120
        or len(summary) > 500
        or len(technologies) > 500
    ):
        return jsonify({"error": "The draft exceeds the project field limits"}), 400

    author = Author.query.filter_by(name=SEEDED_AUTHOR_NAME).first()
    if author is None:
        return jsonify({"error": "Seeded author not found"}), 400

    next_id = db.session.query(func.coalesce(func.max(Project.id), 0)).scalar() + 1
    project = Project(
        id=next_id,
        title=title,
        description="",
        summary=summary,
        technologies=technologies,
        difficulty=draft.difficulty,
        likes=0,
        author=author,
    )
    db.session.add(project)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A project with that title already exists"}), 400
    return jsonify(project.to_dict()), 201


@app.route("/assets/avatar.png")
def avatar():
    return send_from_directory(app.static_folder, "assets/avatar.png")


if __name__ == "__main__":
    app.run(debug=True)
