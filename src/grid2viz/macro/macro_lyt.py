import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objects as go
import dash_table as dt
import pandas as pd

from collections import namedtuple

from src.grid2viz.macro.macro_clbk import episode, agent_ref, agents, \
    get_score_agent, get_nb_action_agent, get_nb_overflow_agent, \
    action_repartition_pie
from src.grid2kpi.episode_analytics import actions_model
from src.grid2kpi.episode_analytics.maintenances import hist_duration_maintenances
from src.grid2kpi.manager import make_episode, base_dir, episode_name, agent_ref

layout_def = {
    'legend': {'orientation': 'h'},
    'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0},
}


def indicator_line(episode=episode, agent_name=agent_ref):
    return html.Div(className="lineBlock card", children=[
        html.H4("Indicators"),
        html.Div(className="card-body row", children=[
            html.Div(className="col-2", children=[
                dcc.Dropdown(
                    id='agent_log_selector',
                    options=[{'label': agent, 'value': agent}
                             for agent in agents],
                    value=agent_name,
                    placeholder="Agent log"
                ),
                html.Div(className="m-2", children=[
                    html.P(id="indicator_score_output",
                           className="border-bottom h3 mb-0 text-right",
                           children=get_score_agent(episode)),
                    html.P(className="text-muted", children="Score")
                ]),
                html.Div(className="m-2", children=[
                    html.P(id="indicator_nb_overflow",
                           className="border-bottom h3 mb-0 text-right",
                           children=get_nb_action_agent(episode)),
                    html.P(className="text-muted",
                           children="Number of Overflow")
                ]),
                html.Div(className="m-2", children=[
                    html.P(id="indicator_nb_action",
                           className="border-bottom h3 mb-0 text-right",
                           children=get_nb_overflow_agent(episode)),
                    html.P(className="text-muted ",
                           children="Number of Action")
                ])
            ]),

            html.Div(className="col-3", children=[
                html.H6(className="text-center",
                        children="Type Action Repartition"),
                dcc.Graph(
                    id="agent_study_pie_chart",
                    figure=go.Figure(
                        layout=layout_def,
                        data=action_repartition_pie(episode)
                    )
                )

            ]),

            html.Div(className="col-7", children=[
                html.H6(className="text-center",
                        children="Action Maintenance Duration"),
                dcc.Graph(
                    id="maintenance_duration",
                    figure=maitenance_duration_distrib(episode)
                )
            ])
        ]),
    ])


def overview_line(study_agent=episode, timestamps=None):
    if timestamps is None:
        timestamps = []
    return html.Div(id="overview_line_id", className="lineBlock card", children=[
        html.H4("Overview"),
        html.Div(className="card-body row", children=[

            html.Div(className="col-2", children=[
                dt.DataTable(
                    id="timeseries_table",
                    columns=[{"name": "Timestamps", "id": "Timestamps"}],
                    style_as_list_view=True,
                    row_deletable=True,
                    data=timestamps,
                    filter_action="native",
                    sort_action="native",
                    style_table={
                        'overflow-y': 'scroll',
                        'width': 'auto',
                        'height': '100%'
                    },
                )

            ]),

            html.Div(className="col-10", children=[
                html.Div(className="row", children=[
                    html.Div(className="col-6", children=[
                        html.H6(className="text-center",
                                children="Instant and Cumulated Reward"),
                        dcc.Graph(
                            id="cumulated_rewards_timeserie",
                            figure=go.Figure(
                                layout=layout_def,
                            )
                        )
                    ]),

                    html.Div(className="col-6", children=[
                        html.H6(className="text-center",
                                children="Overflow and Maintenances"),
                        dcc.Graph(
                            id="overflow_graph_study",
                            figure=go.Figure(
                                layout=layout_def,
                                data=[dict(type="scatter")]
                            )
                        )
                    ]),
                ]),

                html.Div(className="row", children=[
                    html.Div(className="col-6", children=[
                        html.H6(className="text-center", children="Actions"),
                        dcc.Graph(
                            id="action_timeserie",
                            figure=go.Figure(
                                layout=layout_def,
                                data=[dict(type="scatter")]
                            )
                        )
                    ]),
                    html.Div(className="col-6", children=[
                        html.H6(className="text-center",
                                children="Usage Rate"),
                        dcc.Graph(
                            id="usage_rate_graph_study",
                            figure=go.Figure(
                                layout=layout_def,
                                data=[dict(type="scatter")]
                            )
                        )
                    ]),
                ]),
            ])
        ])
    ])


def inspector_line(table_cols, table_data, episode):
    actions_distribution = action_distrubtion(episode)
    return html.Div(className="lineBlock card ", children=[
        html.H4("Inspector"),
        html.Div(className="card-body col row", children=[
            html.Div(className="col", children=[
                dt.DataTable(
                    id="inspector_datable",
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    page_action="native",
                    page_current=0,
                    page_size=20,
                    style_table={
                        'overflow': 'auto',
                        'width': '100%',
                        'max-width': '100%',
                        'height': '200px'
                    },
                    columns=table_cols,
                    data=table_data
                ),
                html.Label(children=[
                    'The documentation for the filtering syntax can be found ',
                    html.A('here.', href='https://dash.plot.ly/datatable/filtering', target="_blank")]),
            ]),
            html.Div(className="col-12 row", children=[
                html.Div(className="col", children=[
                    html.P(id="tooltip_table", className="more-info-table", children=[
                        "Click on a row to have more info on the action"
                    ])
                ])
            ]),
            html.Div(className="col-12 row", children=[
                html.Div(className="col", children=[
                    html.H6(className="text-center",
                            children="Distribution of Substation action"),
                    dcc.Graph(
                        id="distribution_substation_action_chart",
                        figure=actions_distribution.on_subs
                    )
                ]),
                html.Div(className="col", children=[
                    html.H6(className="text-center",
                            children="Distribution of line action"),
                    dcc.Graph(
                        id="distribution_line_action_chart",
                        figure=actions_distribution.on_lines
                    )
                ]),
            ]),

        ])
    ])


def get_table(episode):
    table = actions_model.get_action_table_data(episode)
    return [{"name": i, "id": i} for i in table.columns], table.to_dict("record")


def maitenance_duration_distrib(episode):
    figure = go.Figure(
        layout=layout_def,
        data=[go.Histogram(x=hist_duration_maintenances(episode))]
    )
    return figure


ActionsDistribution = namedtuple("ActionsDistribution", ["on_subs", "on_lines"])


def action_distrubtion(episode):
    figure_subs = go.Figure(
        layout=layout_def,
        data=actions_model.get_action_per_sub(episode)
    )
    figure_lines = go.Figure(
        layout=layout_def,
        data=actions_model.get_action_per_line(episode)
    )
    return ActionsDistribution(on_subs=figure_subs, on_lines=figure_lines)


def layout(study_agent=episode, timestamps=None):
    new_episode = make_episode(study_agent, episode_name)
    return html.Div(id="overview_page", children=[
        dcc.Store(id='relayoutStoreMacro'),
        # TODO I don't know where the layout param is filled this is a temporary trick to get the whole default episode
        indicator_line(new_episode, study_agent),
        overview_line(new_episode, timestamps),
        inspector_line(*get_table(new_episode), new_episode)
    ])
