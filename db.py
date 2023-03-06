import pymongo
from dotenv import dotenv_values
from logic import run_mail_feature

config = dotenv_values(".env")

env = config["MONGO_URL"]
client = pymongo.MongoClient(env)
db = client["data"]
col = db["emails"]


def db_checks():
    search = list(col.find({}, {"_id": 0}))
    for each in search:
        x = run_mail_feature(each["email"], each["champions"])
        if x is not None:
            col.update_one({"email": each["email"]}, {"$set": {"champions": x}})
        if x is None:  # If their list is now empty, remove them from the list
            col.delete_one({"email": each["email"]})


db_checks()


def db_inserts(email, champs):
    champs = champs.split(",")

    col.insert_one({"email": email, "champions": champs})
