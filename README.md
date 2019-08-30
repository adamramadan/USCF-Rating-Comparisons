# USCF Player Elo State Analysis

This project's goal is to determine if 'Player 1 from State A with Elo X' is the same chess strength as 'Player 2 from State B with Elo X' 

## Introduction
The United States Chess Federation (USCF) uses the Elo system to rank players. All players start at a predetermined Elo (1200) and 
gain/lose rating points as they play opponents based on their opponents rating and the score of the game (https://en.wikipedia.org/wiki/Elo_rating_system).

Because the rating change is a function of only one's opponents' rating it becomes a measurement of how strong one is in a pool of players.
One could imagine two isolated pools of players with drastic difference in objective skill, but having a similar mean rating.

This project is aimed to determine if these pools occur at a state by state basis i.e. for any state is said state objectively stronger or weaker
than others? 

To determine this we will look at how each state performs when the players play against a player from a different state. 

I.e. if players from state A consistently 'steal' rating points from players of state 'B' (performing at a standard higher 
than their expected performance), then we can say they are 'underrated' (a pool exists)

## scrapers
This folder contains script to web scrape the corresponding website. The 'uschess' script will contain functions to scrape player/tournament data
which will be saved to panda dataframes locally.

## analyze
Scripts to analyze saved data, including tournament games to flattend games utility (all games played in a list of tournament games), and 
compare states script (the main script to analyze the objective of the project)

## data
Folder for data

Usage Example
```
import elo_location_comparison as elc

out_dir = 'path/to/data/'

#scrapes 10 pages of player data to outdir in pickle named 'player_data.pkl
scrape_players(start=1, stop=10, saving=True, out_dir=out_dir)

saves tournaments to 'all_tournaments.npy')
tournaments = create_tournament_list(out_dir+'player_data.pkl', saving=True, out_dir=out_dir)

city_variable_names = ['NEW YORK,NY', 'NEW YORK, NY'] # check tournament page for possible matches
tournament_games = create_tournament_games(out_dir, matches, out_dir+'all_tournaments.npy')

#save tournament games in a pkl
create_games_df(tournaments, out_dir+'tournament_games'/, city_variable_names, tournament_path)

slimmed_games = elc.tournament_to_games.create_games_df(out_dir+'tournament_games/', out_dir+'slimmed_games/')
spread, _ = elc.compare_states.calculate_spread(out_dir+'slimmed_games/' + states_to_compare='NY')
print(spread.head(3))
#NY   AL   .03
#NY   AK   -.02
#NY   AZ   .04
```