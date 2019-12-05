import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

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
    dcc.Store(id="store"),
    navbar,
    body
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == "/episodes":
        return episodes_lyt
    elif pathname == "/overview" or pathname == "/":
        return overview_lyt()
    elif pathname == "/macro":
        return macro_lyt
    elif pathname == "/micro":
        return micro_lyt
    else:
        return 404


@app.callback(Output("ref_ag_lbl", "children"),
              [Input("input_agent_selector", "value")])
def update_ref_agent_label(agent):
    return agent


server = app.server
if __name__ == "__main__":
    app.run_server(port=8050, debug=False)
