import json
from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Grid, Right
from textual.keys import Keys
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Label, Markdown, TabbedContent, TabPane


class Details(ModalScreen[None]):
    CSS = """
    Details {
        align: center middle;
        overflow-y: hidden;
    }
    Details > Grid {
        width: 80%;
        height: 35;
        grid-size: 1 3;
        grid-rows: 3 25 3;
        grid-gutter: 1;
        border: thick $background 80%;
        background: $surface;
        padding-left: 1;
        padding-right: 1;
    }
    Details > Grid > Label {
        height: 3;
        width: 1fr;
        content-align: center middle;
        background: $panel;
        color: $foreground;
    }
    """

    BINDINGS = [
        (Keys.Escape, "dismiss", "Close"),
    ]

    def __init__(
        self,
        dialog_title: str,
        object: dict[str, Any],
        panes: list[TabPane] | None = None,
    ):
        super().__init__()
        self.dialog_title = dialog_title
        self.object = object
        self.panes = panes or []

    def compose(self) -> ComposeResult:
        with Grid():
            yield Label(self.dialog_title)
            with TabbedContent():
                if self.panes:
                    yield from self.panes
                with TabPane("JSON"):
                    yield Markdown(f"```json\n{json.dumps(self.object, indent=2)}\n```")
            with Right():
                yield Button("Close", id="close")
        yield Footer()

    def action_dismiss(self):
        self.dismiss()

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        self.dismiss()
