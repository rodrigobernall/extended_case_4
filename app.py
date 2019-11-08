import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import dash_table

df = pd.read_csv('aggr.csv', parse_dates=['Entry time'])
df['YearMonth']= df['Entry time'].dt.year.astype(str)+"-"+ df['Entry time'].dt.month.astype(str)
print(df.head())
#print(df.tail(1)['BTC Price'].values[0])



app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/uditagarwal/pen/oNvwKNP.css', 'https://codepen.io/uditagarwal/pen/YzKbqyV.css'])



app.layout = html.Div(children=[
    html.Div(
            children=[
                html.H2(children="Bitcoin Leveraged Trading Backtest Analysis", className='h2-title'),
            ],
            className='study-browser-banner row'
    ),
    html.Div(
        className="row app-body",
        children=[
            html.Div(
                className="twelve columns card",
                children=[
                    html.Div(
                        className="padding row",
                        children=[
                            # Exchange Selector
                            html.Div(
                                className="two columns card",
                                children=[
                                    html.H6("Select Exchange",),
                                    dcc.RadioItems(
                                        id="exchange-select",
                                        options=[
                                            {'label': label, 'value': label} for label in df['Exchange'].unique()
                                        ],
                                        value='Bitmex',
                                        labelStyle={'display': 'inline-block'}
                                    )
                                ]
                            ),
                            # Leverage Selector
                            html.Div(
                                className="two columns card",
                                children=[
                                    html.H6("Select Leverage"),
                                    dcc.RadioItems(
                                        id="leverage-select",
                                        options=[
                                            {'label': str(label), 'value': str(label)} for label in df['Margin'].unique()
                                        ],
                                        value='1',
                                        labelStyle={'display': 'inline-block'}
                                    ),
                                ]
                            ),
                            # Date Selector
                            html.Div(
                                className="three columns card",
                                children=[
                                    html.H6("Select a Date Range"),
                                    dcc.DatePickerRange(
                                        id="date-range",
                                        display_format="MMM YY",
                                        start_date=df['Entry time'].min(),
                                        end_date=df['Entry time'].max()
                                    ),
                                ]
                            ),
                            #Strategy Returns box
                            html.Div(
                                id="strat-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-returns", className="indicator_value"),
                                    html.P('Strategy Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            #Market Returns box
                            html.Div(
                                id="market-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="market-returns", className="indicator_value"),
                                    html.P('Market Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            #Strategy vs. Returns box
                            html.Div(
                                id="strat-vs-market-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-vs-market", className="indicator_value"),
                                    html.P('Strategy vs. Market Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                        ]
                )
        ]),
        html.Div(
            className="twelve columns card",
            children=[
                dcc.Graph(
                    id="monthly-chart",
                    figure={
                        'data': []
                    }
                )
            ]
        ),
        html.Div(
                className="padding row",
                children=[
                    html.Div(
                        className="six columns card",
                        children=[
                            dash_table.DataTable(
                                id='table',
                                columns=[
                                    {'name': 'Number', 'id': 'Number'},
                                    {'name': 'Trade type', 'id': 'Trade type'},
                                    {'name': 'Exposure', 'id': 'Exposure'},
                                    {'name': 'Entry balance', 'id': 'Entry balance'},
                                    {'name': 'Exit balance', 'id': 'Exit balance'},
                                    {'name': 'Pnl (incl fees)', 'id': 'Pnl (incl fees)'},
                                ],
                                style_cell={'width': '50px'},
                                style_table={
                                    'maxHeight': '450px',
                                    'overflowY': 'scroll'
                                },
                            )
                        ]
                    ),
                    dcc.Graph(
                        id="pnl-types",
                        className="six columns card",
                        figure={
                            'data': [go.Bar()],
                        }
                    )
                ]
            ),
            html.Div(
                className="padding row",
                children=[
                    dcc.Graph(
                        id="daily-btc",
                        className="six columns card",
                        figure={
                            'data': [go.Scatter()]
                        }
                    ),
                    dcc.Graph(
                        id="balance",
                        className="six columns card",
                        figure={
                            'data': [go.Scatter()]
                        }
                    )
                ]
            )
    ])        
])



def filter_df(df,exchange,leverage, start_date,end_date):
    #Condicion exchange
    condicion_exchange=df['Exchange']==exchange
    #Condicion leverage
    condicion_leverage=df['Margin']==int(leverage)
    #Condicion start_date
    condicion_start_date=df['Entry time']>=start_date
    #Condicion end_date
    condicion_end_date=df['Entry time']<=end_date
    data = df[condicion_exchange & condicion_leverage & condicion_start_date & condicion_end_date].copy()

    return data

def calc_returns_over_month(dff):
    out = []

    for name, group in dff.groupby('YearMonth'):
        exit_balance = group.head(1)['Exit balance'].values[0]
        entry_balance = group.tail(1)['Entry balance'].values[0]
        monthly_return = (exit_balance*100 / entry_balance)-100
        out.append({
            'month': name,
            'entry': entry_balance,
            'exit': exit_balance,
            'monthly_return': monthly_return
        })
    return out


def calc_btc_returns(dff):
    btc_start_value = dff.tail(1)['BTC Price'].values[0]
    btc_end_value = dff.head(1)['BTC Price'].values[0]
    btc_returns = (btc_end_value * 100/ btc_start_value)-100
    return btc_returns

def calc_strat_returns(dff):
    start_value = dff.tail(1)['Exit balance'].values[0]
    end_value = dff.head(1)['Entry balance'].values[0]
    returns = (end_value * 100/ start_value)-100
    return returns

@app.callback(
    [
        dash.dependencies.Output('monthly-chart', 'figure'),
        dash.dependencies.Output('market-returns', 'children'),
        dash.dependencies.Output('strat-returns', 'children'),
        dash.dependencies.Output('strat-vs-market', 'children'),
    ],
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),

    )
)

def update_monthly(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    data = calc_returns_over_month(dff)
    btc_returns = calc_btc_returns(dff)
    strat_returns = calc_strat_returns(dff)
    strat_vs_market = strat_returns - btc_returns

    return {
        'data': [
            go.Candlestick(
                open=[each['entry'] for each in data],
                close=[each['exit'] for each in data],
                x=[each['month'] for each in data],
                low=[each['entry'] for each in data],
                high=[each['exit'] for each in data]
            )
        ],
        'layout': {
            'title': 'Overview of Monthly performance'
        }
    }, f'{btc_returns:0.2f}%', f'{strat_returns:0.2f}%', f'{strat_vs_market:0.2f}%'

@app.callback(
    dash.dependencies.Output('table', 'data'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    )
)
def update_table(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    return dff.to_dict('records')

@app.callback(
    dash.dependencies.Output('pnl-types', 'figure'),
    [
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    ]
)

def update_pnl_bar_plot(exchange, leverage, start_date, end_date):
    dff = filter_df(df,exchange, leverage, start_date, end_date)
    dff['date']=dff['Entry time'].dt.date
    dff_short=dff[dff['Trade type']=='Short']
    y_short=list(dff_short['Pnl (incl fees)'])
    x_short=list(dff_short['date'])
    dff_long=dff[dff['Trade type']!='Short']
    y_long=list(dff_long['Pnl (incl fees)'])
    x_long=list(dff_long['date'])

    series_short={'x':x_short,'y':y_short,'type':'bar','name':'Short'}
    series_long={'x':x_long,'y':y_long,'type':'bar','name':'Long'}
    result=[series_short,series_long]
    
    return { 
        'data': result,
        'layout': {
            'title': {
                'text': 'PnL vs Trade Type',
            },
            'height':500
        }
    }

@app.callback(
    dash.dependencies.Output('daily-btc', 'figure'),
    [
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    ]
)

def update_daily_btc_scatter_plot(exchange, leverage, start_date, end_date):
    dff = filter_df(df,exchange, leverage, start_date, end_date)
    dff['date']=dff['Entry time'].dt.date
    y_btc=list(dff['BTC Price'])
    x_btc=list(dff['date'])
    series_btc=[{'x':x_btc,'y':y_btc,'mode':'lines','name':'BTC Price'}]
    return { 
        'data': series_btc,
        'layout': {
            'title': {
                'text': 'Daily BTC Price',
            },
            'height':500
        }
    }

@app.callback(
    dash.dependencies.Output('balance', 'figure'),
    [
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    ]
)

    
def update_daily_balance_scatter_plot(exchange, leverage, start_date, end_date):
    dff = filter_df(df,exchange, leverage, start_date, end_date)
    dff['date']=dff['Entry time'].dt.date
    y_balance=list(dff['Exit balance'])
    x_balance=list(dff['date'])
    series_balance=[{'x':x_balance,'y':y_balance,'mode':'lines','name':'Balance'}]

    return { 
        'data': series_balance,
        'layout': {
            'title': {
                'text': 'Balance Overtime',
            },
            'height':500
        }
    }


if __name__ == "__main__":
    app.run_server(debug=True)