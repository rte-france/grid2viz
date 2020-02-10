import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from dash.exceptions import PreventUpdate

import plotly.graph_objects as go

app = dash.Dash(__name__)

app.layout = html.Div(
    children=[
        dcc.Graph(
            id='dummygraph1',
            figure=go.Figure(
                data=[go.Scatter(x=list(range(5)), y=list(range(5)))],
                layout=go.Layout(showlegend=True))
        )
    ]
)


def get_axis_relayout(xaxis, yaxis, relayout_data):
    res = {}
    if "xaxis.range[0]" in relayout_data:
        xmin, xmax = relayout_data["xaxis.range[0]"], relayout_data["xaxis.range[1]"]
        if [xmin, xmax] != xaxis["range"]:
            res.update(xaxis=dict(range=[xmin, xmax], autorange=False))
    if "yaxis.range[0]" in relayout_data:
        ymin, ymax = relayout_data["yaxis.range[0]"], relayout_data["yaxis.range[1]"]
        if [ymin, ymax] != yaxis["range"]:
            res.update(yaxis=dict(range=[ymin, ymax], autorange=False))
    if "xaxis.autorange" in relayout_data:
        res.update(xaxis=dict(autorange=relayout_data["xaxis.autorange"]))
    if "yaxis.autorange" in relayout_data:
        res.update(yaxis=dict(autorange=relayout_data["yaxis.autorange"]))
    if res:
        return res


server = app.server
