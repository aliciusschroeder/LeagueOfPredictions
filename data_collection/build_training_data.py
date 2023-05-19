import time
from riotwatcher import LolWatcher, ApiError
import datetime
import numpy as np
import csv
import os

lol_watcher = LolWatcher('RGAPI-e2eca008-bd0e-422a-84f3-df8e3132f6b2')
my_region = 'euw1'
min_time = int(time.mktime((datetime.date.today() - datetime.timedelta(days=14)).timetuple())) # defining the max age in days until matches aren't taken into account anymore

currMatchCreationDate = 0
pastMatchesCount = 3 #17

queue_nr = 420 # 420 = Ranked 5v5 Solo Queue. Full list of queue types at: https://static.developer.riotgames.com/docs/lol/queues.json

PLAYER_ATTRIBUTES = ['winrate','champ_winrate','avgKda','champ_avgKda','streak','consistency','champMastery']

myGame = {} # for debugging after running main()

def handle_api_error(err):
    if err.response.status_code == 429:
        print('this retry-after is handled by default by the RiotWatcher library')
        print('future requests wait until the retry-after time passes')
    elif err.response.status_code == 404:
        print('Match not found.')
    elif err.response.status_code == 503:
        print('Small server of indie company is too busy...')
    else:
        print('Something weird happened, wait 15 sec and try again...')
        time.sleep(15)

  
def update_status(str):
    print('\r'+str, end='', flush=True)


def analyze_game(match_id):
    # Retrieves information about summoners and their champions in a certain match Returns a list of dictionaries, 
    # each representing one summoner who participated in the given match. 
    # Dictionary attributes include per summoner: puuid, championId, summonerId and whether they won.
    SAC = get_summoners_and_champ(match_id)

    excluded_matches = [match_id] # we don't want to include the current match in their past-game analysis

    game = {}
    game['id']=match_id
    summoners = []
    
    summoner_count = 0
    for s in SAC:
        summoner_count += 1
        print(f'[{summoner_count}/10] Analyzing summoner')
        summoners.append(analyze_summoner(s, excluded_matches))

    if SAC[4]['win']==SAC[5]['win']:
        win = "ERR"
    else:
        win = 0 if SAC[4]['win'] else 1
    
    for summoner_nr, summoner in enumerate(summoners, start=1):
        for attribute in PLAYER_ATTRIBUTES:
            key = f'summoner_{summoner_nr}_{attribute}'
            game[key] = summoner[attribute]
    game['win'] = win
    return game


def analyze_summoner(summoner_data, excluded_matches):

    past_matches = get_past_matches_ids(summoner_data['puuid'], excluded_matches)
    details = get_details_by_matchlist(past_matches, summoner_data['puuid'])
    if len(details) > 0:
        champion_performance = get_collected_info_by_champ(details, summoner_data['champ'])
    else:
        champion_performance = {}
        for a in PLAYER_ATTRIBUTES:
            champion_performance[a] = 'EMPTY'
            print ('- NO PAST MATCHES FOR THIS SUMMONER -'*2)
    champion_performance['champMastery'] = get_champion_mastery(summoner_data['sid'], summoner_data['champ'])
    return champion_performance


def get_champion_mastery(sId, championId):
    return lol_watcher.champion_mastery.by_summoner_by_champion(my_region, sId, championId)['championPoints']

def get_summoners_and_champ(match_id):
    '''Retrieves information about summoners and their champions in a certain match
    Returns a list of dictionaries, each representing one summoner who participated 
    in the given match. Dictionary attributes include per summoner: puuid, championId, summonerId and whether they won.'''
    global currMatchCreationDate    
    match = get_match(match_id)
    currMatchCreationDate = int(match['info']['gameCreation'] / 1000)
    summonersAndChamps = []
    for summoner in match['info']['participants']:
        summonersAndChamps.append({
            'puuid': summoner['puuid'],
            'champ': summoner['championId'],
            'sid': summoner['summonerId'],
            'win': summoner['win']
        })
    return summonersAndChamps



def get_past_matches_ids(puuid, excluded_matches):
    matchlist = lol_watcher.match.matchlist_by_puuid(my_region, puuid, start_time = min_time, queue = queue_nr, count = pastMatchesCount, end_time = currMatchCreationDate)
    matchlist = [i for i in matchlist if not i in excluded_matches or excluded_matches.remove(i)]
    return matchlist


def get_match(match_id):
    while True:
        try:
            req_match = lol_watcher.match.by_id(my_region, match_id)
        except ApiError as err:
            handle_api_error(err)
            continue
        break
    return req_match


def extract_participant_from_match(match, puuid):
    return next((participant for participant in match['info']['participants'] if participant['puuid'] == puuid), None)


def get_details_by_matchlist(matchlist, puuid):
    playerMatchesDetails = []
    matches_total = len(matchlist)
    for match_count, match_id in enumerate(matchlist, start=1):
        update_status(f'[{match_count}/{matches_total}] GetDetailsByMatchlist')
        match_details = get_match(match_id)
        this_participant = extract_participant_from_match(match_details, puuid)
        playerMatchesDetails.append({
            'champ': this_participant['championId'],
            'kda': this_participant['challenges']['kda'],
            'win': this_participant['win']
        })
    print('')
    return playerMatchesDetails

def trimmed_average(lst):
    '''Return the average trimmed by 2 standard deviations'''
    elements = np.array(lst)
    
    # Calculate the mean and standard deviation of the elements
    mean = np.mean(elements, axis=0)
    sd = np.std(elements, axis=0)
    
    # Create a new list by filtering out elements that fall within two standard deviations from the mean
    final_list = [x for x in lst if (x > mean - 2 * sd)]
    final_list = [x for x in final_list if (x < mean + 2 * sd)]
    
    # Calculate the average of the filtered elements
    
    return round(np.average(np.array(final_list)), 3)


def get_winrate(wins, losses):
    return round((wins/(max(1,wins+losses)))*100)

def get_kda_and_winloss(list_of_match_details, champion_id):
    wins, losses, champ_wins, champ_losses, kda, champ_kda = 0, 0, 0, 0, [], []
    for match in list_of_match_details:
        champ_id_matching = match['champ'] == champion_id
        if match['win']:
            wins += 1
            if champ_id_matching: champ_wins += 1
        else:
            losses += 1
            if champ_id_matching: champ_losses += 1
        kda.append(match['kda'])
        if champ_id_matching:
            champ_kda.append(match['kda'])
    return wins, losses, champ_wins, champ_losses, kda, champ_kda

def count_streak(DetailsByMatchlist):
    first_value = DetailsByMatchlist[0]['win']
    count = 0
    for i in DetailsByMatchlist:
        if i['win'] == first_value:
            count += 1
        else:
            break
    return count if first_value else -count

def get_collected_info_by_champ(DetailsByMatchlist, champId):
    wins, losses, champ_wins, champ_losses, kda, champ_kda = get_kda_and_winloss(DetailsByMatchlist, champId)
    streak = count_streak(DetailsByMatchlist)
    winrate = get_winrate(wins, losses)
    champ_winrate = get_winrate(champ_wins, champ_losses)
    avgKda = trimmed_average(kda)
    champ_avgKda = trimmed_average(champ_kda)
    # if a player hasn't played the current champion recently we can't calculate champion-specific kda and use general kda instead
    if np.isnan(champ_avgKda): champ_avgKda = avgKda
    consistency = round(((champ_wins+champ_losses)/(wins+losses))*100)
    
    return {
        'winrate': winrate,
        'champ_winrate': champ_winrate,
        'avgKda': avgKda,
        'champ_avgKda': champ_avgKda,
        'streak': streak,
        'consistency': consistency
        }

def analyze_match(match_id):
    print(f'[{match_id}] Going to analyze match')
    while True:
        try:
            myGame = analyze_game(match_id)
        except ApiError as err:
            handle_api_error(err)
            continue
        break
    
    print(f'[{match_id}] Analysis completed')
    update_status(f'[{match_id}] Successfully added to csv')
    return myGame

def write_to_csv(filename, data, firstrun):
    f_mode = 'w' if firstrun else 'a'
    with open(filename, f_mode, newline='') as f:
        w = csv.DictWriter(f, data.keys(), delimiter=';')
        if firstrun:
            w.writeheader()
        w.writerow(data)

def main():
    filename = f'output_{int(time.time())}.csv'
    firstrun = True
    mf = open(os.path.join(os.path.dirname(__file__), 'matches_002.txt'))
    matchesFromFile = mf.readlines()
    for mt in matchesFromFile:
        match_id = mt.strip()
        analyzed_match = analyze_match(match_id)
        write_to_csv(filename, analyzed_match, firstrun)
        firstrun = False

main()