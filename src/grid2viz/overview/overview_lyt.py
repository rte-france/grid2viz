import dash_html_components as html

content = html.Div("exampleGraph")

indicators_line = html.Div(children=[
    html.H2("Indicators"),
    html.Div(content)
], className="lineBlock")

summary_line = html.Div(children=[
    html.H2("Summary"),
    html.Div(content)
], className="lineBlock")

ref_agent_line = html.Div(children=[
    html.H2("Ref Agent"),
    html.Div(content)
], className="lineBlock")

layout = html.Div([
    indicators_line,
    summary_line,
    ref_agent_line
])
