import datetime
import requests
from dotenv import dotenv_values 
from pymongo import MongoClient
array = [0,1,2,4,5,6,7,8]
class Logic:
    riotSession = None
    dSession = None 
    mongo = None
    @staticmethod 
    def imageDownload():
        Logic.imageDB['runes'].delete_many({})
        for rune in Logic.runesObject:
            path = rune["iconPath"].lower().split("/")
            path = "/".join(path[5:])
            image = Logic.dSession.get("https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/perk-images/"+path)
            if image.status_code == 200:
                Logic.imageDB['runes'].insert_one({'id':rune['id'],"image":image.content})
        Logic.imageDB['item'].delete_many({})
        for id in Logic.itemsObject['data']:
            image = Logic.dSession.get(f"http://ddragon.leagueoflegends.com/cdn/{Logic.patch}/img/item/{id}.png")
            if image.status_code == 200:
                Logic.imageDB['item'].insert_one({'id':id , 'image' : image.content})
        Logic.imageDB['champIcon'].delete_many({})
        for id in Logic.champObject['data']:
            image = Logic.dSession.get(f"http://ddragon.leagueoflegends.com/cdn/{Logic.patch}/img/champion/{id}.png")
            if image.status_code == 200:
                Logic.imageDB['champIcon'].insert_one({'id':id.lower() , 'image' : image.content})
            else:
                print(id)
        Logic.imageDB['summonerSpells'].delete_many({})
        for spell in Logic.summonerSpellObject:
            path = spell["iconPath"].lower().split("/")
            image = Logic.dSession.get("https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/data/spells/icons2d/"+path[len(path)-1])
            if image.status_code == 200:
                Logic.imageDB['summonerSpells'].insert_one({'id':spell['id'],"image":image.content})
       

    @staticmethod
    def start_up():
        config = dotenv_values(".env")
        mongo = MongoClient(config["ATLAS_URL"])
        appData = mongo["data"]
        riotSess = requests.session()
        riotSess.headers.update({'X-RIOT-TOKEN':config['API_KEY']})
        Logic.riotSession = riotSess
        Logic.dSession = requests.session()
        Logic.mongo = mongo
        Logic.matchData = appData['match']
        Logic.imageDB = mongo['image']
        Logic.patch = Logic.dSession.get("https://ddragon.leagueoflegends.com/api/versions.json").json()[0]
        Logic.itemsObject =  Logic.dSession.get(f"http://ddragon.leagueoflegends.com/cdn/{Logic.patch}/data/en_US/item.json").json()
        Logic.champObject =  Logic.dSession.get(f"http://ddragon.leagueoflegends.com/cdn/{Logic.patch}/data/en_US/champion.json").json()
        Logic.runesObject = Logic.dSession.get(f"https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/perks.json").json()
        Logic.summonerSpellObject = Logic.dSession.get("https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/summoner-spells.json").json()
        Logic.itemImages = {}
        Logic.runeImages = {}
        Logic.champIcons = {}
        Logic.summonerSpellImages = {}
    
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
        obj =  self.getNextGames(),self.summonerObject,self.rankedStats,(datetime.datetime.now()-x).total_seconds()
        return obj
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
        print(self.rankedStats)
    def getNextGames(self,type=''):
        if(type != self.type):
            self.type = type
            self.matchesGotten = 0 
        self.matchList = self.getMatchesArray(self.matchesGotten+20,20,self.type)
        self.fullMatchObjects = self.getMatchInfo()
        self.keyMatchInfo = self.getFullSummonerStatsForMatch()
        self.myLast20Games = self.getSpecificSummonerStats()
        self.last20WR()
        return self.myLast20Games
        
    def getItemName(self,id):
        try:
            return Logic.itemsObject['data'][id]['name']
        except:
            return 'None'
        
    def summonerObj (self):
        obj =  Logic.riotSession.get(f"https://{self.server}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{self.summonerName}").json()
        try:
            obj.update({'iconImage':self.summonerIcon(obj['profileIconId']).content})
        except KeyError:
            raise Exception(obj['status']['message'],obj['status']['status_code'])
        return obj
    
    def getItemImage(self,id):
         if id == '0':
            return 'None'
         elif id not in Logic.itemImages.keys():
            itemImage = Logic.imageDB['item'].find_one({"id":id},{"_id":0})
            Logic.itemImages.update({id:itemImage['image']})
            return itemImage['image']
         else:
            return Logic.itemImages[id]
        
    def getStatName(self,statObject):
        list = []
        for id in statObject.values():
            for rune in Logic.runesObject:
                if rune['id'] == id:
                    list.append({id:rune['name']})
        return list
    def getPrimaryRuneName(self,styleList):
        list = []
        for id in styleList[0]['selections']:
            for rune in Logic.runesObject:
                if rune['id'] == id['perk']:
                    list.append({"id":id['perk'] , "name":rune['name']})
        return list
    
    def getSecondaryRuneName(self,styleList):
        list = []
        for id in styleList[1]['selections']:
            for rune in Logic.runesObject:
                if rune['id'] == id['perk']:
                    list.append({"id":id['perk'] , "name":rune['name']})
        return list
    def getRuneImage(self,id):
        if id not in Logic.runeImages.keys():
            runeImage = Logic.imageDB['runes'].find_one({"id":id},{"_id":0})
            Logic.runeImages.update({id:runeImage['image']})
            return runeImage['image']
        else:
            print("already gotten")
            return Logic.runeImages[id]
    def getChampIcon(self,id):
        if id not in Logic.champIcons.keys():
            Image = Logic.imageDB['champIcon'].find_one({"id":id},{"_id":0})git 
            Logic.champIcons.update({id:Image['image']})
            return Image['image']
        else:
            return Logic.champIcons[id]
    def rankedWR (self):
        rankedWins =  Logic.riotSession.get(f"https://{self.server}.api.riotgames.com/lol/league/v4/entries/by-summoner/{self.summonerObject['id']}").json()
        list = []
        try:
            for gameMode in rankedWins:
                list.append({
                        "QueueType" : gameMode['queueType'],
                        "Rank":f"{gameMode['tier']} {gameMode['rank']} {gameMode['leaguePoints']}LP",
                        "Total Games" : gameMode['wins'] + gameMode['losses'],
                        "Wins" : gameMode['wins'],
                        "Losses" : gameMode['losses']
                        })
            return list
        except:
            raise Exception(rankedWins.status.message)

    def getMatchesArray(self,start,count,type):
        self.matchesGotten += count
        return Logic.riotSession.get(f"https://{self.region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{self.summonerObject['puuid']}/ids?start={start}&count={count}&type={type}").json()

    def getMatchInfo(self):
        list = [] 
        for matchID in self.matchList:
            search = Logic.matchData.find_one({"metadata.matchId":matchID},{"_id":0}) 
            if(search == None):
                print('calling api')
                match = self.riotSession.get(f"https://{self.region}.api.riotgames.com/lol/match/v5/matches/{matchID}")
                if(match.status_code == 200):
                    Logic.matchData.insert_one(match.json())
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
                for player in match['info']['participants']:
                    list1.append({
                        "matchDuration" : match['info']['gameDuration'],
                        "summonerName" : player['summonerName'],
                        "championName" : player['championName'],
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
                        "fullRunes" :player['perks'],
                        "goldEarned" : player['goldEarned'],
                        "runeStats": self.getStatName(player['perks']['statPerks']),
                        "primaryRunes": self.getPrimaryRuneName(player['perks']['styles']),
                        "secondaryRunes": self.getSecondaryRuneName(player['perks']['styles']),
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
                        stat.update({'image':self.getItemImage(item['id'])})
                    for prune in player['primaryRunes']:
                        prune.update({'image':self.getItemImage(item['id'])})
                    for srune in player['secondaryRunes']:
                        srune.update({'image':self.getItemImage(item['id'])})
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
        return Logic.dSession.get(f"http://ddragon.leagueoflegends.com/cdn/{Logic.patch}/img/profileicon/{id}.png")
    
    # def allImageDownloader(self,redownload,overwrite=False):
    #     directories = ['profileIcons','champIcons','items','runes','spells']
    #     for folder in directories:
    #         try:
    #             os.makedirs(f'./images/{folder}',exist_ok=overwrite)
    #         except FileExistsError:
    #             continue
    #     if(redownload):
    #         for id in Logic.itemsObject['data']:
    #             with open(f'./images/items/{id}.png','wb') as f:
    #                 f.write(self.getItemImage(id).content)
    #                 f.close()


    



