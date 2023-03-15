from flask import Flask, request, render_template
import base64
from db import db_inserts
from search import Search

app = Flask(__name__)
Search.start_up()

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
    if request.method == "GET":
        return render_template("summoner.html",summoner=Search(region,nick))


@app.get("/404/")
def test404():
    return render_template("404.html")

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
