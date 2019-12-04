import dash_bootstrap_components as dbc
import plotly.io as pio

from .grid2viz import create_app

pio.templates.default = "seaborn"

app = create_app(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config.suppress_callback_exceptions = True
