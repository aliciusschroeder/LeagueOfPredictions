import os
import csv
import time
import datetime
import configparser

import numpy as np

from riotwatcher import LolWatcher, ApiError


class LeagueAnalyzer:
    # Constants for debug levels
    DEBUG_LEVEL_DEBUG = 1
    DEBUG_LEVEL_INFO = 2
    DEBUG_LEVEL_WARNING = 3
    DEBUG_LEVEL_ERROR = 4
    DEBUG_LEVEL_VERBOSE = 5

    # Constant for queue type
    # 420 = Ranked 5v5 Solo Queue. 
    # Full list of queue types at: https://static.developer.riotgames.com/docs/lol/queues.json
    QUEUE_TYPE_RANKED_SOLO = 420

    def __init__(self, config_file="config.ini", api_key=None, server_region='euw1', max_age_days=14, search_depth=3, queue_type=QUEUE_TYPE_RANKED_SOLO, debug_level=DEBUG_LEVEL_INFO):
        # cutoff creation date during match analysis (to exclude matches in the future)
        self.DEBUG_LEVEL = debug_level
        self.SERVER_REGION = server_region
        # Calculate cutoff UNIX timestamp based on max_age_days
        self.MATCHES_MAX_AGE = int(time.mktime((datetime.date.today() - datetime.timedelta(days=max_age_days)).timetuple()))
        self.MATCH_HISTORY_SEARCH_DEPTH = search_depth
        
        self.QUEUE_TYPE = queue_type
        self.PLAYER_ATTRIBUTES = ['winrate', 'champ_winrate', 'avgKda', 'champ_avgKda', 'streak', 'consistency', 'champMastery']

        self.API_KEY = api_key

        self.load_config(config_file)
        self.current_match_creation_date = 0
        self.lol_watcher = LolWatcher(self.API_KEY)

    def load_config(self, filename):
        config = configparser.ConfigParser()
        config.read('config.ini')
        if self.API_KEY == None: self.API_KEY = config['DEFAULT']['API_KEY']

    def handle_api_error(self, err):
        '''Handles different Riot API errors and prints appropriate messages'''
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

    
    def update_status(self, status_message):
        '''Prints an updated status message during the analysis process'''
        print(f'\r{status_message}', end='', flush=True)


    def analyze_game(self, match_id):
        """Analyzes a League of Legends game by retrieving information about summoners and their champions.

        Args:
            match_id (int): The ID of the game to be analyzed.

        Returns:
            dict: A dictionary containing the analyzed information for the game. The dictionary includes the following keys:
                - 'id': The ID of the analyzed match.
                - 'win': Indicates the result of the game. 0 represents a win for summoners 1-5. 1 represents a win for summoners 6-10, and 'ERR' indicates an error in determining the result.
                - For each summoner in the game (up to 10 summoners), the following keys are included:
                    - 'summoner_X_winrate': The overall win rate of the summoner (X represents the summoner number).
                    - 'summoner_X_champ_winrate': The win rate of the summoner on the champion they played.
                    - 'summoner_X_avgKda': The average KDA (Kill/Death/Assist ratio) of the summoner.
                    - 'summoner_X_champ_avgKda': The average KDA of the summoner on the champion they played.
                    - 'summoner_X_streak': The latest unbroken streak of wins or losses for the summoner.
                    - 'summoner_X_consistency': The consistency of the summoner's champion pick as a percentage.
                    - 'summoner_X_champMastery': The mastery points of the summoner on the champion they played.

        Raises:
            ApiError: If there is an error while retrieving data from the League of Legends API.

        Note:
            - This function depends on other helper methods within the LeagueAnalyzer class to retrieve the necessary information.
            - The summoners are numbered from 1 to 10 based on their order in the game. Only available summoners will have their data analyzed.
            - The 'win' key represents the result of the game. 0 represents a win for summoners 1-5. 1 represents a win for summoners 6-10, and 'ERR' indicates an error in determining the result.
        """
        summoners_and_champ = self.get_summoners_and_champ(match_id) # returns summoner details numbered 0-9

        # we don't want to include the current match in past-game analysis
        excluded_matches = [match_id]

        game = {'id': match_id}

        summoners = []
        for summoner_count, summoner in enumerate(summoners_and_champ, start=1):
            if self.DEBUG_LEVEL <= self.DEBUG_LEVEL_DEBUG: print(f'[{summoner_count}/10] Analyzing summoner')
            summoners.append(self.analyze_summoner(summoner, excluded_matches))


        if summoners_and_champ[4]['win']==summoners_and_champ[5]['win']:
            win = "ERR"
        else:
            win = 0 if summoners_and_champ[4]['win'] else 1

        for summoner_nr, summoner in enumerate(summoners, start=1):
            for attribute in self.PLAYER_ATTRIBUTES:
                key = f'summoner_{summoner_nr}_{attribute}'
                game[key] = summoner[attribute]
        game['win'] = win
        return game


    def analyze_summoner(self, summoner_data, excluded_matches):
        '''Analyzes a summoner's past matches and calculates various performance metrics'''
        past_match_ids = self.get_past_match_ids(summoner_data['puuid'], excluded_matches)
        details = self.get_details_by_matchlist(past_match_ids, summoner_data['puuid'])
        if len(details) > 0:
            champion_performance = self.get_collected_info_by_champ(details, summoner_data['champ'])
        else:
            champion_performance = {}
            for a in self.PLAYER_ATTRIBUTES:
                champion_performance[a] = 'EMPTY'
                if self.DEBUG_LEVEL <= self.DEBUG_LEVEL_DEBUG: print('- NO PAST MATCHES FOR THIS SUMMONER -'*2)
        champion_performance['champMastery'] = self.get_champion_mastery(summoner_data['sid'], summoner_data['champ'])
        return champion_performance


    def get_champion_mastery(self, sId, championId):
        '''Retrieves a summoner's mastery points (proprietary Riot Games metric) for a specific champion'''
        return self.lol_watcher.champion_mastery.by_summoner_by_champion(self.SERVER_REGION, sId, championId)['championPoints']

    def get_summoners_and_champ(self, match_id):
        '''Retrieves information about summoners and their champions in a certain
        match Returns a list of dictionaries, each representing one summoner who 
        participated in the given match. Dictionary attributes include per 
        summoner: puuid, championId, summonerId and whether they won.'''

        match = self.get_match(match_id)
        self.current_match_creation_date = int(match['info']['gameCreation'] / 1000)
        summoners_and_champs = []
        for summoner in match['info']['participants']:
            summoners_and_champs.append({
                'puuid': summoner['puuid'],
                'champ': summoner['championId'],
                'sid': summoner['summonerId'],
                'win': summoner['win']
            })
        return summoners_and_champs



    def get_past_match_ids(self, puuid, excluded_matches):
        '''Return a list of id's from past matches of a summoner identified by his puuid'''
        matchlist = self.lol_watcher.match.matchlist_by_puuid(self.SERVER_REGION, puuid, start_time = self.MATCHES_MAX_AGE, queue = self.QUEUE_TYPE, count = self.MATCH_HISTORY_SEARCH_DEPTH, end_time = self.current_match_creation_date)
        matchlist = [i for i in matchlist if not i in excluded_matches or excluded_matches.remove(i)]
        return matchlist


    def get_match(self, match_id):
        '''Retrieves details of a specific match from Riot API'''
        while True:
            try:
                req_match = self.lol_watcher.match.by_id(self.SERVER_REGION, match_id)
            except ApiError as err:
                self.handle_api_error(err)
                continue
            break
        return req_match


    def extract_participant_from_match(self, match, puuid):
        '''Extracts a specific participant's information from a match'''
        return next((participant for participant in match['info']['participants'] if participant['puuid'] == puuid), None)


    def get_details_by_matchlist(self, match_ids_list, puuid):
        """Retrieves match details for a given list of match IDs and a summoner's PUUID.    

        Args:
            match_ids_list (list): A list of match IDs to retrieve details for.
            puuid (str): PUUID (Player Universally Unique Identifier) of the summoner.
            
        Returns:
            list: A list of dictionaries representing match details for the summoner. Each dictionary contains the following keys:
                - champ (int): Champion ID played in the match.
                - kda (str): Kill/Death/Assist ratio for the summoner in the match.
                - win (bool): Indicates whether the summoner won the match.
        """
        details_of_player = []
        matches_total = len(match_ids_list)
        for match_count, match_id in enumerate(match_ids_list, start=1):
            if self.DEBUG_LEVEL <= self.DEBUG_LEVEL_DEBUG: self.update_status(f'[{match_count}/{matches_total}] GetDetailsByMatchlist')
            match_details = self.get_match(match_id)
            this_participant = self.extract_participant_from_match(match_details, puuid)
            details_of_player.append({
                'champ': this_participant['championId'],
                'kda': this_participant['challenges']['kda'],
                'win': this_participant['win']
            })
        if self.DEBUG_LEVEL <= self.DEBUG_LEVEL_DEBUG: print('')
        return details_of_player

    def trimmed_average(self, values_list):
        '''Return the average trimmed by 2 standard deviations, return 0 if
        list is empty. No trimming if it would reduce sample size to 0'''

        if len(values_list) == 0: return 0.0
        
        elements = np.array(values_list)
        
        # Calculate the mean and standard deviation of the elements
        mean = np.mean(elements, axis=0)
        sd = np.std(elements, axis=0)
        
        # Create a new list by filtering out elements that fall within two standard deviations from the mean
        final_list = [x for x in values_list if (x > mean - 2 * sd)]
        final_list = [x for x in final_list if (x < mean + 2 * sd)]
        
        if len(final_list) == 0: final_list = values_list

        # Calculate the average of the filtered elements
        return round(np.average(np.array(final_list)), 3)


    def get_winrate(self, wins, losses):
        '''Calculates the win rate based on the number of wins and losses'''
        return round((wins/(max(1,wins+losses)))*100)

    def get_kda_and_winloss(self, match_details_list, champion_id):
        """Calculates the number of wins, losses, and KDA (Kill/Death/Assist) statistics for a specific champion.

        Args:
            match_details_list (list): List of match details containing champion performance information.
            champion_id (int): ID of the champion for which the statistics are calculated.

        Returns:
            tuple: A tuple containing the following information:
                - wins (int): Number of wins for the summoner.
                - losses (int): Number of losses for the summoner.
                - champ_wins (int): Number of wins specifically with the champion.
                - champ_losses (int): Number of losses specifically with the champion.
                - kda (list): List of KDA values for all matches.
                - champ_kda (list): List of KDA values specifically with the champion.
        """
        wins, losses, champ_wins, champ_losses, kda, champ_kda = 0, 0, 0, 0, [], []
        for match in match_details_list:
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

    def count_streak(self, match_details_list):
        '''Calculate latest unbroken streak of wins/losses'''
        first_value = match_details_list[0]['win']
        streak_count = 0
        for match in match_details_list:
            if match['win'] == first_value:
                streak_count += 1
            else:
                break
        return streak_count if first_value else -streak_count

    def get_collected_info_by_champ(self, match_details_list, champ_id):
        """Collects various performance information for a specific champion.

        Args:
            match_details_list (list): List of dictionaries containing match details.
                                    Each dictionary represents a match and should
                                    have 'champ', 'kda', and 'win' keys.
            champ_id (int): The champion ID for which to collect the information.

        Returns:
            dict: A dictionary containing the collected performance information for
                the specified champion. The dictionary includes the following keys:
                - 'winrate': The overall win rate of the player.
                - 'champ_winrate': The win rate specifically for the champion.
                - 'avgKda': The average KDA (Kill/Death/Assist) ratio of the player.
                - 'champ_avgKda': The average KDA ratio specifically for the champion.
                - 'streak': The latest unbroken streak of wins (positive value) or losses (negative value).
                - 'consistency': The percentage of games played with the champion
                                compared to the total number of games played.

        Note:
            If a player hasn't played the current champion recently, the 'champ_avgKda'
            value will be equal to 'avgKda' since champion-specific KDA cannot be calculated.

        """
        wins, losses, champ_wins, champ_losses, kda, champ_kda = self.get_kda_and_winloss(match_details_list, champ_id)
        streak = self.count_streak(match_details_list)
        winrate = self.get_winrate(wins, losses)
        champ_winrate = self.get_winrate(champ_wins, champ_losses)
        avgKda = self.trimmed_average(kda)
        champ_avgKda = self.trimmed_average(champ_kda)
        # if a player hasn't played the current champion recently we can't 
        # calculate champion-specific kda and use general kda instead
        if np.isnan(champ_avgKda): champ_avgKda = avgKda
        champion_playrate = round(((champ_wins+champ_losses)/(wins+losses))*100)
        
        return {
            'winrate': winrate,
            'champ_winrate': champ_winrate,
            'avgKda': avgKda,
            'champ_avgKda': champ_avgKda,
            'streak': streak,
            'consistency': champion_playrate
            }

    def analyze_match(self, match_id):
        '''Analyzes match_id via analyze_game() plus Error-handling and Debugging'''
        if self.DEBUG_LEVEL <= self.DEBUG_LEVEL_INFO: print(f'[{match_id}] Going to analyze match')
        while True:
            try:
                myGame = self.analyze_game(match_id)
            except ApiError as err:
                self.handle_api_error(err)
                continue
            break
        
        if self.DEBUG_LEVEL <= self.DEBUG_LEVEL_INFO: print(f'[{match_id}] Analysis completed')
        if self.DEBUG_LEVEL <= self.DEBUG_LEVEL_INFO: self.update_status(f'[{match_id}] Successfully added to csv')
        return myGame

    def write_to_csv(self, filename, data, firstrun):
        f_mode = 'w' if firstrun else 'a'
        with open(filename, f_mode, newline='') as f:
            w = csv.DictWriter(f, data.keys(), delimiter=';')
            if firstrun:
                w.writeheader()
            w.writerow(data)

    def start_analysis_process(self, inputfile= 'matches_002.txt', outputfile = f'output_{int(time.time())}.csv'):
        firstrun = True
        matchlist_file = open(os.path.join(os.path.dirname(__file__), inputfile))
        matches_from_file = matchlist_file.readlines()
        for match_id in matches_from_file:
            analyzed_match = self.analyze_match(match_id.strip())
            self.write_to_csv(outputfile, analyzed_match, firstrun)
            firstrun = False

if __name__ == '__main__':
    analyzer = LeagueAnalyzer()
    print(analyzer.API_KEY)
    analyzer.start_analysis_process()