from functools import partial
from typing import Any

from textual.validation import Length
from textual.widgets import Input, Label, Select, TabPane

from fico.screens.actions import Action
from fico.screens.dialogs import ConfirmDialog
from fico.screens.redeem import RedeemEntitlementDialog
from fico.utils import format_at, format_by, format_object_label, format_status, handle_error_notification
from fico.widgets.datagrid import DataGridColumn, DataGrid
from fico.widgets.form import FormItem
from fico.widgets.view import View


class Entitlements(View):

    OBJECT_NAME = "Entitlement"
    OBJECT_NAME_PLURAL = "Entitlements"
    COLLECTION_NAME = "entitlements"

    def get_form_items(self):
        return [
            FormItem(
                Label("Name"),
                Input(
                    id="name",
                    name="Name",
                    validate_on=["blur"],
                    validators=[Length(minimum=1)],
                )
            ),
            FormItem(
                Label("Affiliate Additional ID"),
                Input(
                    id="affiliate_external_id",
                    name="Affiliate Additional ID",
                    validate_on=["blur"],
                    validators=[Length(minimum=1)],
                )
            ),
            FormItem(
                Label("Datasource ID"),
                Input(
                    id="datasource_id",
                    name="Datasource ID",
                    validate_on=["blur"],
                    validators=[Length(minimum=1)],
                )
            ),
            FormItem(
                Label("Affiliate"),
                Select([], id="owner", name="Affiliate"),
                id="fi_owner",
            ),
        ]

    async def prepare_add_form(self):
        if self.is_operations_account:
            self.query_one("#fi_owner", FormItem).remove_class("-hidden")
            self.query_one("#owner", Select).disabled = False
            rql = "and(eq(type,affiliate),eq(status,active))&order_by(name)"
            accounts = await self.api_client.get_all_objects("accounts", rql=rql)
            self.query_one("#owner", Select).set_options(
                [
                    (f"{format_object_label(account)}", account["id"])
                    for account in accounts
                ]
            )
        else:
            self.query_one("fi_owner", FormItem).add_class("-hidden")
            self.query_one("#owner", Select).disabled = True

    async def prepare_edit_form(self, selected: dict[str, Any]) -> dict[str, Any] | None:
        obj = await super().prepare_edit_form(selected)
        self.query_one("#fi_owner", FormItem).add_class("-hidden")
        self.query_one("#owner", Select).disabled = True
        return obj


    def get_available_actions(self, object: dict[str, Any]) -> dict[str, Action]:
        actions = super().get_available_actions(object)
        actions["edit"].disabled = True
        actions["delete"].disabled = not self.is_operations_account
        if (
            object["status"] == "new"
            and self.is_operations_account
        ):
            actions["redeem"] = Action(
                id="redeem",
                label="Redeem",
                handler=self.redeem_entitlement,
            )
        elif object["status"] == "active":
            actions["terminate"] = Action(
                id="terminate",
                label="Terminate",
                handler=self.terminate_entitlement,
            )
        return actions

    async def redeem_entitlement(self, selected: dict[str, Any]):
        orgs = await self.api_client.get_all_objects(
            "organizations",
            rql="eq(status,active)&order_by(name)",
        )
        self.app.push_screen(
            RedeemEntitlementDialog(self.api_client, selected["id"], orgs),
            partial(self.perform_redeem_entitlement_action, selected["id"]),
        )

    async def terminate_entitlement(self, selected: dict[str, Any]):
        self.app.push_screen(
            ConfirmDialog(
                dialog_title="Confirm termination",
                dialog_message=(
                    f"Are you sure you want terminate entitlement "
                    f"{selected['id']}? This process cannot be reversed."
                ),
                btn_label="Terminate",
                btn_variant="error",
            ),
            self.perform_terminate_entitlement_action,
        )

    @handle_error_notification(f"Error redeem entitlement")
    async def perform_redeem_entitlement_action(self, id: str, data: dict[str, Any] | None):
        if not data:
            return

        await self.api_client.execute_object_action(
            collection=self.get_collection_name(),
            method="POST",
            id=id,
            action="redeem",
            payload={
                "organization": {
                    "id": data["organization"],
                },
                "datasource": {
                    "id": data["datasource"]["id"],
                    "name": data["datasource"]["name"],
                    "type": data["datasource"]["type"],
                }
            },
        )
        self.query_one(DataGrid).reload()
        self.notify(
            title="Success",
            message="Entitlement successfully redeemed",
        )

    @handle_error_notification(f"Error terminate entitlement")
    async def perform_terminate_entitlement_action(self, confirm: bool | None):
        selected = self.query_one(DataGrid).selected_object
        if not (selected and confirm):
            return

        await self.api_client.execute_object_action(
            collection=self.get_collection_name(),
            method="POST",
            id=selected["id"],
            action="terminate",
        )
        self.query_one(DataGrid).reload()
        self.notify(
            title="Success",
            message="Entitlement successfully terminated",
        )

    def get_details_extra_panes(self, selected: dict[str, Any]) -> list[TabPane]:
        return []

    def prepare_create_payload(self, data):
        owner = data.pop("owner")
        if self.is_operations_account:
            data["owner"] = {"id": owner}
        return data

    def get_columns(self):
        return [
            DataGridColumn(title="ID", field="id"),
            DataGridColumn(title="Name", field="name"),
            DataGridColumn(title="Affiliate", field="owner", formatter=format_object_label),
            DataGridColumn(
                title="Datasource", field="datasource_id"
            ),
            DataGridColumn(title="Status", field="status", formatter=format_status),
            DataGridColumn(title="Created at", field="events.created", formatter=format_at),
            DataGridColumn(title="Created by", field="events.created", formatter=format_by),
            DataGridColumn(title="Updated at", field="events.updated", formatter=format_at),
            DataGridColumn(title="Updated by", field="events.updated", formatter=format_by),
        ]
