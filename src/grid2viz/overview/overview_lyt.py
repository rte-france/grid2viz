import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objects as go



pie_charts = html.Div(children=dcc.Graph(
    figure=go.Figure(
        data=[go.Pie(
            title="Pie Charts Indicator", showlegend=False,
            labels=['Oxygen', 'Hydrogen', 'Carbon_Dioxide', 'Nitrogen'],
            values=[4500, 2500, 1053, 500]
        )]
    )))


indicators_line = html.Div(children=[
    html.H2("Indicators"),
    html.Div(children=[
        html.Div(className="col-xl-6",
                 children=dcc.Graph(
                     id="indicator_line_charts",
                     figure=dict(
                         data=[
                             dict(type="scatter")
                         ]
                     )
                 )),
        html.Div(pie_charts, className="col-xl-4"),
        html.Div(children=[
            html.Div(
                className="card text-center mt-4 mb-4 p-3",
                children=[html.H5(className="card-title", children="Number of Steps"),
                          html.P(className="card-text", children="42")]
            ),
            html.Div(
                className="card text-center mb-4 p-3",
                children=[html.H5(className="card-title", children="Number of Maintenance"),
                          html.P(className="card-text", children="1")]
            ),
            html.Div(
                className="card text-center mb-4 p-3",
                children=[html.H5(className="card-title", children="Number of Hazard"),
                          html.P(className="card-text", children="3")]
            ),
            html.Div(
                className="card text-center p-3",
                children=[html.H5(className="card-title", children="Duration Maintenance"),
                          html.P(className="card-text", children="3")]
            )
        ], className="col-xl-2")
    ], className="card-body row "),
], className="lineBlock card")

summary_line = html.Div(children=[
    html.H2("Summary"),
    html.Div(children=[
       # TODO div with line charts
        dcc.Dropdown(
            id="summary_charts_selector",
            placeholder="select a charts",
            options=[
                {'label': 'test', 'value': 1},
                {'label': 'test1', 'value': 2}
            ]
        )
    ]),
    html.Div(pie_charts)
], className="lineBlock card")

ref_agent_line = html.Div(children=[
    html.H2("Ref Agent"),
    html.Div(pie_charts)
], className="lineBlock card")

layout = html.Div([
    indicators_line,
    summary_line,
    ref_agent_line
])
