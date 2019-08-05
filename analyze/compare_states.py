import pandas
import numpy as np
import string

data_path = data_path = 'C:\\Users\\AdamsPC\\Projects\\USCF-Rating-Comparisons\\data\\'

games_df = pandas.read_pickle(data_path + 'games\\slimmed_games\\3074587.pkl')

temp = games_df.to_numpy()

trimmed = []

for x in temp:
    if isinstance(x[0], str) and isinstance(x[1], str):
        x[0] = x[0].strip('()')
        x[1] = x[1].strip('()')

        if any([char not in string.digits for char in x[2].strip()]):
            continue
        if any([char not in string.digits for char in x[3].strip()]):
            continue

        x[-1] = x[-1].strip()[:4]

        


        trimmed.append(x)

games_df = pandas.DataFrame(trimmed, index=range(len(trimmed)), columns=['state_a', 'state_b', 'rating_a', 'rating_b', 'result', 'tourny_id'])
games_df['tourny_id'] = pandas.to_numeric(games_df['tourny_id'])

STATES=['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL',
        'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT',
        'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI',
        'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

combinations = []
state_only = []
for state in STATES:
    total_points_gained = 0
    total_samples = 0
    # state_df = games_df[games_df.a_state == state]
    for other_state in STATES:

        if state == other_state:
            continue


        

        pair_df = games_df[ (games_df.state_a == state) & (games_df.state_b == other_state)]



        if not pair_df.empty:
            try:
                pair_df['rating_a'] = pandas.to_numeric(pair_df['rating_a'])
                pair_df['rating_b'] = pandas.to_numeric(pair_df['rating_b'])
                pair_df['result'] = pandas.to_numeric(pair_df['result'])
            except ValueError:
                continue



            pair_values = pair_df[['rating_a', 'rating_b', 'result']].to_numpy()

            my_range = [1800, 3000]

            mask = np.where(np.logical_and(pair_values[:,1] >= my_range[0], pair_values[:,1] <= my_range[1]))

            pair_values = pair_values[mask]

            mask = np.where(np.logical_and(pair_values[:,0] >= my_range[0], pair_values[:,0] <= my_range[1]))

            pair_values = pair_values[mask]

            if not pair_values.shape[0]:
                continue
            expected_score = 1 / (1 + (10**    ((pair_values[:, 1] - pair_values[: , 0]) / 400.0  )        ))

            if np.amax(expected_score) > 1:
                exit()


            points_gained = pair_values[:,2] - expected_score
            samples = points_gained.shape[0]
            combinations.append(
                [state, other_state, np.mean(points_gained), samples])

            total_points_gained += np.sum(points_gained)

            total_samples += len(points_gained)
            
    state_only.append([total_points_gained/total_samples, total_samples])
states = pandas.DataFrame(state_only, index=STATES, columns=['spread', 'num_samples'])
combinations=pandas.DataFrame(combinations, index = range(len(combinations)), columns = [
                              'state', 'opposing_state', 'spread', 'num_samples'])
