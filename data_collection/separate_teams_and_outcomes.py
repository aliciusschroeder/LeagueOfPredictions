'''
To use our Riot API contingent effectively we collect data for all 10 summoners of a match.
But when training and predicting we look only on one team. This helper file splits a csv
file containing matches with both teams into a new file where each team is represented separately.

Example for easier understanding:
original file:
+------+----------+----------+----------+----------+-----+
| id   | player 1 | player 2 | player 3 | player 4 | win |
+------+----------+----------+----------+----------+-----+
| 0001 | 15       | 20       | 16       | 21       | 0   |
| 0002 | 17       | 18       | 14       | 15       | 0   |
| 0003 | 200      | 250      | 210      | 220      | 1   |
+------+----------+----------+----------+----------+-----+

new file:
+--------+----------+----------+-----+
| id     | player 1 | player 2 | win |
+--------+----------+----------+-----+
| 0001_A | 15       | 20       | 1   |
| 0001_B | 16       | 21       | 0   |
| 0002_A | 17       | 18       | 1   |
| 0002_B | 14       | 15       | 0   |
| 0003_A | 200      | 250      | 0   |
| 0003_B | 210      | 220      | 1   |
+--------+----------+----------+-----+

'''

import pandas as pd

FILENAME = 'input.csv'

# Load the csv file
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