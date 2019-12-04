import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import argparse

from src.app import app
from src.grid2viz.episodes import episodes_lyt
from src.grid2viz.macro import macro_lyt
from src.grid2viz.micro import micro_lyt
from src.grid2viz.overview import overview_lyt

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Episodes", href="/episodes")),
        dbc.NavItem(dbc.NavLink("Overview", href="/overview")),
        dbc.NavItem(dbc.NavLink("Macro", href="/macro")),
        dbc.NavItem(dbc.NavLink("Micro", href="/micro")),
    ],
    brand="grid2viz",
    brand_href="/episodes",
    sticky="top",
    color="#2196F3",
    dark=True,
    fluid=True
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


if __name__ == "__main__":
    app.run_server(port=8050, debug=False)
