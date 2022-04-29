#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MIT License

Copyright (c) 2022 Michael Czigler

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import json
import pandas
import requests
import plotly.express as px

from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output
from flask_caching import Cache

MEMOIZE_TIMEOUT = 60

CACHE_CONFIG = {
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
}

DATE_SOURCES = {
    'minusrus': {
        'uri': 'https://www.minusrus.com/en',
        'api': 'https://api.storyblok.com/v2/cdn/stories?cv=1651219553&starts_with=losses%2F&token=xqjd6rLprbjdQg3i06E8Pgtt&version=published'
    }
}

HTML_ATTR = {
    'title': 'Russian-Ukranian War',
    'meta': [
        {'name': 'viewport', 'content': 'width=device-width, initial-scale=1'},
        {'name': 'description', 'content': 'A timeseries analysis and trending of Russian military forces and corresponding losses'},
        {'name': 'author', 'content': 'Michael Czigler'},
        {'name': 'keywords', 'content': 'Ukraine, Russia, War, Statistics, Trending, Losses'}
    ] 
}

def dataframe(value: str):
    return pandas.read_json(get(DATE_SOURCES[value]['api']), orient='split')

app = Dash(__name__, meta_tags=HTML_ATTR['meta'])
server = app.server
cache = Cache(server, config=CACHE_CONFIG)
app.title = HTML_ATTR['title']
app.layout = html.Div(
    [
        html.H1('Russian-Ukrainian War'),
        html.P(
            [
                'A timeseries analysis and trending of Russian military forces and corresponding losses. '
                'These metrics use "conservative" sources and, therefore, should only by considered for reference only. ',
                'Refer to ',
                html.A('github', href='http://github.com/mcpcpc/pvalue.xyz'),
                ' for additional information about this project.'
            ]
        ),
        dcc.Dropdown(
            options=[
                {'label': 'minusrus.com', 'value': 'minusrus'}
            ],
            clearable=False,
            searchable=False,
            value='minusrus',
            id='sources'
        ),
        dcc.Loading(dcc.Graph(id='trending-infantry')),
        dcc.Loading(dcc.Graph(id='trending-equipment')),
        html.Footer('Copyright \xa9 2022 Michael Czigler. All Rights Reserved')
    ]
)

@cache.memoize(timeout=MEMOIZE_TIMEOUT)
def get(api: str):
    resp = requests.get(api)
    json = resp.json()
    stat = []
    for story in json['stories']:
        stat.append(story['content'])
    df = pandas.DataFrame.from_dict(stat)
    df.date = df.date.astype('datetime64')
    df.killed = df.killed.astype('int')
    df.wounded = df.wounded.astype('int')
    df.artillery = df.artillery.astype('int')
    df.aircraft = df.aircraft.astype('int')
    df.helicopters = df.helicopters.astype('int')
    df['armored'] = df.armored_combat_vehicles.astype('int')
    df['ships'] = df.ships_boats.astype('int')
    return df.to_json(date_format='iso', orient='split')

@app.callback(
        Output('trending-infantry', 'figure'),
        Output('trending-equipment', 'figure'),
        Input('sources', 'value'))
def update_figure(value):
    df =  dataframe(value)
    infantry = px.area(
            df,
            x='date',
            y=['wounded', 'killed']
    )
    equipment = px.area(
            df, 
            x='date', 
            y=['armored', 'tanks', 'artillery', 'aircraft', 'helicopters', 'ships']
    )
    infantry.update_traces(hovertemplate=None)
    infantry.update_layout(
            legend_title='Infantry',
            yaxis_title='Russian Infantry Losses',
            xaxis_title='', 
            hovermode='x',
            template='plotly_dark'
    )
    equipment.update_traces(hovertemplate=None)
    equipment.update_layout(
            legend_title='Equipment',
            yaxis_title='Russian Equipment Destroyed', 
            xaxis_title='', 
            hovermode='x',
            template='plotly_dark'
    )
    return infantry, equipment

if __name__ == '__main__':
    app.run_server(debug=False)
