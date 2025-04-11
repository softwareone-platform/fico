from typing import Any

from textual.validation import Length
from textual.widgets import Input, Label

from fico.screens.actions import Action
from fico.utils import format_at, format_by, format_status
from fico.widgets.datagrid import DataGridColumn
from fico.widgets.form import FormItem
from fico.widgets.view import View


class Accounts(View):

    OBJECT_NAME = "Affiliate"
    OBJECT_NAME_PLURAL = "Affiliates"
    COLLECTION_NAME = "accounts"

    def prepare_create_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            **data,
            "type": "affiliate",
        }

    def get_columns(self) -> list[DataGridColumn]:
        return [
            DataGridColumn(title="ID", field="id"),
            DataGridColumn(title="Name", field="name"),
            DataGridColumn(title="Additional ID", field="external_id"),
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
                Label("Operations Additional ID"),
                Input(
                    id="external_id",
                    name="Additional ID",
                    validate_on=["blur"],
                    validators=[Length(minimum=1)],
                ),
            ),
        ]

    def get_available_actions(self, object: dict[str, Any]) -> dict[str, Action]:
        actions = super().get_available_actions(object)
        actions["delete"] = Action(id="delete", label="Delete", disabled=True)
        return actions
