from ..manager import episode, prod_types
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from .env_actions import env_actions


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
    data = new_episode.action_data_table
    count = data[(data["action_line"] == 1) | (data["action_subs"] == 1)]["sub_name"].value_counts()
    # sub_names = new_episode.name_subs
    return [go.Bar(x=count.index.values.tolist(), y=count)]
