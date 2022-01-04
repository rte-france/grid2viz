# Copyright (C) 2021, RTE (http://www.rte-france.com/)
# See AUTHORS.txt
# SPDX-License-Identifier: MPL-2.0

"""
This file handles the html entry point of the application through dash components.
It will generate the layout of a given page and handle the routing
"""

import dash_bootstrap_components as dbc
from dash import Dash
import sys
import warnings

# We need to create app before importing the rest of the project as it uses @app decorators
font_awesome = [
    {
        "href": "https://use.fontawesome.com/releases/v5.8.1/css/all.css",
        "rel": "stylesheet",
        "integrity": "sha384-50oBUHEmvpQ+1lW4y57PTFmhCaXp0ML5d60M1M7uH2+nqUivzIebhndOJK28anvf",
        "crossorigin": "anonymous",
    }
]
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, *font_awesome])

"""
Get Imports to create layout and callbacks 
"""
from grid2viz.main_callbacks import register_callbacks_main
from grid2viz.layout import make_layout as layout

from grid2viz.src.episodes.episodes_clbk import register_callbacks_episodes
from grid2viz.src.overview.overview_clbk import (
    register_callbacks_overview,
)  # as overview_clbk
from grid2viz.src.macro.macro_clbk import register_callbacks_macro  # as macro_clbk
from grid2viz.src.micro.micro_clbk import register_callbacks_micro  # as micro_clbk
from grid2viz.src.simulation.simulation_clbk import register_callbacks_simulation

try:
    from grid2viz.src.simulation.ExpertAssist import Assist
except (ImportError, ModuleNotFoundError):
    from grid2viz.src.simulation.simulation_assist import EmptyAssist as Assist

    warnings.warn(
        "ExpertOp4Grid is not installed and the assist feature will not be available."
        " To use the Assist feature, you can install ExpertOp4Grid by "
        "\n\t{} -m pip install ExpertOp4Grid\n".format(sys.executable)
    )

"""
End Warning
"""
def define_layout_and_callbacks(
    scenario=None,
    agent_ref=None,
    agent_study=None,
    user_timestep=None,
    window=None,
    page=None,
    config=None,
    activate_simulation=False,
):
    ##create layout
    layout(
        app,
        scenario,
        agent_ref,
        agent_study,
        user_timestep,
        window,
        page,
        activate_simulation,
    )

    ##create callbaks
    register_callbacks_main(app)
    register_callbacks_episodes(app)
    register_callbacks_overview(app)
    register_callbacks_macro(app)
    register_callbacks_micro(app)
    if activate_simulation:
        assistant = Assist()
        register_callbacks_simulation(app, assistant)
        assistant.register_callbacks(app)
    if config is not None:
        for key, value in config.items():
            app.server.config[key] = value


def app_run(port=8050, debug=False, page=None):
    if page is not None:
        print(f"Warm start is running on http://127.0.0.1:{port}/{page}")
    app.run_server(port=port, debug=debug)


app.config.suppress_callback_exceptions = True

app.title = "Grid2Viz"
app.server.secret_key = "Grid2Viz"
#define_layout_and_callbacks(activate_simulation=True)
define_layout_and_callbacks(activate_simulation=False)#as we don't always have the grid2op environment available for demos
server=app.server


if __name__ == "__main__":
    app_run()
