import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from src.app import app
from src.grid2viz.episodes import episodes_lyt
from src.grid2viz.utils.perf_analyser import timeit, decorate_all_in_module

import src.grid2viz.macro.macro_clbk as macro_clbk
import src.grid2viz.macro.macro_lyt as macro
import src.grid2viz.micro.micro_clbk as micro_clbk
import src.grid2viz.micro.micro_lyt as micro
import src.grid2viz.overview.overview_clbk as overview_clbk
import src.grid2viz.overview.overview_lyt as overview

decorate_all_in_module(macro_clbk, timeit)
decorate_all_in_module(macro, timeit)
decorate_all_in_module(micro_clbk, timeit)
decorate_all_in_module(micro, timeit)
decorate_all_in_module(overview_clbk, timeit)
decorate_all_in_module(overview, timeit)

nav_items = [
    dbc.NavItem(dbc.NavLink("Scenario Selection", href="/episodes")),
    dbc.NavItem(dbc.NavLink("Scenario Overview", href="/overview")),
    dbc.NavItem(dbc.NavLink("Agent Overview", href="/macro")),
    dbc.NavItem(dbc.NavLink("Agent Study", href="/micro"))
]

navbar = dbc.Navbar(
    [
        html.Div([html.Span("Scenario:", className="badge badge-secondary"),
                  html.Span("None", className="badge badge-light", id="scen_lbl")],
                 className="reminder float-left"),
        html.Div([html.Span("Ref Agent:", className="badge badge-secondary"),
                  html.Span("None", className="badge badge-light", id="ref_ag_lbl")],
                 className="reminder float-left"),
        html.Div([html.Span("Studied Agent:", className="badge badge-secondary"),
                  html.Span("None", className="badge badge-light", id="study_ag_lbl")],
                 className="reminder float-left"),
        html.Div([
            html.Div(
                [
                    dbc.Button(
                    id="enlarge_left",
                    children="-5",
                    color="dark",
                    className="float-left mr-1"
                    ),
                    dbc.Tooltip('Enlarge left', target='enlarge_left',
                                placement='bottom'),
                ]
            ),
            dcc.Dropdown(id="user_timestamps", className="",
                         style={"width": "200px"}),
            html.Div(
                [
                    dbc.Button(
                        id="enlarge_right",
                        children="+5",
                        color="dark",
                        className="float-left ml-1"
                    ),
                    dbc.Tooltip('Enlarge right', target='enlarge_right',
                                placement='bottom')
                ]
                
            )
        ], id="user_timestamp_div", className="col-xl-1"),
        html.Div(
            dbc.Nav(nav_items, navbar=True), className="nav_menu"
        ),
    ],
    color="#2196F3",
    sticky="top",
    dark=True,
)

body = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content", className="main-container"),

    dbc.Modal([
        dbc.ModalBody([
            dbc.Spinner(color="primary", type="grow"),
            html.P('loading graph...')
        ])
    ], id='loading_modal')
])

app.layout = html.Div([
    dcc.Store(id="scenario", storage_type='memory'),
    dcc.Store(id="agent_ref", storage_type='memory'),
    dcc.Store(id="agent_study", storage_type='memory'),
    dcc.Store(id="user_timestamps_store"),
    dcc.Store(id="page"),
    navbar,
    body
])


@app.callback(
    [Output('page-content', 'children'), Output('page', 'data')],
    [Input('url', 'pathname')],
    [State("scenario", "data"),
     State("agent_ref", "data"),
     State("agent_study", "data"),
     State("user_timestamps", "value"),
     State("page", "data"),
     State("user_timestamps_store", "data")]
)
def display_page(pathname, scenario, ref_agent, study_agent, user_selected_timestamp, prev_page, timestamps_store):
    if timestamps_store is None:
        timestamps_store = []
    timestamps = [dict(Timestamps=timestamp["label"]) for timestamp in timestamps_store]
    if pathname[1:] == prev_page:
        raise PreventUpdate
    if pathname == "/episodes" or pathname == "/":
        return episodes_lyt, "episodes"
    elif pathname == "/overview":
        return overview.layout(scenario), "overview"
    elif pathname == "/macro":
        return macro.layout(timestamps, scenario), "macro"
    elif pathname == "/micro":
        return micro.layout(user_selected_timestamp, study_agent, ref_agent, scenario), "micro"
    else:
        return 404, ""


@app.callback(Output('scen_lbl', 'children'),
              [Input('scenario', 'data')])
def update_scenario_label(scenario):
    return scenario


@app.callback(Output("ref_ag_lbl", "children"),
              [Input("agent_ref", "data")])
def update_ref_agent_label(agent):
    return agent


@app.callback(Output("study_ag_lbl", "children"),
              [Input("agent_study", "data")])
def update_study_agent_label(agent):
    return agent


@app.callback(Output("user_timestamp_div", "className"),
              [Input("url", "pathname")])
def show_user_timestamps(pathname):
    class_name = "ml-4 row"
    if pathname != "/micro":
        class_name = " ".join([class_name, "hidden"])
    return class_name


@app.callback(Output("user_timestamps", "options"),
              [Input("user_timestamps_store", "data")])
def update_user_timestamps_options(data):
    return data


@app.callback(Output("user_timestamps", "value"),
              [Input("user_timestamps_store", "data")])
def update_user_timestamps_value(data):
    if not data:
        raise PreventUpdate
    return data[0]["value"]


@app.callback(Output("enlarge_left", "n_clicks"),
              [Input("user_timestamps", "value")])
def reset_n_cliks_left(value):
    return 0


@app.callback(Output("enlarge_right", "n_clicks"),
              [Input("user_timestamps", "value")])
def reset_n_cliks_right(value):
    return 0


server = app.server
if __name__ == "__main__":
    app.run_server(port=8050, debug=False)
