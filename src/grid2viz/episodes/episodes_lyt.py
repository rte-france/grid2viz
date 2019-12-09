import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from src.grid2kpi.manager import scenarios

episode_graph_layout = {
    'autosize': True,
    'showlegend': False,
    'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0},
}

cards = html.Div([
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody([
                            html.H5(
                                "Scenario {0}".format(scenario),
                                className="card-title",
                            ),
                            dbc.Row([
                                dbc.Col([dcc.Graph(figure=go.Figure(
                                    layout=episode_graph_layout,
                                    data=[go.Pie(
                                        labels=['Oxygen', 'Hydrogen', 'Carbon_Dioxide', 'Nitrogen'],
                                        values=[4500, 2500, 1053, 500]
                                    )],
                                ))], width=4),
                                dbc.Col([dcc.Graph(figure=go.Figure(
                                    layout=episode_graph_layout,
                                    data=[dict(type="scatter")]
                                ))], width=8)
                            ], className="align-items-center")
                        ]),
                        dbc.CardFooter(dbc.Button(
                            "Open", className="btn-block",
                            style={"background-color": "#2196F3"}))
                    ], className="mb-3"), width=4)
                for scenario in list(scenarios) + list(scenarios)]),
        ], width=12),
    ], className="justify-content-md-center")
], className="m-3 mt-5")

layout = cards
