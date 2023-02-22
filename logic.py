import datetime
import requests
import json
from dotenv import dotenv_values 
import os
from pymongo import MongoClient

config = dotenv_values(".env")
x=datetime.datetime.now()
riotAPISession = requests.session()
dDragonSession = requests.session()
riotAPISession.headers.update({"X-Riot-Token": config["API_KEY"]})
mongo = MongoClient(config["ATLAS_URL"])
appData = mongo["data"]
matchData = appData["match"]

def mostRecentLolPatch():
    return requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()[0]

patch = mostRecentLolPatch()

def getItemsJSON():
    return requests.get(f"http://ddragon.leagueoflegends.com/cdn/{patch}/data/en_US/item.json").json()

itemsObject = getItemsJSON()

def getItemObject(id):
    try:
        itemsObject['data'][id].update({'id':id})
        return itemsObject['data'][id]
    except:
        return 'None'

def getItemName(id):
    try:
        return itemsObject['data'][id]['name']
    except:
        return 'None'

def getItemImage(session,id):
    return session.get(f"http://ddragon.leagueoflegends.com/cdn/{patch}/img/item/{id}.png")

def summoner (session,server,summonerName):
    return session.get(f"https://{server}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summonerName}")
    
def rankedWR (session,server,summonerID):
    rankedWins =  session.get(f"https://{server}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summonerID}").json()
    list = []
    for gameMode in rankedWins:
        list.append({
                "QueueType" : gameMode['queueType'],
                "Rank":f"{gameMode['tier']} {gameMode['rank']} {gameMode['leaguePoints']}LP",
                "Total Games" : gameMode['wins'] + gameMode['losses'],
                "Wins" : gameMode['wins'],
                "Losses" : gameMode['losses']
                })
    return list

def getMatchesArray(session,region,puuid,start,count,type):
    return session.get(f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}&type={type}")

def getMatchInfo(session,region,matchList):
    list = []
    for matchID in matchList:
        search = matchData.find_one({"metadata.matchId":matchID}) 
        if(search == None):
            print('calling api')
            match = session.get(f"https://{region}.api.riotgames.com/lol/match/v5/matches/{matchID}?api_key={config['API_KEY']}")
            if(match.status_code == 200):
                match = match.json()
                match.update({'status_code':200})
                matchData.insert_one(match)
                list.append(match)
            else:
                list.append(match.json()['status'])
                break
        else:
            list.append(search)
    return list

def getFullSummonerStatsForMatch(match):
    if(match['status_code'] == 200):
        list = []
        for player in match['info']['participants']:
            list.append({
                "summonerName" : player['summonerName'],
                "champion" : player['championName'],
                "kills" : player['kills'],
                "deaths" : player['deaths'],
                "assists" : player['assists'],
                "creepScore" : player['totalMinionsKilled'] + player['neutralMinionsKilled'],
                "items" : [
                    getItemObject(f"{player['item0']}"),
                    getItemObject(f"{player['item1']}"),
                    getItemObject(f"{player['item2']}"),
                    getItemObject(f"{player['item3']}"),
                    getItemObject(f"{player['item4']}"),
                    getItemObject(f"{player['item5']}"),
                    getItemObject(f"{player['item6']}"),
                ],
                "goldEarned" : player['goldEarned'],
                "win" : player['win']
                })
        return list
    else:
        return f"Match Object request did not have a 200 it had a {match['status_code']}"

def getSpecificSummonerStats(summoner):
    print('')
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

def mostRecentLolPatch():
    return requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()[0]

def champIcon(session,champion):
    return session.get(f"http://ddragon.leagueoflegends.com/cdn/{patch}/img/champion/{champion}.png")

def imageDownloader(matchObjects,summonerName):
    icons = os.listdir('./images/icons')
    items = os.listdir('./images/items')
    count = 1
    for match in matchObjects:
        if(match['status_code'] == 200):
            summonerStats = getFullSummonerStatsForMatch(match)
            for each in summonerStats:
                if each['summonerName'] == summonerName:
                    print(each['champion']) 

            # for summoner in summonerStats:
            #     print(summoner['champion'])
            #     if(f"{summoner['champion']}.png") not in icons:
            #         with open(f"./images/icons/{summoner['champion']}.png","wb") as f:
            #             f.write(champIcon(dDragonSession,summoner['champion']).content)
            #             f.close()
            #     for item in summoner['items']:
            #         if(item != 'None') and f"{item['name']}.png" not in items:
            #             with open(f"./images/items/{item['name'].replace(' ','')}.png","wb") as f:
            #                 f.write(getItemImage(dDragonSession,item['id']).content)
            #                 f.close()
                
        else:
             print(match)
            
def search (session,server,summonerName,start):
    summonerObj = summoner(session,server,summonerName).json()
    print(summonerObj)
    rankedWins = rankedWR(session,server,summonerObj['id'])
    print(rankedWins)
    region = getRegionFromServer(server)
    matchList = getMatchesArray(session,region,summonerObj['puuid'],start,20,"ranked").json()
    matchObjects = getMatchInfo(session,region,matchList)
    imageDownloader(matchObjects,summonerName)
    

search(riotAPISession,'euw1','Elite500',150)


print((datetime.datetime.now()-x).total_seconds())