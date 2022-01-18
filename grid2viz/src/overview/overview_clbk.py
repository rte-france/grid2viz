# Copyright (C) 2021, RTE (http://www.rte-france.com/)
# See AUTHORS.txt
# SPDX-License-Identifier: MPL-2.0

import datetime as dt
from pathlib import Path

import pandas as pd
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from grid2viz.src.kpi import observation_model, EpisodeTrace
from grid2viz.src.manager import make_episode, best_agents, grid2viz_home_directory
from grid2viz.src.utils import common_graph
from grid2viz.src.utils.callbacks_helpers import toggle_modal_helper
from grid2viz.src.utils.constants import DONT_SHOW_FILENAME
from grid2viz.src.utils.graph_utils import relayout_callback, get_axis_relayout


def filter_table_datetime(
    df, timestamp_col_name="timestamp", start_date=None, end_date=None
):
    """
    Filter and return the table in the range [strat_date, end_date)
    """
    if start_date is not None:
        df = df[df[timestamp_col_name] >= start_date]
    if end_date is not None:
        df = df[df[timestamp_col_name] < end_date]
    return df


def register_callbacks_overview(app):
    @app.callback(
        Output("relayoutStoreOverview", "data"),
        [
            Input("input_env_charts", "relayoutData"),
            Input("usage_rate_graph", "relayoutData"),
            Input("overflow_graph", "relayoutData"),
        ],
        [State("relayoutStoreOverview", "data")],
    )
    def relayout_store_overview(*args):
        return relayout_callback(*args)

    @app.callback(
        [
            Output("input_assets_selector", "options"),
            Output("input_assets_selector", "value"),
        ],
        [Input("scen_overview_ts_switch", "value")],
        [State("scenario", "data")],
    )
    def update_ts_graph_avail_assets(kind, scenario):
        """
        Change the selector's options according to the kind of trace selected.

        Triggered when user click on one of the input in the scen_overview_ts_switch
        component in overview layout.
        """
        best_agent_ep = make_episode(best_agents[scenario]["agent"], scenario)
        return common_graph.ts_graph_avail_assets(kind, best_agent_ep)

    @app.callback(
        Output("input_env_charts", "figure"),
        [
            Input("input_assets_selector", "value"),
            Input("relayoutStoreOverview", "data"),
        ],
        [
            State("input_env_charts", "figure"),
            State("scen_overview_ts_switch", "value"),
            State("scenario", "data"),
        ],
    )
    def load_environments_ts(equipments, relayout_data_store, figure, kind, scenario):
        """
        Load selected kind of environment for chosen equipments in a scenario.

        Triggered when user click on a equipment displayed in the
        input_assets_selector in the overview layout.
        """
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

        figure["data"] = common_graph.environment_ts_data(
            kind, make_episode(best_agents[scenario]["agent"], scenario), equipments
        )

        return figure

    @app.callback(
        Output("select_loads_for_tb", "options"),
        [Input("indicator_line", "children")],
        [State("scenario", "data")],
    )
    def update_select_loads(children, scenario):
        """
        Display list of loads in a the select_loads_for_tb component.

        Triggered when indicator line is loaded.
        """
        episode = make_episode(best_agents[scenario]["agent"], scenario)
        return [
            {"label": load, "value": load}
            for load in [*episode.load_names, "total", "total_intercos"]
        ]

    @app.callback(
        Output("select_prods_for_tb", "options"),
        [Input("indicator_line", "children")],
        [State("scenario", "data")],
    )
    def update_select_prods(children, scenario):
        """
        Display list of production in a the select_prods_for_tb component.

        Triggered when indicator line is loaded.
        """
        episode = make_episode(best_agents[scenario]["agent"], scenario)
        return [{"label": prod, "value": prod} for prod in episode.prod_names]

    @app.callback(
        [Output("inspection_table", "columns"), Output("inspection_table", "data")],
        [
            Input("select_loads_for_tb", "value"),
            Input("select_prods_for_tb", "value"),
            Input("agent_ref", "data"),
            Input("date_range", "start_date"),
            Input("date_range", "end_date"),
        ],
        [State("inspection_table", "data"), State("scenario", "data")],
    )
    def update_table(loads, prods, agent_ref, start_date, end_date, data, scenario):
        """
        Update the inspection table with the loads and prods selected.

        Triggered when the select a load or a prods and when the ref agent is changed.
        """
        if agent_ref is None:
            raise PreventUpdate
        episode = make_episode(agent_ref, scenario)
        df = observation_model.init_table_inspection_data(episode)
        if data is None:
            return [{"name": i, "id": i} for i in df.columns], df.to_dict("records")
        if loads is None:
            loads = []
        if prods is None:
            prods = []
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        cols_to_drop = []
        for col in df.columns[4:]:
            if col not in loads and col not in prods:
                cols_to_drop.append(col)
        cols_to_add = [col for col in loads + prods if col not in df.columns]
        df = df.drop(cols_to_drop, axis=1)
        if cols_to_add:
            df_col = observation_model.get_prod_and_conso(episode)[cols_to_add]
            df_col.index = pd.to_datetime(df_col.index)
            df = df.merge(
                df_col,
                left_on="timestamp",
                right_index=True,
                how="right",
            )
        start_date_timestamp = None
        end_date_timestamp = None
        if start_date is not None:
            start_date_timestamp = dt.datetime.strptime(start_date, "%Y-%m-%d")
        if end_date is not None:
            end_date_timestamp = dt.datetime.strptime(
                end_date, "%Y-%m-%d"
            ) + dt.timedelta(days=1)
        df = filter_table_datetime(
            df, start_date=start_date_timestamp, end_date=end_date_timestamp
        )
        cols = [{"name": i, "id": i} for i in df.columns]
        df.timestamp=df.timestamp.astype('category')
        return cols, df.to_dict("records")

    @app.callback(Output("nb_steps_card", "children"), [Input("scenario", "data")])
    def update_card_step(scenario):
        """Display the best agent number of step when the page is loaded."""
        best_agent_ep = make_episode(best_agents[scenario]["agent"], scenario)
        return "{} / {}".format(
            best_agent_ep.meta["nb_timestep_played"],
            best_agent_ep.meta["chronics_max_timestep"],
        )

    @app.callback(
        Output("nb_maintenance_card", "children"), [Input("scenario", "data")]
    )
    def update_card_maintenance(scenario):
        """Display the number of maintenance of the best agent when page is loaded."""
        best_agent_ep = make_episode(best_agents[scenario]["agent"], scenario)
        return best_agent_ep.nb_maintenances

    @app.callback(Output("nb_hazard_card", "children"), [Input("scenario", "data")])
    def update_card_hazard(scenario):
        """Display the number of hazard of the best agent when page is loaded."""
        best_agent_ep = make_episode(best_agents[scenario]["agent"], scenario)
        return best_agent_ep.nb_hazards

    @app.callback(
        Output("duration_maintenance_card", "children"), [Input("scenario", "data")]
    )
    def update_card_duration_maintenances(scenario):
        """
        Display the total duration of maintenances made by the best agent when
        page is loaded.
        """
        best_agent_ep = make_episode(best_agents[scenario]["agent"], scenario)
        return best_agent_ep.total_maintenance_duration

    # @app.callback(
    #     Output("agent_ref", "data"),
    #     [Input("input_agent_selector", "value")],
    #     [State("scenario", "data")]
    # )
    # def update_selected_ref_agent(ref_agent, scenario):
    #     """
    #         Change the agent of reference for the given scenario.
    #
    #         Triggered when user select a new agent with the agent selector on layout.
    #     """
    #     make_episode(ref_agent, scenario)
    #     return ref_agent

    @app.callback(
        [Output("overflow_graph", "figure"), Output("usage_rate_graph", "figure")],
        [
            Input("agent_ref", "data"),
            Input("scenario", "data"),
            Input("relayoutStoreOverview", "data"),
        ],
        [State("overflow_graph", "figure"), State("usage_rate_graph", "figure")],
    )
    def update_agent_ref_graph(
        ref_agent, scenario, relayout_data_store, figure_overflow, figure_usage
    ):
        if ref_agent is None or scenario is None:
            raise PreventUpdate
        if relayout_data_store is not None and relayout_data_store["relayout_data"]:
            relayout_data = relayout_data_store["relayout_data"]
            layout_usage = figure_usage["layout"]
            new_axis_layout = get_axis_relayout(figure_usage, relayout_data)
            if new_axis_layout is not None:
                layout_usage.update(new_axis_layout)
                figure_overflow["layout"].update(new_axis_layout)
                return figure_overflow, figure_usage

        return common_graph.agent_overflow_usage_rate_trace(
            make_episode(ref_agent, scenario), figure_overflow, figure_usage
        )

    @app.callback(
        Output("indicator_line_charts", "figure"),
        [Input("scenario", "data")],
        [State("indicator_line_charts", "figure")],
    )
    def update_profile_conso_graph(scenario, figure):
        """Display best agent's consumption profile when page is loaded"""
        best_agent_ep = make_episode(best_agents[scenario]["agent"], scenario)
        figure["data"] = best_agent_ep.profile_traces
        return figure

    @app.callback(
        Output("production_share_graph", "figure"),
        [Input("scenario", "data")],
        [State("production_share_graph", "figure")],
    )
    def update_production_share_graph(scenario, figure):
        """Display best agent's production share when page load"""
        best_agent_ep = make_episode(best_agents[scenario]["agent"], scenario)
        share_prod = EpisodeTrace.get_prod_share_trace(best_agent_ep)
        figure["data"] = share_prod
        return figure

    @app.callback(
        [Output("date_range", "start_date"), Output("date_range", "end_date")],
        [Input("agent_ref", "data")],
        [State("scenario", "data")],
    )
    def update_date_range(agent_ref, scenario):
        """Change the date range for the date picker in inspector line"""
        if agent_ref is None or scenario is None:
            raise PreventUpdate
        episode = make_episode(agent_ref, scenario)
        return (
            episode.production["timestamp"].dt.date.values[0],
            episode.production["timestamp"].dt.date.values[-1],
        )

    @app.callback(
        [
            Output("modal_overview", "is_open"),
            Output("dont_show_again_div_overview", "className"),
        ],
        [Input("close_overview", "n_clicks"), Input("page_help", "n_clicks")],
        [
            State("modal_overview", "is_open"),
            State("dont_show_again_overview", "checked"),
        ],
    )
    def toggle_modal(close_n_clicks, open_n_clicks, is_open, dont_show_again):
        dsa_filepath = Path(grid2viz_home_directory) / DONT_SHOW_FILENAME("overview")
        return toggle_modal_helper(
            close_n_clicks,
            open_n_clicks,
            is_open,
            dont_show_again,
            dsa_filepath,
            "page_help",
        )

    @app.callback(Output("modal_image_overview", "src"), [Input("url", "pathname")])
    def show_image(pathname):
        return app.get_asset_url("screenshots/scenario_overview.png")
