import dash_html_components as html
import dash_core_components as dcc
import dash_table as dt
import plotly.graph_objects as go

layout_def = {
    'legend': {'x': 0, 'y': 0, 'orientation': 'h'},
    'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0}
}

indicators_line = html.Div(id="temporaryid", children=[
    html.H2("Indicators"),
    html.Div(children=[

        html.Div(className="col-xl-5",
                 children=[
                     html.H3("Consumption Profiles"),
                     dcc.Graph(
                         id="indicator_line_charts",
                         style={'margin-top': '1em'},
                         figure=go.Figure(
                             layout=layout_def
                         ),
                         config=dict(displayModeBar=False)
                     )
                 ]
                 ),

        html.Div(children=[
            html.H3("Production shares"),
            dcc.Graph(
                id="production_share_graph",
                figure=go.Figure(
                    layout=layout_def
                ),
                config=dict(displayModeBar=False))],
            className="col-xl-4"),

        # number summary column
        html.Div(children=[
            html.Div(children=[
                html.Div(id="nb_steps", className="card text-center p-2 mb-4",
                         children=[html.H5(className="card-title", children="Steps"),
                                   html.P(id="nb_steps_card", className="card-text", children="")]),

                html.Div(id="nb_maintenance", className="card text-center p-2",
                         children=[html.H5(className="card-title", children="Maintenances"),
                                   html.P(id="nb_maintenance_card", className="card-text", children="")]),
            ], className="col-6"),
            html.Div(children=[
                html.Div(id="nb_hazard", className="card text-center p-2 mb-4",
                         children=[html.H5(className="card-title", children="Hazards"),
                                   html.P(id="nb_hazard_card", className="card-text", children="")]),

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
                          layout=layout_def
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
                        layout=layout_def
                    ),
                    config=dict(displayModeBar=False)
                ),
                dcc.Graph(
                    id='overflow_graph',
                    className="col-6",
                    style={'margin-top': '1em'},
                    figure=go.Figure(
                        layout=layout_def
                    ),
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
            )
        ], className="col-xl-10")
    ], className="col-xl-10 p-2")
], className="lineBlock card")

layout = html.Div(id="overview_page", children=[
    indicators_line,
    summary_line,
    ref_agent_line
])


def get_layout():
    return layout
