from ..manager import episode
import plotly.graph_objects as go


def get_episode_active_consumption_ts():
    ret = []
    for i in range(episode.observations):
        obs = episode.get_observation(i)
        ret.append(sum(obs.load_p))
    return ret


def get_prod():
    return episode.production


def get_load():
    return episode.load


def get_prod_trace_per_equipment():
    return get_df_trace_per_equipment(get_prod())


def get_load_trace_per_equipment():
    return get_df_trace_per_equipment(get_load())


def get_df_trace_per_equipment(df):
    trace = []
    for equipment in df["equipment"].drop_duplicates():
        trace.append(go.Scatter(
            x=df.loc[df["equipment"] == equipment, :]["time"],
            y=df.loc[df["equipment"] == equipment, :]["value"]
        ))
    return trace


def create_ts_data(object_type, id):
    return {
        'x': [],
        'y': [],
        'type': 'scatter',
        'name': 'equipment' + str(id),
        'mode': 'lines',
        # 'line': {'color': get_color(object_type, id)}
    }


def get_color(object_type, id):
    return '#'  # TODO : figure out a way to have the same colors everytime
