"""
This file builds the layout for the scenario overview tab.
This tab handles the generic information about the environment and the selection of a reference agent for future analysis.
"""
import base64
import io
from pathlib import Path

import dash_antd_components as dac
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go

from grid2viz.src.manager import (agent_scenario, make_episode, best_agents,
                                  make_network_matplotlib, grid2viz_home_directory)
from grid2viz.src.utils.constants import DONT_SHOW_FILENAME
from grid2viz.src.utils.layout_helpers import modal, should_help_open

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


def indicators_line(encoded_image):
    return html.Div(id="indicator_line", children=[
        html.H4("Indicators"),
        html.Div(children=[

            html.Div([
                html.H5("Distribution of Daily Load Profiles (MW)"),
                dcc.Graph(
                    id="indicator_line_charts",
                    style={'margin-top': '1em'},
                    figure=go.Figure(
                        layout=layout_def
                    ),
                )
            ], className="col-xl-5"),

            html.Div(children=[
                html.H5("Production Shares"),
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
                    html.P(className="text-muted", children="Number of Hazards")
                ]),
                html.Div(className="mb-4", children=[
                    html.P(id="nb_maintenance_card", className="border-bottom h3 mb-0 text-right",
                           children=""),
                    html.P(className="text-muted", children="Number of Maintenances")
                ]),
                html.Div(className="mb-4", children=[
                    html.P(id="duration_maintenance_card", className="border-bottom h3 mb-0 text-right",
                           children=""),
                    html.P(className="text-muted",
                           children="Maintenances Duration (min)")
                ])
            ], className="col-xl-3 align-self-center"),
            html.Div([
                html.H5("Max prod & laod values and dashed lines in maintenance on Power grid",
                        style={"margin-top": "2%"}),
                html.Img(src='data:image/png;base64,{}'.format(encoded_image))
            ], className="col-xl-12"),
        ], className="card-body row"),
    ], className="lineBlock card")


def summary_line(episode, ref_agent, scenario):
    return html.Div(children=[
        html.H4("Summary"),
        html.Div(children=[
            html.Div(children=[
                html.H5("Environment Time Series"),
                dac.Radio(options=[
                    {'label': 'Production (MW)', "value": "Production"},
                    {'label': 'Load (MW)', "value": "Load"},
                    {'label': 'Hazards', "value": "Hazards"},
                    {'label': 'Maintenances', "value": "Maintenances"}],
                    value="Production",
                    id="scen_overview_ts_switch",
                    buttonStyle="solid"
                ),
                dac.Select(
                    id='input_assets_selector',
                    options=[{'label': prod_name,
                              'value': prod_name}
                             for prod_name in episode.prod_names],
                    value='solar',
                    # episode.prod_names[3],#[episode.prod_names[0],episode.prod_names[1]],#[prod_name for prod_name in episode.prod_names if prod_name in ['wind','solar']],#episode.prod_names[0]
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
                html.H5("Reference agent Metrics"),
                dcc.Dropdown(
                    id="input_agent_selector", placeholder="select a ref agent",
                    options=[{'label': agent, 'value': agent}
                             for agent in agent_scenario[scenario]],
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
                    ], className='col-6')
                ], className="row"),
            ], className="col-xl-7"),
        ], className="card-body row"),
    ], className="lineBlock card")


ref_agent_line = html.Div(children=[
    html.H4("Inspector"),
    html.Div(children=[

        html.Div(children=[
            html.H5("Table Filters Selection"),
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
            html.Label(
                children=[
                    'The documentation for the filtering syntax within the data table header can be found ',
                    html.A('here.', href='https://dash.plot.ly/datatable/filtering',
                           target="_blank")]
            ),
            dt.DataTable(
                id="inspection_table",
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                page_action="native",
                page_current=0,
                page_size=20,
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
        ref_agent = best_agents[scenario]["agent"]
    max_loads = episode.load[["value", "equipement_id"]].groupby("equipement_id").max().sort_index()
    max_gens = episode.production[["value", "equipement_id"]].groupby("equipement_id").max().sort_index()
    lines_in_maintenance = list(episode.maintenances['line_name'][episode.maintenances.value == 1].unique())

    graph = make_network_matplotlib(episode)

    # to color assets on our graph with different colors while not overloading it with information
    # we will use plot_obs instead of plot_info for now
    ####
    # For that we override an observation with the desired values
    obs_colored = episode.observations[0]

    # having a rho with value 0.1 give us a blue line while 0.5 gives us an orange line
    # line in maintenance would display as dashed lines
    rho_to_color = np.array([float(0.0) if line in lines_in_maintenance else float(0.4) for line in episode.line_names])
    line_status_colored = np.array([False if line in lines_in_maintenance else True for line in episode.line_names])
    obs_colored.rho = rho_to_color
    obs_colored.line_status = line_status_colored

    obs_colored.load_p = np.array(max_loads.value)
    obs_colored.prod_p = np.array(max_gens.value)

    network_graph = graph.plot_obs(obs_colored, line_info=None)  # )
    # network_graph=graph.plot_info(
    #    #observation=episode.observations[0],
    #    load_values=max_loads.values.flatten(),
    #    load_unit="MW",
    #    gen_values=max_gens.values.flatten(),
    #    gen_unit="MW"
    #    #line_values=[ 1 if line in lines_in_maintenance else 0 for line in  episode.line_names],
    #    #coloring="line"
    # )
    best_agent_ep = make_episode(best_agents[scenario]['agent'], scenario)

    # /!\ As of 2020/10/29 the mpl_to_plotly functions is broken and not maintained
    # It calls a deprecated function of matplotlib.
    # Work around below : insert the image.
    # https://stackoverflow.com/questions/63120058/plotly-mpl-to-plotly-error-spine-object-has-no-attribute-is-frame-like
    buf = io.BytesIO()
    plt.figure(network_graph.number)
    plt.savefig(buf, format='png')
    buf.seek(0)
    encoded_image = base64.b64encode(buf.read())
    buf.close()

    open_help = should_help_open(
        Path(grid2viz_home_directory) / DONT_SHOW_FILENAME("overview")
    )
    header = "Take a look at the Scenario"
    body = "Select a reference agent in the dropdown menu and explore the " \
           "Scenario's characteristics through the eyes of the best agent."
    return html.Div(id="overview_page", children=[
        dcc.Store(id="relayoutStoreOverview"),
        indicators_line(encoded_image.decode()),
        summary_line(episode, ref_agent, scenario),
        ref_agent_line,
        modal(id_suffix="overview", is_open=open_help,
              header=header, body=body)
    ])
