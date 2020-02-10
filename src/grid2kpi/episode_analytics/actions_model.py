import plotly.graph_objects as go


def get_action_set_line_trace(new_episode):
    data = new_episode.action_data
    return [go.Bar(x=new_episode.line_names, y=sum(data["set_line"]))]


def get_action_switch_line_trace(new_episode):
    data = new_episode.action_data
    return [go.Bar(x=new_episode.line_names, y=sum(data["switch_line"]))]


def get_action_set_topo_trace(new_episode):
    data = new_episode.action_data
    return [go.Bar(x=list(range(len(data["set_topo"]))), y=sum(data["set_topo"]))]


def get_action_change_bus_trace(new_episode):
    data = new_episode.action_data
    return [go.Bar(x=list(range(len(data["change_bus"]))), y=sum(data["change_bus"]))]


def get_action_table_data(new_episode):
    return new_episode.action_data_table


def get_action_per_sub(new_episode):
    data = get_action_table_data(new_episode)
    count = data[(data["action_subs"] > 0)]["sub_name"].map(lambda x: " ".join(x)).value_counts()
    sub_names = new_episode.name_sub
    return [go.Bar(x=count.index, y=count.values)]
