from dataclasses import dataclass
from typing import Any

from textual import on
from textual.containers import Container
from textual.message import Message
from textual.reactive import Reactive, reactive
from textual.widgets import Label, ListItem, ListView, Rule


class NavBar(Container):
    DEFAULT_CSS = """
    NavBar {
        border: round $primary;
        width: 28;
        height: 100%;
    }
    NavBar > ListView {
        width: 100%;
        height: auto;
        margin: 2 2;
    }
    .menu-item {
        width: 1fr;
        padding: 1 2;
        content-align: right middle;
    }

    .group-header {
        width: 1fr;
        text-style: bold;
        color: white;
        background: $accent;
        padding: 1 2;
        content-align: left middle;
    }
    .hidden {
        display: none;
    }
    """
    @dataclass
    class Navigate(Message):
        view: str | None


    current_account: Reactive[dict[str, Any] | None] = reactive(None)


    def __init__(self, name=None, id=None, classes=None, disabled=False, markup=True):
        super().__init__(name=name, id=id, classes=classes, disabled=disabled, markup=markup)

    def compose(self):
        with ListView():
            yield ListItem(
                Label("Administration", classes="group-header"), disabled=True, id="admin"
            )
            yield ListItem(Label("Affiliates", classes="menu-item"), id="accounts")
            yield ListItem(Label("Organizations", classes="menu-item"), id="organizations")
            yield ListItem(Rule(line_style="heavy"), disabled=True, id="rule")
            yield ListItem(Label("Billing", classes="group-header"), disabled=True)
            yield ListItem(Label("Entitlements", classes="menu-item"), id="entitlements")
            yield ListItem(Label("Charges", classes="menu-item"), id="charges")
            yield ListItem(Rule(line_style="heavy"), disabled=True)
            yield ListItem(Label("Settings", classes="group-header"), disabled=True)
            yield ListItem(Label("Users", classes="menu-item"), id="users")
            yield ListItem(Label("Tokens", classes="menu-item"), id="systems")

    @on(ListView.Selected)
    def on_menu(self, event: ListView.Selected) -> None:
        self.post_message(self.Navigate(event.item.id))

    def watch_current_account(self, new_account: dict[str, Any] | None) -> None:
        if new_account and new_account["type"] == "operations":
            self.query_one("#admin").remove_class("hidden")
            self.query_one("#accounts").remove_class("hidden")
            self.query_one("#organizations").remove_class("hidden")
            self.query_one("#rule").remove_class("hidden")
        else:
            self.query_one("#admin").add_class("hidden")
            self.query_one("#accounts").add_class("hidden")
            self.query_one("#organizations").add_class("hidden")
            self.query_one("#rule").add_class("hidden")
