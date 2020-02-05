import plotly.graph_objects as go


def get_action_set_line_trace(new_episode):
    data = new_episode['data'].action_data
    return [go.Bar(x=new_episode['data'].line_names, y=sum(data["set_line"]))]


def get_action_switch_line_trace(new_episode):
    data = new_episode['data'].action_data
    return [go.Bar(x=new_episode['data'].line_names, y=sum(data["switch_line"]))]


def get_action_set_topo_trace(new_episode):
    data = new_episode['data'].action_data
    return [go.Bar(x=list(range(len(data["set_topo"]))), y=sum(data["set_topo"]))]


def get_action_change_bus_trace(new_episode):
    data = new_episode['data'].action_data
    return [go.Bar(x=list(range(len(data["change_bus"]))), y=sum(data["change_bus"]))]


def get_action_table_data(new_episode):
    return new_episode['data'].action_data_table


def get_action_per_sub(new_episode):
    data = new_episode['data'].action_data_table
    count = data[(data["action_subs"] == 1)]["sub_name"].value_counts()
    sub_names = new_episode['data'].name_sub
    return [go.Bar(x=sub_names, y=count)]
