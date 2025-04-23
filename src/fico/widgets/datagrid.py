import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from rich.text import Text
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Grid
from textual.message import Message
from textual.reactive import Reactive, reactive
from textual.widgets import DataTable

from fico.screens.actions import Action, Actions
from fico.screens.notification import Notification
from fico.widgets.pagination import Pagination

logger = logging.getLogger(__name__)

@dataclass
class DataGridColumn:
    title: str
    field: str
    formatter: Callable[[Any], str | Text] | None = None

    def get_field(self, object: dict[str, Any]) -> str:
        parts = self.field.split(".")
        obj: dict | str | None = object
        for part in parts:
            if not obj or not isinstance(obj, dict):
                return "-"
            obj = obj.get(part)

        if not obj:
            return "-"
        return str(obj if not self.formatter else self.formatter(obj))


class DataGrid(Grid):
    DEFAULT_CSS = """
    DataGrid {
        grid-size: 1 2;
        grid-rows: 1fr 3;
        grid-gutter: 1;
        padding: 1;
    }
    DataGrid > DataTable {
        height: 100%;
    }
    """

    BINDINGS = [
        ("a", "show_actions()", "Actions"),
    ]

    @dataclass
    class SelectionChanged(Message):
        item: Any

    total_rows: Reactive[int] = reactive(0)
    selected_object: Reactive[dict[str, Any] | None] = reactive(None, bindings=True)

    def __init__(
        self,
        columns: list[DataGridColumn],
        datasource: Callable[[int, int, str | None], Coroutine[None, None, dict[str, Any]]],
        actions: Callable[[dict[str, Any]], dict[str, Action]] | None = None,
        pagination: bool = True,
        id=None,
        disabled=False,
        markup=True,
    ) -> None:
        super().__init__(name=None, id=id, classes=None, disabled=disabled, markup=markup)
        self.columns = columns
        self.datasource = datasource
        self.actions = actions
        self.pagination = pagination
        self.current_limit = 10
        self.current_offset = 0
        self.objects: dict[str, dict[str, Any]] = {}
        self.selected_object: dict[str, Any] | None = None
        self.rql_expression: str | None = None

    def compose(self) -> ComposeResult:
        yield DataTable(cursor_type="row", zebra_stripes=True)
        if self.pagination:
            yield Pagination().data_bind(DataGrid.total_rows)

    @work
    async def reload(self) -> None:
        if self.disabled:
            return
        self.loading = True
        logger.info(f"{self.__class__.__name__} reload")
        try:
            args = []
            if self.pagination:
                args = [self.current_limit, self.current_offset, self.rql_expression]
            data = await self.datasource(*args)  # type: ignore

            self.total_rows = data.get("total", len(data.get("items", [])))
            table = self.query_one(DataTable)
            table.clear()
            self.selected_object = None
            self.post_message(self.SelectionChanged(item=None))
            for object in data["items"]:
                self.objects[object["id"]] = object
                table.add_row(
                    *(column.get_field(object) for column in self.columns), key=object["id"]
                )
            table.focus()
        except Exception as e:
            self.app.push_screen(
                Notification(
                    "Error getting data.",
                    str(e),
                    severity="error",
                )
            )
        self.loading = False

    async def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns(*(column.title for column in self.columns))

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected):
        if event.row_key.value:
            self.selected_object = self.objects[event.row_key.value]
        self.post_message(self.SelectionChanged(item=event.row_key.value))

    @on(Pagination.Navigate)
    async def navigate(self, event: Pagination.Navigate) -> None:
        if not self.pagination:
            return
        self.current_limit = event.limit
        self.current_offset = event.offset
        logger.info(f"{self.__class__.__name__} navigate -> reload")
        self.reload()

    def reset(self, rql_expression: str | None = None) -> None:
        if not self.pagination:
            return
        self.rql_expression = rql_expression
        pagination = self.query_one(Pagination)
        pagination.current_offset = 0
        logger.info(f"{self.__class__.__name__} reset -> navigate -> reload")
        pagination.navigate()

    def show_actions(self):
        if not self.selected_object:
            return
        actions = self.actions(self.selected_object)
        self.app.push_screen(Actions(list(actions.values())), self.run_object_action)

    async def run_object_action(self, action: Action) -> None:
        if action and self.selected_object and action.handler:
            await action.handler(self.selected_object)


    async def action_show_actions(self):
        self.show_actions()

    def check_action(
        self, action: str, parameters: tuple[object, ...]
    ) -> bool | None:
        if action == "show_actions" and self.selected_object is not None:
            return True
        return False
