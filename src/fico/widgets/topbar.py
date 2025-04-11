from textual import on
from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Button, Label

from fico.widgets.filterbar import FilterBar


class TopBar(Horizontal):

    DEFAULT_CSS = """
    TopBar {
        height: 5;
        content-align: center middle;
    }
    TopBar > Label {
        height: 5;
        width: 15;
        content-align: left middle;
        padding-left: 1;
        color: $primary;
        text-style: bold;
    }
    #add {
        margin-top: 1;
        margin-right: 1;
    }
    #actions {
        margin-top: 1;
        min-width: 5;
    }
    """

    class AddPressed(Message):
         pass

    class ActionsPressed(Message):
         pass


    def __init__(
        self,
        title: str,
        support_rql: bool = False,
        add_disabled: bool = False,
        rql_help: str | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        markup: bool = True,
    ):
           super().__init__(name=name, id=id, classes=classes, disabled=disabled, markup=markup)
           self.title = title
           self.add_disabled = add_disabled
           self.support_rql = support_rql
           self.rql_help = rql_help

    def compose(self):
        yield Label(self.title, id="title")
        yield FilterBar(help_text=self.rql_help, disabled=not self.support_rql)
        yield Button("Add", variant="primary", id="add", disabled=self.add_disabled)
        yield Button("\u2630", id="actions", disabled=True)


    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed):
        event.stop()
        if event.button.id == "add":
              self.post_message(self.AddPressed())
        if event.button.id == "actions":
              self.post_message(self.ActionsPressed())

    def enable_actions(self):
        self.query_one("#actions").disabled = False

    def disable_actions(self):
        self.query_one("#actions").disabled = True

    def reset(self):
         self.query_one(FilterBar).reset()
