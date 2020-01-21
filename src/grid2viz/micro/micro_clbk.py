import datetime as dt

from dash.dependencies import Input, Output, State
from src.app import app
import pandas as pd
import plotly.graph_objects as go
from src.grid2viz.utils.graph_utils import relayout_callback, get_axis_relayout
from src.grid2kpi.episode import observation_model, env_actions, profiles_traces
from src.grid2kpi.manager import episode, make_episode, base_dir, indx, agent_ref, prod_types


@app.callback(
    Output("relayoutStoreMicro", "data"),
    [Input("env_charts_ts", "relayoutData"),
     Input("usage_rate_ts", "relayoutData"),
     Input("overflow_ts", "relayoutData")],
    [State("relayoutStoreMicro", "data")]
)
def relayout_store_overview(*args):
    return relayout_callback(*args)


# flux line callback
@app.callback(
    [Output('line_side_choices', 'options'),
     Output('line_side_choices', 'value')],
    [Input('voltage_flow_selector', 'value')]
)
def load_voltage_flow_line_choice(value):
    option = []
    for names in episode.line_names:
        option.append({
            'label': 'ex_' + names,
            'value': 'ex_' + names
        })
        option.append({
            'label': 'or_' + names,
            'value': 'or_' + names
        })
    return option, [option[0]['value']]


@app.callback(
    Output('voltage_flow_graph', 'figure'),
    [Input('line_side_choices', 'value')],
    [State('voltage_flow_graph', 'figure')]
)
def load_flow_voltage_graph(values, figure):
    if values is not None:
        voltage_ex = pd.DataFrame(
            [obs.v_ex for obs in episode.observations], columns=episode.line_names)
        voltage_or = pd.DataFrame(
            [obs.v_or for obs in episode.observations], columns=episode.line_names)
        traces = []

        for value in values:
            # the first 2 characters are the side of line ('ex' or 'or')
            line_side = str(value)[:2]
            line_name = str(value)
            if line_side == 'ex':
                traces.append(go.Scatter(
                    x=episode.timestamps,
                    # remove the first 3 char to get the line name and round to 3 decimals
                    y=voltage_ex[line_name[3:]].round(3),
                    name=line_name)
                )
            if line_side == 'or':
                traces.append(go.Scatter(
                    x=episode.timestamps,
                    y=voltage_or[line_name[3:]].round(3),
                    name=line_name)
                )

        figure['data'] = traces

    return figure


# context line callback

@app.callback(
    [Output("asset_selector", "options"),
     Output("asset_selector", "value")],
    [Input("environment_choices_buttons", "value")]
)
def update_ts_graph_avail_assets(kind):
    if kind in ["Hazards", "Maintenances"]:
        options, value = [{'label': line_name, 'value': line_name}
                          for line_name in [*episode.line_names, 'total']], episode.line_names[0]
    elif kind == 'Production':
        options = [{'label': prod_name,
                    'value': prod_name}
                   for prod_name in [*episode.prod_names, *list(set(prod_types.values())), 'total']]
        value = episode.prod_names[0]
    else:
        options = [{'label': load_name,
                    'value': load_name}
                   for load_name in [*episode.load_names, 'total']]
        value = episode.load_names[0]

    return options, value


@app.callback(
    Output("env_charts_ts", "figure"),
    [Input("asset_selector", "value"),
     Input("relayoutStoreMicro", "data")],
    [State("env_charts_ts", "figure"),
     State("environment_choices_buttons", "value")]
)
def load_context_data(equipments, relayout_data_store, figure, kind):
    if relayout_data_store is not None and relayout_data_store["relayout_data"]:
        relayout_data = relayout_data_store["relayout_data"]
        layout = figure["layout"]
        new_axis_layout = get_axis_relayout(figure, relayout_data)
        if new_axis_layout is not None:
            layout.update(new_axis_layout)
            return figure
    if kind is None:
        return figure
    if isinstance(equipments, str):
        equipments = [equipments]  # to make pd.series.isin() work

    if kind == "Load":
        figure["data"] = observation_model.get_load_trace_per_equipment(
            equipments)
    if kind == "Production":
        figure["data"] = observation_model.get_all_prod_trace(equipments)
    if kind == "Hazards":
        figure["data"] = observation_model.get_hazard_trace(equipments)
    if kind == "Maintenances":
        figure["data"] = observation_model.get_maintenance_trace(equipments)

    return figure


@app.callback(
    [Output("overflow_ts", "figure"), Output("usage_rate_ts", "figure")],
    [Input('agent_selector', 'value'),
     Input("relayoutStoreMicro", "data"),
     Input("user_timestamps", "value"),
     Input("enlarge_left", "n_clicks"),
     Input("enlarge_right", "n_clicks")],
    [State("overflow_ts", "figure"),
     State("usage_rate_ts", "figure")]
)
def update_agent_ref_graph(study_agent, relayout_data_store,
                           user_selected_timestamp, n_clicks_left, n_clicks_right,
                           figure_overflow, figure_usage):
    if relayout_data_store is not None and relayout_data_store["relayout_data"]:
        relayout_data = relayout_data_store["relayout_data"]
        layout_usage = figure_usage["layout"]
        new_axis_layout = get_axis_relayout(figure_usage, relayout_data)
        if new_axis_layout is not None:
            layout_usage.update(new_axis_layout)
            figure_overflow["layout"].update(new_axis_layout)
            return figure_overflow, figure_usage
    if study_agent == agent_ref:
        new_episode = episode
    else:
        new_episode = make_episode(base_dir, study_agent, indx)
    figure_overflow["data"] = observation_model.get_total_overflow_trace(
        new_episode)
    figure_usage["data"] = observation_model.get_usage_rate_trace(new_episode)
    if user_selected_timestamp is not None:
        if n_clicks_left is None:
            n_clicks_left = 0
        if n_clicks_right is None:
            n_clicks_right = 0
        center_indx = new_episode.timestamps.index(
            dt.datetime.strptime(user_selected_timestamp, '%Y-%m-%d %H:%M')
        )
        timestamp_range = new_episode.timestamps[
            max([0, (center_indx - 10 - 5 * n_clicks_left)]):(center_indx + 10 + 5 * n_clicks_right)
        ]
        xmin = timestamp_range[0].strftime("%Y-%m-%dT%H:%M:%S")
        xmax = timestamp_range[-1].strftime("%Y-%m-%dT%H:%M:%S")
        figure_overflow["layout"].update(
            xaxis=dict(range=[xmin, xmax], autorange=False)
        )
        figure_usage["layout"].update(
            xaxis=dict(range=[xmin, xmax], autorange=False)
        )

    return figure_overflow, figure_usage


@app.callback(
    Output("timeseries_table_micro", "data"),
    [Input("timeseries_table", "data")]
)
def sync_timeseries_table(data):
    return data
