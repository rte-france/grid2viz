import dash_bootstrap_components as dbc
from dash import Dash

from simulation_clbk import register_callbacks_simulation
from simulation_lyt import layout
from manager_simulation import assistant

# We need to create app before importing the rest of the project as it uses @app decorators
font_awesome = [
    {
        "href": "https://use.fontawesome.com/releases/v5.8.1/css/all.css",
        "rel": "stylesheet",
        "integrity": "sha384-50oBUHEmvpQ+1lW4y57PTFmhCaXp0ML5d60M1M7uH2+nqUivzIebhndOJK28anvf",
        "crossorigin": "anonymous",
    }
]
app = Dash("simulation", external_stylesheets=[dbc.themes.BOOTSTRAP, *font_awesome])

scenario = "000"
agent = "do-nothing-baseline"
agent_dir = "D:/Projects/RTE-Grid2Viz/grid2viz/grid2viz/data/agents/" + agent
path = r"D:\Projects\RTE-Grid2Viz\grid2viz\grid2viz\data\agents\_cache\000\do-nothing-baseline.dill"
agent_path = (
    r"D:/Projects/RTE-Grid2Viz/grid2viz/grid2viz/data/agents/do-nothing-baseline"
)
env_path = r"D:\Projects\RTE-Grid2Viz\Grid2Op\grid2op\data\rte_case14_realistic"

t = 1
app.layout = layout(scenario=scenario, study_agent="do-nothing-baseline", timestep=t)

register_callbacks_simulation(app)
assistant.register_callbacks(app)

if __name__ == "__main__":
    app.run_server(port=8008)
