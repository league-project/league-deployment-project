import pymongo
from dotenv import dotenv_values
from logic import run_mail_feature

config = dotenv_values(".env")

mongo_url = config["MONGO_URL"]
client = pymongo.MongoClient(mongo_url)
db = client["data"]
col = db["emails"]


def db_checks():
    search = list(col.find({}, {"_id": 0}))
    if search is None:
        return None
    for each in search:
        x = run_mail_feature(each["email"], each["champions"])
        if x is False:
            pass
        if x:
            col.update_one({"email": each["email"]}, {"$set": {"champions": x}})
        if x is None:  # If their list is now empty, remove them from the list
            col.delete_one({"email": each["email"]})


db_checks()


def db_inserts(email, champs):
    champs = champs.split(",")
    for index, each in enumerate(champs):
        champs[index] = each.strip()

    col.insert_one({"email": email, "champions": champs})
