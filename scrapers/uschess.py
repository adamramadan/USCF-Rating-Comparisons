import requests
import pandas
from bs4 import BeautifulSoup
import pdb
from html.parser import HTMLParser
from collections import namedtuple
import csv
import numpy as np
import string

# FIXME R's reader read_table function can replace most of this function
def scrape_players(start=1, stop=10003, saving=False, out_dir=None):
    base_url = 'http://www.uschess.org/assets/msa_joomla/MbrLst.php?*,*;'
    NUM_PAGES = stop
    HEADERS_ROW = 2
    NUM_FIELDS_BEFORE_NAME = 6

    BAD_WORDS = ['Dupl', '(  )']

    def scrape_player_page(page):
        data = requests.get(base_url + str(page))

        soup = BeautifulSoup(data.text, 'lxml')

        # player table is a <pre> object, should be single on page
        test_table = pandas.read_csv(soup.find('pre').text)
        print(test_table)
        rows = soup.find('pre').text.split('\n')
        for idx, row in enumerate(rows):
            if any(word in row for word in BAD_WORDS):
                del rows[idx]
                continue
            rows[idx] = rows[idx].split()

        rows = rows[HEADERS_ROW:]  # trim top headers of table
        if rows[-1] == []:
            del rows[-1]  # seems to be an empty list on last element

        for row in rows:
            temp = row[:NUM_FIELDS_BEFORE_NAME]
            temp.extend([''.join(row[NUM_FIELDS_BEFORE_NAME:])])

        return temp

    players = []

    for page in range(1, NUM_PAGES+1):
        players.extend(scrape_player_page(page))

    df = pandas.DataFrame(players, index=len(players), columns=[
                          'ID', 'State', 'Exp Date', 'Reg', 'Quick', 'Blitz', 'Name'])

    if saving:
        df.to_pickle(out_dir + 'player_data.pkl')

    return df


def create_tournament_list(df_path, saving=False, out_dir=None):
    """for player name in dataset, go to tournament history page,
        for each tournament they played in,
        if that tournament is not in our tournament database,
        append it
        Leaves us with full list of tournament IDs for later parser
    """
    
    df = pandas.read_pickle(df_path)

    base_url = "http://www.uschess.org/msa/MbrDtlTnmtHst.php?"
    ids = (x for x in df.id)

    TOURN_OFFSET = 10  # row.text returns something like '2015-03-8201503089742'
    # where first 10 chars are date

    tournaments = []
    count = 1
    for count, ID in enumerate(ids):
        url = base_url + ID

        data = requests.get(url)

        soup = BeautifulSoup(data.text, 'lxml')

        # empirical 120 width for rows so we search for that
        rows = soup.findAll('td', {'width': 120})
        if rows:
            temp = [tourn.text[TOURN_OFFSET:] for tourn in rows]
            for tourn in temp:
                if tourn not in tournaments:
                    tournaments.append(tourn)

        # currently for QA purposes
        check_point = 1000
        if count % check_point == 0:
            np.save(str(count)+'_tournaments', tournaments)

    if saving:
        np.save(out_dir + 'all_tournaments.npy', tournaments)

    return tournaments


def scrape_tournament(tournament_id, matches=None):
    unwanted_chars = ''.join(
        [x for x in tournament_id if x not in string.digits])

    tournament_id = tournament_id.strip(unwanted_chars)
    tournament_id = str(int(tournament_id))
    base_url = 'http://www.uschess.org/assets/msa_joomla/XtblMain.php?'

    # .0 flag flattens tournament into one section
    url = base_url + tournament_id + '.0'

    data = requests.get(url)
    soup = BeautifulSoup(data.text, 'lxml')

    if matches:
        if not any([word in soup.text for word in matches]):
            return None

    table = soup.find('pre')

    if table is None:
        return table

    table = table.text.split('\n')

    def raw_parse_table(table):
        player = namedtuple(
            'player', ['id', 'placement', 'score', 'progression', 'results'])
        players = []

        def parse_name_row(row):
            SEED_IDX = 0
            SCORE_IDX = 2
            GAMES_IDX_START = 3
            row = row.replace(' ', '').split('|')
            possible_results = ('W', 'L', 'D')
            seed = row[SEED_IDX]
            try:
                score = row[SCORE_IDX]
            except IndexError:
                pdb.set_trace()
            results = []
            for x in row[GAMES_IDX_START:]:
                if any(result in x for result in possible_results):
                    results.append(x)
            return seed, score, results

        def parse_id_row(row):
            STATE_IDX = 0

            row = row.replace(' /', '').split('|')

            state = row[STATE_IDX]

            row = row[1].split(':')

            ID = row[0]

            try:
                progression = row[1]
            except IndexError:
                progression = 'NaN'
            return state, ID, progression

        found_pair = False
        found_num = False

        for i in range(len(table)-1):
            if 'Pair' in table[i]:
                found_pair = True
            if 'Num' in table[i+1]:
                found_num = True
                num_idx = i+1
                # num_col = table[i+1].find('Num')
                if found_pair and found_num:
                    break
            else:
                found_pair = False

        if found_pair and found_num:
            start_of_table = num_idx

        else:
            return None

        table = table[start_of_table:]

        printing = 0
        if printing:
            for x in table:
                print(x)
        current_placement = 1

        i_iter = iter(range(len(table)))
        for i in i_iter:  # while loop here because we increment i later
            # placement should be around 0->8
            if str(current_placement) in table[i][:8]:
                split = table[i].split('|')
                if ['F' in col for col in split[2:]][0]:

                    current_placement += 1
                    continue
                if 'NOSHOW/UNKNOWN' in table[i]:
                    current_placement += 1
                    continue
                needed_chars = 'RQB'
                if not any(char in table[i+1] for char in needed_chars):
                    continue
                seed, score, results = parse_name_row(table[i])
                _, ID, progression = parse_id_row(table[i+1])
                if 'R' in ID:
                    ID = ID.strip('R')
                    progression = 'R ' + progression
                elif 'Q' in ID:
                    ID = ID.strip('Q')
                    progression = 'Q ' + progression
                elif 'B' in ID:
                    ID = ID.strip('B')
                    progression = 'B' + progression
                temp_player = player(ID, seed, score, progression, results)
                players.append(temp_player)
                current_placement += 1
                i_iter.__next__()

        return players

    # needed a quick container for players and games
    # a bit messy but it will suffice for now
    class Player():
        def __init__(self, ID, placement, score, progression, results):
            self.ID = ID
            self.placement = placement
            self.score = score
            self.progression = progression
            self.results = results

    class Game():
        def __init__(self, my_id, opp_id, my_rating, opp_rating, result, time_control):
            self.my_id = my_id
            self.opp_id = opp_id
            self.my_rating = my_rating
            self.opp_rating = opp_rating
            self.result = result
            self.time_control = time_control

    def clean_up_raw_parse(players):
        new_players = [Player(*player) for player in players]

        # df = pandas.DataFrame(players
        # num_players = df.seed.astype(int).max()

        players = new_players

        game_t = namedtuple('game_t', [
            'my_id', 'opponent_id', 'my_rating', 'opponent_rating', 'result', 'time_control'])

        player_t = namedtuple(
            'player_t', ['ID', 'placement', 'score', 'progression', 'games'])

        for p_idx, player in enumerate(players):
            games = []
            for result in player.results:
                opp_idx = result.strip(string.ascii_letters)
                for k, _ in enumerate(players):
                    if opp_idx == players[k].placement:
                        opp = players[k]

                try:
                    test = opp
                except UnboundLocalError:
                    continue

                my_id = player.ID.strip()
                opp_id = opp.ID.strip()
                my_rating = player.progression.split('->')[0]
                opp_rating = opp.progression.split('->')[0]

                if 'R' in my_rating:
                    my_rating = my_rating.strip('R')
                    opp_rating = opp_rating.strip('R')
                    time_control = 'standard'

                elif 'Q' in my_rating:
                    my_rating = my_rating.strip('Q')
                    opp_rating = opp_rating.strip('Q')
                    time_control = 'quick'

                elif 'B' in my_rating:
                    my_rating = my_rating.strip('B')
                    opp_rating = opp_rating.strip('Q')
                    time_control = 'blitz'

                else:
                    time_control = 'unknown'

                if 'W' in result:
                    score = 1.0

                elif 'L' in result:
                    score = 0.0

                elif 'D' in result:
                    score = 0.5

                else:
                    score = 'NaN'

                game = Game(my_id, opp_id, my_rating,
                            opp_rating, score, time_control)

                games.append(game)

            game_tuples = []

            for game in games:
                game_tuples.append(game_t(game.my_id, game.opp_id, game.my_rating,
                                          game.opp_rating, game.result, game.time_control))

            setattr(players[p_idx], 'games', pandas.DataFrame(game_tuples))

        players_t = []

        for player in players:
            players_t.append(player_t(
                player.ID, player.placement, player.score, player.progression, player.games))

        return pandas.DataFrame(players_t)

    return clean_up_raw_parse(raw_parse_table(table))


def create_tournament_games(tournaments, out_dir, matches, tournament_path):
    for idx, tournament in enumerate(tournaments):
        tournaments[idx] = tournaments[idx].strip(
            ''.join([char for char in tournaments[idx] if char not in string.digits]))
        data = scrape_tournament(tournaments[idx], matches=matches)
        try:
            data.to_pickle(out_dir+tournaments[idx]+matches[0]+'.pkl')

        except AttributeError:
            continue
