import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc

layout = html.Div([
    dbc.Button("Load Data", color="success", id="load_data"),
    html.Div(
        className="card-deck mt-3 px-5",
        children=[
            html.Div(
                className="card text-center",
                children=[html.H5(className="card-title", children="Number of Steps"),
                          html.P(className="card-text", children="42")]
            ),
            html.Div(
                className="card text-center",
                children=[html.H5(className="card-title", children="Number of Hazards"),
                          html.P(className="card-text", children="1")]
            ),
            html.Div(
                className="card text-center",
                children=[html.H5(className="card-title", children="Number of Maintenance"),
                          html.P(className="card-text", children="3")]
            ),
            # html.Div(
            #     className="card text-center",
            #     children=[html.H5(className="card-title", children="Number of Steps"),
            #               html.P(className="card-text", children="42")]
            # ),
        ]
    ),
    html.Div(
        className="card-deck mt-3 px-5",
        children=[
            html.Div(
                className="card",
                children=dcc.Graph(
                    id='graph1',
                    figure=dict(
                        data=[
                            dict(type="scatter"),
                            dict(type="scatter")
                        ]
                    )
                )
            ),
            html.Div(
                className="card",
                children=dcc.Graph(
                    id='graph2',
                    figure=dict(
                        data=[
                            dict(type="scatter"),
                            dict(type="scatter")
                        ]
                    )
                )
            ),
        ]
    )
])
