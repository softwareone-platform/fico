from typing import Any

from textual import on
from textual.binding import Binding
from textual.containers import Horizontal
from textual.keys import Keys
from textual.reactive import Reactive, reactive
from textual.screen import Screen
from textual.widgets import ContentSwitcher, Footer, Header

from fico.api import FFCOpsClient
from fico.screens.accounts import AccountSwitcher
from fico.utils import format_object_label, handle_error_notification
from fico.views.accounts import Accounts
from fico.views.charges import Charges
from fico.views.entitlements import Entitlements
from fico.views.organizations import Organizations
from fico.views.systems import Systems
from fico.views.users import Users
from fico.widgets.navbar import NavBar


class MainScreen(Screen):
    TITLE = "SoftwareOne"
    SUB_TITLE = "FinOps For Cloud Admin Console"
    CSS = """
    NavBar.-hidden {
        display: none;
    }
    """
    BINDINGS = [
        Binding("m", "toggle_menu()", "Toggle Menu"),
        Binding(Keys.ControlA, "show_accounts()", "Affiliates", show=False),
        Binding(Keys.ControlO, "show_organizations()", "Organizations", show=False),
        Binding(Keys.ControlE, "show_entitlements()", "Entitlements", show=False),
        Binding(Keys.ControlG, "show_charges()", "Charges", show=False),
        Binding(Keys.ControlU, "show_users()", "Users", show=False),
        Binding(Keys.ControlT, "show_systems()", "Tokens", show=False),
        Binding("s", "switch_account()", "Switch account"),
    ]

    current_user: Reactive[dict[str, Any] | None] = reactive(None)
    current_account: Reactive[dict[str, Any] | None] = reactive(None, bindings=True)

    def __init__(
        self,
        api_client: FFCOpsClient,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ):
        super().__init__(name=name, id=id, classes=classes)
        self.api_client = api_client
        self.set_reactive(
            MainScreen.current_user,
            self.api_client.get_current_user(),
        )
        self.set_reactive(MainScreen.current_account, self.api_client.get_current_account())
        self.sub_title = (
            f"{self.__class__.SUB_TITLE} - "
            f"{format_object_label(self.current_account)} - {self.api_client.get_url()}"
        )

    def compose(self):
        yield Header()
        with Horizontal(id="main-screen"):
            yield NavBar(id="navbar", classes="-hidden").data_bind(
                current_account=MainScreen.current_account
            )
            with ContentSwitcher(id="switcher", initial="accounts"):
                yield Accounts(
                    self.api_client,
                    id="accounts",
                    disabled=self.current_account["type"] != "operations",
                )
                yield Organizations(
                    self.api_client,
                    id="organizations",
                    disabled=self.current_account["type"] != "operations",
                )
                yield Entitlements(self.api_client, id="entitlements")
                yield Charges(self.api_client, id="charges")
                yield Users(self.api_client, id="users").data_bind(
                    current_user=MainScreen.current_user,
                )
                yield Systems(self.api_client, id="systems")
        yield Footer()

    async def on_mount(self):
        self.setup_for_account()

    @on(NavBar.Navigate)
    def on_switch_view(self, event: NavBar.Navigate) -> None:
        self.query_one(ContentSwitcher).current = event.view

    def action_toggle_menu(self):
        self.query_one(NavBar).toggle_class("-hidden")

    async def action_switch_account(self):
        accounts = await self.api_client.get_current_user_accounts()
        self.app.push_screen(
            AccountSwitcher(accounts),
            self.switch_account,
        )

    @handle_error_notification(f"Error switching account")
    async def switch_account(self, account):
        if not account:
            return
        await self.api_client.switch_account(account["id"])
        self.current_account = account
        self.setup_for_account()

    def setup_for_account(self):
        self.sub_title = (
            f"{self.__class__.SUB_TITLE} - {format_object_label(self.current_account)} - "
            f"{self.api_client.get_url()}"
        )
        self.query_one(Accounts).disabled = self.current_account["type"] != "operations"
        self.query_one(Organizations).disabled = self.current_account["type"] != "operations"
        if self.current_account["type"] == "affiliate":
            self.query_one(ContentSwitcher).current = "entitlements"
            for view in (Entitlements, Users, Systems):
                self.query_one(view).current_account = self.current_account
                self.query_one(view).reset()
        else:
            self.query_one(ContentSwitcher).current = "accounts"
            for view in (Accounts, Organizations, Entitlements, Users, Systems):
                self.query_one(view).current_account = self.current_account
                self.query_one(view).reset()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if (
            action == "show_accounts"
            and self.current_account
            and self.current_account["type"] == "affiliate"
        ):
            return False
        if (
            action == "show_organizations"
            and self.current_account
            and self.current_account["type"] == "affiliate"
        ):
            return False
        return True

    def action_show_accounts(self):
        self.query_one(ContentSwitcher).current = "accounts"

    def action_show_organizations(self):
        self.query_one(ContentSwitcher).current = "organizations"

    def action_show_entitlements(self):
        self.query_one(ContentSwitcher).current = "entitlements"

    def action_show_users(self):
        self.query_one(ContentSwitcher).current = "users"

    def action_show_systems(self):
        self.query_one(ContentSwitcher).current = "systems"

    def action_show_charges(self):
        self.query_one(ContentSwitcher).current = "charges"
