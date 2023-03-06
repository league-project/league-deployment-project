from logic import Logic

Logic.start_up()

def search(server,summonerName):
    try:
        summoner = Logic(server,summonerName)
        print(summoner.getNextGames())
        print(summoner.getNextGames())
    except AttributeError:
        print("Call the start up function first!")

search("euw1","HaroldBoiii")
