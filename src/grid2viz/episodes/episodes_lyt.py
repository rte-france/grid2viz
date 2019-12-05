import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc

from src.grid2kpi.manager import scenarios


cards = html.Div([
    dbc.Row(
        [
            dbc.Col(
                 [
                     dbc.CardDeck(
                         [
                             dbc.Col(
                                 dbc.Card(
                                     [
                                         dbc.CardHeader("Header"),
                                         dbc.CardBody(
                                             [
                                                 html.H5(
                                                     "This card has a title",
                                                     className="card-title",
                                                 ),
                                                 html.P(
                                                     scenario, className="card-text"),
                                             ]
                                         ),
                                         dbc.CardFooter(dbc.Button(
                                             "Open", className="btn-block",
                                             style={"background-color": "#2196F3"}))
                                     ],
                                     className="mb-4"
                                 ), width=4) for scenario in list(scenarios)+list(scenarios)]
                     ),
                 ],
                 width=10
                 ),

        ],
        className="justify-content-md-center"
    )

])

layout = cards
