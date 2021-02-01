import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

nav_items = [
    dbc.NavItem(
        dbc.NavLink(
            "Scenario Selection", active=True, href="/episodes", id="nav_scen_select"
        )
    ),
    dbc.NavItem(dbc.NavLink("Scenario Overview", href="/overview", id="nav_scen_over")),
    dbc.NavItem(dbc.NavLink("Agent Overview", href="/macro", id="nav_agent_over")),
    dbc.NavItem(dbc.NavLink("Agent Study", href="/micro", id="nav_agent_study")),
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


def navbar(scenario=None):
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
                        id="user_timestamps", className="", style={"width": "200px"}
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
            html.Div(dbc.Nav(nav_items, navbar=True, pills=True), className="nav_menu"),
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
    user_timestamps=None,
    window=None,
    page=None,
):
    app.layout = html.Div(
        [
            dcc.Store(id="scenario", storage_type="memory", data=scenario),
            dcc.Store(id="agent_ref", storage_type="memory", data=agent_ref),
            dcc.Store(id="agent_study", storage_type="memory", data=agent_study),
            dcc.Store(id="user_timestamps_store", data=user_timestamps),
            dcc.Store(id="window", data=window),
            dcc.Store(id="page", data=page),
            dcc.Store(id="relayoutStoreMicro"),
            dcc.Store(id="reset_timeseries_table_macro", data=True),
            navbar(scenario),
            body(page),
        ]
    )
