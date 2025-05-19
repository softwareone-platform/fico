from textual import on
from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select

from fico.constants import APIS, DEFAULT_API


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
    
     /* Full form for a new user */
    .new_user {
        grid-size: 2 6;
        grid-rows: 1fr 1fr 1fr 1fr 1fr 3;
        height: 24;
    }

    /* Just token to accept invitation */
    .existing_user {
        grid-size: 2 3;
        grid-rows: 1fr 1fr 3;
        height: 12;
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

    def __init__(self, invitation_data: dict[str, str] | None = None, new_user: bool = True) -> None:
        super().__init__()
        invitation_data = invitation_data or {}
        self.new_user = new_user

        if self.new_user:
            self.rows = [
                Select(
                    options=APIS,
                    id="url",
                    value=invitation_data.get("url", DEFAULT_API),
                ),
                Input(placeholder="User", id="user", value=invitation_data.get("user")),
                Input(placeholder="Invitation token", id="token", value=invitation_data.get("token")),
                Input(placeholder="Password", id="password", value=invitation_data.get("password"), password=True),
            ]
        else:
            self.rows = [
                Input(placeholder="Invitation token", id="token", value=invitation_data.get("token")),
            ]

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("FinOps For Cloud Accept Invitation", id="title"),
            *self.rows,
            Button("Accept", variant="primary", id="accept"),
            Button("Cancel", id="cancel"),
            id="dialog",
            classes="new_user" if self.new_user else "existing_user",
        )

    @on(Input.Submitted)
    def on_submit(self, event: Input.Submitted) -> None:
        event.stop()
        if event.input.id == "user":
            self.query_one("#token", Input).focus()
        elif event.input.id == "token":
            if self.new_user:
                self.query_one("#password", Input).focus()
            else:
                self.query_one("#accept", Button).press()
        elif event.input.id == "password":
            self.query_one("#accept", Button).press()

    @on(Button.Pressed, "#accept")
    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()

        data = {"token": self.query_one("#token", Input).value}
        if self.new_user:
             for field, selector in [("url", Select), ("user", Input), ("password", Input)]:
                 data[field] = self.query_one(f"#{field}", selector).value

        if not all(data.values()):
            self.app.notify(
                severity="warning",
                title="Invitation validation error",
                message="Please fill all inputs and try again.",
            )
            return

        self.dismiss(data)

    @on(Button.Pressed, "#cancel")
    def on_cancel(self, event: Button.Pressed) -> None:
        event.stop()
        self.dismiss(None)
