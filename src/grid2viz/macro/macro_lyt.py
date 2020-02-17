import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objects as go
import dash_table as dt

from collections import namedtuple

from src.grid2viz.macro.macro_clbk import agents, get_score_agent, get_nb_action_agent, get_nb_overflow_agent, \
    action_repartition_pie
from src.grid2kpi.episode_analytics import actions_model
from src.grid2kpi.episode_analytics.maintenances import hist_duration_maintenances
from src.grid2kpi.manager import make_episode

layout_def = {
    'legend': {'orientation': 'h'},
    'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0},
}


def indicator_line(scenario):
    return html.Div(className="lineBlock card", children=[
        html.H4("Indicators"),
        html.Div(className="card-body row", children=[
            html.Div(className="col-2", children=[
                dcc.Dropdown(
                    id='agent_log_selector',
                    options=[{'label': agent, 'value': agent}
                             for agent in agents],
                    value=agents[0],
                    placeholder="Agent log"
                ),
                html.Div(className="m-2", children=[
                    html.P(id="indicator_score_output",
                           className="border-bottom h3 mb-0 text-right",
                           children=""),
                    html.P(className="text-muted", children="Score")
                ]),
                html.Div(className="m-2", children=[
                    html.P(id="indicator_nb_overflow",
                           className="border-bottom h3 mb-0 text-right",
                           children=""),
                    html.P(className="text-muted",
                           children="Number of Overflow")
                ]),
                html.Div(className="m-2", children=[
                    html.P(id="indicator_nb_action",
                           className="border-bottom h3 mb-0 text-right",
                           children=""),
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
                        layout=layout_def
                    )
                )

            ]),

            html.Div(className="col-7", children=[
                html.H6(className="text-center",
                        children="Action Maintenance Duration"),
                dcc.Graph(
                    id="maintenance_duration",
                    figure=go.Figure(
                        layout=layout_def
                    )
                )
            ])
        ]),
    ])


def overview_line(timestamps=None):
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
                ),
                html.Div(html.P(
                    'Select an Actions on the "Instant and Accumulated Reward" '
                    'Time Serie to study it on the next page'
                ), className='mt-1')
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


def inspector_line():
    return html.Div(className="lineBlock card ", children=[
        html.H4("Inspector For Study Agent", style={'margin-left': '-50px'}),
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
                    }
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
                        figure=go.Figure(
                            layout=layout_def,
                        )
                    )
                ]),
                html.Div(className="col", children=[
                    html.H6(className="text-center",
                            children="Distribution of line action"),
                    dcc.Graph(
                        id="distribution_line_action_chart",
                        figure=go.Figure(
                            layout=layout_def,
                        )
                    )
                ]),
            ]),

        ])
    ])


def get_table(episode):
    table = actions_model.get_action_table_data(episode)
    return [{"name": i, "id": i} for i in table.columns], table.to_dict("record")


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


def layout(timestamps, scenario):
    return html.Div(id="overview_page", children=[
        dcc.Store(id='relayoutStoreMacro'),
        indicator_line(scenario),
        overview_line(timestamps),
        inspector_line()
    ])
