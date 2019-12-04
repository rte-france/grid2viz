import dash_html_components as html
import dash_core_components as dcc
import dash_table as dt
import plotly.graph_objects as go
import pandas as pd

from src.grid2kpi.episode import (observation_model, env_actions,
                                  consumption_profiles
                                  )

active_load_trace = observation_model.get_load_trace_per_equipment()
share_prod = observation_model.get_prod()
episode = observation_model.episode
profiles = consumption_profiles(observation_model.episode)

ts_hazards = env_actions(episode, which="hazards", kind="ts", aggr=True)
ts_hazards = ts_hazards.rename(columns={"value": "Hazards"})
ts_maintenances = env_actions(
    episode, which="maintenances", kind="ts", aggr=True)
ts_maintenances = ts_maintenances.rename(columns={"value": "Maintenances"})


table = ts_hazards.merge(ts_maintenances, left_index=True, right_index=True)
table = table.reset_index()
table["IsWorkingDay"] = table["timestamp"].dt.weekday < 5

nb_hazards = env_actions(episode, which="hazards", kind="nb", aggr=True)

nb_maintenances = env_actions(
    episode, which="maintenances", kind="nb", aggr=True)

overflow = observation_model.get_total_overflow_trace()
usage_rate = observation_model.get_usage_rate_trace()

df = pd.read_csv(
    'https://raw.githubusercontent.com/plotly/datasets/master/solar.csv')  # TODO remove with backend working

layout_def = {
    'legend': {'x': 0, 'y': 0, 'orientation': 'h'},
    'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0}
}

indicators_line = html.Div(children=[
    html.H2("Indicators"),
    html.Div(children=[

        html.Div(className="col-xl-5",
                 children=[
                     html.H3("Consumption Profiles"),
                     dcc.Graph(
                         id="indicator_line_charts",
                         style={'margin-top': '1em'},
                         figure=go.Figure(
                            layout=layout_def,
                            data=[go.Scatter(
                                x=profiles.index, y=profiles[col], name=col
                            ) for col in profiles.columns]
                         ),
                         config=dict(displayModeBar=False)
                     )
                 ]
                 ),

        html.Div(children=[
            html.H3("Production shares"),
            dcc.Graph(
                figure=go.Figure(
                    layout=layout_def,
                    data=[go.Pie(
                        labels=share_prod["equipment_name"],
                        values=share_prod.groupby("equipment_name")[
                            "value"].sum()
                    )],
                ),
                config=dict(displayModeBar=False))],
            className="col-xl-4"),

        # number summary column
        html.Div(children=[
            html.Div(children=[
                html.Div(id="nb_steps", className="card text-center p-2 mb-4",
                         children=[html.H5(className="card-title", children="Steps"),
                                   html.P(className="card-text", children=len(episode.observations))]),

                html.Div(id="nb_maintenance", className="card text-center p-2",
                         children=[html.H5(className="card-title", children="Maintenances"),
                                   html.P(className="card-text", children=nb_maintenances)]),
            ], className="col-6"),
            html.Div(children=[
                html.Div(id="nb_hazard", className="card text-center p-2 mb-4",
                         children=[html.H5(className="card-title", children="Hazards"),
                                   html.P(className="card-text", children=nb_hazards)]),

                html.Div(id="maintenance_duration", className="card text-center p-2",
                         children=[html.H5(className="card-title", children="Duration of Maintenances"),
                                   html.P(className="card-text", children="3")])
            ], className="col-6")
        ], className="col-xl-3 row align-self-center")
    ], className="card-body row"),
], className="lineBlock card")

summary_line = html.Div(children=[
    html.H2("Summary"),
    html.Div(children=[
        html.Div(children=[
            html.H3("Environments Time Series"),
            dcc.Dropdown(
                id='input_env_selector',
                options=[
                    {'label': 'Load', "value": "1"},
                    {'label': 'Production', "value": "2"},
                    {'label': 'Hazards', "value": "3"},
                    {'label': 'Maintenances', "value": "4"},
                ],
                value="1",
            ),
            dcc.Graph(id='input_env_charts',
                      style={'margin-top': '1em'},
                      figure=go.Figure(
                          layout=layout_def,
                          data=active_load_trace
                      ),
                      config=dict(displayModeBar=False)
                      )
        ], className="col-xl-5"),

        html.Div(children=[
            html.H3("OverFlow and Usage rate"),
            dcc.Dropdown(
                id="input_agent_selector", placeholder="select a ref agent",
                options=[{'label': 'test', 'value': 1},
                         {'label': 'test1', 'value': 2}]
            ),
            html.Div(children=[
                dcc.Graph(
                    id='usage_rate_graph',
                    className="col-6",
                    style={'margin-top': '1em'},
                    figure=go.Figure(
                        layout=layout_def,
                        data=overflow),
                    config=dict(displayModeBar=False)
                ),
                dcc.Graph(
                    id='usage_overview_graph',
                    className="col-6",
                    style={'margin-top': '1em'},
                    figure=go.Figure(
                        layout=layout_def,
                        data=usage_rate),
                    config=dict(displayModeBar=False)
                ),
            ], className="row"),
        ], className="col-xl-6"),
    ], className="card-body row"),
], className="lineBlock card")

ref_agent_line = html.Div(children=[
    html.H2("Inspector"),
    html.Div(children=[
        html.Div(children=[
            dcc.DatePickerRange(
                start_date=episode.production["timestamp"].dt.date.values[0],
                end_date=episode.production["timestamp"].dt.date.values[-1],
                display_format='MMM Do, YY',
                # start_date_placeholder_text='MMM Do, YY'
            ),
            html.H5("Loads"),
            dcc.Dropdown(
                id='select_loads_for_tb',
                options=[
                    {'label': load, "value": load} for load in episode.load_names
                ],
                # value=episode.load_names[0],
                multi=True,
                style=dict(marginBottom="1em")),
            html.H5("Generators"),
            dcc.Dropdown(
                id='select_prods_for_tb',
                options=[
                    {'label': prod, "value": prod} for prod in episode.prod_names
                ],
                # value=episode.prod_names[0],
                multi=True,
                style=dict(marginBottom="1em"))
        ], className="col-xl-2"),
        dt.DataTable(
            id="inspection_table",
            columns=[{"name": i, "id": i} for i in table.columns],
            data=table.to_dict('records'),
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            page_action="native",
            page_current=0,
            page_size=20,
        )
    ], className="col-xl-10 p-2")
], className="lineBlock card")

layout = html.Div(id="overview_page", children=[
    indicators_line,
    summary_line,
    ref_agent_line
])
