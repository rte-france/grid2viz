"""
This file handles the html entry point of the application through dash components.
It will generate the layout of a given page and handle the routing
"""

from dash import Dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

# We need to create app before importing the rest of the project as it uses @app decorators
font_awesome = [
{
    'href': 'https://use.fontawesome.com/releases/v5.8.1/css/all.css',
    'rel': 'stylesheet',
    'integrity': 'sha384-50oBUHEmvpQ+1lW4y57PTFmhCaXp0ML5d60M1M7uH2+nqUivzIebhndOJK28anvf',
    'crossorigin': 'anonymous'
}
]
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, *font_awesome])

'''
WARNING :
These imports are mandatory to build the dependance tree and actually add the callbacks to the dash decoration routine
Do not remove !
The "as ..." are also mandatory, other nothing is done.
'''
from grid2viz.src.episodes import episodes_lyt
from grid2viz.src.episodes import episodes_clbk as episodes_clbk
from grid2viz.src.overview import overview_lyt as overview
from grid2viz.src.overview import overview_clbk as overview_clbk
from grid2viz.src.macro import macro_lyt as macro
from grid2viz.src.macro import macro_clbk as macro_clbk
from grid2viz.src.micro import micro_lyt as micro
from grid2viz.src.micro import micro_clbk as micro_clbk
'''
End Warning
'''

app.config.suppress_callback_exceptions = True
app.title = "Grid2Viz"
app.server.secret_key = "Grid2Viz"

nav_items = [
    dbc.NavItem(dbc.NavLink("Scenario Selection",
                            active=True, href="/episodes", id="nav_scen_select")),
    dbc.NavItem(dbc.NavLink("Scenario Overview",
                            href="/overview", id="nav_scen_over")),
    dbc.NavItem(dbc.NavLink("Agent Overview",
                            href="/macro", id="nav_agent_over")),
    dbc.NavItem(dbc.NavLink("Agent Study",
                            href="/micro", id="nav_agent_study"))
]

navbar = dbc.Navbar(
    [
        html.Div([html.Span("Scenario:", className="badge badge-secondary"),
                  html.Span("", className="badge badge-light", id="scen_lbl")],
                 className="reminder float-left"),
        html.Div([html.Span("Ref Agent:", className="badge badge-secondary"),
                  html.Span("", className="badge badge-light", id="ref_ag_lbl")],
                 className="reminder float-left"),
        html.Div([html.Span("Studied Agent:", className="badge badge-secondary"),
                  html.Span("", className="badge badge-light", id="study_ag_lbl")],
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
    dcc.Store(id="relayoutStoreMicro"),
    navbar,
    body
])


@app.callback(
    [Output('page-content', 'children'), Output('page', 'data'),
     Output("nav_scen_select", "active"), Output("nav_scen_over", "active"),
     Output("nav_agent_over", "active"), Output("nav_agent_study", "active")],
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
    
    if pathname and pathname[1:] == prev_page:
        raise PreventUpdate
    
    if pathname == "/episodes" or pathname == "/" or not pathname:
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

def app_run(port=8050, debug=False):
    app.run_server(port=port, debug=debug)
    
if __name__ == "__main__":
    app_run()
