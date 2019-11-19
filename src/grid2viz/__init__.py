from dash import Dash


def create_app(name, external_stylesheets):
    app = Dash(name=name, external_stylesheets=external_stylesheets)
    return app
