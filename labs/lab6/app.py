from flask import Flask, jsonify, render_template, send_from_directory

app = Flask(__name__)

projects_db = [
    {
        "id": 1,
        "title": "A 3D game that uses only built in frontend commands",
        "description": "A 3D game built using only built-in frontend commands.",
        "likes": 0,
    },
    {
        "id": 2,
        "title": "A RPG style game with selfmade graphics",
        "description": "An RPG-style game featuring self-made graphics.",
        "likes": 0,
    },
    {
        "id": 3,
        "title": "A bad game that utilizes a backend to allow for smoother gameplay",
        "description": "A game using a backend to support smoother gameplay.",
        "likes": 0,
    },
    { #hand-edited by JM
        "id": 4,
        "title": "A chess application that uses AI to find the best move",
        "description": "A chess application that utilizes AI to determine the best moves.",
        "likes": 0,
    },
]


@app.route("/")
def index():
    return render_template("index.html", projects=projects_db)


@app.route("/api/projects/<int:project_id>/upvote", methods=["POST"])
def upvote_project(project_id):
    project = next(
        (project for project in projects_db if project["id"] == project_id),
        None,
    )
    if project is None:
        return jsonify({"error": "Project not found"}), 404

    project["likes"] += 1
    return jsonify({"id": project_id, "likes": project["likes"]})


@app.route("/assets/avatar.png")
def avatar():
    return send_from_directory(app.static_folder, "assets/avatar.png")


if __name__ == "__main__":
    app.run(debug=True)
