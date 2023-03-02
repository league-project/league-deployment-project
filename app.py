from logic import Logic

Logic.start_up()

def search(server,summonerName):
    try:
        summoner = Logic.search(server,summonerName,40)
        print(summoner.getKeyInfo())
    except AttributeError:
        print("Call the start up function first!")

search("euw1","HaroldBoiii")
