import logging
import math
from dataclasses import dataclass

from textual import on
from textual.containers import Grid, Horizontal
from textual.message import Message
from textual.reactive import Reactive, reactive
from textual.validation import Function, Integer
from textual.widgets import Button, Input, Label, Select

logger = logging.getLogger(__name__)


class  Pagination(Grid):
    DEFAULT_CSS = """
    Pagination {
        grid-size: 2 1;
        grid-columns: 1fr 1fr;
    }
    #left-controls {
        align: left middle;
    }
    #right-controls {
        align: right middle;
    }

    #current-page {
        width: 10;
    }
    #rows-per-page {
        width: 10;
    }
    #left-controls > Label {
        content-align: center middle;
        height: 1fr;
        padding-left: 1;
        padding-right: 1;
    }
    #right-controls > Label {
        content-align: center middle;
        height: 1fr;
        padding-left: 1;
        padding-right: 1;
    }
    """

    @dataclass
    class Navigate(Message):
        limit: int
        offset: int

    total_rows: Reactive[int] = reactive(0)
    previous_diabled: Reactive[bool] = reactive(True)
    next_disabled: Reactive[bool] = reactive(False)

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        markup: bool = True,
    ):
        super().__init__(name=name, id=id, classes=classes, disabled=disabled, markup=markup)
        self.current_offset = 0
        self.rows_per_page = 10
        self.select_initialized = False

    def compose(self):
        with Horizontal(id="left-controls"):
            yield Button("← Previous", id="btn-previous").data_bind(
                disabled=Pagination.previous_diabled,
            )
            yield Label("Page")
            yield Input(
                "1",
                name="Page",
                id="current-page",
                max_length=1,
                restrict="[0-9]*",
                validate_on=["blur"],
                validators=[
                    Integer(
                        minimum=1,
                        failure_description="The current page must be an integer greater than 1.",
                    ),
                    Function(
                        self.validate_current_page,
                        "The current page must be an integer that "
                        "cannot exceed the total number of pages.",
                    ),
                ],
            )
            yield Label("of 1", id="total-pages")
            yield Button("Next →", id="btn-next").data_bind(disabled=Pagination.next_disabled)

        with Horizontal(id="right-controls"):
            yield Label("Rows per page")
            yield Select[int](
                [("5", 5), ("10", 10), ("25", 25), ("50", 50), ("100", 100)],
                id="rows-per-page",
                allow_blank=False,
                value=10,
            )
            yield Label("0-0 of 0 rows", id="rows-info")

    def validate_current_page(self, value: int | None) -> bool:
        if not value:
            return False
        return int(value) <= math.ceil(self.total_rows / self.rows_per_page)

    def watch_total_rows(self):
        self.refresh_counters()
        self.check_buttons_state()

    @on(Select.Changed)
    def rows_per_page_changed(self, event: Select.Changed):
        event.stop()
        if not self.select_initialized:
            self.select_initialized = True
            return
        self.rows_per_page = int(event.value)  # type: ignore
        self.current_offset = 0
        logger.info(f"{self.__class__.__name__} row_per_page_changed -> navigate")
        self.navigate()

    @on(Button.Pressed)
    def navigation_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn-previous":
            self.current_offset -= self.rows_per_page
        if event.button.id == "btn-next":
            self.current_offset += self.rows_per_page
        logger.info(f"{self.__class__.__name__} navigation_button_pressed -> navigate")
        self.navigate()
        event.stop()

    @on(Input.Submitted)
    @on(Input.Blurred)
    def navigate_to_page(self, event: Input.Submitted | Input.Blurred):
        if event.validation_result and not event.validation_result.is_valid:
            self.notify(
                severity="error",
                title="Error",
                message="\n".join(event.validation_result.failure_descriptions)
            )
            event.stop()
            return
        self.current_offset = (int(event.value) - 1) * self.rows_per_page
        logger.info(f"{self.__class__.__name__} navigate_to_page -> navigate")
        self.navigate()

    def refresh_counters(self):
        first_row = self.current_offset + 1
        last_row = min(self.current_offset + self.rows_per_page, self.total_rows)
        text = f"{first_row}-{last_row} of {self.total_rows} rows"
        self.query_one(Input).value = str((self.current_offset // self.rows_per_page) + 1)
        self.query_one("#total-pages", Label).update(
            f"of {math.ceil(self.total_rows / self.rows_per_page)}"
        )
        self.query_one("#rows-info", Label).update(text)

    def check_buttons_state(self):
        self.next_disabled = self.current_offset + self.rows_per_page >= self.total_rows
        self.previous_diabled = self.current_offset == 0

    def navigate(self):
        self.post_message(self.Navigate(limit=self.rows_per_page, offset=self.current_offset))
        self.check_buttons_state()
        self.refresh_counters()
