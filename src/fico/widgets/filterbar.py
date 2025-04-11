from dataclasses import dataclass

from textual import on
from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Button, Label

from fico.screens.rql import RQLEditor


class FilterBar(Horizontal):
    DEFAULT_CSS = """
    FilterBar {
        height: 5;
        border: round $primary;
        margin-left: 1;
        margin-right: 1;
    }
    FilterBar > Label {
        width: 1fr;
        height: 3;
        content-align: left middle;
        padding-left: 1;
        color: $primary;
        text-style: bold;
    }
    FilterBar > Button {
        margin-right: 1;
        margin-left: 1;
        min-width: 6;
    }
    """

    @dataclass
    class FilterChanged(Message):
        rql_query: str | None = None

    def __init__(
        self,
        help_text: str | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        markup: bool = True,
    ):
        super().__init__(name=name, id=id, classes=classes, disabled=disabled, markup=markup)
        self.rql_query: str = ""
        self.help_text = help_text

    def compose(self):
        yield Label(self.strip_rql_query())
        yield Button("\U0001f50d", disabled=self.disabled)

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed):
        event.stop()
        self.app.push_screen(
            RQLEditor(self.rql_query, help_text=self.help_text), self.on_rql_editor_dismiss  # type: ignore
        )

    def on_rql_editor_dismiss(self, rql_query: str):
        self.rql_query = rql_query
        self.query_one(Label).update(self.strip_rql_query())
        self.post_message(self.FilterChanged(rql_query=self.strip_rql_query()))

    def reset(self):
        self.rql_query = ""
        self.query_one(Label).update(self.strip_rql_query())

    def strip_rql_query(self):
        lines = self.rql_query.split("\n")
        return "".join([line.strip() for line in lines])
