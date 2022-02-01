# Copyright (C) 2021, RTE (http://www.rte-france.com/)
# See AUTHORS.txt
# SPDX-License-Identifier: MPL-2.0

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
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import plotly.graph_objects as go

from grid2viz.src.manager import (
    agent_scenario,
    make_episode,
    best_agents,
    grid2viz_home_directory,
    make_network_scenario_overview,
)
from grid2viz.src.utils.constants import DONT_SHOW_FILENAME
from grid2viz.src.utils.layout_helpers import modal, should_help_open

layout_def = {
    "legend": {"orientation": "h"},
    "showlegend": True,
    "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
}

layout_pie = {
    "legend": {"orientation": "h"},
    "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
}


def indicators_line(encoded_image):
    return html.Div(
        id="indicator_line",
        children=[
            html.H4("Indicators"),
            html.Div(
                children=[
                    html.Div(
                        [
                            html.H5("Distribution of Daily Load Profiles (MW)"),
                            dcc.Graph(
                                id="indicator_line_charts",
                                style={"margin-top": "1em"},
                                figure=go.Figure(layout=layout_def),
                            ),
                        ],
                        className="col-xl-5",
                    ),
                    html.Div(
                        children=[
                            html.H5("Production Shares"),
                            dcc.Graph(
                                id="production_share_graph",
                                figure=go.Figure(layout=layout_pie),
                            ),
                        ],
                        className="col-xl-4",
                    ),
                    # number summary column
                    html.Div(
                        children=[
                            html.Div(
                                className="mb-4",
                                children=[
                                    html.P(
                                        id="nb_steps_card",
                                        className="border-bottom h3 mb-0 text-right",
                                        children="",
                                    ),
                                    html.P(
                                        className="text-muted",
                                        children="Best Agent's Steps (step / nb actions)",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="mb-4",
                                children=[
                                    html.P(
                                        id="nb_hazard_card",
                                        className="border-bottom h3 mb-0 text-right",
                                        children="",
                                    ),
                                    html.P(
                                        className="text-muted",
                                        children="Number of Hazards",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="mb-4",
                                children=[
                                    html.P(
                                        id="nb_maintenance_card",
                                        className="border-bottom h3 mb-0 text-right",
                                        children="",
                                    ),
                                    html.P(
                                        className="text-muted",
                                        children="Number of Maintenances",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="mb-4",
                                children=[
                                    html.P(
                                        id="duration_maintenance_card",
                                        className="border-bottom h3 mb-0 text-right",
                                        children="",
                                    ),
                                    html.P(
                                        className="text-muted",
                                        children="Maintenances Duration (min)",
                                    ),
                                ],
                            ),
                        ],
                        className="col-xl-3 align-self-center",
                    ),
                    html.Div(
                        [
                            html.H5(
                                "Max prod & laod values and dashed lines in maintenance on Power grid",
                                style={"margin-top": "2%"},
                            ),
                            #dcc.Graph(id="network_actions", figure=encoded_image),
                            html.Img(
                                src="data:image/png;base64,{}".format(encoded_image)
                            ),
                        ],
                        className="col-xl-8",
                    ),
                ],
                className="card-body row",
            ),
        ],
        className="lineBlock card",
    )


def summary_line(episode, ref_agent, scenario):
    return html.Div(
        children=[
            html.H4("Summary"),
            html.Div(
                children=[
                    html.Div(
                        children=[
                            html.H5("Environment Time Series"),
                            dac.Radio(
                                options=[
                                    {"label": "Production (MW)", "value": "Production"},
                                    {"label": "Load (MW)", "value": "Load"},
                                    {"label": "Hazards", "value": "Hazards"},
                                    {"label": "Maintenances", "value": "Maintenances"},
                                ],
                                value="Production",
                                id="scen_overview_ts_switch",
                                buttonStyle="solid",
                            ),
                            dac.Select(
                                id="input_assets_selector",
                                options=[
                                    {"label": prod_name, "value": prod_name}
                                    for prod_name in episode.prod_names
                                ],
                                value="solar",
                                mode="multiple",
                                showArrow=True,
                            ),
                            dcc.Graph(
                                id="input_env_charts",
                                style={"margin-top": "1em"},
                                figure=go.Figure(layout=layout_def),
                                config=dict(displayModeBar=False),
                            ),
                        ],
                        className="col-xl-5",
                    ),
                    html.Div(
                        children=[
                            html.H5("Reference agent Metrics"),
                            # dcc.Dropdown(
                            #     id="input_agent_selector", placeholder="select a ref agent",
                            #     options=[{'label': agent, 'value': agent}
                            #              for agent in agent_scenario[scenario]],
                            #     value=ref_agent
                            # ),
                            html.Div(
                                children=[
                                    html.Div(
                                        children=[
                                            html.H5(
                                                "Usage rate", className="text-center"
                                            ),
                                            dcc.Graph(
                                                id="usage_rate_graph",
                                                style={"margin-top": "1em"},
                                                figure=go.Figure(layout=layout_def),
                                                config=dict(displayModeBar=False),
                                            ),
                                        ],
                                        className="col-6",
                                    ),
                                    html.Div(
                                        children=[
                                            html.H5(
                                                "Overflow", className="text-center"
                                            ),
                                            dcc.Graph(
                                                id="overflow_graph",
                                                style={"margin-top": "1em"},
                                                figure=go.Figure(layout=layout_def),
                                                config=dict(displayModeBar=False),
                                            ),
                                        ],
                                        className="col-6",
                                    ),
                                ],
                                className="row",
                            ),
                        ],
                        className="col-xl-7",
                    ),
                ],
                className="card-body row",
            ),
        ],
        className="lineBlock card",
    )


ref_agent_line = html.Div(
    children=[
        html.H4("Inspector"),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.H5("Table Filters Selection"),
                        dcc.DatePickerRange(
                            id="date_range",
                            display_format="MMM Do, YY",
                        ),
                        html.H5("Loads"),
                        dcc.Dropdown(
                            id="select_loads_for_tb",
                            options=[],
                            multi=True,
                            style=dict(marginBottom="1em"),
                        ),
                        html.H5("Generators"),
                        dcc.Dropdown(
                            id="select_prods_for_tb",
                            options=[],
                            multi=True,
                            style=dict(marginBottom="1em"),
                        ),
                    ],
                    className="col-xl-2",
                ),
                html.Div(
                    children=[
                        html.Label(
                            children=[
                                "The documentation for the filtering syntax within the data table header can be found ",
                                html.A(
                                    "here.",
                                    href="https://dash.plot.ly/datatable/filtering",
                                    target="_blank",
                                ),
                            ]
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
                    ],
                    className="col-xl-10",
                ),
            ],
            className="col-xl-10 p-2",
        ),
    ],
    className="lineBlock card",
)


def layout(scenario, ref_agent):
    try:
        episode = make_episode(best_agents[scenario]["agent"], scenario)
    except Exception as ex:
        print(ex)
        return
    if ref_agent is None:
        ref_agent = agent_scenario[scenario][0]

    #fig = plt.figure()
    make_network_scenario_overview(episode)
#
    ## /!\ As of 2020/10/29 the mpl_to_plotly functions is broken and not maintained
    ## It calls a deprecated function of matplotlib.
    ## Work around below : insert the image.
    ## https://stackoverflow.com/questions/63120058/plotly-mpl-to-plotly-error-spine-object-has-no-attribute-is-frame-like
    buf = io.BytesIO()
    #plt.figure(network_graph.number)
    #plt.close(fig)
    plt.savefig(buf, format="png")
    buf.seek(0)
    encoded_image = base64.b64encode(buf.read())
    buf.close()
#
    open_help = should_help_open(
        Path(grid2viz_home_directory) / DONT_SHOW_FILENAME("overview")
    )
    header = "Take a deeper look at the Scenario"
    body = (
        "Look at the grid, inspect indicators as well as chronics"
        "Select a reference agent in the dropdown menu to get a sense of flows and overflows over the scenario"
        "When done, move to Agent Overview section. The reference agent will be used there as baseline to compare with"
    )
    return html.Div(
        id="overview_page",
        children=[
            dcc.Store(id="relayoutStoreOverview"),
            indicators_line(encoded_image.decode()),
            summary_line(episode, ref_agent, scenario),
            ref_agent_line,
            modal(id_suffix="overview", is_open=open_help, header=header, body=body),
        ],
    )
