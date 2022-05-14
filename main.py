import requests as r
import re
from bs4 import BeautifulSoup

def get_data():
    wiki = 'https://en.wikipedia.org/'
    page_title = 'List_of_Falcon_9_and_Falcon_Heavy_launches'
    source_page = r.get(f'{wiki}api/rest_v1/page/html/{page_title}')

    return source_page.text

def find_flight_tables(html):
    soup = BeautifulSoup(html, 'html.parser')
    tables_with_headers = [table for table in soup.find_all('table') if table.find_all('th')]

    flight_tables = [table for table in tables_with_headers if 'Flight No.' in table.find_all('th')[0]]
    return flight_tables

def make_row_dict(flight_table):
    table_rows = flight_table.find_all('tr')
    table_rows = table_rows[1:]
    flight_rows = [row for row in table_rows if len(row.find_all('th')) > 0]

    def strip_citations(text):
        text = re.sub('\[\d*\]', ' ', text)
        return text

    row_dict = {}
    for row in flight_rows:
        flight_no = row.find_all('th')[0].contents[0]
        if flight_no != 0:
            cells = row.find_all('td')
            cells_text = [strip_citations(cell.get_text()) for cell in cells]
            row_dict[flight_no] = {
                'date_time': cells_text[0],
                'booster_version': cells_text[1],
                'launch_site': cells_text[2],
                'payload': cells_text[3],
                'payload_mass': {
                    'kg': cells_text[4].split('\xa0')[0].replace(',', ''),
                    'lbs': cells_text[4].split('(')[1].split('\xa0')[0].replace(',', '')
                },
                'orbit': cells_text[5],
                'customer': cells_text[6].split('\\n'),
                'launch_outcome': cells_text[7],
                'landing_outcome': cells_text[8]

            }
    return row_dict