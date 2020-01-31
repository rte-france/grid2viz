import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from src.app import app
from src.grid2viz.episodes import episodes_lyt
from src.grid2viz.macro import macro_lyt
from src.grid2viz.micro import micro_lyt
from src.grid2viz.overview import overview_lyt
from src.grid2kpi.manager import agent_ref, indx

nav_items = [
    dbc.NavItem(dbc.NavLink("Scenario Selection", href="/episodes")),
    dbc.NavItem(dbc.NavLink("Scenario Overview", href="/overview")),
    dbc.NavItem(dbc.NavLink("Agent Overview", href="/macro")),
    dbc.NavItem(dbc.NavLink("Agent Study", href="/micro"))
]

navbar = dbc.Navbar(
    [
        html.Div([html.Span("Scenario:", className="badge badge-secondary"),
                  html.Span(indx, className="badge badge-light", id="scen_lbl")],
                 className="reminder float-left"),
        html.Div([html.Span("Ref Agent:", className="badge badge-secondary"),
                  html.Span(agent_ref, className="badge badge-light", id="ref_ag_lbl")],
                 className="reminder float-left"),
        html.Div([html.Span("Studied Agent:", className="badge badge-secondary"),
                  html.Span("None", className="badge badge-light", id="study_ag_lbl")],
                 className="reminder float-left"),
        dbc.Button(
            id="enlarge_left",
            children="-5",
            color="dark",
            className="float-left mr-1 hidden"
        ),
        dcc.Dropdown(id="user_timestamps", className="col-xl-1 hidden",
                     style={"width": "200px", "margin-right": "4px"}),
        dbc.Button(
            id="enlarge_right",
            children="+5",
            color="dark",
            className="float-left hidden"
        ),
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
    html.Div(id="page-content", className="main-container")
])

app.layout = html.Div([
    dcc.Store(id="agent_ref", storage_type='memory'),
    dcc.Store(id="agent_study", storage_type='memory'),
    dcc.Store(id="user_timestamps_store"),
    navbar,
    body
])


@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')],
    [State("agent_ref", "data"),
     State("agent_study", "data"),
     State("user_timestamps", "value")]
)
def display_page(pathname, ref_agent, study_agent, user_selected_timestamp):
    if ref_agent is None:
        ref_agent = agent_ref
    if study_agent is None:
        study_agent = agent_ref
    if pathname == "/episodes":
        return episodes_lyt
    elif pathname == "/overview" or pathname == "/":
        return overview_lyt(ref_agent)
    elif pathname == "/macro":
        return macro_lyt(study_agent)
    elif pathname == "/micro":
        return micro_lyt(user_selected_timestamp, study_agent)
    else:
        return 404


@app.callback(Output("ref_ag_lbl", "children"),
              [Input("agent_ref", "data")])
def update_ref_agent_label(agent):
    return agent


@app.callback(Output("study_ag_lbl", "children"),
              [Input("agent_study", "data")])
def update_study_agent_label(agent):
    return agent


@app.callback(Output("user_timestamps", "className"),
              [Input("url", "pathname")])
def show_user_timestamps(pathname):
    class_name = "mr-1"
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


@app.callback(Output("enlarge_left", "className"),
              [Input("url", "pathname")])
def show_minus_five_button(pathname):
    class_name = "float-left mr-1"
    if pathname != "/micro":
        class_name = " ".join([class_name, "hidden"])
    return class_name


@app.callback(Output("enlarge_right", "className"),
              [Input("url", "pathname")])
def show_plus_five_button(pathname):
    class_name = "float-left"
    if pathname != "/micro":
        class_name = " ".join([class_name, "hidden"])
    return class_name


server = app.server
if __name__ == "__main__":
    app.run_server(port=8050, debug=False)
