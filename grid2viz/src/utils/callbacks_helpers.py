# Copyright (C) 2021, RTE (http://www.rte-france.com/)
# See AUTHORS.txt
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

from dash import callback_context as ctx
from dash.exceptions import PreventUpdate


def toggle_modal_helper(
    n_clicks_close: int,
    n_clicks_open: int,
    is_open: bool,
    dont_show_again: bool,
    dsa_filepath: str,
    open_btn_id: str,
):
    if not ctx.triggered:
        raise PreventUpdate
    else:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == open_btn_id:
        class_name = "hidden"
    else:
        class_name = None
    if dont_show_again:
        Path(dsa_filepath).touch()
    if n_clicks_close or n_clicks_open:
        return not is_open, class_name
    return is_open, class_name
