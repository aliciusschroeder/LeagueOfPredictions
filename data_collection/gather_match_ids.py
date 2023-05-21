"""
This script uses the RiotWatcher API to gather a list of League of Legends Match-ID's. It follows these steps:

1. It starts by obtaining the unique identifier (puuid) of a summoner based on their name (considered as a seed).
2. Next, it retrieves the summoner's past matches using the get_past_matches function. The OLDEST_ALLOWED_DATE 
   variable defines the maximum date for considering matches.
3. The script extracts the puuid of all summoners who participated in the past matches and removes any duplicates 
   from the list.
4. It then iterates over the summoners and retrieves their respective past matches, appending them to the matches list.
5. Any duplicate match IDs are removed from the matches list.
6. Finally, the script writes the match IDs to a file named "manymatches.txt" by opening the file in "append" mode.

Depending on player-overlap you can expect around 9*n^2 match ids where n is the number of past matches you fetch
"""


import time
import datetime
from riotwatcher import LolWatcher, ApiError
import os
import configparser

#API_KEY = os.getenv("LOL_API_KEY")

config = configparser.ConfigParser()
config.read('config.ini')
API_KEY = config['DEFAULT']['API_KEY']

LOL_WATCHER = LolWatcher(API_KEY)
QUEUE_TYPE = 400  # 420 = Ranked 5v5 Solo Queue. 400 = Normal Draft 5v5. Full list of queue types at: https://static.developer.riotgames.com/docs/lol/queues.json
REGION = 'euw1'
PAST_MATCHES_COUNT = 1 # number of last matches we gather
SEED_USER_NAME = 'OrangenSandwich' # Seed username we get the first few matches from
OLDEST_ALLOWED_DATE = datetime.date.today() - datetime.timedelta(days=14) # Define cutoff date for matches that are taken into account
OLDEST_ALLOWED_DATE = int(time.mktime(OLDEST_ALLOWED_DATE.timetuple())) # Convert the datetime object into an integer Unix timestamp


def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', print_end="\r"):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=print_end)
    if iteration == total:
        print()


def get_past_matches(puuid):
    match_list = LOL_WATCHER.match.matchlist_by_puuid(REGION, puuid, start_time=OLDEST_ALLOWED_DATE, queue=QUEUE_TYPE, count=PAST_MATCHES_COUNT)
    return match_list


def get_match(match_id):
    while True:
        try:
            req_match = LOL_WATCHER.match.by_id(REGION, match_id)
        except ApiError as err:
            if err.response.status_code == 429:
                print('This retry-after is handled by default by the RiotWatcher library')
                print('Future requests wait until the retry-after time passes')
            elif err.response.status_code == 404:
                print('Match not found.')
            elif err.response.status_code == 503:
                print('Server is too busy...')
            else:
                print('Something weird happened, wait 15 sec and try again...')
                time.sleep(15)
                continue
        break
    return req_match




def get_summoner_puuid(region, username):
    # Get the unique identifier (puuid) of a summoner by their name
    return LOL_WATCHER.summoner.by_name(region, username)['puuid']

def get_all_summoners(past_matches):
    # Extract the puuid of all summoners in the past matches
    summoners = []
    for match_id in past_matches:
        match = get_match(match_id)
        summoners.extend([participant['puuid'] for participant in match['info']['participants']])
    # Remove duplicates from the list of summoners
    return list(set(summoners))

def get_all_matches(summoners):
    matches = []
    for summoner in summoners:
        matches.extend(get_past_matches(summoner))
    # Remove duplicates from the list of matches
    return list(set(matches))


def write_matches_to_file(matches, filename):
    with open(filename, "a") as f:
        for match_id in matches:
            f.write(f"{match_id}\n")


def main():
    puuid = get_summoner_puuid(REGION, SEED_USER_NAME)
    past_matches = get_past_matches(puuid)
    summoners = get_all_summoners(past_matches)
    matches = get_all_matches(summoners)
    write_matches_to_file(matches, "manymatches.txt")

if __name__ == "__main__":
    main()