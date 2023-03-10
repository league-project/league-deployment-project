from logic2 import Logic

Logic.start_up()
Logic.imageDownload()
def search(server,summonerName):
    summoner = Logic(server,summonerName)
    print(summoner.search())

search("euw1","HaroldBoiii")
search("euw1","smhbro")
