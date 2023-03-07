from flask import Flask, request, render_template

app = Flask(__name__)


@app.route("/")
def index():
    messages = [
        {"title": "Message One", "content": "Message One Content"},
        {"title": "Message Two", "content": "Message Two Content"},
    ]
    return render_template("index.html", messages=messages)


@app.route("/watchlist/", methods=("GET", "POST"))
def watchlist():
    return render_template("watchlist.html")
