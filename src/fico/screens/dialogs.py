from typing import Literal

from textual import on
from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class ConfirmDialog(ModalScreen[bool]):
    CSS = """
    ConfirmDialog {
        align: center middle;
    }
    #dialog {
        grid-size: 2 3;
        grid-rows: 1fr 2fr 3;
        padding: 0 1;
        width: 60;
        height: 15;
        border: thick $background 80%;
        background: $surface;
    }
    #title {
        column-span: 2;
        height: 1fr;
        width: 1fr;
        content-align: center middle;
        background: $panel;
        color: $foreground;
        text-style: bold;
    }
    #message {
        margin-top: 1;
        column-span: 2;
        height: 1fr;
        width: 1fr;
        content-align: center top;
    }
    Button {
        width: 100%;
    }
    """

    def __init__(
        self,
        dialog_title: str,
        dialog_message: str,
        btn_label: str = "OK",
        btn_variant: Literal["default", "primary", "success", "warning", "error"] = "default",
    ):
        super().__init__()
        self.dialog_title = dialog_title
        self.dialog_message = dialog_message
        self.btn_label = btn_label
        self.btn_variant = btn_variant

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(self.dialog_title, id="title"),
            Label(self.dialog_message, id="message"),
            Button(self.btn_label, variant=self.btn_variant, id="confirm"),
            Button("Cancel", id="cancel"),
            id="dialog",
        )

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)
