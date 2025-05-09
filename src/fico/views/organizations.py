from datetime import datetime
from functools import partial
from typing import Any

from textual.validation import Length
from textual.widgets import Input, Label, Select, TabPane

from fico.constants import CURRENCIES
from fico.screens.actions import Action
from fico.utils import (
    format_at,
    format_by,
    format_currency,
    format_status,
    handle_error_notification,
)
from fico.widgets.datagrid import DataGrid, DataGridColumn
from fico.widgets.form import Form, FormItem
from fico.widgets.view import View


class Organizations(View):
    OBJECT_NAME = "Organization"
    OBJECT_NAME_PLURAL = "Organizations"
    COLLECTION_NAME = "organizations"

    def get_available_actions(self, object: dict[str, Any]) -> dict[str, Action]:
        actions = super().get_available_actions(object)
        actions["delete"] = Action(id="delete", label="Delete", disabled=True)
        return actions

    def get_columns(self) -> list[DataGridColumn]:
        return [
            DataGridColumn(title="ID", field="id"),
            DataGridColumn(title="Name", field="name"),
            DataGridColumn(title="Currency", field="currency", formatter=format_currency),
            DataGridColumn(
                title="Billing Currency", field="billing_currency", formatter=format_currency
            ),
            DataGridColumn(title="Operations ID", field="operations_external_id"),
            DataGridColumn(title="Linked Organization ID", field="linked_organization_id"),
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
                    validate_on=[],
                    validators=[Length(minimum=1)],
                ),
            ),
            FormItem(
                Label("Operations Additional ID"),
                Input(
                    id="operations_external_id",
                    name="Operations Additional ID",
                    validate_on=[],
                    validators=[Length(minimum=1)],
                ),
            ),
            FormItem(
                Label("Currency"),
                Select(CURRENCIES, id="currency"),
                id="fi_currency",
            ),
            FormItem(
                Label("Billing Currency"),
                Select(CURRENCIES, id="billing_currency"),
                id="fi_billing_currency",
            ),
            FormItem(
                Label("Admin Name"),
                Input(
                    id="admin_name",
                    name="Admin Name",
                    validate_on=[],
                    validators=[Length(minimum=1)],
                ),
                id="fi_admin_name",
            ),
            FormItem(
                Label("Admin Email"),
                Input(
                    id="admin_email",
                    name="Admin Email",
                    validate_on=[],
                    validators=[Length(minimum=1)],
                ),
                id="fi_admin_email",
            ),
        ]

    async def prepare_add_form(self) -> None:
        await super().prepare_add_form()
        self.query_one("#fi_admin_name", FormItem).remove_class("-hidden")
        self.query_one("#fi_admin_email", FormItem).remove_class("-hidden")
        self.query_one("#fi_currency", FormItem).remove_class("-hidden")
        self.query_one("#fi_billing_currency", FormItem).remove_class("-hidden")
        self.query_one("#admin_name", Input).disabled = False
        self.query_one("#admin_email", Input).disabled = False
        self.query_one("#currency", Select).disabled = False
        self.query_one("#billing_currency", Select).disabled = False

    async def prepare_edit_form(self, selected: dict[str, Any]) -> dict[str, Any] | None:
        obj = await super().prepare_edit_form(selected)
        self.query_one("#fi_admin_name", FormItem).add_class("-hidden")
        self.query_one("#fi_admin_email", FormItem).add_class("-hidden")
        self.query_one("#fi_currency", FormItem).add_class("-hidden")
        self.query_one("#fi_billing_currency", FormItem).add_class("-hidden")
        self.query_one("#admin_name", Input).disabled = True
        self.query_one("#admin_email", Input).disabled = True
        self.query_one("#currency", Select).disabled = True
        self.query_one("#billing_currency", Select).disabled = True
        return obj

    def prepare_update_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        data.pop("admin_name", None)
        data.pop("admin_email", None)
        data.pop("currency", None)
        data.pop("billing_currency", None)
        return data

    @handle_error_notification("Error creating organization")
    async def create_object(self, payload: dict[str, Any]) -> dict[str, Any]:
        admin_name = payload.pop("admin_name")
        admin_email = payload.pop("admin_email")
        employee = await self.api_client.get_employee(admin_email)
        if not employee:
            employee = await self.api_client.create_employee(
                {
                    "email": admin_email,
                    "display_name": admin_name,
                }
            )
        organization = await self.api_client.create_object(
            self.get_collection_name(),
            {
                **payload,
                "user_id": employee["id"],
            },
        )
        return organization

    def get_details_extra_panes(self, object: dict[str, Any]) -> list[TabPane]:
        employees_list = DataGrid(
            columns=[
                DataGridColumn(title="ID", field="id"),
                DataGridColumn(title="Name", field="display_name"),
                DataGridColumn(title="Email", field="email"),
                DataGridColumn(
                    title="Created At",
                    field="created_at",
                    formatter=lambda d: datetime.fromisoformat(d).strftime("%d/%m/%Y %H:%M:%S"),
                ),
                DataGridColumn(
                    title="Last login",
                    field="last_login",
                    formatter=lambda d: datetime.fromisoformat(d).strftime("%d/%m/%Y %H:%M:%S"),
                ),
            ],
            datasource=partial(self.api_client.get_organization_employees, object["id"]),  # type: ignore
            pagination=False,
        )
        employees_list.reload()

        datasources_list = DataGrid(
            columns=[
                DataGridColumn(title="ID", field="id"),
                DataGridColumn(title="Name", field="name"),
                DataGridColumn(
                    title="Resources Charged (this month)", field="resources_charged_this_month"
                ),
                DataGridColumn(
                    title="Expenses to date (this month)", field="expenses_so_far_this_month"
                ),
                DataGridColumn(
                    title="Expenses forecast (this month)", field="expenses_forecast_this_month"
                ),
                DataGridColumn(title="Parent datasource ID", field="parent_id"),
            ],
            datasource=partial(self.api_client.get_organization_datasources, object["id"]),  # type: ignore
            pagination=False,
        )
        datasources_list.reload()

        return [
            TabPane("Datasources", datasources_list),
            TabPane("Users", employees_list),
        ]
