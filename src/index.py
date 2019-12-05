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

link_style = {"padding-right": "1rem", "padding-left": "1rem"}

nav_items = [
    dbc.NavItem(dbc.NavLink("Scenario Selection",
                            href="/episodes", style=link_style)),
    dbc.NavItem(dbc.NavLink("Scenario Overview",
                            href="/overview", style=link_style)),
    dbc.NavItem(dbc.NavLink("Agent Overview",
                            href="/macro", style=link_style)),
    dbc.NavItem(dbc.NavLink("Agent Study", href="/micro", style=link_style)),
]

style = {"color": "rgb(255,255,255)", "padding": "8px", "margin": "0px"}
style_values = {"color": "rgba(255,255,255, 0.5)",
                "padding": "8px", "margin": "0px"}

navbar = dbc.Navbar(
    [
        # dbc.Col(dbc.NavbarBrand("grid2viz", href="#"), width=1),
        dbc.Col([html.Label("Scenario:", style=style),
                 html.Label(indx,
                            style=style_values, id="scen_lbl")], width=2),
        dbc.Col([html.Label("Ref Agent:", style=style),
                 html.Label(agent_ref,
                            style=style_values, id="ref_ag_lbl")], width=2),
        dbc.Col([html.Label("Studied Agent:", style=style),
                 html.Label("No Agent Selected",
                            style=style_values, id="study_ag_lbl")], width=2),
        dbc.Col(
            dbc.Nav(nav_items, navbar=True, className="float-right",
                    style={"font-size": "1.5rem"}),
            # className="ml-auto",
            width=6
        ),
    ],
    color="#2196F3",
    className="mb-5",
    sticky="top",
    dark=True,
    style={"font-size": "1.25rem"}
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
