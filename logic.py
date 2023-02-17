import smtplib
import ssl
from dotenv import dotenv_values
import requests

config = dotenv_values(".env")

port = 587  # For SSL
password = config["SMTP_PASS"]

sender_email = config["SMTP_EMAIL"]
# receiver_email = "preston.harry2003@gmail.com "
receiver_email = "ryan.curry1@directlinegroup.co.uk"
# c1 = ["Malzahar"]
# c2 = ["Aatrox", "Midstar", "That crusty Renekton you play"]

# Create a secure SSL context
context = ssl.create_default_context()

# version = requests.get("https://ddragon.leagueoflegends.com/api/versions.json")
# current = version.json()[0]

fwrota = f"https://euw1.api.riotgames.com/lol/platform/v3/champion-rotations?api_key={config['API_KEY']}"
print(requests.get(fwrota).json()["freeChampionIds"])


def payload_gen(champions):
    if len(champions) == 1:
        verb = "is"
        champions = "".join(champions)
    else:
        verb = "are"
        champions = ", ".join(champions)

    message = f"""\
        Subject: Free Week Rotation

        Hey, this is a reminder from LossGBT that {champions} {verb} currently in the free week rotation!

        Enjoy your time in the rift Summoner"""

    return send_mail(message)


def send_mail(message):
    with smtplib.SMTP("smtp-mail.outlook.com", port) as server:
        server.starttls(context=context)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)
