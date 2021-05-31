from abc import abstractmethod, ABC
from itertools import chain

import dash_core_components as dcc
import dash_html_components as html


class BaseAssistant(ABC):
    def __init__(self):
        self._layout = None

    @abstractmethod
    def layout(self, *args):
        pass

    @abstractmethod
    def register_callbacks(self, app):
        pass

    @abstractmethod
    def store_to_graph(self, store_data):
        """
        Returns a Grid2Op network graph for the data stored in store_data
        Parameters
        ----------
        store_data

        Returns
        -------

        """
        pass

    def register_layout(self, *layout_args, layout_to_ckeck_against=None):
        self._layout = self.layout(*layout_args)
        self.check_layout(layout_to_ckeck_against)
        return self._layout

    def check_layout(self, layout_to_check_against):
        try:
            if (
                self._layout.children[0]._type != "Store"
                or self._layout.children[0].id != "assistant_store"
            ):
                raise Exception(
                    f"The first child of the Assistant layout should be a Store with id assistant_store, found {self._layout.children[0]}"
                )
        except:
            raise Exception(
                f"The first child of the Assistant layout should be a Store with id assistant_store, found {self._layout}"
            )
        layouts_conflicts = self.layouts_conflicts(
            self._layout, layout_to_check_against
        )
        if layouts_conflicts:
            raise Exception(
                f"The {self.__class__.__name__} layout has ids conflict with the parent layout : {layouts_conflicts}"
            )

    @staticmethod
    def layouts_conflicts(layout1, layout2):
        """
        Check that two layouts do not share identical ids
        Parameters
        ----------
        layout1
        layout2

        Returns
        -------

        """
        ids_layout1 = BaseAssistant.get_layout_ids(layout1)
        ids_layout2 = BaseAssistant.get_layout_ids(layout2)

        return set(ids_layout1) & set(ids_layout2)

    def get_layout_ids():
        def get_layout_ids(layout):
            """
            Traverse a dash layout to retrieve declared ids
            Parameters
            ----------
            layout

            Returns
            -------

            """

            if hasattr(layout, "children") and isinstance(layout.children, list):
                children_ids = list(
                    chain.from_iterable(
                        [get_layout_ids(child) for child in layout.children]
                    )
                )
                if hasattr(layout, "id"):
                    return [layout.id, *children_ids]
                else:
                    return children_ids
            else:
                if hasattr(layout, "id"):
                    return [layout.id]
                return []

        return get_layout_ids

    get_layout_ids = staticmethod(get_layout_ids())


class EmptyAssist(BaseAssistant):
    def __init__(self):
        super().__init__()

    def layout(self, *args):
        return html.Div(
            [
                dcc.Store(id="assistant_store"),
                dcc.Store(id="assistant_actions"),
                dcc.Store(
                    id="assistant-size", data=dict(assist="col-3", graph="col-9")
                ),
                html.P("No Assistant found.", className="my-2"),
            ]
        )

    def register_callbacks(self, app):
        pass

    def store_to_graph(self, store_data):
        pass


if __name__ == "__main__":
    import dash
    import dash_core_components as dcc
    import dash_html_components as html
    from dash.dependencies import Input, Output

    external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    class Assist(BaseAssistant):
        def __init__(self):
            super().__init__()

        def layout(self):
            return html.Div(
                [
                    dcc.Store(id="assistant_store", data="Toto"),
                    html.H6(
                        "Change the value in the text box to see callbacks in action!"
                    ),
                    html.Div(
                        [
                            "Input: ",
                            dcc.Input(
                                id="my-input", value="initial value", type="text"
                            ),
                        ]
                    ),
                    html.Br(),
                    html.Div(id="my-output"),
                ]
            )

        def register_callbacks(self, app):
            @app.callback(
                Output(component_id="my-output", component_property="children"),
                Input(component_id="my-input", component_property="value"),
            )
            def update_output_div(input_value):
                return "Output: {}".format(input_value)

        def store_to_graph(self, store_data):
            return store_data

    assistant = Assist()
    layout = html.Div(id="my-output-")
    assistant.register_layout(layout_to_ckeck_against=layout)
    assistant.register_callbacks(app)

    app.run_server()
