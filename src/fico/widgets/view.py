from typing import Any

from textual import log, on
from textual.containers import Container, Grid, Horizontal
from textual.reactive import Reactive, reactive
from textual.widgets import ContentSwitcher, TabPane

from fico.api import FFCOpsClient
from fico.screens.actions import Action
from fico.screens.details import Details
from fico.screens.dialogs import ConfirmDialog
from fico.screens.notification import Notification, SeverityType
from fico.utils import format_object_label, handle_error_notification
from fico.widgets.datagrid import DataGrid, DataGridColumn
from fico.widgets.filterbar import FilterBar
from fico.widgets.form import Form, FormItem
from fico.widgets.topbar import TopBar


class View(Container):
    DEFAULT_CSS = """
    #list-grid {
        grid-size: 1 2;
        grid-rows: 5 1fr;
        grid-gutter: 0;
        padding: 1;
    }
    #list {
        width: 100%;
    }
    .hidden {
        display: none;
    }
    """

    OBJECT_NAME = "Object"
    OBJECT_NAME_PLURAL = "Objects"
    SUPPORT_RQL = True

    total_rows: Reactive[int] = reactive(0)
    selected_object: Reactive[dict[str, Any] | None] = reactive(None, bindings=True)

    def __init__(
        self,
        api_client: FFCOpsClient,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        markup: bool = True,
    ):
        super().__init__(name=name, id=id, classes=classes, disabled=disabled, markup=markup)
        self.api_client = api_client
        self.edit_disabled = False
        self.current_account: dict[str, Any] | None = None
        self.current_user: dict[str, Any] | None = None

    @classmethod
    def get_collection_name(cls) -> str:
        if not hasattr(cls, "COLLECTION_NAME"):
            raise NotImplementedError("`COLLECTION_NAME` must be defined in subclasses.")
        return cls.COLLECTION_NAME

    def compose(self):
        form_items = self.get_form_items()
        self.edit_disabled = not form_items
        with ContentSwitcher(id="switcher", initial="list"):
            with Horizontal(id="list"):
                with Grid(id="list-grid"):
                    yield TopBar(
                        self.OBJECT_NAME_PLURAL,
                        support_rql=self.SUPPORT_RQL,
                        add_disabled=self.edit_disabled,
                        rql_help=(
                            self.api_client.get_rql_help(self.get_collection_name())
                            if self.SUPPORT_RQL
                            else None
                        ),
                    )
                    yield DataGrid(
                        columns=self.get_columns(),
                        datasource=self.list_objects,
                        actions=self.get_available_actions,
                        disabled=self.disabled,
                    )
            if form_items:
                yield Form(*form_items, id="form")

    @on(TopBar.ActionsPressed)
    def on_actions(self, event: TopBar.ActionsPressed):
        self.query_one(DataGrid).show_actions()

    @on(DataGrid.SelectionChanged)
    def on_selection_changed(self, event: DataGrid.SelectionChanged):
        self.selected_object = event.item
        if event.item:
            self.query_one(TopBar).enable_actions()
        else:
            self.query_one(TopBar).disable_actions()

    @on(TopBar.AddPressed)
    async def add(self):
        await self.prepare_add_form()
        self.show_form(f"Add {self.OBJECT_NAME}")

    @on(Form.Cancel)
    def cancel(self):
        self.query_one(ContentSwitcher).current = "list"
        self.current_view = "list"
        self.query_one(Form).reset()

    @on(Form.Save)
    async def save(self, event: Form.Save):
        data = event.data
        obj = None
        if event.object_id:
            payload = self.prepare_update_payload(data)
            obj = await self.update_object(event.object_id, payload)
        else:
            payload = self.prepare_create_payload(data)
            obj = await self.create_object(payload)

        if obj:
            self.show_grid()

    def show_grid(self):
        self.query_one(DataGrid).reset()
        self.query_one(ContentSwitcher).current = "list"
        self.current_view = "list"
        self.query_one(Form).reset()

    def show_form(self, form_title: str):
        self.query_one(Form).form_title = form_title
        self.query_one(ContentSwitcher).current = "form"
        self.current_view = "form"

    @on(FilterBar.FilterChanged)
    def on_filter_changed(self, event: FilterBar.FilterChanged):
        self.query_one(DataGrid).reset(event.rql_query)

    @handle_error_notification(f"Error retrieving {OBJECT_NAME}")
    async def perform_details_action(self, selected):
        obj = await self.get_object(selected["id"])
        self.app.push_screen(
            Details(
                f"{self.OBJECT_NAME} {format_object_label(obj)} details",
                obj,
                self.get_details_extra_panes(selected),
            ),
        )

    @handle_error_notification(f"Error retrieving {OBJECT_NAME}")
    async def perform_edit_action(self, selected):
        obj = await self.prepare_edit_form(selected)
        if not obj:
            return
        form = self.query_one(Form)
        form.load(obj["id"], obj)
        self.show_form(f"Edit {self.OBJECT_NAME}: {selected['id']}")

    async def perform_delete_action(self, selected: dict[str, Any]) -> None:
        self.app.push_screen(
            ConfirmDialog(
                dialog_title="Confirm deletion",
                dialog_message=(
                    f"Are you sure you want delete the "
                    f"{self.OBJECT_NAME} {format_object_label(selected)} ?"
                ),
                btn_label="Delete",
                btn_variant="error",
            ),
            self.confirm_delete,
        )

    @handle_error_notification(f"Error deleting {OBJECT_NAME}")
    async def confirm_delete(self, confirm: bool | None) -> None:
        selected = self.query_one(DataGrid).selected_object
        log(f"{selected} - {confirm}")
        if selected and confirm:
            await self.delete_object(selected)
            self.query_one(DataGrid).reset()


    async def prepare_add_form(self) -> None:
        pass

    async def prepare_edit_form(self, selected) -> dict[str, Any] | None:
        return await self.get_object(selected["id"])

    def get_available_actions(self, object: dict[str, Any]) -> dict[str, Action]:
        actions = {
            "edit": Action(id="edit", label="Edit", handler=self.perform_edit_action),
            "details": Action(id="details", label="Details", handler=self.perform_details_action),
            "delete": Action(
                id="delete",
                label="Delete",
                handler=self.perform_delete_action,
                disabled=object["status"] == "deleted",
            ),
        }
        return actions


    def get_details_extra_panes(self, object: dict[str, Any]) -> list[TabPane]:
        return []

    def prepare_create_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        return data

    def prepare_update_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        return data

    def get_columns(self) -> list[DataGridColumn]:
        raise NotImplementedError("`get_columns` must be implemented in subclasses.")

    def get_form_items(self) -> list[FormItem]:
        return []

    @handle_error_notification(f"Error creating {OBJECT_NAME}")
    async def create_object(self, data: dict[str, Any]) -> dict[str, Any]:
        object = await self.api_client.create_object(self.get_collection_name(), data)
        self.notify_created_success(object)
        return object

    @handle_error_notification(f"Error fetching {OBJECT_NAME}")
    async def get_object(self, id: str) -> dict[str, Any]:
        return await self.api_client.get_object(self.get_collection_name(), id)

    @handle_error_notification(f"Error updating {OBJECT_NAME_PLURAL}")
    async def update_object(self, id: str, data: dict[str, Any]) -> dict[str, Any]:
        object = await self.api_client.update_object(self.get_collection_name(), id, data)
        self.notify_updated_success(object)
        return object

    async def delete_object(self, object: dict[str, Any]) -> None:
        try:
            await self.api_client.delete_object(self.get_collection_name(), object["id"])
        except Exception as e:
            self.notify_error(f"Error deleting {self.OBJECT_NAME}", e)
            return
        self.notify_deleted_success(object)

    @handle_error_notification(f"Error fetching {OBJECT_NAME_PLURAL}")
    async def list_objects(self, limit: int, offset: int, rql_query: str | None) -> dict[str, Any]:
        return await self.api_client.list_objects(
            self.get_collection_name(), limit, offset, rql_query
        )

    def reset(self):
        if self.disabled:
            return
        self.query_one(ContentSwitcher).current = "list"
        self.current_view = "list"
        self.query_one(DataGrid).reset()
        self.query_one(Form).reset()
        self.query_one(TopBar).reset()
        self.selected_object = None

    def watch_disabled(self, disabled):
        self.query_one(DataGrid).disabled = disabled
        if not disabled:
            self.reset()
        return super().watch_disabled(disabled)

    def show_notification(
        self, title: str, message: str, severity: SeverityType = "success", timeout: int = 3
    ):
        self.app.push_screen(
            Notification(
                title,
                message,
                severity=severity,
                timeout=timeout,
            )
        )

    def notify_success(self, object: dict[str, Any], action: str) -> None:
        self.show_notification(
            severity="success",
            title="Success",
            message=(
                f"{self.OBJECT_NAME} {action} successfully: "
                f"[bold]{format_object_label(object)}[/]."
            ),
        )

    def notify_error(self, title: str, error: Exception) -> None:
        self.show_notification(
            severity="error",
            title=title,
            message=str(error)
        )

    def notify_created_success(self, object: dict[str, Any]) -> None:
        self.notify_success(object, "created")

    def notify_updated_success(self, object: dict[str, Any]) -> None:
        self.notify_success(object, "updated")

    def notify_deleted_success(self, object: dict[str, Any]) -> None:
        self.notify_success(object, "deleted")

    @property
    def is_operations_account(self):
        return self.current_account and self.current_account["type"] == "operations"

    @property
    def is_affiliate_account(self):
        return self.current_account and self.current_account["type"] == "affiliate"
