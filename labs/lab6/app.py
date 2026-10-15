from flask import Flask, render_template, send_from_directory

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
        "title": "A really really bad game that utilizes a backend to allow for smoother gameplay",
        "description": "A game using a backend to support smoother gameplay.",
        "likes": 0,
    },
]


@app.route("/")
def index():
    return render_template("index.html", projects=projects_db)


@app.route("/assets/avatar.png")
def avatar():
    return send_from_directory(app.static_folder, "assets/avatar.png")


if __name__ == "__main__":
    app.run(debug=True)
