from typing import Any

from textual.widgets import TabPane

from fico.screens.actions import Action
from fico.utils import format_at, format_object_label, format_status
from fico.widgets.datagrid import DataGridColumn
from fico.widgets.view import View


class Charges(View):

    OBJECT_NAME = "Charges Files"
    OBJECT_NAME_PLURAL = "Charges File"
    COLLECTION_NAME = "charges"


    def get_available_actions(self, object: dict[str, Any]) -> dict[str, Action]:
        actions = super().get_available_actions(object)

        return actions

    def get_details_extra_panes(self, selected: dict[str, Any]) -> list[TabPane]:
        return []


    def get_columns(self):
        return [
            DataGridColumn(title="ID", field="id"),
            DataGridColumn(title="Document date", field="document_date"),
            DataGridColumn(title="Currency", field="currency"),
            DataGridColumn(title="Amount", field="amount"),
            DataGridColumn(title="Affiliate", field="owner", formatter=format_object_label),
            DataGridColumn(title="Status", field="status", formatter=format_status),
            DataGridColumn(title="Created at", field="events.created", formatter=format_at),
            DataGridColumn(title="Updated at", field="events.updated", formatter=format_at),
        ]
