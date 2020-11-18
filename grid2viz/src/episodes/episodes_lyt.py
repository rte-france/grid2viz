import os
from pathlib import Path

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly.figure_factory as ff
import seaborn as sn

from grid2viz.src.manager import survival_df, grid2viz_home_directory
from grid2viz.src.utils.constants import DONT_SHOW_FILENAME
from grid2viz.src.utils.layout_helpers import modal, should_help_open


# This is to improve readability of the heatmap of survival steps for agents
def get_heatmap_survival_score(df):
    if (df.shape[0] >= 2) and (df.shape[1] >= 2):
        clustered_df = sn.clustermap(df)
        reordered_scenarios = clustered_df.dendrogram_row.reordered_ind
        reordered_agents = clustered_df.dendrogram_col.reordered_ind
        return df.iloc[reordered_scenarios, reordered_agents]
    else:
        return df


def create_heatmap_figure(df):

    clustered_survival_df = get_heatmap_survival_score(df)

    z_text = clustered_survival_df.copy().astype(str)
    z_text[z_text == "-1"] = ""

    heatmap_figure = ff.create_annotated_heatmap(  # go.Figure(data=go.Heatmap(
        z=clustered_survival_df.values,  # survival_df.values,#z=pd.concat([survival_df, survival_df]))),
        x=clustered_survival_df.columns.tolist(), y=clustered_survival_df.index.tolist(),
        colorscale='RdYlGn',
        zmid=50,
        annotation_text=z_text.values
    )
    return heatmap_figure


def generate_heatmap_components(df):

    heatmap_div = html.Div(children=[
        html.H5("Agents' survival in percent of the scenario length"),
        dcc.Graph(
            id="heatmap",
            figure=create_heatmap_figure(df),
        ),
    ], style={'textAlign': 'center'}, className="col-xl-12 align-self-center")

    return html.Div(id="h", children=[
        html.Div(children=[
            html.H5(
                dbc.Button(
                    "Scenarios comparison",
                    id="collapse-button",
                    color="link",
                )
            ),
            dbc.Collapse(
                heatmap_div,
                id="collapse"
            ),
        ], className='card-body row p-1'),
    ], className="lineBlockSlim card")


def layout():
    open_help = should_help_open(
        Path(grid2viz_home_directory) / DONT_SHOW_FILENAME("episodes")
    )
    header = "Take a look at the Scenarios"
    body = "The heatmap provides a quick look at the agents' performances across " \
           "all scenarios. Click the open button to continue the analysis on a " \
           "specific scenario. Once you're down, go on to the Agent overview."
    return html.Div(
        id="scenario_page",
        children=[dcc.Store(id="relayoutStoreScenario"),
                  generate_heatmap_components(survival_df),
                  dbc.Row(id='cards_container', className="m-1"),
                  modal(id_suffix="episodes", is_open=open_help,
                        header=header, body=body)]
    )
