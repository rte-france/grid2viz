"""Utility functions for manipulating plotly figures"""


def get_axis_relayout(figure, relayout_data):

    layout = figure["layout"]
    template_layout = figure["layout"]["template"]["layout"]
    if "xaxis" in layout:
        xaxis = layout["xaxis"]
    else:
        xaxis = template_layout["xaxis"]
    if "yaxis" in layout:
        yaxis = layout["yaxis"]
    else:
        yaxis = template_layout["yaxis"]
    if "range" not in xaxis:
        xaxis.update(
            range=[
                min(figure["data"][0]["x"]),
                max(figure["data"][0]["x"])
            ]
        )
    if "range" not in yaxis:
        yaxis.update(
            range=[
                min(figure["data"][0]["y"]),
                max(figure["data"][0]["y"])
            ]
        )
    res = {}
    if "xaxis.range[0]" in relayout_data:
        xmin, xmax = relayout_data["xaxis.range[0]"], relayout_data["xaxis.range[1]"]
        if [xmin, xmax] != xaxis["range"]:
            res.update(xaxis=dict(range=[xmin, xmax], autorange=False))
    if "yaxis.range[0]" in relayout_data:
        ymin, ymax = relayout_data["yaxis.range[0]"], relayout_data["yaxis.range[1]"]
        if [ymin, ymax] != yaxis["range"]:
            res.update(yaxis=dict(range=[ymin, ymax], autorange=False))
    if "xaxis.autorange" in relayout_data:
        res.update(xaxis=dict(autorange=relayout_data["xaxis.autorange"]))
    if "yaxis.autorange" in relayout_data:
        res.update(yaxis=dict(autorange=relayout_data["yaxis.autorange"]))
    if res:
        return res
