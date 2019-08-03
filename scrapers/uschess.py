import requests
import pandas
from bs4 import BeautifulSoup


NUM_PAGES = 10003

players = []


for page in range(1, NUM_PAGES+1):
    print(page)
    data = requests.get('http://www.uschess.org/assets/msa_joomla/MbrLst.php?*,*;' + str(page))

    soup = BeautifulSoup(data.text, 'lxml')
    rows = soup.find('pre').text.split('\n')
    for i in range(len(rows)-1, -1, -1):
        if 'Dupl' in rows[i] or '(  )' in rows[i]:
            del rows[i]
            continue
        rows[i] = rows[i].split()
    
    rows = rows[2:]
    del rows[-1]

    for i in range(len(rows)):
        temp = rows[i][:6]
        temp.extend([''.join(rows[i][6:])])
        players.append(temp)


df = pandas.DataFrame(players)
df.columns = ['ID', 'State', 'Exp Date', 'Reg', 'Quick', 'Blitz', 'Name']

df.to_pickle('player_data.pkl')