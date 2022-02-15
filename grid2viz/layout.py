# Copyright (C) 2021, RTE (http://www.rte-france.com/)
# See AUTHORS.txt
# SPDX-License-Identifier: MPL-2.0

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

from grid2viz.src.manager import make_episode

nav_items = [
    dbc.NavItem(
        dbc.NavLink(
            "Scenario Selection", active=True, href="/episodes", id="nav_scen_select"
        )
    ),
    dbc.NavItem(dbc.NavLink("Scenario Overview", href="/overview", id="nav_scen_over", n_clicks=0)),
    dbc.NavItem(dbc.NavLink("Agent Overview", href="/macro", id="nav_agent_over", n_clicks=0)),
    dbc.NavItem(dbc.NavLink("Agent Study", href="/micro", id="nav_agent_study", n_clicks=0)),
    dbc.NavItem(dbc.NavLink("Simulation", href="/simulation", id="nav_simulation", n_clicks=0)),
    dbc.DropdownMenu(
        label="Help",
        color="link",
        in_navbar=True,
        nav=True,
        right=True,
        children=[
            dbc.DropdownMenuItem("Page Help", id="page_help"),
            dbc.DropdownMenuItem(divider=True),
            dbc.NavLink(
                "Documentation",
                href="https://grid2viz.readthedocs.io/en/latest/",
                id="nav_help",
                target="_blank",
            ),
        ],
    ),
]

nav_items_no_simulation = [
    dbc.NavItem(
        dbc.NavLink(
            "Scenario Selection", active=True, href="/episodes", id="nav_scen_select"
        )
    ),
    dbc.NavItem(dbc.NavLink("Scenario Overview", href="/overview", id="nav_scen_over")),
    dbc.NavItem(dbc.NavLink("Agent Overview", href="/macro", id="nav_agent_over")),
    dbc.NavItem(dbc.NavLink("Agent Study", href="/micro", id="nav_agent_study")),
    dbc.NavItem(dbc.NavLink("", href="#", disabled=True, id="nav_simulation")),
    dbc.DropdownMenu(
        label="Help",
        color="link",
        in_navbar=True,
        nav=True,
        right=True,
        children=[
            dbc.DropdownMenuItem("Page Help", id="page_help"),
            dbc.DropdownMenuItem(divider=True),
            dbc.NavLink(
                "Documentation",
                href="https://grid2viz.readthedocs.io/en/latest/",
                id="nav_help",
                target="_blank",
            ),
        ],
    ),
]


def navbar(
    scenario=None,
    ts="",
    timestamp_dropdown_options=None,
    timestamp_dropdown_value="",
    items=nav_items,
):
    if timestamp_dropdown_options is None:
        timestamp_dropdown_options = []
    return dbc.Navbar(
        [
            html.Div(
                [
                    html.Span(
                        "Scenario:",
                        className="badge badge-secondary",
                    ),
                    html.Span(
                        scenario if scenario is not None else "",
                        className="badge badge-light",
                        id="scen_lbl",
                    ),
                ],
                className="reminder float-left",
            ),
            html.Div(
                [
                    html.Span("Ref Agent:", className="badge badge-secondary"),
                    html.Span(
                        children=[
                            dbc.Select(
                                id="select_ref_agent",
                                bs_size="sm",
                                #size="sm",
                                disabled=True,
                                placeholder="Ref Agent",
                            )
                        ],
                        className="badge",
                    ),
                ],
                className="reminder float-left",
            ),
            html.Div(
                [
                    html.Span("Studied Agent:", className="badge badge-secondary"),
                    html.Span(
                        children=[
                            dbc.Select(
                                id="select_study_agent",
                                bs_size="sm",
                                #size="sm",
                                disabled=True,
                                placeholder="Study Agent",
                            )
                        ],
                        className="badge",
                    ),
                ],
                className="reminder float-left",
            ),
            html.Div(
                [
                    html.Div(
                        children=[
                            dbc.Badge("TS:", color="secondary", className="ml-1"),
                            dbc.Badge(
                                ts, color="light", className="ml-1", id="badge_ts"
                            ),
                        ],
                        className="reminder float-left mt-2",
                    ),
                    html.Div(
                        [
                            dbc.Button(
                                id="enlarge_left",
                                children="-5",
                                color="dark",
                                className="float-left mr-1",
                            ),
                            dbc.Tooltip(
                                "Enlarge left",
                                target="enlarge_left",
                                placement="bottom",
                            ),
                        ]
                    ),
                    dcc.Dropdown(
                        id="user_timestamps",
                        className="",
                        style={"width": "200px"},
                        options=timestamp_dropdown_options,
                        value=timestamp_dropdown_value,
                    ),
                    html.Div(
                        [
                            dbc.Button(
                                id="enlarge_right",
                                children="+5",
                                color="dark",
                                className="float-left ml-1",
                            ),
                            dbc.Tooltip(
                                "Enlarge right",
                                target="enlarge_right",
                                placement="bottom",
                            ),
                        ]
                    ),
                ],
                id="user_timestamp_div",
                className="col-xl-1",
            ),
            html.Div(dbc.Nav(items, navbar=True, pills=True), className="nav_menu"),
        ],
        color="#2196F3",
        sticky="top",
        dark=True,
    )


def body(page=""):
    return html.Div(
        [
            dcc.Location(id="url", refresh=False),
            html.Div(id="page-content", className="main-container"),
            dbc.Modal(
                [
                    dbc.ModalBody(
                        [
                            dbc.Spinner(color="primary", type="grow"),
                            html.P("loading graph..."),
                        ]
                    )
                ],
                id="loading_modal",
            ),
        ]
    )


def make_layout(
    app,
    scenario=None,
    agent_ref=None,
    agent_study=None,
    user_timestep=None,
    window=None,
    page=None,
    activate_simulation=False,
):
    if user_timestep is None:
        user_timestep = 0
    if scenario is None or agent_study is None:
        timestamp_str = ""
    else:
        episode = make_episode(episode_name=scenario, agent=agent_study)
        timestamp_str = episode.timestamps[int(user_timestep)].strftime(
            "%Y-%m-%d %H:%M"
        )
    user_timestamp = [dict(label=timestamp_str, value=timestamp_str)]
    if activate_simulation:
        items = nav_items
    else:
        items = nav_items_no_simulation
    app.layout = html.Div(
        [
            dcc.Store(id="scenario", storage_type="memory", data=scenario),
            dcc.Store(id="agent_ref", storage_type="memory", data=agent_ref),
            dcc.Store(id="agent_study", storage_type="memory", data=agent_study),
            dcc.Store(id="user_timestep_store", data=user_timestep),
            dcc.Store(id="user_timestamps_store", data=user_timestamp),
            dcc.Store(id="window", data=window),
            dcc.Store(id="page", data=page),
            dcc.Store(id="relayoutStoreMicro"),
            dcc.Store(id="reset_timeseries_table_macro", data=True),
            navbar(
                scenario,
                ts=user_timestep,
                timestamp_dropdown_options=user_timestamp,
                timestamp_dropdown_value=user_timestamp[0]["value"],
                items=items,
            ),
            dbc.Button(
                [dbc.Spinner(size="md", id="loading-2",fullscreen=True,
                             children=html.Div(id="loading-output-2")), " Loading data on page ..."],  # all the scenarios..."],
                id="loading-episode-button",
                color="grey",
                disabled=True,
                block=True,
                style=dict()
            ),
            dcc.Interval(id='loading-stepper-episode', interval=2000, n_intervals=0),
            body(page),

        ]
    )
