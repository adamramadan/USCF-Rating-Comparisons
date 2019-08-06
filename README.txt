# USCF Player Elo State Analysis

This project's goal is to determine if 'Player 1 from State A with elo X' is the same chess strength as 'Player 2 from State B with elo X' 

## Introduction
The United States Chess Federation (USCF) uses the Elo system to rank players. All players start at a predetermined Elo (1200) and 
if gain/lose rating points as they play opponents based on their opponents rating and the score of the game (https://en.wikipedia.org/wiki/Elo_rating_system).

Because the rating change is a function of only one's opponents rating it becomes a measurement of how strong one is in a pool of players.
One could imagine two isolated pools of players with drastic difference in objective skill, but having a similar mean rating.

This project is aimed to determine if these pools occur at a state by state basis i.e. for any state is said state objectively stronger or weaker
than others? 

To determine this we will look at how each state performs when the players play against a player from a different state. 

I.e. if players from state A consistently 'steal' rating points from players of state 'B' (performing at a standard higher 
than their expected performance), then we can say they are 'underrated' (a pool exists)
