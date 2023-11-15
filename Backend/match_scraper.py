import json
import requests
from os import listdir
from time import sleep

BATCHES = 2
URL = "https://api.henrikdev.xyz"
REGION = "na"
DIR = "matches"
INITIAL_PUUID = "00d2e83d-3374-515e-b511-396aa99a8d10"

match_names = listdir(DIR)


def get_match_hist(puuid, mode="competitive"):

    r = requests.get(URL + "/valorant/v3/by-puuid/matches/" + REGION + "/" + puuid + "?filter=" + mode)

    while r.status_code != 200:
        print("invalid status: " + str(r.status_code) + "retrying in 10 seconds")
        sleep(10)
        r = requests.get(URL + "/valorant/v3/by-puuid/matches/" + REGION + "/" + puuid + "?filter=" + mode)

    return r.json()["data"]


def get_puuids(match):

    return [player["puuid"] for player in match["players"]["all_players"]]


def get_match_id(match):

    return match["metadata"]["matchid"]


def write_match_data(match):

    name = get_match_id(match) + ".json"

    if (not name in match_names):

        print("new match found: " + name)
    
        match_names.append(name)

        with open(DIR + "/" + name , "w") as match_file:

            match_file.write(json.dumps(match, indent=4))
    
    else:

        print("repeat game: " + name)

batch = 0
puuids = [INITIAL_PUUID]
new_puuids = []

for i in range(BATCHES):

    print("\nBATCH " + str(i) + " OF " + str(BATCHES))
    print(str(len(puuids)) + " NEW PUUID(S)\n")

    for puuid in puuids:

        for match in get_match_hist(puuid):

            write_match_data(match)

            for new_puuid in get_puuids(match):

                new_puuids.append(new_puuid)

    puuids = new_puuids
    new_puuids = []
        
            










