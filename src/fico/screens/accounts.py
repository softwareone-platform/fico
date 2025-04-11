from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Grid
from textual.keys import Keys
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Label, OptionList
from textual.widgets.option_list import Option


class AccountSwitcher(ModalScreen[dict[str, Any] | None]):
    CSS = """
    AccountSwitcher {
        align: center middle;
    }
    AccountSwitcher > Grid {
        grid-size: 2 3;
        grid-rows: 3 1fr 3;
        grid-gutter: 1;
        padding: 1;
        width: 50;
        height: 25;
        border: thick $background 80%;
        background: $surface;
    }
    AccountSwitcher > Grid > OptionList {
        column-span: 2;
        width: 60;
        height: 23;
    }
    AccountSwitcher > Grid > Label {
        column-span: 2;
        height: 1fr;
        width: 1fr;
        content-align: center middle;
        background: $panel;
        color: $foreground;
        text-style: bold;
    }
    AccountSwitcher > Grid > Button {
        width: 100%;
    }
    """

    BINDINGS = [
        (Keys.Escape, "dismiss", "Close"),
    ]

    def __init__(
        self,
        accounts: list[dict[str, Any]],
    ):
        super().__init__()
        self.accounts = accounts

    def compose(self) -> ComposeResult:
        with Grid():
            yield Label("Choose the Account you want to use")
            options = [
                Option(
                    f"[bold $accent]{account["name"]}[/]\n{account['id']} - {account['type']}",
                    id=account["id"])
                for account in self.accounts
                if account["account_user"]["status"] == "active"
            ]
            yield OptionList(*options)
            yield Button("Choose", variant="primary", id="choose")
            yield Button("Cancel", id="cancel")
        yield Footer()

    @on(OptionList.OptionSelected)
    def option_selected(self, event: OptionList.OptionSelected):
        event.stop()
        self.option_choosed()


    def option_choosed(self):
        option_list = self.query_one(OptionList)
        option = option_list.get_option_at_index(option_list.highlighted)
        account = next(filter(lambda x: x["id"] == option.id, self.accounts))
        self.dismiss(account)


    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "choose":
            self.option_choosed()
        else:
            self.action_dismiss()

    def action_dismiss(self):
        self.dismiss(None)
