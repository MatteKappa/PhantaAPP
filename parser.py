''' Parser.py is a Python script that parses the data of the players 
    from the Fantacalciopedia website and writes them in a .csv file.'''

# TODO: I Trequartisti sono considerati come Centrocampisti, ma alcuni sono attaccanti.

import os
import csv
import requests
import pandas as pd
from bs4 import BeautifulSoup

ROLE_PLAYERS = {
    'P': 'portieri',
    'D': 'difensori',
    'C': 'centrocampisti',
    'T': 'trequartisti',
    'A': 'attaccanti'
}
URL = 'https://www.fantacalciopedia.com/lista-calciatori-serie-a/'



def get_xlsx_file_path():
    """Returns the path of the .xlsx file containing the data."""
    files_in_directory = os.listdir()
    xlsx_files = [file for file in files_in_directory if file.endswith('.xlsx')]
    if xlsx_files:
        return os.path.join(os.getcwd(), xlsx_files[0])
    else:
        raise FileNotFoundError('No .xlsx file found in the current directory')


print("\n📊 Caricamento del file Excel...")
df = pd.read_excel(get_xlsx_file_path(), skiprows=1)
names_list = df['Nome']
df.set_index('Nome', inplace=True)
print(f"✅ File Excel caricato con successo. Totale giocatori: {len(names_list)}")


def get_tags(soup):
    """Returns the evaluation tags of the player."""
    tags_section = soup.find('div', {'class': 'col_full center mc_hookEvolution'})
    tags = {
        'Assistman': '', 'Buona Media': '', 'Falloso': '', 'Fuoriclasse': '',
        'Goleador': '', 'Giovane talento': '', 'Outsider': '', 'Panchinaro': '',
        'Piazzati': '', 'Rigorista': '', 'Titolare': ''
    }
    if tags_section:
        divs = tags_section.find_all('div', {'class': 'col_one_fourth'})
        for div in divs:
            span_text = div.find('span', {'class': 'stickdanpic'}).text.strip()
            if span_text in tags:
                tags[span_text] = span_text
    return tags


def get_predicted_stats(soup):
    """Returns the predicted statistics of the player."""
    stats_section = soup.find('div', {'class': 'col_one_third col_last'})
    stats = {
        'Presenze previste': '',
        'Gol previsti': '',
        'Assist previsti': ''
    }

    if stats_section:
        labels = stats_section.find_all('div', {'class': 'label12'})
        for label in labels:
            strong_text = label.find_all('strong')
            spans = label.find_all('span', {'class': 'stickdan'})
            for strong, span in zip(strong_text, spans):
                stat_name = strong.text.strip().rstrip(':')
                if stat_name in stats:
                    stats[stat_name] = span.text.strip()
    return stats


def main():
    for role in ROLE_PLAYERS.values():
        print(f"\n🔍 Analisi ruolo: {role.upper()}")

        # Get the page of the role
        role_url = f'{URL}{role.lower()}/'
        page = requests.get(role_url)
        soup = BeautifulSoup(page.content, 'html.parser')

        # Get the divs of the players
        divs = soup.find_all('div', {'class': 'col_full giocatore'})
        print(f"📋 Trovati {len(divs)} giocatori per il ruolo {role}")

        if role != 'Attaccanti':
            dict_player = {}

        for index, player_page in enumerate(divs, 1):
            mean_skill = 0

            # Get link of the player's page
            href = player_page.find_all('a', {'class': 'label label-default fondoindaco'})[0]['href']
            role_site = role[0].upper()
            if role_site == 'T':
                role_site = 'C'

            # Get player's page
            name_player = player_page.find('h3', {'class': 'tit_calc'})
            page = requests.get(href)
            soup = BeautifulSoup(page.content, 'html.parser')

            print(f"  👤 Analisi giocatore {index}/{len(divs)}: {name_player.text}")

            # Get player's values (Algoritmo, Media Fanta, Media Fanta, Media Fanta)
            values = soup.find_all('div', {'class': 'label12'})
            app_val = str(values[4].text).split(':')
            team_site = app_val[-1].replace('\n', '').replace(' ', '')

            # Get player's skill(ALG FCP, Punteggio Fantacalciopedia, Solidita' fantainvestimento, Resistenza infortuni)
            skills_player = soup.find_all('ul', {'class': 'skills'})
            skill_values = []
            for skill_ul in skills_player:
                skills_li = skill_ul.find_all('li')
                for skill_li in skills_li:
                    skills_div = skill_li.find_all('div', {'class': 'counter counter-inherit counter-instant'})
                    for skill_div in skills_div:
                        skills_span = skill_div.find_all('span')
                        for skill in skills_span:
                            mean_skill += int(skill.text)
                            skill_values.append(int(skill.text))

            # Get player's evaluation tags (Es. 'Outsider', 'Titolare')
            tags = get_tags(soup)
            # Get predicted statistics of the player (Es. 'Gol', 'Assist')
            stats = get_predicted_stats(soup)

            dict_player[name_player.text.lower()] = {
                "Media": mean_skill / 4,
                "Ruolo": role_site,
                "Squadra": team_site,
                "ALG FCP": skill_values[0],
                "Punteggio FantaCalcioPedia": skill_values[1],
                "Solidità fantainvestimento": skill_values[2],
                "Resistenza infortuni": skill_values[3],
                **tags,
                **stats
            }

        if role != 'trequartisti':
            dict_player = sorted(dict_player.items(), key=lambda x: x[1]['Media'], reverse=True)
            if role == 'trequartisti':
                role = 'centrocampisti'

            print(f"\n📝 Scrittura dati per il ruolo {role} nel file CSV...")
            # Write Role's data in a csv file
            with open(f'meanSkill{role}.csv', 'a+', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Nome', 'Media', 'Ruolo', 'Squadra', 'ALG FCP',
                                 'Punteggio FantaCalcioPedia', 'Solidità fantainvestimento',
                                 'Resistenza infortuni'] + list(tags.keys()) +
                                ['Presenze previste', 'Gol previsti', 'Assist previsti'])

                # Write player's data in the csv file
                players_written = 0
                for key, value in dict_player:
                    flag = 0
                    for name in names_list:
                        name_player = str(name).replace(' ', '').replace('-', ' ').lower()
                        team = df.loc[name, 'Squadra']
                        ruolo = df.loc[name, 'R']
                        ruolo_site = value['Ruolo']
                        team_site = value['Squadra']
                        if name_player in key and ruolo == ruolo_site and team == team_site:
                            writer.writerow(
                                [name.upper(), team, ruolo, value['Media'],
                                 value['ALG FCP'], value['Punteggio FantaCalcioPedia'],
                                 value['Solidità fantainvestimento'],
                                 value['Resistenza infortuni']] +
                                [value[tag] for tag in tags.keys()] +
                                [value['Presenze previste'], value['Gol previsti'],
                                 value['Assist previsti']]
                            )
                            flag = 1
                            players_written += 1
                            break
                    # 
                    if flag == 0:
                        writer.writerow(
                            [key.upper(), team_site, ruolo_site,
                             value['Media'], value['ALG FCP'],
                             value['Punteggio FantaCalcioPedia'],
                             value['Solidità fantainvestimento'],
                             value['Resistenza infortuni']] +
                            [value[tag] for tag in tags.keys()] +
                            [value['Presenze previste'],
                             value['Gol previsti'], value['Assist previsti']]
                        )
                        players_written += 1

            print(f"✅ Dati scritti con successo. Totale giocatori scritti: {players_written}")

    print("\n🎉 Elaborazione completata per tutti i ruoli!")


if __name__ == '__main__':
    main()