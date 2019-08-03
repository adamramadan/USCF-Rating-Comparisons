import requests
import pandas
from bs4 import BeautifulSoup
import pdb
from html.parser import HTMLParser
from collections import namedtuple
import csv
import numpy as np


def scrape_players(saving=True):
    base_url = 'http://www.uschess.org/assets/msa_joomla/MbrLst.php?*,*;'
    NUM_PAGES = 10003
    BAD_WORDS = ['Dupl', '(  )']

    players = []



    for page in range(1, NUM_PAGES+1):
        print(page)
        data = requests.get(
            base_url + str(page))

        soup = BeautifulSoup(data.text, 'lxml')
        rows = soup.find('pre').text.split('\n') # player table is a <pre> object, should be single on page
        for i in range(len(rows)-1, -1, -1):
            if any(word in rows[i] for word in BAD_WORDS):
                del rows[i]
                continue
            rows[i] = rows[i].split()

        rows = rows[2:]  # trim top headers of table
        del rows[-1]  # empty list on last element

        NUM_FIELDS_BEFORE_NAME = 6

        for i in range(len(rows)):
            temp = rows[i][:NUM_FIELDS_BEFORE_NAME] 
            temp.extend([''.join(rows[i][NUM_FIELDS_BEFORE_NAME:])])
            players.append(temp)

    df = pandas.DataFrame(players)
    df.columns = ['ID', 'State', 'Exp Date', 'Reg', 'Quick', 'Blitz', 'Name']
    
    if saving:
        df.to_pickle('data\\player_data.pkl')

    return df


def list_of_tournaments(df=None):
    """for player name in dataset, go to tournament history page,
        for each tournament they played in,
        if that tournament is not in our tournament database,
        append it
        Leaves us with full list of tournament IDs for later parser
    """

    df = pandas.read_pickle(
        'C:\\Users\\AdamsPC\\Projects\\USCF-Rating-Comparisons\\data\\player_data.pkl')
    base_url = "http://www.uschess.org/msa/MbrDtlTnmtHst.php?"
    ids = [x for x in df.ID]

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
        if count == 50:
            return tournaments
    return tournaments


def scrape_tournament(tournament_id):

    tournament_id = str(int(tournament_id))
    base_url = 'http://www.uschess.org/assets/msa_joomla/XtblMain.php?'

    url = base_url + tournament_id + '.0' # .0 flag flattens tournament into one section

    data = requests.get(url)
    soup = BeautifulSoup(data.text, 'lxml')

    table = soup.find('pre')

    table = table.text.split('\n')

    def trim_and_examine_table(table):
        dotted_rows = ['-------' in x for x in table]
        for idx in range(len(dotted_rows) - 1, -1, -1):
            if dotted_rows[idx]:
                end_of_table = idx - 1
                break
        count = 0
        for idx in range(0, len(dotted_rows)):
            if dotted_rows[idx]:
                count += 1
                if count == 3:
                    start_of_table = idx + 1
                    break

        table = table[start_of_table:end_of_table]
        dotted_rows = dotted_rows[start_of_table:end_of_table]

        time_since_last_bar = 0
        spaces = []
        for i in range(len(dotted_rows)):
            if dotted_rows[i]:
                spaces.append(time_since_last_bar)
                time_since_last_bar = 0
            else:
                time_since_last_bar += 1

        spaces_per_entry = np.round(np.mean(spaces)).astype(np.int32)

        while spaces[-1] != spaces_per_entry:
            del table[-spaces[-1]-1:]
            del spaces[-1]

        return table, spaces_per_entry

    table, spaces_per_entry = trim_and_examine_table(table)

    def parse_table(table, rows_per_entry):
        rows = [x for x in table]

        def parse_name_row(row):
            row = row.replace(' ', '').split('|')
            possible_results = ('W', 'L', 'D')
            seed = row[0]
            score = row[2]
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
            progression = row[1]

            return state, ID, progression

        player = namedtuple(
            'player', ['id', 'seed', 'score', 'progression', 'results'])

        players = []

        for i in range(0, len(table)):

            for_modulo = i
            if for_modulo % (rows_per_entry+1) == 0:
                seed, score, results = parse_name_row(rows[i])
            elif for_modulo % (rows_per_entry+1) == 1:
                _, ID, progression = parse_id_row(rows[i])
                if 'R' in ID:
                    ID = ID.strip('R')
                    progression = 'R ' + progression
                elif 'Q' in ID:
                    ID = ID.strip('Q')
                    progression = 'Q ' + progression
                temp_player = player(ID, seed, score, progression, results)
                players.append(temp_player)
            else:
                continue

        return players

    return parse_table(table, spaces_per_entry)


if __name__ == "__main__":
    tournies = list_of_tournaments()
    for tourn in tournies:
        t = scrape_tournament(tourn)
        for x in t:
            print(x)
