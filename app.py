import json
import pandas
import requests
import plotly.express as px

from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output
from flask_caching import Cache

def dataframe(value: str):
    return pandas.read_json(get(sources[value]['api']), orient='split')

with open('sources.json', 'r') as f:
    sources = json.load(f)



app = Dash(
        __name__, 
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1"},
            {"name": "description", "content": "A timeseries analysis and trending of Russian military forces and corresponding losses"},
            {"name": "author", "content": "Michael Czigler"},
            {"name": "keywords", "content": "Ukraine, Russia, War, Statistics, Trending, Losses"}
        ]
)

server = app.server

cache = Cache(server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
})

app.title ="Russian-Ukranian War"

app.layout = html.Div(
    [
        html.H1('Russian-Ukrainian War'),
        html.P(
            [
                'A timeseries analysis and trending of Russian military forces and corresponding losses. '
                'These metrics use "conservative" sources and, therefore, should only by considered for reference only.',
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
        dcc.Graph(
            id='trending-infantry',
            #style={'height':'45vh'}
        ),
        dcc.Graph(
            id='trending-equipment',
            #style={'height':'45vh'}
        ),
        html.Footer('Copyright \xa9 2022 Michael Czigler. All Rights Reserved')
    ]
)

@cache.memoize(timeout=60)
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
            y=['artillery', 'aircraft', 'helicopters', 'tanks', 'armored', 'ships']
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