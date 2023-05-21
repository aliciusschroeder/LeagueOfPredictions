'''
To use our Riot API contingent effectively we collect data for all 
10 summoners of a match. But when training and predicting we look 
only on one team. This helper file splits a csv file containing 
matches with both teams into a new file where each team is 
represented separately.

Example for easier understanding:
Original file:
+------+----------+----------+----------+----------+-----+
| id   | player 1 | player 2 | player 3 | player 4 | win |
+------+----------+----------+----------+----------+-----+
| 0001 | 15       | 20       | 16       | 21       | 0   |
| 0002 | 17       | 18       | 14       | 15       | 0   |
| 0003 | 200      | 250      | 210      | 220      | 1   |
+------+----------+----------+----------+----------+-----+

Separation:
         _______Team A______   ______Team B_______
        |                   | |                   |
+------+----------+----------+----------+----------+-----+
| id   | player 1 | player 2 | player 3 | player 4 | win | <- win == 0: Team A wins, win == 1: Team B wins
+------+----------+----------+----------+----------+-----+
| 0001 | 15       | 20       | 16       | 21       | 0   |
| 0002 | 17       | 18       | 14       | 15       | 0   |
| 0003 | 200      | 250      | 210      | 220      | 1   |
+------+----------+----------+----------+----------+-----+

New file:
+--------+----------+----------+-----+
| id     | player 1 | player 2 | win |
+--------+----------+----------+-----+
| 0001_A | 15       | 20       | 1   |     <- Team A from game 0001
| 0001_B | 16       | 21       | 0   |     <- Team B from game 0001
| 0002_A | 17       | 18       | 1   |
| 0002_B | 14       | 15       | 0   |
| 0003_A | 200      | 250      | 0   |
| 0003_B | 210      | 220      | 1   |
+--------+----------+----------+-----+

real-life columns look more like this: 
id;summoner_1_winrate;summoner_1_champ_winrate;summoner_1_avgKda;
summoner_1_champ_avgKda;summoner_1_streak;summoner_1_consistency;
summoner_1_champMastery;summoner_2_winrate;summoner_2_champ_winrate;
summoner_2_avgKda;summoner_2_champ_avgKda;summoner_2_streak;
summoner_2_consistency;summoner_2_champMastery;summoner_3_winrate;
summoner_3_champ_winrate;summoner_3_avgKda;summoner_3_champ_avgKda;
summoner_3_streak;summoner_3_consistency;summoner_3_champMastery;
summoner_4_winrate;summoner_4_champ_winrate;summoner_4_avgKda;
summoner_4_champ_avgKda;summoner_4_streak;summoner_4_consistency;
summoner_4_champMastery;summoner_5_winrate;summoner_5_champ_winrate;
summoner_5_avgKda;summoner_5_champ_avgKda;summoner_5_streak;
summoner_5_consistency;summoner_5_champMastery;summoner_6_winrate;
summoner_6_champ_winrate;summoner_6_avgKda;summoner_6_champ_avgKda;
summoner_6_streak;summoner_6_consistency;summoner_6_champMastery;
summoner_7_winrate;summoner_7_champ_winrate;summoner_7_avgKda;
summoner_7_champ_avgKda;summoner_7_streak;summoner_7_consistency;
summoner_7_champMastery;summoner_8_winrate;summoner_8_champ_winrate;
summoner_8_avgKda;summoner_8_champ_avgKda;summoner_8_streak;
summoner_8_consistency;summoner_8_champMastery;summoner_9_winrate;
summoner_9_champ_winrate;summoner_9_avgKda;summoner_9_champ_avgKda;
summoner_9_streak;summoner_9_consistency;summoner_9_champMastery;
summoner_10_winrate;summoner_10_champ_winrate;summoner_10_avgKda;
summoner_10_champ_avgKda;summoner_10_streak;summoner_10_consistency;
summoner_10_champMastery;win
'''

import pandas as pd

FILENAME = 'input.csv'

df = pd.read_csv(FILENAME, delimiter=';')

# Filter out rows with 'ERR' in 'win'
df = df[df['win'] != 'ERR']

# Split into Team A and Team B
team_a_cols = [col for col in df.columns if "summoner_" in col and int(col.split('_')[1]) <= 5] + ['id', 'win']
team_b_cols = [col for col in df.columns if "summoner_" in col and int(col.split('_')[1]) > 5] + ['id', 'win']

team_a = df[team_a_cols]
team_b = df[team_b_cols]

# Adjust 'id' and 'win' columns for each team
team_a['id'] = team_a['id'] + "_A"
team_a['win'] = team_a['win'].apply(lambda x: 1 if x == 0 else 0)
team_b['id'] = team_b['id'] + "_B"
team_b['win'] = team_b['win'].apply(lambda x: 1 if x == 1 else 0)

# Rename columns for team_b to match team_a
rename_dict = {col: col.replace(str(int(col.split('_')[1])), str(int(col.split('_')[1])-5)) for col in team_b.columns if 'summoner' in col}
team_b.rename(columns=rename_dict, inplace=True)

# Combine dataframes and sort by 'id'
result = pd.concat([team_a, team_b]).sort_values(by='id')

# Write to new csv file
result.to_csv('new.csv', index=False, sep=';')