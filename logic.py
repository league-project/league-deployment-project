import smtplib
import ssl
from dotenv import dotenv_values
import requests

config = dotenv_values(".env")

port = 587  # For SSL
password = config["SMTP_PASS"]

sender_email = config["SMTP_EMAIL"]

# Create a secure SSL context
context = ssl.create_default_context()

version = requests.get("https://ddragon.leagueoflegends.com/api/versions.json")
current = version.json()[0]
champ_url = f"https://ddragon.leagueoflegends.com/cdn/{current}/data/en_US/champion.json"

fwrota = f"https://euw1.api.riotgames.com/lol/platform/v3/champion-rotations?api_key={config['API_KEY']}"
champ_ids = requests.get(fwrota).json()["freeChampionIds"]
# Champion ids come from fw rota as ints but are nums in DDragon
for index, champ_num in enumerate(champ_ids):
    champ_ids[index] = str(champ_num)

champ_data = requests.get(champ_url).json()["data"]
rota_names = []


def id_assigner():
    for each in champ_data:
        if champ_data[each]["key"] in champ_ids:
            rota_names.append(champ_data[each]["id"])


id_assigner()


def rota_vs_watchlist(wl):
    watchlist_match = []
    for each in wl:
        if each in rota_names:
            watchlist_match.append(each)

    return watchlist_match


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

    return message


def html_payload_gen(champions):
    if len(champions) == 1:
        verb = "is"
        champions = "".join(champions)
    else:
        verb = "are"
        champions = ", ".join(champions)

    urls = []

    for each in champions:
        urls.append(f"https://ddragon.leagueoflegends.com/cdn/{current}/img/champion/{each}.png")
    urls = ["https://ddragon.leagueoflegends.com/cdn/13.4.1/img/champion/Kaisa.png",
            "https://ddragon.leagueoflegends.com/cdn/13.4.1/img/champion/Tristana.png",
            "https://ddragon.leagueoflegends.com/cdn/13.4.1/img/champion/Sett.png"]

    for i, each in enumerate(urls):
        urls[i] = f'<img src="{each}">'
    x = " ".join(urls)

    message = f"""\
    <html>
        <style>
            * {{text-align:center;font-family: "Comic Sans MS", "Comic Sans", cursive;}} 
            .images{{margin:1rem;}}
            body{{background-image: url('https://lol-stats.net/uploads/sxpVPO9w4T9YlJfk4hruCobM2lNeYFNVQPnT8dkR.jpeg');
            background-repeat: no-repeat;background-position: top;}}
            h2 {{color:#e70c50}}
        </style>
        <body>
            <h2>Free week rotation alert</h2>
            <br>
            <div class="images">
            {x}
            </div>
            <p>Hey, this is a reminder from LossGBT that <strong>{champions}</strong> {verb} currently in the free 
            week rotation!</p> <br> <p>Enjoy your time in the rift Summoner</p> </body> </html> """

    return message


def wl_adjusting(wl, fw_match):
    for each in fw_match:
        wl.remove(each)

    return wl


def send_mail(message, receiver_email):
    with smtplib.SMTP("smtp-mail.outlook.com", port) as server:
        server.starttls(context=context)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)


def run_mail_feature(recipient, wl):
    match = rota_vs_watchlist(wl)
    if match is None:
        return None  # No need to keep going as there aren't any matches
    payload = payload_gen(match)
    send_mail(payload, recipient)
    return wl_adjusting(wl, match)
