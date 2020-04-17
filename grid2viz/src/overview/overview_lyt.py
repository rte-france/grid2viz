"""
This file builds the layout for the scenario overview tab.
This tab handles the generic information about the environment and the selection of a reference agent for future analysis.
"""

import dash_core_components as dcc
import dash_html_components as html
import dash_antd_components as dac
import dash_table as dt
import plotly.graph_objects as go

from grid2viz.src.manager import agents, make_episode, best_agents

layout_def = {
    'legend': {'orientation': 'h'},
    "showlegend": True,
    'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0},
}

layout_pie = {
    'legend': {'orientation': 'h'},
    'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0},
    'paper_bgcolor': 'rgba(0,0,0,0)',
    'plot_bgcolor': 'rgba(0,0,0,0)'

}

indicators_line = html.Div(id="indicator_line", children=[
    html.H4("Indicators"),
    html.Div(children=[

        html.Div([
            html.H5("Best Agent's Consumption Profiles (MW)"),
            dcc.Graph(
                id="indicator_line_charts",
                style={'margin-top': '1em'},
                figure=go.Figure(
                    layout=layout_def
                ),
            )
        ], className="col-xl-5"),

        html.Div(children=[
            html.H5("Best Agent's Production Shares"),
            dcc.Graph(
                id="production_share_graph",
                figure=go.Figure(
                    layout=layout_pie
                ),
            )], className="col-xl-4"),

        # number summary column
        html.Div(children=[
            html.Div(className="mb-4", children=[
                html.P(id="nb_steps_card", className="border-bottom h3 mb-0 text-right",
                       children=""),
                html.P(className="text-muted", children="Best Agent's Steps (step / nb actions)")
            ]),
            html.Div(className="mb-4", children=[
                html.P(id="nb_hazard_card", className="border-bottom h3 mb-0 text-right",
                       children=""),
                html.P(className="text-muted", children="Best Agent's Hazards")
            ]),
            html.Div(className="mb-4", children=[
                html.P(id="nb_maintenance_card", className="border-bottom h3 mb-0 text-right",
                       children=""),
                html.P(className="text-muted", children="Best Agent's Maintenances")
            ]),
            html.Div(className="mb-4", children=[
                html.P(id="duration_maintenance_card", className="border-bottom h3 mb-0 text-right",
                       children=""),
                html.P(className="text-muted",
                       children="Best Agent Maintenances Duration (min)")
            ])
        ], className="col-xl-3 align-self-center")
    ], className="card-body row"),
], className="lineBlock card")


def summary_line(episode, ref_agent):
    return html.Div(children=[
        html.H4("Summary"),
        html.Div(children=[
            html.Div(children=[
                html.H5("Best Agent's Environment Time Series"),
                dac.Radio(options=[
                    {'label': 'Load (MW)', "value": "Load"},
                    {'label': 'Production (MW)', "value": "Production"},
                    {'label': 'Hazards', "value": "Hazards"},
                    {'label': 'Maintenances', "value": "Maintenances"}],
                    value="Load",
                    id="scen_overview_ts_switch",
                    buttonStyle="solid"
                ),
                dac.Select(
                    id='input_assets_selector',
                    options=[{'label': load_name,
                              'value': load_name}
                             for load_name in episode.load_names],
                    value=episode.load_names[0],
                    mode='multiple',
                    showArrow=True
                ),
                dcc.Graph(
                    id='input_env_charts',
                    style={'margin-top': '1em'},
                    figure=go.Figure(layout=layout_def),
                    config=dict(displayModeBar=False)
                ),

            ], className="col-xl-5"),

            html.Div(children=[

                dcc.Dropdown(
                    id="input_agent_selector", placeholder="select a ref agent",
                    options=[{'label': agent, 'value': agent}
                             for agent in agents],
                    value=ref_agent
                ),
                html.Div(children=[
                    html.Div(children=[
                        html.H5("Usage rate", className='text-center'),
                        dcc.Graph(
                            id='usage_rate_graph',
                            style={'margin-top': '1em'},
                            figure=go.Figure(
                                layout=layout_def
                            ),
                            config=dict(displayModeBar=False)
                        )
                    ], className='col-6'),
                    html.Div(children=[
                        html.H5("Overflow", className='text-center'),
                        dcc.Graph(
                            id='overflow_graph',
                            style={'margin-top': '1em'},
                            figure=go.Figure(
                                layout=layout_def
                            ),
                            config=dict(displayModeBar=False)
                        )
                    ],  className='col-6')
                ], className="row"),
            ], className="col-xl-7"),
        ], className="card-body row"),
    ], className="lineBlock card")


ref_agent_line = html.Div(children=[
    html.H4("Inspector"),
    html.Div(children=[
        html.Div(children=[
            dcc.DatePickerRange(
                id="date_range",
                display_format='MMM Do, YY',
            ),
            html.H5("Loads"),
            dcc.Dropdown(
                id='select_loads_for_tb',
                options=[],
                multi=True,
                style=dict(marginBottom="1em")),
            html.H5("Generators"),
            dcc.Dropdown(
                id='select_prods_for_tb',
                options=[],
                multi=True,
                style=dict(marginBottom="1em"))
        ], className="col-xl-2"),
        html.Div(children=[
            dt.DataTable(
                id="inspection_table",
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                page_action="native",
                page_current=0,
                page_size=20,
            ),
            html.Label(
                children=[
                    'The documentation for the filtering syntax can be found ',
                    html.A('here.', href='https://dash.plot.ly/datatable/filtering',
                           target="_blank")]
            ),
        ], className="col-xl-10")
    ], className="col-xl-10 p-2")
], className="lineBlock card")


def layout(scenario, ref_agent):
    try:
        episode = make_episode(best_agents[scenario]["agent"], scenario)
    except Exception as ex:
        print(ex)
        return
    if ref_agent is None:
        ref_agent = agents[0]
    return html.Div(id="overview_page", children=[
        dcc.Store(id="relayoutStoreOverview"),
        indicators_line,
        summary_line(episode, ref_agent),
        ref_agent_line
    ])
