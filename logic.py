import datetime
import requests
from dotenv import dotenv_values 
from pymongo import MongoClient

class Logic:
    riotSession = None
    dSession = None 
    mongo = None
    @staticmethod 
    def imageDownload():
        Logic.imageDB['item'].delete_many({})
        for id in Logic.itemsObject['data']:
            image = Logic.dSession.get(f"http://ddragon.leagueoflegends.com/cdn/{Logic.patch}/img/item/{id}.png")
            if image.status_code == 200:
                Logic.imageDB['item'].insert_one({'id':id , 'image' : image.content})
        Logic.imageDB['champIcon'].delete_many({})
        for id in Logic.champObject['data']:
            image = Logic.dSession.get(f"http://ddragon.leagueoflegends.com/cdn/{Logic.patch}/img/champion/{id}.png")
            if image.status_code == 200:
                Logic.imageDB['champIcon'].insert_one({'id':id , 'image' : image.content})

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
        Logic.itemImages = {}
    
    def __init__(self,server,summonerName,type=''):
        self.server = server
        self.type = type
        self.summonerName = summonerName
        self.summonerObject = self.summonerObj()
        self.rankedStats = self.rankedWR()
        self.region = self.getRegionFromServer()
        self.matchesGotten = 0
        

       
    # def getItemObject(self,id):
    #     try:
    #         Logic.itemsObject['data'][id].update({'id':id})
    #         return Logic.itemsObject['data'][id]
    #     except:
    #         return 'None'

    def search (self):
        try:
            x=datetime.datetime.now()
            obj = self.getNextGames()
            print((datetime.datetime.now()-x).total_seconds())
            return obj

        except AttributeError:
            return "call start up function to intalize function"
        
    def getNextGames(self,type=''):
        if(type != self.type):
            self.type = type
            self.matchesGotten = 0 
        self.matchList = self.getMatchesArray(self.matchesGotten+20,20,self.type)
        print(self.matchList)
        self.fullMatchObjects = self.getMatchInfo()
        self.keyMatchInfo = self.getFullSummonerStatsForMatch()
        return self.summonerObject,self.rankedStats,self.getSpecificSummonerStats()
        

    def getItemName(self,id):
        try:
            return Logic.itemsObject['data'][id]['name']
        except:
            return 'None'
    def summonerObj (self):
        return Logic.riotSession.get(f"https://{self.server}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{self.summonerName}").json()
    
    def getItemImage(self,id):
         if id == '0':
            return 'None'
         elif id not in Logic.itemImages.keys():
            itemImage = Logic.imageDB['item'].find_one({"id":id},{"_id":0})
            Logic.itemImages.update({id:itemImage['image']})
            return itemImage['image']
         else:
            print("already gotten")
            return Logic.itemImages[id]
    
    def rankedWR (self):
        rankedWins =  Logic.riotSession.get(f"https://{self.server}.api.riotgames.com/lol/league/v4/entries/by-summoner/{self.summonerObject['id']}").json()
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

    def getMatchesArray(self,start,count,type):
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
                        "summonerName" : player['summonerName'],
                        "champion" : player['championName'],
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
                    list.append(player)
        return list

    def getRegionFromServer(self):
        servers = {
        "EUROPE":("euw1","eun1","ru"),
        "AMERICAS":("na1","la1","la2","br1"),
        "ASIA":("jp1","kr"),
        "SEA":("ph2","sg2","th2","tw2","vn2")
        }
        for x, y in servers.items():
            if self.server in y:
                return x

    def champIcon(self,champion):
        return Logic.dSession.get(f"http://ddragon.leagueoflegends.com/cdn/{Logic.patch}/img/champion/{champion}.png")

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


    



