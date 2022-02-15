# Copyright (C) 2021, RTE (http://www.rte-france.com/)
# See AUTHORS.txt
# SPDX-License-Identifier: MPL-2.0

from collections import namedtuple
from pathlib import Path

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import plotly.graph_objects as go

from grid2viz.src.kpi import actions_model
from grid2viz.src.manager import (
    make_episode,
    agents,
    make_network_agent_overview,
    best_agents,
    grid2viz_home_directory,
)
from grid2viz.src.utils.constants import DONT_SHOW_FILENAME
from grid2viz.src.utils.graph_utils import layout_def, layout_no_data, max_or_zero
from grid2viz.src.utils.layout_helpers import modal, should_help_open


def indicator_line(scenario, study_agent, ref_agent):
    episode = make_episode(study_agent, scenario)
    ref_episode = make_episode(ref_agent, scenario)
    figures_distribution = action_distrubtion(episode, ref_episode)

    network_graph = make_network_agent_overview(episode)

    nb_actions = episode.action_data_table[
        ["action_line", "action_subs", "action_redisp"]
    ].sum()

    if nb_actions.sum() == 0:
        pie_figure = go.Figure(layout=layout_no_data("No Actions for this Agent"))
    else:
        pie_figure = go.Figure(
            layout=layout_def,
            data=[
                go.Pie(
                    labels=[
                        "Actions on Lines",
                        "Actions on Substations",
                        "Redispatching Actions",
                    ],
                    values=[
                        nb_actions["action_line"],
                        nb_actions["action_subs"],
                        nb_actions["action_redisp"],
                    ],
                )
            ],
        )

    return html.Div(
        className="lineBlock card",
        children=[
            html.H4("Indicators"),
            html.Div(
                className="card-body row",
                children=[
                    html.Div(
                        className="col-2",
                        children=[
                            html.H5("Study Agent Summary"),
                            html.Div(
                                className="m-2",
                                children=[
                                    html.P(
                                        id="indicator_score_output",
                                        className="border-bottom h3 mb-0 text-right",
                                        children=round(
                                            episode.meta["cumulative_reward"]
                                        ),
                                    ),
                                    html.P(className="text-muted", children="Score"),
                                ],
                            ),
                            html.Div(
                                className="m-2",
                                children=[
                                    html.P(
                                        id="indicator_survival_time",
                                        className="border-bottom h3 mb-0 text-right",
                                        children="{}/{}".format(
                                            episode.meta["nb_timestep_played"],
                                            episode.meta["chronics_max_timestep"],
                                        ),
                                    ),
                                    html.P(
                                        className="text-muted",
                                        children="Agent's Survival",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="m-2",
                                children=[
                                    html.P(
                                        id="indicator_nb_overflow",
                                        className="border-bottom h3 mb-0 text-right",
                                        children=episode.total_overflow_ts[
                                            "value"
                                        ].sum(),
                                    ),
                                    html.P(
                                        className="text-muted",
                                        children="Number of Overflow",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="m-2",
                                children=[
                                    html.P(
                                        id="indicator_nb_action",
                                        className="border-bottom h3 mb-0 text-right",
                                        children=episode.action_data_table[
                                            ["action_line", "action_subs"]
                                        ]
                                        .sum(axis=1)
                                        .sum(),
                                    ),
                                    html.P(
                                        className="text-muted ",
                                        children="Number of Action",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="m-2",
                                children=[
                                    html.P(
                                        id="indicator_nb_maintenances",
                                        className="border-bottom h3 mb-0 text-right",
                                        children=episode.nb_maintenances,
                                    ),
                                    html.P(
                                        className="text-muted",
                                        children="Number of Maintenances",
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        className="col-3",
                        children=[
                            html.H6(
                                className="text-center",
                                children="Type Action Repartition",
                            ),
                            dcc.Graph(id="agent_study_pie_chart", figure=pie_figure),
                        ],
                    ),
                    html.Div(
                        className="col-7",
                        children=[
                            html.H6(
                                className="text-center",
                                children="Impacted grid assets: attacks (dash orange) & overflow (red) and subs with action",
                            ),
                            dcc.Graph(id="network_actions", figure=network_graph),
                        ],
                    ),
                    html.Div(
                        className="col-12",
                        children=[
                            html.H2(
                                className="text-center",
                                children="Actions Distributions",
                            )
                        ],
                    ),
                    html.Div(
                        className="col-4",
                        children=[
                            html.H6(className="text-center", children="On Substations"),
                            dcc.Graph(
                                id="distribution_substation_action_chart",
                                figure=figures_distribution.on_subs,
                            ),
                        ],
                    ),
                    html.Div(
                        className="col-4",
                        children=[
                            html.H6(className="text-center", children="On Lines"),
                            dcc.Graph(
                                id="distribution_line_action_chart",
                                figure=figures_distribution.on_lines,
                            ),
                        ],
                    ),
                    html.Div(
                        className="col-4",
                        children=[
                            html.H6(className="text-center", children="Redispatching"),
                            dcc.Graph(
                                id="distribution_redisp_action_chart",
                                figure=figures_distribution.redisp,
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def overview_line(timestamps=None, from_scenario_selection=True):
    if timestamps is None or from_scenario_selection:
        timestamps = []
    return html.Div(
        id="overview_line_id",
        className="lineBlock card",
        children=[
            html.H4("Overview"),
            html.Div(
                className="card-body row",
                children=[
                    html.Div(
                        className="col-2",
                        children=[
                            html.H4("Agent study Timestep selection"),
                            dt.DataTable(
                                id="timeseries_table",
                                columns=[{"name": "Timestamps", "id": "Timestamps"}],
                                style_as_list_view=True,
                                row_deletable=True,
                                data=timestamps,
                                filter_action="native",
                                sort_action="native",
                                style_table={
                                    "overflow-y": "scroll",
                                    # 'width': 'auto',
                                    "height": "100%",
                                },
                            ),
                            html.Div(
                                html.P(
                                    'Interactively select a timestep by clicking on the "Instant and Accumulated Reward" '
                                    "Time Serie to study it on the next page"
                                ),
                                className="mt-1",
                            ),
                        ],
                    ),
                    html.Div(
                        className="col-10",
                        children=[
                            html.Div(
                                className="row",
                                children=[
                                    html.Div(
                                        className="col-6",
                                        children=[
                                            html.H6(
                                                className="text-center",
                                                children="Instant and Cumulated Reward",
                                            ),
                                            dbc.Tabs(
                                                children=[
                                                    dbc.Tab(
                                                        label="Instant Reward",
                                                        children=[
                                                            dcc.Graph(
                                                                id="rewards_timeserie",
                                                                figure=go.Figure(
                                                                    layout=layout_def,
                                                                ),
                                                            )
                                                        ],
                                                    ),
                                                    dbc.Tab(
                                                        label="Cumulated Reward",
                                                        children=[
                                                            dcc.Graph(
                                                                id="cumulated_rewards_timeserie",
                                                                figure=go.Figure(
                                                                    layout=layout_def,
                                                                ),
                                                            )
                                                        ],
                                                    ),
                                                ]
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="col-6",
                                        children=[
                                            html.H6(
                                                className="text-center",
                                                children="Overflow, Maintenances, Hazards and Attacks",
                                            ),
                                            dcc.Graph(
                                                id="overflow_graph_study",
                                                figure=go.Figure(
                                                    layout=layout_def,
                                                    data=[dict(type="scatter")],
                                                ),
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            html.Div(
                                className="row",
                                children=[
                                    html.Div(
                                        className="col-6",
                                        children=[
                                            html.H6(
                                                className="text-center",
                                                children="Distance from reference grid configuration",
                                            ),
                                            dcc.Graph(
                                                id="action_timeserie",
                                                figure=go.Figure(
                                                    layout=layout_def,
                                                    data=[dict(type="scatter")],
                                                ),
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="col-6",
                                        children=[
                                            html.H6(
                                                className="text-center",
                                                children="Usage Rate",
                                            ),
                                            dcc.Graph(
                                                id="usage_rate_graph_study",
                                                figure=go.Figure(
                                                    layout=layout_def,
                                                    data=[dict(type="scatter")],
                                                ),
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def inspector_line(study_agent, scenario):
    new_episode = make_episode(study_agent, scenario)
    cols, data = get_table(new_episode)

    data_table = dt.DataTable(
        columns=cols,
        data=data,
        id="inspector_datable",
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        page_action="native",
        page_current=0,
        page_size=7,
    )

    return html.Div(
        className="lineBlock card ",
        children=[
            html.H4("Inspector For Study Agent"),
            html.Div(
                className="container-fluid",
                id="action_table_div",
                children=[
                    html.Div(
                        className="row",
                        children=[
                            html.Div(
                                className="col flex-center", children=[data_table]
                            ),
                        ],
                    ),
                    html.Div(
                        className="row",
                        children=[
                            html.Div(
                                className="col flex-center",
                                children=[
                                    html.Label(
                                        children=[
                                            "The documentation for the filtering syntax can be found ",
                                            html.A(
                                                "here.",
                                                href="https://dash.plot.ly/datatable/filtering",
                                                target="_blank",
                                            ),
                                        ]
                                    ),
                                ],
                            )
                        ],
                    ),
                    html.Div(
                        className="row",
                        children=[
                            html.Div(
                                className="col",
                                children=[
                                    html.P(
                                        id="tooltip_table",
                                        className="more-info-table",
                                        children=[
                                            "Click on a row to have more info on the action"
                                        ],
                                    )
                                ],
                            )
                        ],
                    ),
                ],
            ),
        ],
    )


def get_table(episode):
    table = actions_model.get_action_table_data(episode)
    table["id"] = table["timestep"]
    table["timestep_reward"] = table["timestep_reward"].map(
        lambda x: "{:,.2f}".format(float("".join(str(x).split(","))))
    )
    table.set_index("id", inplace=True, drop=False)
    cols_to_exclude = ["id", "lines_modified", "subs_modified"]
    return [
        {"name": i, "id": i} for i in table.columns if i not in cols_to_exclude
    ], table.to_dict("record")


ActionsDistribution = namedtuple(
    "ActionsDistribution", ["on_subs", "on_lines", "redisp"]
)


def action_distrubtion(episode, ref_episode):
    actions_per_sub = actions_model.get_action_per_sub(episode)
    actions_per_sub.append(actions_model.get_action_per_sub(ref_episode)[0])
    y_max = None

    if len(actions_per_sub[0]["y"]) == 0:
        figure_subs = go.Figure(
            layout=layout_no_data("No Actions on subs for this Agent")
        )
    else:
        figure_subs = go.Figure(layout=layout_def, data=actions_per_sub)
        y_max = max(map(max_or_zero, [trace.y for trace in actions_per_sub])) + 1

    actions_per_lines = actions_model.get_action_per_line(episode)
    actions_per_lines.append(actions_model.get_action_per_line(ref_episode)[0])

    if len(actions_per_lines[0]["y"]) == 0:
        figure_lines = go.Figure(
            layout=layout_no_data("No Actions on lines for this Agent")
        )
    else:
        figure_lines = go.Figure(layout=layout_def, data=actions_per_lines)
        if y_max is None:
            y_max = max(map(max_or_zero, [trace.y for trace in actions_per_lines])) + 1
        if max(map(max_or_zero, [trace.y for trace in actions_per_lines])) > y_max:
            y_max = max(map(max_or_zero, [trace.y for trace in actions_per_lines])) + 1

    actions_redisp = actions_model.get_action_redispatch(episode)
    actions_redisp.append(actions_model.get_action_redispatch(ref_episode)[0])

    if len(actions_redisp[0]["y"]) == 0:
        figure_redisp = go.Figure(
            layout=layout_no_data("No redispatching actions for this Agent")
        )
    else:
        figure_redisp = go.Figure(layout=layout_def, data=actions_redisp)
        if y_max is None:
            y_max = max(map(max_or_zero, [trace.y for trace in actions_redisp])) + 1
        if max(map(max_or_zero, [trace.y for trace in actions_redisp])) > y_max:
            y_max = max(map(max_or_zero, [trace.y for trace in actions_redisp])) + 1

    if y_max:
        figure_subs.update_yaxes(range=[0, y_max])
        figure_lines.update_yaxes(range=[0, y_max])
        figure_redisp.update_yaxes(range=[0, y_max])

    return ActionsDistribution(
        on_subs=figure_subs, on_lines=figure_lines, redisp=figure_redisp
    )


def layout(timestamps, scenario, study_agent, ref_agent, from_scenario_selection):
    if study_agent is None:
        study_agent = best_agents[scenario]["agent"]
    open_help = should_help_open(
        Path(grid2viz_home_directory) / DONT_SHOW_FILENAME("macro")
    )
    header = "Take a look at your agent"
    body = (
        "Select an agent to study in the dropdown menu and analyse it with "
        "respect to the reference agent. Click on the reward graph to select "
        "some time steps to study further your agent. When you have selected time steps, "
        "go on to the Study agent view."
    )

    return html.Div(
        id="macro_page",
        children=[
            dcc.Store(id="relayoutStoreMacro"),
            indicator_line(scenario, study_agent, ref_agent),
            overview_line(timestamps, from_scenario_selection),
            inspector_line(study_agent, scenario),
            modal(id_suffix="macro", is_open=open_help, header=header, body=body),
        ],
    )
