import dash_antd_components as dac
import dash_html_components as html
import dash_core_components as dcc
import dash_table as dt
import plotly.graph_objects as go
from src.grid2kpi.manager import agents, agent_ref, episode
from src.grid2kpi.episode import observation_model

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

indicators_line = html.Div(id="temporaryid", children=[
    html.H4("Indicators"),
    html.Div(children=[

        html.Div(className="col-xl-5",
                 children=[
                     html.H5("Consumption Profiles"),
                     dcc.Loading(
                         id="overview_loading_profiles",
                         children=dcc.Graph(
                             id="indicator_line_charts",
                             style={'margin-top': '1em'},
                             figure=go.Figure(
                                 layout=layout_def
                             ),
                             config=dict(displayModeBar=False)
                         )
                     )
                 ]
                 ),

        html.Div(children=[
            html.H5("Production shares"),
            dcc.Loading(
                id="overview_loading_prod_shares",
                children=dcc.Graph(
                    id="production_share_graph",
                    figure=go.Figure(
                        layout=layout_pie
                    ),
                    config=dict(displayModeBar=False)
                )
            )],
            className="col-xl-4"),
        # number summary column
        html.Div(children=[
            html.Div(className="mb-4", children=[
                html.P(id="nb_steps_card", className="border-bottom h3 mb-0 text-right",
                       children=""),
                html.P(className="text-muted", children="Steps")
            ]),
            html.Div(className="mb-4", children=[
                html.P(id="nb_hazard_card", className="border-bottom h3 mb-0 text-right",
                       children=""),
                html.P(className="text-muted", children="Hazards")
            ]),
            html.Div(className="mb-4", children=[
                html.P(id="nb_maintenance_card", className="border-bottom h3 mb-0 text-right",
                       children=""),
                html.P(className="text-muted", children="Maintenances")
            ]),
            html.Div(className="mb-4", children=[
                html.P(id="duration_maintenance_card", className="border-bottom h3 mb-0 text-right",
                       children="NaN"),
                html.P(className="text-muted",
                       children="Duration of Maintenances (min)")
            ])
        ], className="col-xl-3 align-self-center")
    ], className="card-body row"),
], className="lineBlock card")


def summary_line(ref_agent=agent_ref):
    return html.Div(children=[
        html.H4("Summary"),
        html.Div(children=[
            html.Div(children=[
                html.H5("Environments Time Series"),
                dac.Radio(options=[
                    {'label': 'Load', "value": "Load"},
                    {'label': 'Production', "value": "Production"},
                    {'label': 'Hazards', "value": "Hazards"},
                    {'label': 'Maintenances', "value": "Maintenances"},
                ],
                    value="Load",
                    # name="scen_overview_ts_switch",
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
                html.H5("OverFlow and Usage rate"),
                dcc.Dropdown(
                    id="input_agent_selector", placeholder="select a ref agent",
                    options=[{'label': agent, 'value': agent}
                             for agent in agents],
                    value=ref_agent
                ),
                html.Div(children=[
                    dcc.Graph(
                        id='usage_rate_graph',
                        className="col-6",
                        style={'margin-top': '1em'},
                        figure=go.Figure(
                            layout=layout_def,
                            data=observation_model.get_usage_rate_trace(
                                episode)
                        ),
                        config=dict(displayModeBar=False)
                    ),
                    dcc.Graph(
                        id='overflow_graph',
                        className="col-6",
                        style={'margin-top': '1em'},
                        figure=go.Figure(
                            layout=layout_def,
                            data=observation_model.get_total_overflow_trace(
                                episode)
                        ),
                        config=dict(displayModeBar=False)
                    ),
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
                # className="col row",
                children=[
                    'The documentation for the filtering syntax can be found ',
                    html.A('here.', href='https://dash.plot.ly/datatable/filtering',
                           target="_blank")]
            ),
        ], className="col-xl-10")
    ], className="col-xl-10 p-2")
], className="lineBlock card")


def layout(ref_agent=agent_ref):
    return html.Div(id="overview_page", children=[
        dcc.Store(id="relayoutStoreOverview"),
        indicators_line,
        summary_line(ref_agent),
        ref_agent_line
    ])
