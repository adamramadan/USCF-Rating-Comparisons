import requests
import pandas
from bs4 import BeautifulSoup
import pdb

def scrape_players():

    NUM_PAGES = 10003
    BAD_WORDS = ['Dupl', '(  )']

    players = []

    for page in range(1, NUM_PAGES+1):
        print(page)
        data = requests.get(
            'http://www.uschess.org/assets/msa_joomla/MbrLst.php?*,*;' + str(page))

        soup = BeautifulSoup(data.text, 'lxml')
        rows = soup.find('pre').text.split('\n')
        for i in range(len(rows)-1, -1, -1):
            if any(word in rows[i] for word in BAD_WORDS): 
                del rows[i]
                continue
            rows[i] = rows[i].split()

        rows = rows[2:] # trim top headers of table
        del rows[-1] # empty list on last element

        for i in range(len(rows)):
            temp = rows[i][:6]
            temp.extend([''.join(rows[i][6:])])
            players.append(temp)


    df = pandas.DataFrame(players)
    df.columns = ['ID', 'State', 'Exp Date', 'Reg', 'Quick', 'Blitz', 'Name']

    df.to_pickle('data\\player_data.pkl')

    return df

def list_of_tournaments(df=None):
    df = pandas.read_pickle('C:\\Users\\AdamsPC\\Projects\\USCF-Rating-Comparisons\\data\\player_data.pkl')
    base_url = "http://www.uschess.org/msa/MbrDtlTnmtHst.php?"
    ids = [x for x in df.ID]

    TOURN_OFFSET = 10 # row.text returns something like '2015-03-8201503089742' 
                        # where first 10 chars are date

    tournaments = []
    count = 1
    for ID in ids:
        print(count)
        count += 1
        
        url = base_url + ID
        
        data = requests.get(url)
        
        soup = BeautifulSoup(data.text, 'lxml')
        
        rows = soup.findAll('td', {'width':120}) # empirical 120 width for rows
        if rows:
            temp = [tourn.text[TOURN_OFFSET:] for tourn in rows]
            for tourn in temp:
                if tourn not in tournaments:
                    tournaments.append(tourn)
        

    return tournaments

if __name__ == "__main__":
    rows = list_of_tournaments()



    