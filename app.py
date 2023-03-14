from flask import Flask, request, render_template
from db import db_inserts

app = Flask(__name__)


@app.route("/", methods=("GET", "POST"))
def index():
    return render_template("index.html")


@app.route("/watchlist/", methods=("GET", "POST"))
def watchlist():
    if request.method == "POST":
        email = request.form["email"]
        champs = request.form["content"]
        x = db_inserts(email, champs)
        return render_template("confirmation.html")
    if request.method == "GET":
        return render_template("watchlist.html")


@app.get("/confirmed/")
def confirm():
    return render_template("confirmation.html")


@app.get("/summoner/<region>/<nick>")
def get_summoner_data(region, nick):
    return ""


@app.get("/404/")
def test404():
    return render_template("404.html")
