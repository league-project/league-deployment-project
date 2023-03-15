import datetime
import requests
import os
from pymongo import MongoClient
import base64
import math
array = [0,1,2,4,5,6,7,8]
class Search:
    riotSession = None
    dSession = None 
    mongo = None
    @staticmethod 
    def imageDownload():
        Search.imageDB['runes'].delete_many({})
        for rune in Search.runesObject:
            path = rune["iconPath"].lower().split("/")
            path = "/".join(path[5:])
            image = Search.dSession.get("https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/perk-images/"+path)
            if image.status_code == 200:
                Search.imageDB['runes'].insert_one({'id':rune['id'],"image":base64.b64encode(image.content).decode("UTF-8")})
        Search.imageDB['item'].delete_many({})
        for id in Search.itemsObject['data']:
            image = Search.dSession.get(f"http://ddragon.leagueoflegends.com/cdn/{Search.patch}/img/item/{id}.png")
            if image.status_code == 200:
                Search.imageDB['item'].insert_one({'id':id , 'image' : base64.b64encode(image.content).decode("UTF-8")})

        Search.imageDB['champIcon'].delete_many({})
        for id in Search.champObject['data']:
            image = Search.dSession.get(f"http://ddragon.leagueoflegends.com/cdn/{Search.patch}/img/champion/{id}.png")
            if image.status_code == 200:
                Search.imageDB['champIcon'].insert_one({'id':id.lower() , 'image' : base64.b64encode(image.content).decode("UTF-8")})
            else:
                print(id)
        Search.imageDB['summonerSpells'].delete_many({})
        for spell in Search.summonerSpellObject:
            path = spell["iconPath"].lower().split("/")
            image = Search.dSession.get("https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/data/spells/icons2d/"+path[len(path)-1])
            if image.status_code == 200:
                Search.imageDB['summonerSpells'].insert_one({'id':spell['id'],"image":base64.b64encode(image.content).decode("UTF-8")})
    
    @staticmethod
    def start_up():
        mongo = MongoClient(os.getenv("MONGO_URL"))
        appData = mongo["data"]
        riotSess = requests.session()
        riotSess.headers.update({'X-RIOT-TOKEN':os.getenv('API_KEY')})
        Search.riotSession = riotSess
        Search.dSession = requests.session()
        Search.mongo = mongo
        Search.matchData = appData['match']
        Search.imageDB = mongo['image']
        Search.patch = Search.dSession.get("https://ddragon.leagueoflegends.com/api/versions.json").json()[0]
        Search.itemsObject =  Search.dSession.get(f"http://ddragon.leagueoflegends.com/cdn/{Search.patch}/data/en_US/item.json").json()
        Search.champObject =  Search.dSession.get(f"http://ddragon.leagueoflegends.com/cdn/{Search.patch}/data/en_US/champion.json").json()
        Search.runesObject = Search.dSession.get(f"https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/perks.json").json()
        Search.summonerSpellObject = Search.dSession.get("https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/summoner-spells.json").json()
        Search.itemImages = {}
        Search.runeImages = {}
        Search.champIcons = {}
        Search.summonerIcons = {}
        Search.summonerSpellImages = {}
    
    def __init__(self,server,summonerName,type=''):
        self.server = server
        self.type = type
        self.summonerName = summonerName
        self.summonerObject = self.summonerObj()
        self.rankedStats = self.rankedWR()
        self.region = self.getRegionFromServer()
        self.matchesGotten = 0

    def search (self):
        x=datetime.datetime.now()
        obj =  {"games":self.getNextGames(),"summonerOverall":self.summonerObject,"rankedStats":self.rankedStats}
        return obj
    
    def insertMatch(self,data):
        numberOfDocs = Search.matchData.count_documents({})
        if numberOfDocs > 6000:
            for each in Search.matchData.find({}).limit(numberOfDocs-6000):
                Search.matchData.delete_one({"metadata.matchId":each.metadata.matchId})
        Search.matchData.insert_one(data)

    def last20WR(self):
        wins = 0
        losses = 0
        for game in self.myLast20Games:
            try:
                if game['win']:
                    wins+= 1
                else:
                    losses+=1
            except:
                print(type(game))
        self.rankedStats.append({"last20":{"wins":wins,"losses":losses,"WR%":(wins/20)*100}})

    def getNextGames(self,type=''):
        if(type != self.type):
            self.type = type
            self.matchesGotten = 0 
        self.matchList = self.getMatchesArray(self.matchesGotten,20,self.type)
        self.matchesGotten += 20
        self.fullMatchObjects = self.getMatchInfo()
        self.keyMatchInfo =  self.getFullSummonerStatsForMatch()
        return self.getSpecificSummonerStats()
        
    
    def getItemName(self,id):
        try:
            return Search.itemsObject['data'][id]['name']
        except:
            return 'None'
        
    def summonerObj (self):
        obj =  Search.riotSession.get(f"https://{self.server}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{self.summonerName}").json()
        try:
            obj.update({'iconImage':self.summonerIcon(obj['profileIconId'])})
        except KeyError:
            raise Exception(obj['status']['message'],obj['status']['status_code'])
        return obj
    
    def getItemImage(self,id):
         if id == '0':
            return 'None'
         elif id not in Search.itemImages.keys():
            itemImage = Search.imageDB['item'].find_one({"id":id},{"_id":0})
            Search.itemImages.update({id:itemImage['image']})
            return itemImage['image']
         else:
            return Search.itemImages[id]
        
    def getStatName(self,statObject):
        list = []
        for id in statObject.values():
            for rune in Search.runesObject:
                if rune['id'] == id:
                    list.append({"id":id , "name":rune['name']})
        return list
    def getPrimaryRuneName(self,styleList):
        list = []
        for id in styleList[0]['selections']:
            for rune in Search.runesObject:
                if rune['id'] == id['perk']:
                    list.append({"id":id['perk'] , "name":rune['name']})
        return list
    
    def getSecondaryRuneName(self,styleList):
        list = []
        for id in styleList[1]['selections']:
            for rune in Search.runesObject:
                if rune['id'] == id['perk']:
                    list.append({"id":id['perk'] , "name":rune['name']})
        return list
    def getRuneImage(self,id):
        if id not in Search.runeImages.keys():
            runeImage = Search.imageDB['runes'].find_one({"id":id},{"_id":0})
            Search.runeImages.update({id:runeImage['image']})
            return runeImage['image']
        else:
            print("already gotten")
            return Search.runeImages[id]
    def getChampIcon(self,id):
        if id not in Search.champIcons.keys():
            Image = Search.imageDB['champIcon'].find_one({"id":id},{"_id":0}) 
            Search.champIcons.update({id:Image['image']})
            return Image['image']
        else:
            return Search.champIcons[id]
    def rankedWR (self):
        rankedWins =  Search.riotSession.get(f"https://{self.server}.api.riotgames.com/lol/league/v4/entries/by-summoner/{self.summonerObject['id']}").json()
        list = []
        try:
            for gameMode in rankedWins:
                if gameMode['queueType'] =='RANKED_SOLO_5x5':
                    Type = "Ranked Solo/Duo"
                elif gameMode['queueType'] =='RANKED_FLEX_SR':
                    Type = "Ranked Flex"
                list.append({
                        "QueueType" : Type,
                        "Tier" : gameMode['tier'],
                        "Rank":f"{gameMode['tier']} {gameMode['rank']} {gameMode['leaguePoints']}LP",
                        "Total Games" : gameMode['wins'] + gameMode['losses'],
                        "Wins" : gameMode['wins'],
                        "Losses" : gameMode['losses']
                        })
            return list
        except:
            raise Exception(rankedWins)

    def getMatchesArray(self,start,count,type):
        self.matchesGotten += count
        return Search.riotSession.get(f"https://{self.region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{self.summonerObject['puuid']}/ids?start={start}&count={count}&type={type}").json()

    def getMatchInfo(self):
        list = [] 
        for matchID in self.matchList:
            search = Search.matchData.find_one({"metadata.matchId":matchID},{"_id":0}) 
            if(search == None):
                print('calling api')
                match = self.riotSession.get(f"https://{self.region}.api.riotgames.com/lol/match/v5/matches/{matchID}")
                if(match.status_code == 200):
                    self.insertMatch(match.json())
                    list.append(match.json())
                else:
                    list.append(match.json())
                    break
            else:
                list.append(search)
        return list

    def getFullSummonerStatsForMatch(self):
        list = []
        for match in self.fullMatchObjects:
            try:
                list1 = []
                summonerIcons = []
                for player in match['info']['participants']:
                    summonerIcons.append({
                        "summonerName" : player['summonerName'],
                        "championName" : player['championName'],
                        "champIcon" : self.getChampIcon(player['championName'].lower())
                        })
                for player in match['info']['participants']:
                    list1.append({
                        "players" : summonerIcons,
                        "matchDuration" : f"{math.trunc(match['info']['gameDuration']/60)}m {round((match['info']['gameDuration']/60 - math.trunc(match['info']['gameDuration']/60))*60,0)}s",
                        "summonerName" : player['summonerName'],
                        "championName" : player['championName'],
                        "spell1" : self.getSummonerSpell(player['summoner1Id']),
                        "spell2" : self.getSummonerSpell(player['summoner2Id']),
                        "champIcon" : self.getChampIcon(player['championName'].lower()),
                        "kills" : player['kills'],
                        "deaths" : player['deaths'],
                        "assists" : player['assists'],
                        "creepScore" : player['totalMinionsKilled'] + player['neutralMinionsKilled'],
                        "items" : [
                        {'id':f"{player['item0']}", 'name': self.getItemName(f"{player['item0']}")},
                        {'id':f"{player['item1']}", 'name': self.getItemName(f"{player['item1']}")},
                        {'id':f"{player['item2']}", 'name': self.getItemName(f"{player['item2']}")},
                        {'id':f"{player['item3']}", 'name': self.getItemName(f"{player['item3']}")},
                        {'id':f"{player['item4']}", 'name': self.getItemName(f"{player['item4']}")},
                        {'id':f"{player['item5']}", 'name': self.getItemName(f"{player['item5']}")},
                        {'id':f"{player['item6']}", 'name': self.getItemName(f"{player['item6']}")},
                        ],
                        "goldEarned" : player['goldEarned'],
                        "runeStats": self.getStatName(player['perks']['statPerks']),
                        "primaryRunes": self.getPrimaryRuneName(player['perks']['styles']),
                        "secondaryRunes": self.getSecondaryRuneName(player['perks']['styles']),
                        "totalTeamKills" : match['info']['teams'][(player['teamId']//100) - 1 ]['objectives']['champion']['kills'],
                        "kp" : math.trunc(round(((player['kills']+player['assists'])/match['info']['teams'][(player['teamId']//100) - 1 ]['objectives']['champion']['kills']) * 100,0)),
                        "win" : player['win']
                        })
                list.append(list1)
            except KeyError:
                return f"Match Object request did not have a 200 it had a {match['status_code']}"
        return list 

    def getSpecificSummonerStats(self):
        list = []
        for match in self.keyMatchInfo:
            for player in match:
                if(player['summonerName'] == self.summonerName):
                    for item in player['items']:
                        item.update({'image':self.getItemImage(item['id'])})
                    for stat in player['runeStats']:
                        stat.update({'image':self.getRuneImage(stat['id'])})
                    for prune in player['primaryRunes']:
                        prune.update({'image':self.getRuneImage(prune['id'])})
                    for srune in player['secondaryRunes']:
                        srune.update({'image':self.getRuneImage(srune['id'])})
                    list.append(player)
        return list

    def getRegionFromServer(self):
        servers = {
        "EUROPE":("euw1","eun1","ru","tr1"),
        "AMERICAS":("na1","la1","la2","br1"),
        "ASIA":("jp1","kr"),
        "SEA":("ph2","sg2","th2","tw2","vn2","oc1")
        }
        for x, y in servers.items():
            if self.server in y:
                return x
    def summonerIcon(self,id):
        if id not in Search.summonerIcons.keys():
            image = Search.dSession.get(f"http://ddragon.leagueoflegends.com/cdn/{Search.patch}/img/profileicon/{id}.png").content
            Search.summonerIcons.update({id:base64.b64encode(image).decode("UTF-8")})
        return Search.summonerIcons[id]
    
    def getSummonerSpell(self,id):
        if id not in Search.summonerSpellImages.keys():
             image = Search.imageDB['summonerSpells'].find_one({"id":id},{"_id":0})
             Search.summonerSpellImages.update({id:image['image']})
        return Search.summonerSpellImages[id]

    



