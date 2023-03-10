import smtplib
import ssl
from dotenv import dotenv_values
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
# print(requests.get(fwrota).json())
champ_ids = requests.get(fwrota).json()["freeChampionIds"]
# Champion ids come from fw rota as ints but are nums in DDragon
for index, champ_num in enumerate(champ_ids):
    champ_ids[index] = str(champ_num)

champ_data = requests.get(champ_url).json()["data"]
rota_names = []


def id_assigner():
    for each in champ_data:
        if champ_data[each]["key"] in champ_ids:
            rota_names.append(champ_data[each]["name"])


id_assigner()
print(rota_names)


def rota_vs_watchlist(wl):
    watchlist_match = []
    for each in wl:
        if each in rota_names:
            watchlist_match.append(each)

    return watchlist_match


def payload_gen(champions):
    # MIME has different multiparts with different usages, multipart alternative tries to load the last first and if
    # that doesn't work, it tries to load the other part

    if not champions or champions is None:
        return None
    message = MIMEMultipart("alternative")
    message["Subject"] = "Free week rotation alert"
    message["From"] = config["SMTP_EMAIL"]

    urls = []

    for each in champions:
        each = each.strip().replace("'", "").lower().capitalize()
        urls.append(f"https://ddragon.leagueoflegends.com/cdn/{current}/img/champion/{each}.png")

    for i, each in enumerate(urls):
        urls[i] = f'<img style="height:7.5rem;width:7.5rem;" src="{each}">'
    x = " ".join(urls)

    if len(champions) == 1:
        verb = "is"
        champions = "".join(champions)
    else:
        verb = "are"
        champions = ", ".join(champions).rsplit(",", 1)
        champions = " and".join(champions)

    message_html = f"""\
    <html>
        <body>
            <div style="
            background-image: url(
            'https://lol-stats.net/uploads/sxpVPO9w4T9YlJfk4hruCobM2lNeYFNVQPnT8dkR.jpeg');
            text-align:center;
            min-width:100vh;
            min-height:100vh;
            font-family: 'Comic Sans MS', 'Comic Sans', cursive;
            background-position: top;
            background-repeat: no-repeat;
            background-size: 100% auto;
            margin: -1rem;
            text-shadow: 0.1rem 0.1rem black;
            ">
            <h1 style="color:#e70c50; padding-top:4rem; margin-top:0%;">Free week rotation alert</h1>
            <br>
            <div class="images" style="margin:1rem">
            {x}
            </div>
            <p style="margin:6rem; color:white">Hey, this is a reminder from LossGBT that <strong>{champions}</strong>
             {verb} currently in the free week rotation!</p> 
             <br> 
             <p style="color:white">Enjoy your time in the rift Summoner</p> 
            </div>
        </body> 
    </html> """

    message_txt = f"""\
        Subject: Free Week Rotation

        Hey, this is a reminder from LossGBT that {champions} {verb} currently in the free week rotation!

        Enjoy your time in the rift Summoner"""

    part1 = MIMEText(message_txt, "plain")
    part2 = MIMEText(message_html, "html")

    message.attach(part1)
    message.attach(part2)

    return message


def wl_adjusting(wl, fw_match):
    for each in fw_match:
        wl.remove(each)

    return wl


def send_mail(message, receiver_email):
    with smtplib.SMTP("smtp-mail.outlook.com", port) as server:
        server.starttls(context=context)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())


def run_mail_feature(recipient, wl):
    match = rota_vs_watchlist(wl)
    if match is None:
        return None  # No need to keep going as there aren't any matches
    payload = payload_gen(match)
    if payload is None:
        return None
    send_mail(payload, recipient)
    return wl_adjusting(wl, match)


# pay = payload_gen(["Diana", " Ziggs", " Cho'Gath", " Aatrox"])
# pay2 = payload_gen(["Tristana","Udyr"])
