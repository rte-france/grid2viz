"""Utility functions for manipulating plotly figures"""

from dash.exceptions import PreventUpdate


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
            self.xmin, self.xmax = relayout_data["xaxis.range[0]"], relayout_data["xaxis.range[1]"]
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
        relayout_data_store = dict(
            relayout_history=[], relayout_data=None, reset_nb=0)
    else:
        relayout_data_store = args[-1]

    if all("autosize" in arg for arg in args[:-1]):
        return relayout_data_store

    reset_nb = relayout_data_store["reset_nb"]
    new_reset_nb = 0
    relayouts_indx = []
    relayout_history_x = [
        RelayoutX(rlyt) for rlyt in relayout_data_store["relayout_history"]]
    relayouts_x = [RelayoutX(arg) for arg in args[:-1]]
    for i, arg in enumerate(args[:-1]):
        if (("xaxis.range[0]" in arg or "xaxis.autorange" in arg) and
                (relayouts_x[i] not in relayout_history_x) and ("autosize" not in arg)):
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
            # relayout_data_store["PreventUpdate"] = True
            # return relayout_data_store
    if len(relayouts_indx) > 2:
        # This should never happen
        print(relayouts_indx)
        raise Exception("Weird")

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
    # if "yaxis" in layout:
    #     yaxis = layout["yaxis"]
    # else:
    #     yaxis = template_layout["yaxis"]
    if "range" not in xaxis:
        xaxis.update(
            range=[
                min(figure["data"][0]["x"]),
                max(figure["data"][0]["x"])
            ]
        )
    # if "range" not in yaxis:
    #     yaxis.update(
    #         range=[
    #             min(figure["data"][0]["y"]),
    #             max(figure["data"][0]["y"])
    #         ]
    #     )
    res = {}
    if "xaxis.range[0]" in relayout_data:
        xmin, xmax = relayout_data["xaxis.range[0]"], relayout_data["xaxis.range[1]"]
        if [xmin, xmax] != xaxis["range"]:
            res.update(xaxis=dict(range=[xmin, xmax], autorange=False))
    # if "yaxis.range[0]" in relayout_data:
    #     ymin, ymax = relayout_data["yaxis.range[0]"], relayout_data["yaxis.range[1]"]
    #     if [ymin, ymax] != yaxis["range"]:
    #         res.update(yaxis=dict(range=[ymin, ymax], autorange=False))
    if "xaxis.autorange" in relayout_data:
        res.update(xaxis=dict(autorange=relayout_data["xaxis.autorange"]))
    # if "yaxis.autorange" in relayout_data:
    #     res.update(yaxis=dict(autorange=relayout_data["yaxis.autorange"]))
    if res:
        return res
