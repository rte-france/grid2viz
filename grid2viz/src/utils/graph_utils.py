# Copyright (C) 2021, RTE (http://www.rte-france.com/)
# See AUTHORS.txt
# SPDX-License-Identifier: MPL-2.0

"""Utility functions for manipulating plotly figures"""

from dash.exceptions import PreventUpdate


def max_or_zero(x):
    if len(x) == 0:
        return 0
    else:
        return max(x)


class RelayoutX(object):
    """
    Wrapping class for dash core component Graph relayoutData attribute
    to make it hashable.

    Attributes
    ----------
    xmin : float
        xaxis.range[0] attribute of relayoutData (when it exists, None otherwise).
    xmax : float
        xaxis.range[1] attribute of relayoutData (when it exists, None otherwise).

    """

    def __init__(self, relayout_data=None):

        if "xaxis.range[0]" in relayout_data:
            self.xmin, self.xmax = (
                relayout_data["xaxis.range[0]"],
                relayout_data["xaxis.range[1]"],
            )
        else:
            self.xmin, self.xmax = None, None

        self.relayout_data = relayout_data

    def __eq__(self, other):
        return (self.xmin == other.xmin) and (self.xmax == other.xmax)

    def __hash__(self):
        return hash((self.xmin, self.xmax))


def relayout_callback(*args):
    # This function supposes that it's not possible to get the same
    # relayoutData twice.

    if any(arg is None for arg in args[:-1]):
        raise PreventUpdate
    if args[-1] is None:
        relayout_data_store = dict(relayout_history=[], relayout_data=None, reset_nb=0)
    else:
        relayout_data_store = args[-1]

    if all("autosize" in arg for arg in args[:-1]):
        return relayout_data_store

    reset_nb = relayout_data_store["reset_nb"]
    new_reset_nb = 0
    relayouts_indx = []
    relayout_history_x = [
        RelayoutX(rlyt) for rlyt in relayout_data_store["relayout_history"]
    ]
    relayouts_x = [RelayoutX(arg) for arg in args[:-1]]
    for i, arg in enumerate(args[:-1]):
        if (
            ("xaxis.range[0]" in arg or "xaxis.autorange" in arg)
            and (relayouts_x[i] not in relayout_history_x)
            and ("autosize" not in arg)
        ):
            if "xaxis.autorange" in arg and arg["xaxis.autorange"]:
                new_reset_nb = new_reset_nb + 1
            else:
                relayouts_indx.append(i)
    if not relayouts_indx:
        if new_reset_nb > reset_nb:
            # It's a zoom reset
            relayout_data_store["reset_nb"] = reset_nb + 1
            relayout_data_store["relayout_data"] = {"xaxis.autorange": True}
            return relayout_data_store
        else:
            # No relayout events with xaxis effect
            raise PreventUpdate
    if len(relayouts_indx) > 2:
        # This should never happen
        print(relayouts_indx)
        raise Exception

    relayout_data_store["reset_nb"] = new_reset_nb
    relayout_data_store["relayout_history"].append(args[relayouts_indx[0]])
    relayout_data_store["relayout_data"] = args[relayouts_indx[0]]
    return relayout_data_store


def get_axis_relayout(figure, relayout_data):
    layout = figure["layout"]
    template_layout = figure["layout"]["template"]["layout"]
    if "xaxis" in layout:
        xaxis = layout["xaxis"]
    else:
        xaxis = template_layout["xaxis"]
    if "range" not in xaxis and "x" in figure["data"][0]:
        xaxis.update(range=[min(figure["data"][0]["x"]), max(figure["data"][0]["x"])])
    res = {}
    if "xaxis.range[0]" in relayout_data:
        xmin, xmax = relayout_data["xaxis.range[0]"], relayout_data["xaxis.range[1]"]
        if [xmin, xmax] != xaxis["range"]:
            res.update(xaxis=dict(range=[xmin, xmax], autorange=False))
    if "xaxis.autorange" in relayout_data:
        res.update(xaxis=dict(autorange=relayout_data["xaxis.autorange"]))
    if res:
        return res


layout_def = {
    "legend": {"orientation": "h"},
    "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
    "xaxis": {"visible": True},
    "yaxis": {"visible": True, "fixedrange": True, "autorange": True},
    "annotations": [],
    "plot_bgcolor": "#E5ECF6",
}


def layout_no_data(msg):
    return {
        "xaxis": {"visible": False},
        "yaxis": {"visible": False},
        "plot_bgcolor": "rgba(0, 0, 0, 0)",
        "annotations": [
            {
                "text": msg,
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 28},
            }
        ],
    }
