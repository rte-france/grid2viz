from abc import abstractmethod, ABC
import inspect

from dash.dependencies import Output, Input, State


class BaseAssistant(ABC):
    def __init__(self):
        self._layout = None
        pass

    @abstractmethod
    def simulate(self):
        pass

    @abstractmethod
    def layout(self):
        pass

    def check_layout(self):
        layout = self.layout()
        try:
            if (
                layout.children[0]._type != "Store"
                or layout.children[0].id != "assistant_store"
            ):
                raise Exception(
                    f"The first child of the Assistant layout should be a Store with id assistant_store, found {layout.children[0]}"
                )
        except:
            raise Exception(
                f"The first child of the Assistant layout should be a Store with id assistant_store, found {layout}"
            )

    @abstractmethod
    def register_callbacks(self, app):
        pass

    def decorate_callbacks(self, app):
        self.register_callbacks(app)
        # from dash import Dash
        #
        # app_inner = Dash()
        # self.register_callbacks(app_inner)
        # inital_callback_map = app_inner.callback_map
        # for callback_name in inital_callback_map:
        #     callback = app.callback_map.pop(callback_name)
        #     outputs = self.parse_callback_name(callback_name, self.__class__.__name__)
        #     inputs = self.parse_inputs(callback["inputs"], self.__class__.__name__)
        #     callback["state"] = self.decorate_callback_state(
        #         callback["state"], self.__class__.__name__
        #     )
        # args = inspect.getfullargspec(callback["callback"])[0]
        #
        # @app.callback(outputs, inputs)
        # def assist(*args):
        #     return callback["callback"](*args)

        return

    @staticmethod
    def parse_inputs(inputs, prefix):
        new_inputs = []
        for input_dict in inputs:
            component_id, component_property = input_dict["id"], input_dict["property"]
            component_id = "-".join([prefix, component_id])
            new_inputs = Input(
                component_id=component_id, component_property=component_property
            )
        return new_inputs

    @staticmethod
    def decorate_callback_state(state, prefix):
        for state_dict in state:
            state_dict["id"] = "-".join([prefix, state_dict["id"]])
        return state

    @staticmethod
    def parse_callback_name(callback_name, prefix):
        if not callback_name.startswith(".."):

            new_callback_name = "-".join([prefix, callback_name])
            component_id, component_property = new_callback_name.split(".")
            output = Output(
                component_id=component_id, component_property=component_property
            )
        return output

    def decorate_layout(self):
        initial_layout = self.layout()
        self._layout = self.prefix_layout_element_id(
            initial_layout, self.__class__.__name__
        )
        return

    def decorated_layout(self):
        self.decorate_layout()
        self.check_layout()
        # return self._layout
        return self.layout()

    def prefix_layout_element_id():
        def prefix_layout_element_id(layout, prefix):
            if hasattr(layout, "id"):
                layout.id = "-".join([prefix, layout.id])
            if hasattr(layout, "children") and isinstance(layout.children, list):
                children = [
                    prefix_layout_element_id(child, prefix) for child in layout.children
                ]
                layout.children = children
            return layout

        return prefix_layout_element_id

    prefix_layout_element_id = staticmethod(prefix_layout_element_id())


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

        def simulate(self):
            pass

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

    assistant = Assist()

    app.layout = assistant.decorated_layout()
    assistant.decorate_callbacks(app)

    app.run_server()
