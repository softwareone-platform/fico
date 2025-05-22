from typing import Any

from textual.validation import Length
from textual.widgets import Input, Label, Select, TextArea

from fico.screens.actions import Action
from fico.utils import (
    format_at,
    format_by,
    format_object_label,
    format_status,
    handle_error_notification,
)
from fico.widgets.datagrid import DataGrid, DataGridColumn
from fico.widgets.form import FormItem
from fico.widgets.view import View


class Systems(View):
    OBJECT_NAME = "Token"
    OBJECT_NAME_PLURAL = "Tokens"
    COLLECTION_NAME = "systems"

    async def prepare_add_form(self) -> None:
        if self.is_operations_account:
            self.query_one("#item-owner", FormItem).remove_class("hidden")
            rql = "eq(status,active)&order_by(name)"
            accounts = await self.api_client.get_all_objects("accounts", rql=rql)
            self.query_one("#owner", Select).set_options(
                [(f"{format_object_label(account)}", account["id"]) for account in accounts]
            )
        else:
            self.query_one("#item-owner", FormItem).add_class("hidden")

    def get_available_actions(self, object: dict[str, Any]) -> dict[str, Action]:
        actions = super().get_available_actions(object)
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

    @handle_error_notification(f"Error disabling {OBJECT_NAME}")
    async def perform_disable(self, system: dict[str, Any]):
        await self.api_client.execute_object_action(
            self.get_collection_name(), "POST", system["id"], "disable"
        )
        self.query_one(DataGrid).reload()
        self.notify_success(system, "disabled")


    @handle_error_notification(f"Error enabling {OBJECT_NAME}")
    async def perform_enable(self, system: dict[str, Any]):
        await self.api_client.execute_object_action(
            self.get_collection_name(), "POST", system["id"], "enable"
        )
        self.query_one(DataGrid).reload()
        self.notify_success(system, "disabled")


    def prepare_create_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        owner = data.pop("owner")
        if self.is_operations_account:
            data["owner"] = {"id": owner}
        return data

    def notify_created_success(self, object: dict[str, Any]) -> None:
        self.show_notification(
            severity="success",
            title="Success",
            message=(
                f"{self.OBJECT_NAME} created successfully: "
                f"[bold]{format_object_label(object)}[/]\n\n"
                f"JWT Secret:\n[bold $accent]{object['jwt_secret']}[/]."
            ),
            timeout=0,
        )

    def get_columns(self) -> list[DataGridColumn]:
        return [
            DataGridColumn(title="ID", field="id"),
            DataGridColumn(title="Name", field="name"),
            DataGridColumn(
                title="Account",
                field="owner",
                formatter=format_object_label,
            ),
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
                Label("External ID"),
                Input(
                    id="external_id",
                    name="External ID",
                    validate_on=["blur"],
                    validators=[Length(minimum=1)],
                ),
            ),
            FormItem(
                Label("Description"),
                TextArea(
                    id="description",
                    name="Description",
                ),
            ),
            FormItem(
                Label("Account"),
                Select([], id="owner", name="Account"),
                id="item-owner",
            ),
        ]


