# Copyright (C) 2021, RTE (http://www.rte-france.com/)
# See AUTHORS.txt
# SPDX-License-Identifier: MPL-2.0

import pandas as pd
import plotly.graph_objects as go

from .observation_model import quantile10, quantile25, quantile75, quantile90


def consumption_profiles(episode, freq="30T"):

    # filter intercos
    idx_no_interco = [
        i
        for i in range(len(episode.load.equipment_name))
        if "interco" not in episode.load.equipment_name[i]
    ]

    load = (
        pd.pivot_table(
            episode.load.loc[idx_no_interco],
            index="timestamp",
            columns=["equipment_name"],
            values="value",
        )
        .astype('float64').sum(axis=1)
        .resample(freq)
        .mean()
        .to_frame(name="load")
        .reset_index()
    )

    if freq == "H":
        load["timestamp"] = load.timestamp.dt.hour
    elif "T" in freq:
        load["timestamp"] = load.timestamp.dt.time.map(lambda x: x.strftime("%H:%M"))
    else:
        raise ValueError(
            'Only hourly ("H") or minutely ("xT") freqs are '
            f"supported. Passed: {freq}"
        )

    daily_load_distrib = (
        load.groupby(["timestamp"])
        .aggregate(["median", quantile10, quantile25, quantile75, quantile90, "max"])[
            ["load"]
        ]
        .reset_index()
    )

    return daily_load_distrib


def profiles_traces(episode, freq="30T"):
    episode_data = episode
    df = consumption_profiles(episode_data, freq)
    line = {"shape": "spline", "width": 0, "smoothing": 1}
    trace = [
        go.Scatter(
            x=df["timestamp"], y=df["load"]["quantile10"], name="quantile 10", line=line
        ),
        go.Scatter(
            x=df["timestamp"],
            y=df["load"]["quantile25"],
            name="quantile 25",
            fill="tonexty",
            fillcolor="rgba(159, 197, 232, 0.63)",
            line=line,
        ),
        go.Scatter(
            x=df["timestamp"],
            y=df["load"]["median"],
            name="median",
            fill="tonexty",
            fillcolor="rgba(31, 119, 180, 0.5)",
            line={"color": "rgb(31, 119, 180)", "shape": "spline", "smoothing": 1},
        ),
        go.Scatter(
            x=df["timestamp"],
            y=df["load"]["quantile75"],
            name="quantile 75",
            fill="tonexty",
            fillcolor="rgba(31, 119, 180, 0.5)",
            line=line,
        ),
        go.Scatter(
            x=df["timestamp"],
            y=df["load"]["quantile90"],
            name="quantile 90",
            fill="tonexty",
            fillcolor="rgba(159, 197, 232, 0.63)",
            line=line,
        ),
        go.Scatter(
            x=df["timestamp"],
            y=df["load"]["max"],
            name="Max",
            line={"shape": "spline", "smoothing": 1, "color": "rgba(255,0,0,0.5)"},
        ),
    ]
    return trace
