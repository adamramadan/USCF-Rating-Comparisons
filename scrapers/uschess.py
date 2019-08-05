import requests
import pandas
from bs4 import BeautifulSoup
import pdb
from html.parser import HTMLParser
from collections import namedtuple
import csv
import numpy as np
import string


def scrape_players(start=1, stop=10003, saving=False, out_dir=None):
    base_url = 'http://www.uschess.org/assets/msa_joomla/MbrLst.php?*,*;'
    NUM_PAGES = stop

    HEADERS_ROW = 2
    NUM_FIELDS_BEFORE_NAME = 6

    BAD_WORDS = ['Dupl', '(  )']

    players = []

    for page in range(1, NUM_PAGES+1):
        data = requests.get(
            base_url + str(page))

        soup = BeautifulSoup(data.text, 'lxml')
        # player table is a <pre> object, should be single on page
        rows = soup.find('pre').text.split('\n')
        for i in range(len(rows)-1, -1, -1):
            if any(word in rows[i] for word in BAD_WORDS):
                del rows[i]
                continue
            rows[i] = rows[i].split()

        rows = rows[HEADERS_ROW:]  # trim top headers of table
        if rows[-1] == []:
            del rows[-1] # seems to be an empty list on last element

        for i in range(len(rows)):
            temp = rows[i][:NUM_FIELDS_BEFORE_NAME]
            temp.extend([''.join(rows[i][NUM_FIELDS_BEFORE_NAME:])])
            players.append(temp)

    df = pandas.DataFrame(players, index=len(players), columns = ['ID', 'State', 'Exp Date', 'Reg', 'Quick', 'Blitz', 'Name'])

    if saving:
        df.to_pickle(out_dir + 'player_data.pkl')

    return df


def list_of_tournaments(df=None):
    """for player name in dataset, go to tournament history page,
        for each tournament they played in,
        if that tournament is not in our tournament database,
        append it
        Leaves us with full list of tournament IDs for later parser
    """

    df = pandas.read_pickle(
        'C:\\Users\\AdamsPC\\Projects\\USCF-Rating-Comparisons\\data\\players_df.pkl')
    base_url = "http://www.uschess.org/msa/MbrDtlTnmtHst.php?"
    ids = [x for x in df.id]

    TOURN_OFFSET = 10  # row.text returns something like '2015-03-8201503089742'
    # where first 10 chars are date

    tournaments = []
    count = 1
    for ID in ids:
        print(count)
        count += 1

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

    np.save('data\\tournaments\\all_tournaments.npy', tournaments)

    return tournaments


def scrape_tournament(tournament_id):
    unwanted_chars = ''.join(
        [x for x in tournament_id if x not in string.digits])

    tournament_id = tournament_id.strip(unwanted_chars)
    tournament_id = str(int(tournament_id))
    base_url = 'http://www.uschess.org/assets/msa_joomla/XtblMain.php?'

    # .0 flag flattens tournament into one section
    url = base_url + tournament_id + '.0'

    data = requests.get(url)
    soup = BeautifulSoup(data.text, 'lxml')

    table = soup.find('pre')

    if table is None:
        return table

    table = table.text.split('\n')

    def parse_table(table):
        player = namedtuple(
            'player', ['id', 'placement', 'score', 'progression', 'results'])
        players = []

        def parse_name_row(row):
            row = row.replace(' ', '').split('|')
            possible_results = ('W', 'L', 'D')
            seed = row[0]
            try:
                score = row[2]
            except IndexError:
                pdb.set_trace()
            results = []
            for x in row[3:]:
                if any(result in x for result in possible_results):
                    results.append(x)
            return seed, score, results

        def parse_id_row(row):

            row = row.replace(' /', '').split('|')
            state = row[0]
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
        for i in range(len(table)):
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
                i += 1

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


    def clean_up_parse(players):
        new_players = []  # testing to see if this works
        for i in range(len(players)):
            new_players.append(Player(*players[i]))
        # df = pandas.DataFrame(players
        # num_players = df.seed.astype(int).max()

        players = new_players

        game_t = namedtuple('game_t', [
            'my_id', 'opponent_id', 'my_rating', 'opponent_rating', 'result', 'time_control'])

        player_t = namedtuple(
            'player_t', ['ID', 'placement', 'score', 'progression', 'games'])

        for i in range(len(players)):
            games = []
            for j in range(len(players[i].results)):
                opp_idx = players[i].results[j].strip(string.ascii_letters)
                for k in range(len(players)):
                    if opp_idx == players[k].placement:
                        opp = players[k]
                try:
                    test = opp
                except UnboundLocalError:
                    # games.append(None)
                    continue
                my_id = players[i].ID.strip()
                opp_id = opp.ID.strip()
                my_rating = players[i].progression.split('->')[0]
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

                if 'W' in players[i].results[j]:
                    score = 1.0
                elif 'L' in players[i].results[j]:
                    score = 0.0
                elif 'D' in players[i].results[j]:
                    score = 0.5
                else:
                    score = 'NaN'

                game = Game(my_id, opp_id, my_rating,
                            opp_rating, score, time_control)

                games.append(game)

            game_tuples = []

            for j in range(len(games)):
                game_tuples.append(game_t(games[j].my_id, games[j].opp_id, games[j].my_rating,
                                          games[j].opp_rating, games[j].result, games[j].time_control))


            setattr(players[i], 'games', pandas.DataFrame(game_tuples))

        players_t = []

        for i in range(len(players)):
            players_t.append(player_t(
                players[i].ID, players[i].placement, players[i].score, players[i].progression, players[i].games))

        return pandas.DataFrame(players_t)

    return clean_up_parse(parse_table(table))


if __name__ == "__main__":

    # 139574

    tournaments = np.load('397000_tournaments.npy')
    # tournaments = [tournaments[283]]
    tourn_data = []

    out_dir = "C:\\Users\AdamsPC\\Projects\\USCF-Rating-Comparisons\\data\\tournaments\\tournament_results\\397\\"

    for i in range(139574, len(tournaments)):
        tournaments[i] = tournaments[i].strip(
            ''.join([char for char in tournaments[i] if char not in string.digits]))
        print(tournaments[i])
        data = scrape_tournament(tournaments[i])
        try:
            data.to_pickle(out_dir+tournaments[i]+'.pkl')
        except AttributeError:
            continue
