# Copyright (C) 2021, RTE (http://www.rte-france.com/)
# See AUTHORS.txt
# SPDX-License-Identifier: MPL-2.0

import datetime as dt

import dash_core_components as dcc
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from grid2op.Exceptions import Grid2OpException
from pathlib import Path

from grid2viz.src.manager import grid2viz_home_directory
from grid2viz.src.manager import make_episode, make_network_agent_study
from grid2viz.src.utils import common_graph
from grid2viz.src.utils.callbacks_helpers import toggle_modal_helper
from grid2viz.src.utils.constants import DONT_SHOW_FILENAME
from grid2viz.src.utils.graph_utils import (
    relayout_callback,
    get_axis_relayout,
    layout_no_data,
)


def register_callbacks_micro(app):
    @app.callback(
        [
            Output("slider", "min"),
            Output("slider", "max"),
            Output("slider", "value"),
            Output("slider", "marks"),
        ],
        [Input("window", "data")],
        [
            State("slider", "value"),
            State("user_timestamps", "value"),
            State("agent_study", "data"),
            State("scenario", "data"),
        ],
    )
    def update_slider(window, value, selected_timestamp, study_agent, scenario):
        if window is None:
            raise PreventUpdate
        new_episode = make_episode(study_agent, scenario)

        min_ = new_episode.timestamps.index(
            dt.datetime.strptime(window[0], "%Y-%m-%dT%H:%M:%S")
        )
        max_ = new_episode.timestamps.index(
            dt.datetime.strptime(window[1], "%Y-%m-%dT%H:%M:%S")
        )
        if value not in range(min_, max_):
            value = new_episode.timestamps.index(
                dt.datetime.strptime(selected_timestamp, "%Y-%m-%d %H:%M")
            )

        marks = dict(enumerate(map(lambda x: x.time(), new_episode.timestamps)))

        return min_, max_, value, marks

    @app.callback(
        Output("relayoutStoreMicro", "data"),
        [
            Input("env_charts_ts", "relayoutData"),
            Input("usage_rate_ts", "relayoutData"),
            Input("overflow_ts", "relayoutData"),
            Input("rewards_ts", "relayoutData"),
            Input("cumulated_rewards_ts", "relayoutData"),
            Input("actions_ts", "relayoutData"),
            Input("voltage_flow_graph", "relayoutData"),
        ],
        [State("relayoutStoreMicro", "data")],
    )
    def relayout_store_overview(*args):
        return relayout_callback(*args)

    # indicator line
    @app.callback(
        [
            Output("rewards_ts", "figure"),
            Output("cumulated_rewards_ts", "figure"),
            Output("actions_ts", "figure"),
        ],
        [
            Input("relayoutStoreMicro", "data"),
            Input("window", "data"),
            State("agent_study", "data"),
        ],
        [
            State("rewards_ts", "figure"),
            State("cumulated_rewards_ts", "figure"),
            State("actions_ts", "figure"),
            State("agent_ref", "data"),
            State("scenario", "data"),
        ],
    )
    def load_ts(
        relayout_data_store,
        window,
        study_agent,
        rew_figure,
        cumrew_figure,
        actions_figure,
        agent_ref,
        scenario,
    ):

        figures = [rew_figure, cumrew_figure, actions_figure]

        condition = (
            relayout_data_store is not None and relayout_data_store["relayout_data"]
        )
        if condition:
            relayout_data = relayout_data_store["relayout_data"]
            relayouted = False
            for figure in figures:
                axis_layout = get_axis_relayout(figure, relayout_data)
                if axis_layout is not None:
                    figure["layout"].update(axis_layout)
                    relayouted = True
            if relayouted:
                return figures

        rew_figure, cumrew_figure = common_graph.make_rewards_ts(
            study_agent, agent_ref, scenario, rew_figure, cumrew_figure
        )

        actions_figure = common_graph.make_action_ts(
            study_agent, agent_ref, scenario, actions_figure["layout"]
        )

        figures = [rew_figure, cumrew_figure, actions_figure]

        if window is not None:
            start_datetime = dt.datetime.strptime(window[0], "%Y-%m-%dT%H:%M:%S")
            end_datetime = dt.datetime.strptime(window[-1], "%Y-%m-%dT%H:%M:%S")
            for figure in figures:
                figure["layout"].update(
                    xaxis=dict(range=[start_datetime, end_datetime], autorange=False)
                )

        return figures

    # flux line callback
    @app.callback(
        [Output("line_side_choices", "options"), Output("line_side_choices", "value")],
        [Input("voltage_flow_choice", "value"), Input("flow_radio", "value")],
        [State("agent_study", "data"), State("scenario", "data")],
    )
    def load_voltage_flow_line_choice(category, flow_choice, study_agent, scenario):
        option = []
        new_episode = make_episode(study_agent, scenario)

        if category == "voltage":
            for name in new_episode.line_names:
                option.append({"label": "ex_" + name, "value": "ex_" + name})
                option.append({"label": "or_" + name, "value": "or_" + name})
        if category == "flow":
            for name in new_episode.line_names:
                if flow_choice == "active_flow":
                    option.append(
                        {"label": "ex_active_" + name, "value": "ex_active_" + name}
                    )
                    option.append(
                        {"label": "or_active_" + name, "value": "or_active_" + name}
                    )
                if flow_choice == "current_flow":
                    option.append(
                        {"label": "ex_current_" + name, "value": "ex_current_" + name}
                    )
                    option.append(
                        {"label": "or_current_" + name, "value": "or_current_" + name}
                    )

                if flow_choice == "flow_usage_rate":
                    option.append(
                        {"label": "usage_rate_" + name, "value": "usage_rate_" + name}
                    )
        if category == "redispatch":
            option = [
                {"label": gen_name, "value": gen_name}
                for gen_name in new_episode.prod_names
            ]

        return option, [option[0]["value"]]

    @app.callback(
        Output("voltage_flow_graph", "figure"),
        [
            Input("line_side_choices", "value"),
            Input("voltage_flow_choice", "value"),
            Input("relayoutStoreMicro", "data"),
            Input("window", "data"),
        ],
        [
            State("voltage_flow_graph", "figure"),
            State("agent_study", "data"),
            State("scenario", "data"),
        ],
    )
    def load_flow_voltage_graph(
        selected_objects,
        choice,
        relayout_data_store,
        window,
        figure,
        study_agent,
        scenario,
    ):
        if relayout_data_store is not None and relayout_data_store["relayout_data"]:
            relayout_data = relayout_data_store["relayout_data"]
            layout = figure["layout"]
            new_axis_layout = get_axis_relayout(figure, relayout_data)
            if new_axis_layout is not None:
                layout.update(new_axis_layout)
                return figure
        new_episode = make_episode(study_agent, scenario)
        if selected_objects is not None:
            if choice == "voltage":
                figure["data"] = load_voltage_for_lines(selected_objects, new_episode)
            if "flow" in choice:
                figure["data"] = load_flows_for_lines(selected_objects, new_episode)
            if "redispatch" in choice:
                figure["data"] = load_redispatch(selected_objects, new_episode)

        if window is not None:
            figure["layout"].update(xaxis=dict(range=window, autorange=False))

        return figure

    @app.callback(
        Output("flow_radio", "style"),
        [Input("voltage_flow_choice", "value")],
    )
    def load_flow_graph(choice):
        if choice == "flow":
            return {"display": "block"}
        else:
            return {"display": "none"}

    def load_voltage_for_lines(lines, new_episode):
        voltage = new_episode.flow_and_voltage_line
        traces = []

        for value in lines:
            # the first 2 characters are the side of line ('ex' or 'or')
            line_side = str(value)[:2]
            line_name = str(value)
            if line_side == "ex":
                traces.append(
                    go.Scatter(
                        x=new_episode.timestamps,
                        # remove the first 3 char to get the line name and round to 3 dec
                        y=voltage["ex"]["voltage"][line_name[3:]],
                        name=line_name,
                    )
                )
            if line_side == "or":
                traces.append(
                    go.Scatter(
                        x=new_episode.timestamps,
                        y=voltage["or"]["voltage"][line_name[3:]],
                        name=line_name,
                    )
                )
        return traces

    def load_redispatch(generators, new_episode):
        actual_dispatch = new_episode.actual_redispatch
        target_dispatch = new_episode.target_redispatch
        traces = []

        x = new_episode.timestamps

        for gen in generators:
            traces.append(
                go.Scatter(x=x, y=actual_dispatch[gen], name=f"{gen} actual dispatch")
            )
            traces.append(
                go.Scatter(x=x, y=target_dispatch[gen], name=f"{gen} target dispatch")
            )

        return traces

    def load_flows_for_lines(lines, new_episode):
        flow = new_episode.flow_and_voltage_line
        traces = []

        x = new_episode.timestamps

        for value in lines:
            line_side = str(value)[
                :2
            ]  # the first 2 characters are the side of line ('ex' or 'or')
            flow_type = str(value)[3:].split("_", 1)[
                0
            ]  # the type is the 1st part of the string: 'type_name'
            line_name = str(value)[3:].split("_", 1)[
                1
            ]  # the name is the 2nd part of the string: 'type_name'
            if line_side == "ex":
                traces.append(
                    go.Scatter(x=x, y=flow["ex"][flow_type][line_name], name=value)
                )
            elif line_side == "or":
                traces.append(
                    go.Scatter(x=x, y=flow["or"][flow_type][line_name], name=value)
                )
            else:  # this concern usage rate
                name = value.split("_", 2)[2]  # get the powerline name
                index_powerline = list(new_episode.line_names).index(name)
                usage_rate_powerline = new_episode.rho.loc[
                    new_episode.rho["equipment"] == index_powerline
                ]["value"]

                traces.append(go.Scatter(x=x, y=usage_rate_powerline, name=name))

        return traces

    # context line callback
    @app.callback(
        [Output("asset_selector", "options"), Output("asset_selector", "value")],
        [Input("environment_choices_buttons", "value")],
        [State("agent_study", "data"), State("scenario", "data")],
    )
    def update_ts_graph_avail_assets(kind, study_agent, scenario):
        new_episode = make_episode(study_agent, scenario)
        return common_graph.ts_graph_avail_assets(kind, new_episode)

    @app.callback(
        Output("env_charts_ts", "figure"),
        [
            Input("asset_selector", "value"),
            Input("relayoutStoreMicro", "data"),
            Input("window", "data"),
        ],
        [
            State("env_charts_ts", "figure"),
            State("environment_choices_buttons", "value"),
            State("scenario", "data"),
            State("agent_study", "data"),
        ],
    )
    def load_context_data(
        equipments, relayout_data_store, window, figure, kind, scenario, agent_study
    ):
        if relayout_data_store is not None and relayout_data_store["relayout_data"]:
            relayout_data = relayout_data_store["relayout_data"]
            layout = figure["layout"]
            new_axis_layout = get_axis_relayout(figure, relayout_data)
            if new_axis_layout is not None:
                layout.update(new_axis_layout)
                return figure

        if kind is None:
            return figure
        if isinstance(equipments, str):
            equipments = [equipments]  # to make pd.series.isin() work
        episode = make_episode(agent_study, scenario)
        figure["data"] = common_graph.environment_ts_data(kind, episode, equipments)

        if window is not None:
            figure["layout"].update(xaxis=dict(range=window, autorange=False))

        return figure

    @app.callback(
        [Output("overflow_ts", "figure"), Output("usage_rate_ts", "figure")],
        [Input("relayoutStoreMicro", "data"), Input("window", "data")],
        [
            State("overflow_ts", "figure"),
            State("usage_rate_ts", "figure"),
            State("agent_study", "data"),
            State("scenario", "data"),
        ],
    )
    def update_agent_ref_graph(
        relayout_data_store,
        window,
        figure_overflow,
        figure_usage,
        study_agent,
        scenario,
    ):
        if relayout_data_store is not None and relayout_data_store["relayout_data"]:
            relayout_data = relayout_data_store["relayout_data"]
            layout_usage = figure_usage["layout"]
            new_axis_layout = get_axis_relayout(figure_usage, relayout_data)
            if new_axis_layout is not None:
                layout_usage.update(new_axis_layout)
                figure_overflow["layout"].update(new_axis_layout)
                return figure_overflow, figure_usage

        if window is not None:
            figure_overflow["layout"].update(xaxis=dict(range=window, autorange=False))
            figure_usage["layout"].update(xaxis=dict(range=window, autorange=False))

        return common_graph.agent_overflow_usage_rate_trace(
            make_episode(study_agent, scenario), figure_overflow, figure_usage
        )

    @app.callback(
        Output("timeseries_table_micro", "data"), [Input("timeseries_table", "data")]
    )
    def sync_timeseries_table(data):
        return data

    @app.callback(
        [
            Output("card-content", "children"),
            Output("tooltip_table_micro", "children"),
        ],
        [Input("slider", "value"), Input("card-tabs", "active_tab")],
        [
            State("agent_study", "data"),
            State("scenario", "data"),
            State("agent_ref", "data"),
        ],
    )
    def update_interactive_graph(
        slider_value, active_tab, agent_study, scenario, agent_ref
    ):
        episode = make_episode(
            agent_study if active_tab == "tab-0" else agent_ref, scenario
        )

        try:
            act = episode.actions[slider_value]
        except Grid2OpException as ex:
            return (
                dcc.Graph(
                    figure=go.Figure(
                        layout=layout_no_data(
                            "The agent is game over at this time step."
                        )
                    )
                ),
                "",
            )
        if any(act.get_types()):
            act_as_str = str(act)
        else:
            act_as_str = "NO ACTION"
        return (
            dcc.Graph(figure=make_network_agent_study(episode, timestep=slider_value)),
            act_as_str,
        )

    @app.callback(
        [
            Output("modal_micro", "is_open"),
            Output("dont_show_again_div_micro", "className"),
        ],
        [Input("close_micro", "n_clicks"), Input("page_help", "n_clicks")],
        [State("modal_micro", "is_open"), State("dont_show_again_micro", "checked")],
    )
    def toggle_modal(close_n_clicks, open_n_clicks, is_open, dont_show_again):
        dsa_filepath = Path(grid2viz_home_directory) / DONT_SHOW_FILENAME("micro")
        return toggle_modal_helper(
            close_n_clicks,
            open_n_clicks,
            is_open,
            dont_show_again,
            dsa_filepath,
            "page_help",
        )

    @app.callback(Output("modal_image_micro", "src"), [Input("url", "pathname")])
    def show_image(pathname):
        return app.get_asset_url("screenshots/agent_study.png")
