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
