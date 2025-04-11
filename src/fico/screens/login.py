from textual import on
from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select


class LoginDialog(ModalScreen[dict[str, str] | None]):
    CSS = """
    LoginDialog {
        align: center middle;
    }

    #dialog {
        grid-size: 2 5;
        grid-gutter: 1 2;
        grid-rows: 1fr 1fr 1fr 1fr 3;
        padding: 0 1;
        width: 60;
        height: 20;
        border: thick $background 80%;
        background: $surface;
    }

    #title {
        column-span: 2;
        height: 1fr;
        width: 1fr;
        content-align: center middle;
    }

    #url, #email, #password {
        column-span: 2;
    }

    Button {
        width: 100%;
    }
    """

    def __init__(self):
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("FinOps For Cloud Login", id="title"),
            Select(
                options=[
                    (
                        "https://cloudspend.velasuci.com/ops/v1",
                        "https://cloudspend.velasuci.com/ops/v1",
                    ),
                    ("https://api.finops.s1.today/ops/v1", "https://api.finops.s1.today/ops/v1"),
                    ("https://api.finops.s1.show/ops/v1", "https://api.finops.s1.show/ops/v1"),
                    ("https://api.finops.s1.live/ops/v1", "https://api.finops.s1.live/ops/v1"),
                    (
                        "https://api.finops.softwareone.com/ops/v1",
                        "https://api.finops.softwareone.com/ops/v1",
                    ),
                ],
                id="url",
                value="https://api.finops.softwareone.com/ops/v1",
            ),
            Input(placeholder="Email", id="email"),
            Input(placeholder="Password", id="password", password=True),
            Button("Login", variant="primary", id="login"),
            Button("Cancel", id="cancel"),
            id="dialog",
        )

    @on(Input.Submitted)
    def on_submit(self, event: Input.Submitted) -> None:
        event.stop()
        if event.input.id == "email":
            self.query_one("#password", Input).focus()
        elif event.input.id == "password":
            self.query_one("#login", Button).press()

    @on(Button.Pressed, "#login")
    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        url = self.query_one("#url", Select).value
        email = self.query_one("#email", Input).value
        password = self.query_one("#password", Input).value
        self.dismiss({"url": url, "email": email, "password": password})  # type: ignore

    @on(Button.Pressed, "#cancel")
    def on_cancel(self, event: Button.Pressed) -> None:
        event.stop()
        self.dismiss(None)  # type: ignore
