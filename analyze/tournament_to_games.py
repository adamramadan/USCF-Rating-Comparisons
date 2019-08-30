import pandas
import numpy as np
import os
import elo_location_comparison
import player_state_dict


def create_games_df(tournaments, out_dir_fname, saving=False):
    """
    Parameters:
        tournaments - string, directory of pickles where each contains dataframe of games that occured in a tournament
        out_dir - string, directory to place output games dataframe 
    """
    files = os.listdir(tournaments)
    all_games = []
    count = 0
    for f in files:
        count += 1

        df = pandas.read_pickle(tournaments+f)

        if not df.empty:
            if not df.games.empty:
                for i in range(df.shape[0]):
                    if not df.games[i].empty:
                        temp = df.games[i].to_numpy().tolist()
                        tourn_id = f.strip('.pkl')
                        for j in range(len(temp)):
                            temp[j].append(tourn_id)
                        all_games.append(temp)

    all_games = np.vstack(all_games).tolist()

    for i in range(len(all_games)):
        print(i)
        try:
            my_state = player_state_dict[all_games[i][0]]
            opp_state = player_state_dict[all_games[i][1]]
        except KeyError:
            continue
        if (not isinstance(my_state, str)) or (not isinstance(opp_state, str)):
            continue
        my_state = my_state.strip('()')
        opp_state = opp_state.strip('()')
        all_games[i].append(my_state)
        all_games[i].append(opp_state)

    all_games = pandas.DataFrame(all_games, index=range(len(all_games)), columns=[
        'id_a', 'id_b', 'rating_a', 'rating_b', 'result', 'time_control', 'tourny_id', 'state_a', 'state_b'])
    new_cols = ['state_a', 'state_b', 'rating_a',
                'rating_b', 'result', 'time_control', 'tourny_id']
    all_games = all_games[new_cols]

    slimmed_games = all_games[['state_a', 'state_b',
                               'rating_a', 'rating_b', 'result', 'tourny_id']]

    if saving:
        slimmed_games.to_pickle(out_dir_fname+'.pkl')

    return slimmed_games
