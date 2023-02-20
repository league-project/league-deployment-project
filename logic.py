import requests
from dotenv import dotenv_values 
config = dotenv_values(".env")

s = requests.session()
s.headers.update({"X-Riot-Token": config["API_KEY"]})

def summoner (session,server,summonerName):
    return session.get(f"https://{server}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summonerName}")
    
def rankedWR (session,server,summonerID):
    rankedWins =  session.get(f"https://{server}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summonerID}").json()[0]
    playerObj  = {
                "QueueType" : rankedWins['queueType'],
                "Rank":f"{rankedWins['tier']} {rankedWins['rank']} {rankedWins['leaguePoints']}LP",
                "Total Games" : rankedWins['wins'] + rankedWins['losses'],
                "Wins" : rankedWins['wins'],
                "Losses" : rankedWins['losses']
                }
    return playerObj

def getMatchesArray(session,region,puuid,start,count):
    return session.get(f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}")

def getMatchInfo(session,region,matchList):
    list = []
    for matchID in matchList:
        match = session.get(f"https://{region}.api.riotgames.com/lol/match/v5/matches/{matchID}")
        if(match.status_code == 200):
            match = match.json()
            match.update({'status_code':200})
            list.append(match)
        else:
            return [match.json()['status']]
    return list

def getSummonerStatsForMatch(match,summonerId):
    if(match['status_code'] == 200):
        for player in match['info']['participants']:
            if (player['summonerId'] == summonerId):
                return {
                    "summonerName" : player['summonerName'],
                    "lane" : player["lane"],
                    "role" : player['role'],
                    "champion" : player['championName'],
                    "kills" : player['kills'],
                    "deaths" : player['deaths'],
                    "assists" : player['assists'],
                    "creepScore" : player['totalMinionsKilled']
                    }
    else:
        return "Match Object request did not have a 200 it had a ",match['status_code']
def getRegionFromServer(server):
    servers = {
    "EUROPE":("euw1","eun1","ru"),
    "AMERICAS":("na1","la1","la2","br1"),
    "ASIA":("jp1","kr"),
    "SEA":("ph2","sg2","th2","tw2","vn2")
    }
    for x, y in servers.items():
        if server in y:
            return x
    
def search (session,server,summonerName):
    summonerObj = summoner(session,server,summonerName).json()
    rankedWins = rankedWR(session,server,summonerObj['id'])
    region = getRegionFromServer(server)
    matchList = getMatchesArray(session,region,summonerObj['puuid'],0,50).json()
    print(summonerObj)
    print(rankedWins)
    matchObjects = getMatchInfo(session,region,matchList)
    for match in matchObjects:
        print(match)
        print(getSummonerStatsForMatch(match,summonerObj['id']))
search(s,'euw1','HaroldBoiii')
