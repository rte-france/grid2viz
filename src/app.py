import dash_bootstrap_components as dbc

from .grid2viz import create_app


app = create_app(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config.suppress_callback_exceptions = True
app.title = "Grid2Viz"
app.server.secret_key = "Grid2Viz"
