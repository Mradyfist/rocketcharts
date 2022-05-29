from time import strftime, strptime
import requests as r
import re
import time
from flask import Flask, request, render_template, Response
import json
from bs4 import BeautifulSoup

def get_data():
    wiki = 'https://en.wikipedia.org/'
    page_titles = ['List_of_Falcon_9_and_Falcon_Heavy_launches_(2010–2019)', 'List_of_Falcon_9_and_Falcon_Heavy_launches']
    full_text = ''
    for page in page_titles:
        source_page = r.get(f'{wiki}api/rest_v1/page/html/{page}')
        full_text += source_page.text

    return full_text

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
        flight_no = row.find_all('th')[0].get_text()
        if flight_no != 0:
            cells = row.find_all('td')
            cells_text = [strip_citations(cell.get_text()) for cell in cells]
            row_dict[flight_no] = {
                'date_time': cells_text[0],
                'booster_version': cells_text[1],
                'launch_site': cells_text[2],
                'payload': cells_text[3],
                'payload_mass': {
                    'kg': cells_text[4].split('\xa0')[0].replace(',', '') if '–' not in cells_text[4] else '0',
                    # 'lbs': cells_text[4].split('(')[1].split('\xa0')[0].replace(',', '')
                },
                'orbit': cells_text[5],
                'customer': cells_text[6].split('\n'),
                'launch_outcome': cells_text[7],
                'landing_outcome': cells_text[8]

            }
    return row_dict

def make_rows_dict(chart_data):
    rows_dict = {}
    for table in chart_data:
        table_dict = make_row_dict(table)
        for row in table_dict.keys():
            rows_dict[row] = table_dict[row]
    
    return rows_dict


app = Flask(__name__)



@app.route("/")
def return_slug():
    return 'wrong place!'

@app.route("/json")
def json_info():
    json = make_rows_dict(find_flight_tables(get_data()))
    return json

@app.route("/api/payload")
def payload():
    dataset = make_rows_dict(find_flight_tables(get_data()))
    time_series = {}
    running_payload_tally = 0
    for datapoint in dataset:
        print(dataset[datapoint]['date_time'])
        day = dataset[datapoint]['date_time'].split(' ')[0]
        month = dataset[datapoint]['date_time'].split(' ')[1]
        year = dataset[datapoint]['date_time'].split(' ')[2][:4]
        epoch_time = strptime(day + month + year, '%d%B%Y')
        payload_mass = re.sub('[\D]', '', dataset[datapoint]['payload_mass']['kg'])
        if payload_mass:
            time_series[time.mktime(epoch_time)] = int(payload_mass)

    return time_series


@app.route("/falcon9")
def charts():
    dataset = make_rows_dict(find_flight_tables(get_data()))
    x_axis = []
    y_axis = []
    launch_info = []
    launch_payloads = []
    running_payload_tally = 0
    for datapoint in dataset:

        day = dataset[datapoint]['date_time'].split(' ')[0]
        month = dataset[datapoint]['date_time'].split(' ')[1]
        year = dataset[datapoint]['date_time'].split(' ')[2][:4]

        epoch_time = strptime(day + month + year, '%d%B%Y')
        human_time = strftime('%d %m %Y', epoch_time)

        this_launch_info = {
            'orbit': dataset[datapoint]['orbit'],
            'payload': dataset[datapoint]['payload'],
            'payload_mass': dataset[datapoint]['payload_mass'],
            'booster_version': dataset[datapoint]['booster_version'],
            'launch_site': dataset[datapoint]['launch_site'],
            'customer': dataset[datapoint]['customer'],
        }
        payload_mass = re.sub('[\D]', '', dataset[datapoint]['payload_mass']['kg'])
        if payload_mass:
            running_payload_tally += int(payload_mass)
            x_axis.append(
                time.mktime(epoch_time)
            )
            y_axis.append(
                running_payload_tally
            )
            launch_payloads.append(
                int(payload_mass)
            )
            launch_info.append(
                this_launch_info
            )

    return render_template("chart.html", x_axis=x_axis, y_axis=y_axis, launch_payloads=launch_payloads, launch_info=launch_info, max=running_payload_tally)