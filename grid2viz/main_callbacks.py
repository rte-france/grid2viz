import datetime as dt

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

'''
WARNING :
These imports are mandatory to build the dependance tree and actually add the callbacks to the dash decoration routine
Do not remove !
The "as ..." are also mandatory, other nothing is done.
'''
from grid2viz.src.overview import overview_lyt as overview
from grid2viz.src.macro import macro_lyt as macro
from grid2viz.src.micro import micro_lyt as micro
from grid2viz.src.simulation import simulation_lyt as simulation
from grid2viz.src.episodes import episodes_lyt 
'''
End Warning
'''
from grid2viz.src import manager


def register_callbacks_main(app):
    @app.callback(
        [Output('page-content', 'children'), Output('page', 'data'),
         Output("nav_scen_select", "active"), Output("nav_scen_over", "active"),
         Output("nav_agent_over", "active"), Output("nav_agent_study", "active"),
         Output("nav_simulation", "active"),
         Output("reset_timeseries_table_macro", "data")],
        [Input('url', 'pathname')],
        [State("scenario", "data"),
         State("agent_ref", "data"),
         State("agent_study", "data"),
         State("user_timestamps", "value"),
         State("page", "data"),
         State("user_timestamps_store", "data"),
         State("reset_timeseries_table_macro", "data")]
    )
    def register_page_lyt(pathname, scenario, ref_agent, study_agent,
                          user_selected_timestamp, prev_page, timestamps_store,
                          reset_ts_table_macro):
        if timestamps_store is None:
            timestamps_store = []
        timestamps = [dict(Timestamps=timestamp["label"]) for timestamp in timestamps_store]

        # When you have a proxy, like on Binder, the pathname can be long.
        # So we split it and only keep the last piece
        pathName_split = pathname.split("/")
        pathName_split = pathName_split[len(pathName_split)-1]

        if pathName_split and pathName_split[1:] == prev_page:
            raise PreventUpdate

        if prev_page == "episodes":
            reset_ts_table_macro = True

        if pathName_split == "episodes" or pathName_split == "" or not pathName_split:
            return episodes_lyt, "episodes", True, False, False, False, False, reset_ts_table_macro
        elif pathName_split == "overview":
            return overview.layout(scenario, ref_agent), "overview", False, True, False, False, False, reset_ts_table_macro
        elif pathName_split == "macro":
            if ref_agent is None:
                raise PreventUpdate
            return macro.layout(timestamps, scenario, study_agent, ref_agent, reset_ts_table_macro), "macro", False, False, True, False, False, False
        elif pathName_split == "micro":
            if ref_agent is None or study_agent is None:
                raise PreventUpdate
            return micro.layout(user_selected_timestamp, study_agent, ref_agent, scenario), "micro", False, False, False, True, False, reset_ts_table_macro
        elif pathname == "/simulation":
            if ref_agent is None or study_agent is None:
                raise PreventUpdate
            return simulation.layout(scenario,
                                     study_agent), "simulation", False, False, False, False, True, reset_ts_table_macro
        else:
            return 404, ""

    @app.callback(Output('scen_lbl', 'children'),
                  [Input('scenario', 'data')])
    def update_scenario_label(scenario):
        if scenario is None:
            scenario = ""
        return scenario

    @app.callback(Output("ref_ag_lbl", "children"),
                  [Input("agent_ref", "data")])
    def update_ref_agent_label(agent):
        if agent is None:
            agent = ""
        return agent


    @app.callback(Output("study_ag_lbl", "children"),
                  [Input("agent_study", "data")])
    def update_study_agent_label(agent):
        if agent is None:
            agent = ""
        return agent


    @app.callback(Output("user_timestamp_div", "className"),
                  [Input("url", "pathname")])
    def show_user_timestamps(pathname):
        pathName_split=pathname.split("/")
        pathName_split=pathName_split[len(pathName_split)-1]

        class_name = "ml-4 row"
        if pathName_split != "micro":
            class_name = " ".join([class_name, "hidden"])
        return class_name

    @app.callback(Output("user_timestamps", "options"),
                  [Input("user_timestamps_store", "data"),
                   Input("agent_study", "data")],
                  [State("scenario", "data")])
    def update_user_timestamps_options(data, agent, scenario):
        episode = manager.make_episode(agent, scenario)
        nb_timesteps_played = episode.meta['nb_timestep_played']
        return [ts for ts in data
                if dt.datetime.strptime(ts['value'], '%Y-%m-%d %H:%M') in episode.timestamps[:nb_timesteps_played]]

    @app.callback(Output("user_timestamps", "value"),
                  [Input("user_timestamps_store", "data"), Input("agent_study", "data")],
                  [State("scenario", "data")])
    def update_user_timestamps_value(data, agent, scenario):
        if not data:
            raise PreventUpdate
        episode = manager.make_episode(agent, scenario)
        nb_timesteps_played = episode.meta['nb_timestep_played']
        filtered_data = [ts for ts in data
                         if dt.datetime.strptime(ts['value'], '%Y-%m-%d %H:%M') in episode.timestamps[
                                                                                   :nb_timesteps_played]]
        if filtered_data:
            return filtered_data[0]["value"]


    @app.callback(Output("enlarge_left", "n_clicks"),
                  [Input("user_timestamps", "value")])
    def reset_n_cliks_left(value):
        return 0


    @app.callback(Output("enlarge_right", "n_clicks"),
                  [Input("user_timestamps", "value")])
    def reset_n_cliks_right(value):
        return 0
