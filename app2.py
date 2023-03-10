from logic2 import Logic

Logic.start_up()

def search(server,summonerName):
    try:
        summoner = Logic(server,summonerName)
        print(summoner.search())
    except AttributeError:
        print("Call the start up function first!")

search("euw1","HaroldBoiii")
