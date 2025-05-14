from textual import on
from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select


class InvitationDialog(ModalScreen[dict[str, str] | None]):
    CSS = """
    InvitationDialog {
        align: center middle;
    }

    #dialog {
        grid-size: 2 6;
        grid-gutter: 1 2;
        grid-rows: 1fr 1fr 1fr 1fr 1fr 3;
        padding: 0 1;
        width: 60;
        height: 24;
        border: thick $background 80%;
        background: $surface;
    }

    #title {
        column-span: 2;
        height: 1fr;
        width: 1fr;
        content-align: center middle;
    }

    #url, #user, #token, #password {
        column-span: 2;
    }

    Button {
        width: 100%;
    }
    """

    def __init__(self, invitation_data: dict[str, str] | None = None):
        super().__init__()
        self.invitation_data = invitation_data or {}

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("FinOps For Cloud Accept Invitation", id="title"),
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
                value=self.invitation_data.get("url", "https://api.finops.softwareone.com/ops/v1"),
            ),
            Input(placeholder="User", id="user", value=self.invitation_data.get("user")),
            Input(placeholder="Invitation token", id="token", value=self.invitation_data.get("token")),
            Input(placeholder="Password", id="password", value=self.invitation_data.get("password"), password=True),
            Button("Accept", variant="primary", id="accept"),
            Button("Cancel", id="cancel"),
            id="dialog",
        )

    @on(Input.Submitted)
    def on_submit(self, event: Input.Submitted) -> None:
        event.stop()
        if event.input.id == "user":
            self.query_one("#token", Input).focus()
        elif event.input.id == "token":
            self.query_one("#password", Input).focus()
        elif event.input.id == "password":
            self.query_one("#accept", Button).press()

    @on(Button.Pressed, "#accept")
    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        url = self.query_one("#url", Select).value
        user = self.query_one("#user", Input).value
        token = self.query_one("#token", Input).value
        password = self.query_one("#password", Input).value

        if not (url and user and token and password):
            self.app.notify(
                severity="warning",
                title="Invitation validation error",
                message="Please fill all inputs and try again.",
            )
            return

        self.dismiss({"url": url, "user": user, "token": token, "password": password})  # type: ignore

    @on(Button.Pressed, "#cancel")
    def on_cancel(self, event: Button.Pressed) -> None:
        event.stop()
        self.dismiss(None)  # type: ignore
