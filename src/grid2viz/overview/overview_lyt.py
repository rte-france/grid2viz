import dash_html_components as html
import dash_core_components as dcc
from src.grid2kpi.episode import observation_model

content = html.Div(
    className='graphCard',
    children=[
        dcc.Graph(
            id="rs_overview",
            figure={
                'data': observation_model.get_all_equipment_active_load_ts(),
                'layout': {
                    'height': '300',
                    'width': '500',
                    'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0}
                }
            }
        )
    ]
)


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
