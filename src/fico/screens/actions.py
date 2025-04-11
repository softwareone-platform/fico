from collections.abc import Callable
from dataclasses import dataclass

from textual import on
from textual.app import ComposeResult
from textual.containers import Grid
from textual.keys import Keys
from textual.screen import ModalScreen
from textual.widgets import Footer, Label, OptionList
from textual.widgets.option_list import Option


@dataclass
class Action:
    id: str
    label: str
    disabled: bool = False
    handler: Callable | None = None


class Actions(ModalScreen[Action | None]):
    CSS = """
    Actions {
        align: center middle;
    }
    Actions > Grid {
        grid-size: 1 2;
        grid-rows: 3 1fr;
        grid-gutter: 1;
        padding: 1;
        width: 30;
        height: 17;
        border: thick $background 80%;
        background: $surface;
    }
    Actions > Grid > OptionList {
        width: 30;
        height: 15;
    }
    Actions > Grid > Label {
        height: 1fr;
        width: 1fr;
        content-align: center middle;
        background: $panel;
        color: $foreground;
        text-style: bold;
    }
    """

    BINDINGS = [
        (Keys.Escape, "dismiss", "Close"),
    ]

    def __init__(
        self,
        actions: list[Action],
    ):
        super().__init__()
        self.actions = actions

    def compose(self) -> ComposeResult:
        with Grid():
            yield Label("Actions")
            options = [
                Option(action.label, id=action.id, disabled=action.disabled)
                for action in self.actions
            ]
            yield OptionList(*options)
        yield Footer()

    @on(OptionList.OptionSelected)
    def option_selected(self, event: OptionList.OptionSelected):
        event.stop()
        action = next(filter(lambda x: x.id == event.option_id, self.actions))
        self.dismiss(action)

    def action_dismiss(self):
        self.dismiss(None)
