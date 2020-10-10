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
from grid2viz.src.episodes import episodes_lyt 
'''
End Warning
'''

def register_callbacks_main(app):
    @app.callback(
        [Output('page-content', 'children'), Output('page', 'data'),
         Output("nav_scen_select", "active"), Output("nav_scen_over", "active"),
         Output("nav_agent_over", "active"), Output("nav_agent_study", "active"),
        ],
        [Input('url', 'pathname')],
        [State("scenario", "data"),
         State("agent_ref", "data"),
         State("agent_study", "data"),
         State("user_timestamps", "value"),
         State("page", "data"),
         State("user_timestamps_store", "data")]
    )
    def register_page_lyt(pathname,
                          scenario, ref_agent, study_agent, user_selected_timestamp, prev_page, timestamps_store):
        if timestamps_store is None:
            timestamps_store = []
        timestamps = [dict(Timestamps=timestamp["label"]) for timestamp in timestamps_store]

        print("register_page_lyt")
        if pathname and pathname[1:] == prev_page:
            raise PreventUpdate

        if pathname == "/episodes" or pathname == "/" or not pathname:
            print("episodes_lyt")
            return episodes_lyt, "episodes", True, False, False, False
        elif pathname == "/overview":
            # if ref_agent is None:
            #     raise PreventUpdate
            return overview.layout(scenario, ref_agent), "overview", False, True, False, False
        elif pathname == "/macro":
            if ref_agent is None:
                raise PreventUpdate
            return macro.layout(timestamps, scenario, study_agent), "macro", False, False, True, False
        elif pathname == "/micro":
            if ref_agent is None or study_agent is None:
                raise PreventUpdate
            return micro.layout(user_selected_timestamp, study_agent, ref_agent, scenario), "micro", False, False, False, True
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
        class_name = "ml-4 row"
        print("show_user_timestamps")
        if pathname != "/micro":
            class_name = " ".join([class_name, "hidden"])
        return class_name


    @app.callback(Output("user_timestamps", "options"),
                  [Input("user_timestamps_store", "data")])
    def update_user_timestamps_options(data):
        if data is not None:
            return data
        else:
            return []#{}


    @app.callback(Output("user_timestamps", "value"),
                  [Input("user_timestamps_store", "data")])
    def update_user_timestamps_value(data):
        #if not data:
        #    raise PreventUpdate
        if data is not None:
            return data[0]["value"]
        else:
            return '' #{}


    @app.callback(Output("enlarge_left", "n_clicks"),
                  [Input("user_timestamps", "value")])
    def reset_n_cliks_left(value):
        return 0


    @app.callback(Output("enlarge_right", "n_clicks"),
                  [Input("user_timestamps", "value")])
    def reset_n_cliks_right(value):
        return 0