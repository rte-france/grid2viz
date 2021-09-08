# Copyright (C) 2021, RTE (http://www.rte-france.com/)
# See AUTHORS.txt
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from grid2viz.src.utils.graph_utils import layout_no_data, layout_def


def get_action_per_line(new_episode):
    count = get_modified_lines(new_episode)
    return [go.Bar(x=count.index, y=count.values, name=new_episode.agent)]


def get_modified_lines(new_episode):
    data = get_action_table_data(new_episode)
    # Below to flatten the series of lists "lines_modified"
    try:
        s = data[(data["action_line"] > 0)]["lines_modified"].apply(pd.Series).stack()
        count = s.value_counts()
    except (IndexError, AttributeError):
        count = pd.Series(dtype=np.float64)
    return count


def get_action_redispatch(new_epsiode):
    count = get_modified_gens(new_epsiode)
    return [go.Bar(x=count.index, y=count.values, name=new_epsiode.agent)]


def get_modified_gens(new_episode):
    data = get_action_table_data(new_episode)
    # Below to flatten the series of lists "lines_modified"
    try:
        s = data[(data["action_redisp"] > 0)]["gens_modified"].apply(pd.Series).stack()
        count = s.value_counts()
    except (IndexError, AttributeError):
        count = pd.Series(dtype=np.float64)
    return count


def get_action_table_data(new_episode):
    return new_episode.action_data_table


def get_action_per_sub(new_episode):
    data = get_action_table_data(new_episode)
    # Below to flatten the series of lists "subs_modified"
    try:
        s = data[(data["action_subs"] > 0)]["subs_modified"].apply(pd.Series).stack()
        count = s.value_counts()
    except (IndexError, AttributeError):
        count = pd.Series(dtype=np.float64)
    return [go.Bar(x=count.index, y=count.values, name=new_episode.agent)]


def update_layout(predicate, msg):
    if predicate:
        figure_layout = layout_no_data(msg)
    else:
        figure_layout = layout_def

    return figure_layout


def get_actions_sum(action_data_table):
    return (
        action_data_table.set_index("timestamp")[
            ["action_line", "action_subs", "action_redisp"]
        ]
        .sum(axis=1)
        .to_frame(name="Nb Actions")
    )
