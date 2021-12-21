# Copyright (C) 2021, RTE (http://www.rte-france.com/)
# See AUTHORS.txt
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import dash_antd_components as dac
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly.figure_factory as ff
import seaborn as sn

from grid2viz.src.manager import survival_df, attention_df, grid2viz_home_directory, scenarios
from grid2viz.src.utils.constants import DONT_SHOW_FILENAME
from grid2viz.src.utils.layout_helpers import modal, should_help_open


# This is to improve readability of the heatmap of survival steps for agents
def get_heatmap_survival_attention_score(df_survival,df_attention):
    if (df_survival.shape[0] >= 2) and (df_survival.shape[1] >= 2):
        clustered_df = sn.clustermap(df_survival)
        reordered_scenarios = clustered_df.dendrogram_row.reordered_ind
        reordered_agents = clustered_df.dendrogram_col.reordered_ind
        return df_survival.iloc[reordered_scenarios, reordered_agents], df_attention.iloc[reordered_scenarios, reordered_agents]
    else:
        return df_survival, df_attention


def create_heatmap_figures(df_survival, df_attention):
    clustered_survival_df, clustered_attention_df = get_heatmap_survival_attention_score(df_survival, df_attention)

    z_text = clustered_survival_df.copy().astype(str)
    z_text[z_text == "-1"] = ""

    heatmap_figure_survival = ff.create_annotated_heatmap(  # go.Figure(data=go.Heatmap(
        z=clustered_survival_df.values,  # survival_df.values,#z=pd.concat([survival_df, survival_df]))),
        x=clustered_survival_df.columns.tolist(),
        y=clustered_survival_df.index.tolist(),
        colorscale="RdYlGn",
        zmid=50,
        annotation_text=z_text.values,
    )
    heatmap_figure_survival.update_layout(
        {"yaxis": {"type": "category"}, "xaxis": {"type": "category"}}
    )

    z_text = clustered_attention_df.copy().astype(str)
    #z_text[z_text == "-1"] = ""
    heatmap_figure_attention = ff.create_annotated_heatmap(  # go.Figure(data=go.Heatmap(
        z=clustered_attention_df.values,  # survival_df.values,#z=pd.concat([survival_df, survival_df]))),
        x=clustered_attention_df.columns.tolist(),
        y=clustered_attention_df.index.tolist(),
        colorscale="RdYlGn",
        zmid=0.5,
        annotation_text=z_text.values,
    )
    heatmap_figure_attention.update_layout(
        {"yaxis": {"type": "category"}, "xaxis": {"type": "category"}}
    )

    return heatmap_figure_survival, heatmap_figure_attention



def generate_heatmap_components(df_survival, df_attention):

    heatmap_survival, heatmap_attention=create_heatmap_figures(df_survival, df_attention)
    heatmap_survival_div = html.Div(
        children=[

            html.H3("Percentage of Agents' survival time over a scenario"),
            dcc.Graph(
                id="heatmap survival",
                figure=heatmap_survival,
            ),
        ],
        className="four columns"#"col-xl-12 align-self-center heatmap",
    )

    heatmap_attention_div = html.Div(
        children=[
            html.H3("Agent attention score over a scenario"),
            dcc.Graph(
                id="heatmap attention",
                figure=heatmap_attention,
            ),
        ],
        className="four columns"#"col-xl-12 align-self-center heatmap",
    )

    heatmaps_div=html.Div(className="row", children=[heatmap_survival_div, heatmap_attention_div])

    return html.Div(
        className="lineBlockSlim card",
        children=[html.Div(className="row",
                           children=[dbc.Collapse(heatmaps_div, id="collapse"),
                                     scenarios_filter(sorted(list(scenarios)))
                                     ])
                  ],
    )


def scenarios_filter(scenarios):
    return html.Div(
        id="scenario_filter_div",
        className="four columns",
        children=[
            html.H5("Select the scenarios you want to see in cards below."),
            dac.Select(
                id="scenarios_filter",
                options=[
                    {"label": scenario, "value": scenario} for scenario in scenarios
                ],
                value=scenarios,
                mode="multiple",
            ),
        ],
    )


def comparison_button():
    return html.Div(
        className="row comparison-btn",
        children=[
            dbc.Button(
                "Open scenarios comparison & filtering",
                id="collapse-button",
                color="info",
                size="lg",
                outline=True,
                block=True,
            )
        ],
    )


def layout():
    open_help = should_help_open(
        Path(grid2viz_home_directory) / DONT_SHOW_FILENAME("episodes")
    )
    header = "Take a look at the Scenarios"
    body = (
        " Choose a specific scenario to analyze by clicking its Open button.  "
        "Get more detailed information when choosing your scenario by clicking on the comparison & filtering button"
    )
    return html.Div(
        id="scenario_page",
        children=[
            dcc.Store(id="relayoutStoreScenario"),
            comparison_button(),
            generate_heatmap_components(survival_df, attention_df),
            dbc.Row(id="cards_container", className="m-1"),
            modal(id_suffix="episodes", is_open=open_help, header=header, body=body),
        ],
    )
