from typing import Any

from textual.validation import Length
from textual.widgets import Input, Label, Select, TabPane

from fico.screens.actions import Action
from fico.utils import format_at, format_by, format_object_label, format_status
from fico.widgets.datagrid import DataGridColumn
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
                id="item-owner",
            ),
        ]

    async def prepare_add_form(self):
        if self.current_account and self.current_account["type"] == "operations":
            self.query_one("#item-owner", FormItem).remove_class("hidden")
            rql = "and(eq(type,affiliate),eq(status,active))&order_by(name)"
            accounts = await self.api_client.get_all_objects("accounts", rql=rql)
            self.query_one("#owner", Select).set_options(
                [
                    (f"{format_object_label(account)}", account["id"])
                    for account in accounts
                ]
            )
        else:
            self.query_one("#item-owner", FormItem).add_class("hidden")

    def get_available_actions(self, object: dict[str, Any]) -> dict[str, Action]:
        actions = super().get_available_actions(object)
        if object["status"] == "new":
            actions["redeem"] = Action(
                id="redeem",
                label="Redeem",
                disabled=False,
                handler=self.redeem_entitlement)
        return actions

    async def redeem_entitlement(self, id):
        pass

    def get_details_extra_panes(self, selected: dict[str, Any]) -> list[TabPane]:
        return []

    def prepare_create_payload(self, data):
        owner = data.pop("owner")
        if self.current_account and self.current_account["type"] == "operations":
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
