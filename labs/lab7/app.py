import json
from pathlib import Path

from flask import Flask, jsonify, render_template, send_from_directory

app = Flask(__name__)

PROJECTS_FILE = Path(__file__).with_name("projects.json")


def load_projects():
    with PROJECTS_FILE.open(encoding="utf-8") as projects_file:
        return json.load(projects_file)


def save_projects(projects):
    with PROJECTS_FILE.open("w", encoding="utf-8") as projects_file:
        json.dump(projects, projects_file, indent=2)
        projects_file.write("\n")


@app.route("/")
def index():
    return render_template("index.html", projects=load_projects())


@app.route("/api/projects/<int:project_id>/upvote", methods=["POST"])
def upvote_project(project_id):
    projects_db = load_projects()
    project = next(
        (project for project in projects_db if project["id"] == project_id),
        None,
    )
    if project is None:
        return jsonify({"error": "Project not found"}), 404

    project["likes"] += 1
    save_projects(projects_db)
    return jsonify({"id": project_id, "likes": project["likes"]})


@app.route("/assets/avatar.png")
def avatar():
    return send_from_directory(app.static_folder, "assets/avatar.png")


if __name__ == "__main__":
    app.run(debug=True)
