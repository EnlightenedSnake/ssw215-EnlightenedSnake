import json
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///portfolio.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

PROJECTS_SEED_FILE = Path(__file__).with_name("projects_seed.json")


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.String(500), nullable=False, default="")
    likes = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "likes": self.likes,
        }


def init_seed_data():
    if db.session.query(Project.id).first() is not None:
        return

    with PROJECTS_SEED_FILE.open("r", encoding="utf-8") as seed_file:
        seed_projects = json.load(seed_file)

    db.session.add_all([
        Project(
            id=project["id"],
            title=project["title"],
            description=project.get("description", ""),
            likes=project.get("likes", 0),
        )
        for project in seed_projects
    ])
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()


with app.app_context():
    db.create_all()
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
    next_id = db.session.query(func.coalesce(func.max(Project.id), 0)).scalar() + 1
    project = Project(id=next_id, title=title, description="", likes=0)
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
