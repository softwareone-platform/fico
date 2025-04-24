from typing import Any

from textual import log, on
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import (
    Footer,
    Label,
    Select,
)

from fico.api import FFCOpsClient
from fico.utils import format_object_label
from fico.widgets.form import Form, FormItem


class RedeemEntitlementDialog(ModalScreen[dict[str, Any]]):
    CSS = """
    RedeemEntitlementDialog {
        align: center middle;
    }
    RedeemEntitlementDialog > Form {
        width: 120;
        height: 20;
    }
    """

    def __init__(
        self, api_client: FFCOpsClient, entitlement_id: str, organizations: list[dict[str, Any]]
    ):
        super().__init__()
        self.api_client = api_client
        self.entitlement_id = entitlement_id
        self.organizations = organizations

    def compose(self) -> ComposeResult:
        with Form(
            id="form",
            form_title=f"Redeem Entitlement {self.entitlement_id}",
            save_button_label="Redeem",
        ):
            with FormItem(id="fi_organization"):
                yield Label("Organization")
                yield Select(
                    [(format_object_label(org), org["id"]) for org in self.organizations],
                    id="organization",
                    name="Organization",
                )
            with FormItem(id="fi_datasource"):
                yield Label("Datasource")
                yield Select([], id="datasource", name="Datasource")
        yield Footer()

    @on(Select.Changed, "#organization")
    async def on_organization_changed(self, event: Select.Changed) -> None:
        log("Organization changed", event.value)
        ds_dropdown = self.query_one("#datasource", Select)
        datasources = await self.api_client.get_organization_datasources(event.value)
        if not datasources:
            return

        ds_dropdown.set_options(
            [(format_object_label(ds), ds["id"]) for ds in datasources["items"]]
        )

    @on(Form.Save)
    def do_redeem(self, event: Form.Save) -> None:
        event.stop()
        if not event.data["organization"]:
            self.notify(
                severity="error",
                title="Error",
                message="Please select an organization and a datasource.",
            )
            return
        if not event.data["datasource"]:
            self.notify(
                severity="error",
                title="Error",
                message="Please select a datasource.",
            )
            return
        self.dismiss(event.data)

    @on(Form.Cancel)
    def do_cancel(self, event: Form.Cancel) -> None:
        event.stop()
        self.app.pop_screen()
