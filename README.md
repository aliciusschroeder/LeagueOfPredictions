# LeagueOfPredictions: Predictive Analytics for League of Legends

LeagueOfPredictions is an experimental project for League of Legends players that aims to predict the outcome of games during the "Pick & Ban Phase" with higher accuracy than the expected 50% chance based on the elo system. By factoring in player's recent performance, proficiency with chosen champions, and team compatibility, it aims to provide an advantage for players to strategically decide whether to continue or dodge a game, ultimately improving their ranking.

## 📚 Table of Contents

- [The Underlying Idea](#-the-underlying-idea)
- [Achievements So Far](#-achievements-so-far)
- [Project Overview](-#project-overview)
- [Technical Explanation](#-technical-explanation)
  - [Data Collection](#data-collection)
    - [gather_match_ids.py](#gathermatchidspy)
    - [build_training_data.py](#buildtrainingdatapy)
    - [separate_teams_and_outcomes.py](#separateteamsandoutcomespy)
  - [Training & Validation](#training--validation)
    - [train.py](#trainpy)
    - [validate.py](#validatepy)
  - [Prediction](#prediction)
    - [prediction.py](#predictionpy)
  - [Prerequisites](#prerequisites)
  - [Usage](#usage)
- [Disclaimer](#-disclaimer)
- [Thought-Provoking Questions](#-thought-provoking-questions)
- [Contributions / Your turn!](#-contributions--your-turn)


## 🧠 The Underlying Idea

In League of Legends, players are matched based on their preferred role and their elo - a rating system designed to estimate a player's skill level. While the elo system is designed to ensure a long-term win chance of exactly 50%, it has its limitations. It does not account for subtle yet influential variables like the player's current mood, the level of proficiency on the champion they have chosen for the match, or their compatibility with their team's playstyle.

This is where LeagueOfPredictions steps in. It aims to fill the gap left by the elo system by providing a sophisticated model that leverages these variables. Players are equipped with this information during the "Pick & Ban Phase" - a critical stage where a player can opt to leave the game, incurring a loss of only a tenth of the ranking ladder points they would lose in the event of a lost game. An accurate prediction model can provide a significant advantage, enabling players to make informed decisions and navigate their way up the ranking ladder effectively.

## 🏆 Achievements So Far

Our project, though still in the experimental phase, has shown promising results. We have trained the model on 3,000 datasets and managed to achieve an accuracy of 87.9% for predicting outcomes of ranked games in silver elo. This accuracy far surpasses the expected 50%, paving the way for a player to improve their rank by strategically choosing whether to play or dodge games. It also provides us with a concrete basis for further improvements and refinements in the model.

## 📋 Project Overview

LeagueOfPredictions consists of three key stages: 

1. **Data Collection** - This stage involves a rigorous process of gathering match data through Riot Games API, calculating summoner and champion-specific performance scores, and establishing various metrics that form the base of our predictive model.
2. **Training & Validation** - Using tabular data for binary classification (win/loss) and testing the model.
3. **Prediction** - Deploying an assistant that predicts the win/loss probability based on user inputs and then helping the user decide whether to continue with the game.

## 💻 Technical Explanation

### Data Collection

The data collection process is a crucial step in our project, laying the foundation for the later stages of analysis and prediction. It involves using a suite of Python scripts to interact with the Riot Games API and gather relevant game data.

- **gather_match_ids.py**: This script uses the RiotWatcher API to gather a list of League of Legends Match-ID's.
- **build_training_data.py**: A central part of the data collection process, this script defines the LeagueAnalyzer class. The purpose of this class is to analyze LoL games in depth, gathering data on summoners, champions, and game outcomes. The core functionality is extracting information about the summoners and their champions for a given match ID, and analyzing past matches of these summoners to calculate performance metrics. The script consolidates all the gathered and analyzed data into an output file, ready for the next stage of the project.
- **separate_teams_and_outcomes.py**: Helper script that splits the output csv files into the appropriate format for further processing.

### Training & Validation

- **train.py**: This script is responsible for training our model using the data gathered and processed in the previous stage.
- **validate.py**: After training, this script validates the model, helping to refine and improve its accuracy.

### Prediction

- **prediction.py**: A tool to predict the game's outcome during champ-select based on summoner performance and their picked champions.

### Prerequisites

To run this project, you will need access to the Riot Games API. Access is easily granted but, at the time of writing, the number of requests is very limited.

[RiotWatcher](https://github.com/pseudonym117/Riot-Watcher) is used as a thin wrapper on top of the [Riot Games API for League of Legends](https://developer.riotgames.com/).

To install RiotWatcher:

    pip install riotwatcher
    
### Usage

Here's the rough workflow of how to use the scripts. Keep in mind that this repository is still in the experimental phase and no 1Click-run-to-finish solution is provided yet:

1. Gather match IDs:
   ```
   python gather_match_ids.py
   ```
2. Build the training data:
   ```
   python build_training_data.py
   ```
3. Separate teams and outcomes:
   ```
   python separate_teams_and_outcomes.py
   ```
4. Train the model:
   ```
   python train.py
   ```
5. Validate the model:
   ```
   python validate.py
   ```
6. Make predictions:
   ```
   python prediction.py
   ```

## ❗ Disclaimer

This project is purely an experiment driven by scientific curiosity and the love for the game. It is in no way intended to provide an unfair advantage to players in League of Legends or inflict harm on Riot Games. 

This project was build in compliance with Riot Games' "Legal Jibber Jabber" policy using assets owned by Riot Games. Riot Games does not endorse or sponsor this project. Any trademark terms used in this repository are for informational purposes only and belong to their respective owners.

## 💭 Thought-Provoking Questions

Embarking on this journey has brought forth some interesting philosophical and practical questions. 
- If a player, equipped with the knowledge of the likely game outcome, decides to play regardless, would this awareness influence their in-game decisions and tactics? 
- How would this newfound knowledge change their interaction with teammates or opponents? 
- If such predictive models become mainstream in the gaming world, what implications would it have on the landscape of e-sports? 
- Would it lead to more strategic gameplay, or would it distort the spirit of competition?

## 🙌 Contributions / Your turn!
Contributions to LeagueOfPredictions are greatly appreciated! A lot of things are still on my ToDo-List and I welcome any suggestions for improvement, new ideas, challenges to my assumptions, additional data points, or analyses of the importance of various factors.

I encourage you to participate and share your insights. If you find this repository interesting or inspiring, please let me know! 

Together we can deepen our understanding of predictive analytics in gaming!
