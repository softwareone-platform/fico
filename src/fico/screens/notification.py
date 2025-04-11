from typing import Literal

from textual import on
from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

SeverityType = Literal["info", "success", "warning", "error"]


class Notification(ModalScreen):
    CSS = """
    Notification {
        align: center middle;
    }
    .info {
        border-top: outer $primary;
    }
    .success {
        border-top: outer $success;
    }
    .warning {
        border-top: outer $warning;
    }
    .error {
        border-top: outer $error;
    }
    #content {
        grid-size: 1 3;
        grid-rows: 3 2fr 3;
        grid-gutter: 1;
        padding: 0 1 1 1;
        width: 78;
        height: 20;
        background: $surface;
    }

    #title {
        height: 3;
        width: 1fr;
        content-align: center middle;
        background: $panel;
        color: $foreground;
        text-style: bold;
    }
    #message {
        margin-top: 1;
        height: 1fr;
        width: 1fr;
        content-align: center top;
    }
    Button {
        width: 100%;
    }
    """
    ICONS = {
        "info": "📓",
        "success": "✅",
        "warning": "🟡",
        "error": "💥",
    }

    def __init__(
        self,
        title_text: str,
        message_text: str,
        severity: SeverityType = "info",
        timeout: int = 3,
    ):
        super().__init__()
        self.title_text = title_text
        self.message_text = message_text
        self.severity = severity
        self.timeout = timeout

    def compose(self) -> ComposeResult:
        row3 = Static() if self.timeout > 0 else Button("Dismiss", id="dismiss")
        yield Grid(
            Label(f"{self.ICONS[self.severity]}  {self.title_text}", id="title"),
            Label(self.message_text, id="message"),
            row3,
            id="content",
        )

    def on_mount(self) -> None:
        self.query_one(Grid).add_class(self.severity)
        if self.timeout > 0:
            self.dismiss_timer = self.set_timer(self.timeout, self.close)

    @on(Button.Pressed)
    def on_dismiss_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        self.dismiss()

    async def close(self) -> None:
        self.dismiss()
