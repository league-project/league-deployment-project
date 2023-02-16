import requests
from dotenv import dotenv_values 
config = dotenv_values(".env")
servers = {
    "EUROPE":("euw1","eun1","ru"),
    "AMERICAS":("na1","la1","la2","br1"),
    "ASIA":("jp1","kr"),
    "SEA":("ph2","sg2","th2","tw2","vn2")
}
s = requests.session()
s.headers.update({"X-Riot-Token": config["API_KEY"]})

def summoner (session,server,summonerName):
    return session.get(f"https://{server}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summonerName}")
    
def rankedWR (session,server,summonerID):
    return  session.get(f"https://{server}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summonerID}")

def matches(session,region,puuid,start,count):
    return session.get(f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}")

def search (session,server,summonerName):
    summonerObj = summoner(session,server,summonerName).json()
    rankedWins = rankedWR(session,server,summonerObj['id']).json()
    region = ''
    for x, y in servers.items():
        if server in y:
            region = x
    matchList = matches(session,region,summonerObj['puuid'],0,20).json()
    print(rankedWins)
    print(matchList)
search(s,'euw1','HaroldBoiii')
