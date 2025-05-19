from datetime import datetime
from functools import partial
from typing import Any

from textual import log
from textual.validation import Length
from textual.reactive import Reactive, reactive
from textual.widgets import Input, Label, Select, TabPane

from fico.screens.actions import Action
from fico.screens.invitation import InvitationDialog
from fico.utils import format_at, format_by, format_object_label, format_status
from fico.widgets.datagrid import DataGrid, DataGridColumn
from fico.widgets.form import Form, FormItem
from fico.widgets.view import View


class Users(View):
    OBJECT_NAME = "User"
    OBJECT_NAME_PLURAL = "Users"
    COLLECTION_NAME = "users"

    current_user: Reactive[dict[str, Any] | None] = reactive(None, bindings=True)

    async def prepare_add_form(self) -> None:
        if self.current_account and self.current_account["type"] == "operations":
            self.query_one("#item-account", FormItem).remove_class("hidden")
            rql = "eq(status,active)&order_by(name)"
            accounts = await self.api_client.get_all_objects("accounts", rql=rql)
            self.query_one("#account", Select).set_options(
                [(f"{format_object_label(account)}", account["id"]) for account in accounts]
            )
        else:
            self.query_one("#item-account", FormItem).add_class("hidden")
        self.query_one(Form).form_title = "Invite User"

    def get_available_actions(self, object: dict[str, Any]) -> dict[str, Action]:
        actions = super().get_available_actions(object)
        actions["edit"] = Action(id="edit", label="Edit", disabled=True)
        actions["enable"] = Action(
            id="enable",
            label="Enable",
            disabled=object["status"] != "disabled",
            handler=self.perform_enable,
        )
        actions["disable"] = Action(
            id="disable",
            label="Disable",
            disabled=object["status"] != "active",
            handler=self.perform_disable,
        )
        return actions

    async def perform_disable(self, user: dict[str, Any]):
        try:
            await self.api_client.execute_object_action(
                self.get_collection_name(), "POST", user["id"], "disable"
            )
            self.query_one(DataGrid).reload()
            self.notify(
                severity="information",
                title="Success",
                message=f"{self.OBJECT_NAME} {format_object_label(user)} has been disabled.",
            )
        except Exception as e:
            self.notify(
                severity="error",
                title="Error",
                message=f"Cannot disable {self.OBJECT_NAME} {format_object_label(user)}: {e}.",
            )

    async def perform_enable(self, user: dict[str, Any]):
        try:
            await self.api_client.execute_object_action(
                self.get_collection_name(), "POST", user["id"], "enable"
            )
            self.query_one(DataGrid).reload()
            self.notify(
                severity="information",
                title="Success",
                message=f"{self.OBJECT_NAME} {format_object_label(user)} has been enabled.",
            )
        except Exception as e:
            self.notify(
                severity="error",
                title="Error",
                message=f"Cannot enable {self.OBJECT_NAME} {format_object_label(user)}: {e}.",
            )

    def prepare_create_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        account_id = data.pop("account")
        if self.current_account and self.current_account["type"] == "operations":
            data["account"] = {"id": account_id}
        log(data)
        return data


    def notify_created_success(self, object: dict[str, Any]) -> None:
        self.show_notification(
            severity="success",
            title="Success",
            message=(
                f"{self.OBJECT_NAME} [bold]{format_object_label(object)}[/] has been "
                f"invited to [bold]{format_object_label(object['account_user']['account'])}[/].\n\n"
                f"Invitation token:\n[bold $accent]{object['account_user']['invitation_token']}[/]."
            ),
            timeout=0,
        )

    def get_user_account_actions(self, object: dict[str, Any]) -> dict[str, Action]:
        actions = {
            "remove": Action(
                id="remove",
                label="Remove",
                handler=partial(self.remove_user_from_account, object["id"]),
            )
        }
        if object["account_user"]["status"] == "invited":
            actions["accept_invitation"] = Action(
                id="accept_invitation",
                label="Accept invitation",
                handler=self.accept_pending_invitation,
                disabled=not self.check_user_for_accept(object["account_user"]),
            )

        return actions

    async def remove_user_from_account(self, user_id: str, account: dict[str, Any]) -> None:
        pass

    async def accept_pending_invitation(self, account: dict[str, Any]) -> None:
        self.app.push_screen(InvitationDialog(new_user=False), self.accept_invitation)

    def check_user_for_accept(self, user: dict[str, Any]) -> bool:
        if self.current_user and self.current_user["id"] == user["user"]["id"]:
            return True
        return False

    async def accept_invitation(self, invitation_data: dict[str, str] | None) -> None:
        if not invitation_data:
            return
        try:
            await self.api_client.execute_object_action(
                collection=self.get_collection_name(),
                method="POST",
                id=self.current_user["id"],
                action="accept-invitation",
                payload={"invitation_token": invitation_data["token"]},
            )
            self.query_one(DataGrid).reload()
            self.notify(
                title="Success",
                message="Invitation successfully accepted",
            )
            self.app.pop_screen()
        except Exception as e:
            self.notify(
                severity="error",
                title="Error",
                message=f"Error accepting invitation: {e}",
            )
            return

    def get_details_extra_panes(self, object: dict[str, Any]) -> list[TabPane]:
        if self.current_account and self.current_account["type"] == "affiliate":
            return []
        accounts_list = DataGrid(
            columns=[
                DataGridColumn(title="ID", field="id"),
                DataGridColumn(title="Name", field="name"),
                DataGridColumn(title="Type", field="type"),
                DataGridColumn(
                    title="Status", field="account_user.status", formatter=format_status
                ),
                DataGridColumn(
                    title="Invited",
                    field="account_user.created_at",
                    formatter=lambda d: datetime.fromisoformat(d).strftime(
                        "%d/%m/%Y %H:%M:%S"
                    ),
                ),
                DataGridColumn(
                    title="Joined",
                    field="account_user.joined_at",
                    formatter=lambda d: datetime.fromisoformat(d).strftime(
                        "%d/%m/%Y %H:%M:%S"
                    ),
                ),
            ],
            datasource=partial(self.api_client.get_user_accounts, object["id"]),
            actions=self.get_user_account_actions,
            id="user_accounts"
        )
        accounts_list.reload()
        return [
            TabPane("Accounts", accounts_list)
        ]

    def get_columns(self) -> list[DataGridColumn]:
        return [
            DataGridColumn(title="ID", field="id"),
            DataGridColumn(title="Name", field="name"),
            DataGridColumn(title="Email", field="email"),
            DataGridColumn(title="Status", field="status", formatter=format_status),
            DataGridColumn(title="Created at", field="events.created", formatter=format_at),
            DataGridColumn(title="Created by", field="events.created", formatter=format_by),
            DataGridColumn(title="Updated at", field="events.updated", formatter=format_at),
            DataGridColumn(title="Updated by", field="events.updated", formatter=format_by),
        ]

    def get_form_items(self) -> list[FormItem]:
        return [
            FormItem(
                Label("Name"),
                Input(
                    id="name",
                    name="Name",
                    validate_on=["blur"],
                    validators=[Length(minimum=1)],
                ),
            ),
            FormItem(
                Label("Email"),
                Input(
                    id="email",
                    name="Email",
                    validate_on=["blur"],
                    validators=[Length(minimum=1)],
                ),
            ),
            FormItem(
                Label("Account"),
                Select([], id="account", name="Account"),
                id="item-account",
            ),
        ]
