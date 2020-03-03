import datetime as dt

import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from src.app import app
from ..manager import make_episode, make_network
from ..utils.graph_utils import relayout_callback, get_axis_relayout
from ..utils import common_graph


@app.callback(
    [Output("slider", "min"), Output("slider", "max"), Output("slider", "value"), Output("slider", "marks")],
    [Input("window", "data")],
    [State("slider", "value"), State("agent_study", "data"), State("scenario", "data")]
)
def update_slider(window, value, study_agent, scenario):
    if window is None:
        raise PreventUpdate
    new_episode = make_episode(study_agent, scenario)

    min_ = new_episode.timestamps.index(
        dt.datetime.strptime(window[0], "%Y-%m-%dT%H:%M:%S")
    )
    max_ = new_episode.timestamps.index(
        dt.datetime.strptime(window[1], "%Y-%m-%dT%H:%M:%S")
    )
    if value not in range(min_, max_):
        value = min_

    marks = dict(enumerate(map(lambda x: x.time(), new_episode.timestamps)))

    return min_, max_, value, marks


@app.callback(
    Output("relayoutStoreMicro", "data"),
    [Input("env_charts_ts", "relayoutData"),
     Input("usage_rate_ts", "relayoutData"),
     Input("overflow_ts", "relayoutData"),
     Input("cum_instant_reward_ts", "relayoutData"),
     Input("actions_ts", "relayoutData"),
     Input("voltage_flow_graph", "relayoutData")],
    [State("relayoutStoreMicro", "data")]
)
def relayout_store_overview(*args):
    return relayout_callback(*args)


@app.callback(
    Output("window", "data"),
    [Input("enlarge_left", "n_clicks"),
     Input("enlarge_right", "n_clicks"),
     Input("user_timestamps", "value")],
    [State('agent_study', 'data'), State("scenario", "data")]
)
def compute_window(n_clicks_left, n_clicks_right, user_selected_timestamp,
                   study_agent, scenario):
    if user_selected_timestamp is None:
        raise PreventUpdate
    if n_clicks_left is None:
        n_clicks_left = 0
    if n_clicks_right is None:
        n_clicks_right = 0
    new_episode = make_episode(study_agent, scenario)
    center_indx = new_episode.timestamps.index(
        dt.datetime.strptime(user_selected_timestamp, '%Y-%m-%d %H:%M')
    )
    return common_graph.compute_windows_range(
        new_episode, center_indx, n_clicks_left, n_clicks_right
    )


# indicator line
@app.callback(
    Output("cum_instant_reward_ts", "figure"),
    [Input("relayoutStoreMicro", "data"),
     Input("window", "data"),
     Input("user_timestamps", "value")],
    [State("cum_instant_reward_ts", "figure"),
     State("agent_study", "data"),
     State("agent_ref", "data"),
     State("scenario", "data")]
)
def load_reward_ts(relayout_data_store, window, selected_timestamp, figure, study_agent, agent_ref, scenario):

    layout = figure["layout"]
    if relayout_data_store is not None and relayout_data_store["relayout_data"]:
        relayout_data = relayout_data_store["relayout_data"]
        new_axis_layout = get_axis_relayout(figure, relayout_data)
        if new_axis_layout is not None:
            layout.update(new_axis_layout)
            return figure

    figure = common_graph.make_rewards_ts(study_agent, agent_ref, scenario, layout)

    if window is not None:
        figure["layout"].update(
            xaxis=dict(range=window, autorange=False)
        )

    return figure


@app.callback(
    Output("actions_ts", "figure"),
    [Input('relayoutStoreMicro', 'data'),
     Input("window", "data")],
    [State("actions_ts", "figure"),
     State("user_timestamps", "value"),
     State('agent_study', 'data'),
     State('agent_ref', 'data'),
     State("scenario", "data")]
)
def load_actions_ts(relayout_data_store, window, figure, selected_timestamp, study_agent, agent_ref, scenario):

    layout = figure["layout"]
    if relayout_data_store is not None and relayout_data_store["relayout_data"]:
        relayout_data = relayout_data_store["relayout_data"]

        new_axis_layout = get_axis_relayout(figure, relayout_data)
        if new_axis_layout is not None:
            layout.update(new_axis_layout)
            return figure

    figure = common_graph.make_action_ts(study_agent, agent_ref, scenario, layout)

    if window is not None:
        figure["layout"].update(
            xaxis=dict(range=window, autorange=False)
        )

    return figure


# flux line callback
@app.callback(
    [Output('line_side_choices', 'options'),
     Output('line_side_choices', 'value')],
    [Input('voltage_flow_choice', 'value'),
     Input('flow_radio', 'value')],
    [State('agent_study', 'data'),
     State("scenario", "data")]
)
def load_voltage_flow_line_choice(category, flow_choice, study_agent, scenario):
    option = []
    new_episode = make_episode(study_agent, scenario)

    for name in new_episode.line_names:
        if category == 'voltage':
            option.append({
                'label': 'ex_' + name,
                'value': 'ex_' + name
            })
            option.append({
                'label': 'or_' + name,
                'value': 'or_' + name
            })
        if category == 'flow':
            if flow_choice == 'active_flow':
                option.append({
                    'label': 'ex_active_' + name,
                    'value': 'ex_active_' + name
                })
                option.append({
                    'label': 'or_active_' + name,
                    'value': 'or_active_' + name
                })
            if flow_choice == 'current_flow':
                option.append({
                    'label': 'ex_current_' + name,
                    'value': 'ex_current_' + name
                })
                option.append({
                    'label': 'or_current_' + name,
                    'value': 'or_current_' + name
                })

            if flow_choice == 'flow_usage_rate':
                option.append({
                    'label': 'usage_rate_' + name,
                    'value': 'usage_rate_' + name
                })

    return option, [option[0]['value']]


@app.callback(
    Output('voltage_flow_graph', 'figure'),
    [Input('line_side_choices', 'value'),
     Input('voltage_flow_choice', 'value'),
     Input('relayoutStoreMicro', 'data'),
     Input("window", "data")],
    [State('voltage_flow_graph', 'figure'),
     State('agent_study', 'data'),
     State("scenario", "data")]
)
def load_flow_voltage_graph(selected_lines, choice, relayout_data_store, window, figure, study_agent, scenario):
    if relayout_data_store is not None and relayout_data_store["relayout_data"]:
        relayout_data = relayout_data_store["relayout_data"]
        layout = figure["layout"]
        new_axis_layout = get_axis_relayout(figure, relayout_data)
        if new_axis_layout is not None:
            layout.update(new_axis_layout)
            return figure
    new_episode = make_episode(study_agent, scenario)
    if selected_lines is not None:
        if choice == 'voltage':
            figure['data'] = load_voltage_for_lines(selected_lines, new_episode)
        if 'flow' in choice:
            figure['data'] = load_flows_for_lines(selected_lines, new_episode)

    if window is not None:
        figure["layout"].update(
            xaxis=dict(range=window, autorange=False)
        )

    return figure


@app.callback(
    Output('flow_radio', 'style'),
    [Input('voltage_flow_choice', 'value')],
)
def load_flow_graph(choice):
    if choice == 'flow':
        return {'display': 'block'}
    else:
        return {'display': 'none'}


def load_voltage_for_lines(lines, new_episode):
    voltage = new_episode.flow_and_voltage_line
    traces = []

    for value in lines:
        # the first 2 characters are the side of line ('ex' or 'or')
        line_side = str(value)[:2]
        line_name = str(value)
        if line_side == 'ex':
            traces.append(go.Scatter(
                x=new_episode.timestamps,
                # remove the first 3 char to get the line name and round to 3 dec
                y=voltage['ex']['voltage'][line_name[3:]],
                name=line_name)
            )
        if line_side == 'or':
            traces.append(go.Scatter(
                x=new_episode.timestamps,
                y=voltage['or']['voltage'][line_name[3:]],
                name=line_name)
            )
    return traces


def load_flows_for_lines(lines, new_episode):
    flow = new_episode.flow_and_voltage_line
    traces = []

    for value in lines:
        line_side = str(value)[:2]  # the first 2 characters are the side of line ('ex' or 'or')
        flow_type = str(value)[3:].split('_', 1)[0]  # the type is the 1st part of the string: 'type_name'
        line_name = str(value)[3:].split('_', 1)[1]  # the name is the 2nd part of the string: 'type_name'
        x = new_episode.timestamps
        if line_side == 'ex':
            traces.append(go.Scatter(
                x=x,
                y=flow['ex'][flow_type][line_name],
                name=value)
            )
        elif line_side == 'or':
            traces.append(go.Scatter(
                x=x,
                y=flow['or'][flow_type][line_name],
                name=value)
            )
        else:  # this concern usage rate
            name = value.split('_', 2)[2]  # get the powerline name
            index_powerline = list(new_episode.line_names).index(name)
            usage_rate_powerline = new_episode.rho.loc[new_episode.rho['equipment'] == index_powerline]['value']

            traces.append(go.Scatter(
                x=x,
                y=usage_rate_powerline,
                name=name
            ))

    return traces


# context line callback
@app.callback(
    [Output("asset_selector", "options"),
     Output("asset_selector", "value")],
    [Input("environment_choices_buttons", "value")],
    [State("agent_study", "data"),
     State("scenario", "data")]
)
def update_ts_graph_avail_assets(kind, study_agent, scenario):
    new_episode = make_episode(study_agent, scenario)
    return common_graph.ts_graph_avail_assets(kind, new_episode)


@app.callback(
    Output("env_charts_ts", "figure"),
    [Input("asset_selector", "value"),
     Input("relayoutStoreMicro", "data"),
     Input("window", "data")],
    [State("env_charts_ts", "figure"),
     State("environment_choices_buttons", "value"),
     State("scenario", "data"),
     State('agent_study', 'data')]
)
def load_context_data(equipments, relayout_data_store, window, figure, kind, scenario, agent_study):
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
    episode = make_episode(agent_study, scenario)
    figure['data'] = common_graph.environment_ts_data(kind, episode, equipments)

    if window is not None:
        figure["layout"].update(
            xaxis=dict(range=window, autorange=False)
        )

    return figure


@app.callback(
    [Output("overflow_ts", "figure"), Output("usage_rate_ts", "figure")],
    [Input("relayoutStoreMicro", "data"),
     Input("window", "data")],
    [State("overflow_ts", "figure"),
     State("usage_rate_ts", "figure"),
     State('agent_study', 'data'),
     State('agent_ref', 'data'),
     State("scenario", "data")]
)
def update_agent_ref_graph(relayout_data_store, window,
                           figure_overflow, figure_usage, study_agent, agent_ref, scenario):
    if relayout_data_store is not None and relayout_data_store["relayout_data"]:
        relayout_data = relayout_data_store["relayout_data"]
        layout_usage = figure_usage["layout"]
        new_axis_layout = get_axis_relayout(figure_usage, relayout_data)
        if new_axis_layout is not None:
            layout_usage.update(new_axis_layout)
            figure_overflow["layout"].update(new_axis_layout)
            return figure_overflow, figure_usage

    if window is not None:
        figure_overflow["layout"].update(
            xaxis=dict(range=window, autorange=False)
        )
        figure_usage["layout"].update(
            xaxis=dict(range=window, autorange=False)
        )

    return common_graph.agent_overflow_usage_rate_trace(
        make_episode(study_agent, scenario),
        figure_overflow,
        figure_usage
    )


@app.callback(
    Output("timeseries_table_micro", "data"),
    [Input("timeseries_table", "data")]
)
def sync_timeseries_table(data):
    return data


@app.callback(
    Output("interactive_graph", "figure"),
    [Input("slider", "value")],
    [State("agent_study", "data"),
     State("scenario", "data")]
)
def update_interactive_graph(slider_value, study_agent, scenario):
    new_episode = make_episode(study_agent, scenario)
    return make_network(new_episode).get_plot_observation(new_episode.observations[slider_value])
