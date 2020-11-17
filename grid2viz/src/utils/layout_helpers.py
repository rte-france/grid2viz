from pathlib import Path

import dash_html_components as html
import dash_bootstrap_components as dbc


def modal(id_suffix: str = "", is_open: bool = True,
          header: str = "", body: str = ""):
    """
    Creat a modal used in every view to guide the user.
    Parameters
    ----------
    id_suffix: `str`
        Suffix used to make ids unique
    is_open: `bool`
        Control the visibility of the modal
    header: `str`
        Text for the header of the modal
    body: `str`
        Text for the body fo the modal
    Returns
    -------
    The dash component
    """
    id_modal = f"modal_{id_suffix}"
    id_close_btn = f"close_{id_suffix}"
    id_dont_show_again = f"dont_show_again_{id_suffix}"
    id_dont_show_again_div = f"dont_show_again_div_{id_suffix}"

    return html.Div(
        [
            dbc.Modal(
                [
                    dbc.ModalHeader(header),
                    dbc.ModalBody(body),
                    dbc.ModalFooter(children=[
                        html.Div(id=id_dont_show_again_div, children=[
                            dbc.Checkbox(
                                id=id_dont_show_again, className="form-check-input"
                            ),
                            dbc.Label("Do not show again", html_for=id_dont_show_again,
                                      className="form-check-label"),
                        ], className="ml-auto"),
                        dbc.Button("Close", id=id_close_btn, className="ml-auto"),
                    ]),
                ],
                id=id_modal, is_open=is_open
            ),
        ]
    )


def should_help_open(filepath_to_check: str):
    open_modal = True
    if Path(filepath_to_check).is_file():
        open_modal = False
    return open_modal
