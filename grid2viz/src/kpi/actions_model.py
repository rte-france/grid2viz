import plotly.graph_objects as go


def get_action_per_line(new_episode):
    data = get_action_table_data(new_episode)
    count = data[(data["action_line"] > 0)]["line_name"].map(lambda x: " ".join(x)).value_counts()
    return [go.Bar(x=count.index, y=count.values)]


def get_action_table_data(new_episode):
    return new_episode.action_data_table


def get_action_per_sub(new_episode):
    data = get_action_table_data(new_episode)
    count = data[(data["action_subs"] > 0)]["sub_name"].map(lambda x: " ".join(x)).value_counts()
    return [go.Bar(x=count.index, y=count.values)]


def get_actions_sum(new_episode):
    return new_episode.action_data_table.set_index("timestamp")[[
        'action_line', 'action_subs'
    ]].sum(axis=1).to_frame(name="Nb Actions")
