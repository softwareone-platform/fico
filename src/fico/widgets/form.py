from dataclasses import dataclass
from typing import Any

from textual import on, log
from textual.containers import Grid, Horizontal, Vertical
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import Reactive, reactive
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Select


class FormItem(Grid):
    DEFAULT_CSS = """
    FormItem {
        grid-size: 2 1;
        grid-columns: 1fr 3fr;
        height: 5;
        content-align: left middle;
    }
    FormItem.-hidden {
        display: none;
    }
    FormItem > Label {
        height: 3;
        width: 100%;
        content-align: left middle;
    }
    """


class Form(Grid):
    DEFAULT_CSS = """

    Form {
        grid-size: 1 3;
        grid-rows: 3 1fr 3;
        padding: 1;
    }

    Form > Label {
        height: 3;
        width: 2fr;
        content-align: left middle;
        padding-left: 1;
        color: $primary;
        text-style: bold;
    }

    Form > Horizontal {
        align-horizontal: right;
        content-align: right middle;
    }
    #save {
        margin-right: 1;
    }
    """

    form_title: Reactive[str] = reactive("")

    def __init__(
        self,
        *children: Widget,
        form_title: str | None  = None,
        save_button_label: str = "Save",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        markup: bool = True,
    ):
        super().__init__(name=name, id=id, classes=classes, disabled=disabled, markup=markup)
        self.form_content: list[Widget] = list(children) or []
        self.form_title = form_title or ""
        self.save_button_label = save_button_label
        self.object_id: str | None = None

    @dataclass
    class Save(Message):
        data: dict[str, Any]
        object_id: str | None = None

    class Cancel(Message):
        pass

    def compose(self):
        yield Label(self.form_title, id="form-title")
        with Vertical():
            yield from self.form_content
        with Horizontal(id="form-button"):
            yield Button(self.save_button_label, variant="primary", id="save")
            yield Button("Cancel", id="cancel")

    def compose_add_child(self, widget):
        self.form_content.append(widget)

    @on(Button.Pressed, "#cancel")
    def cancel(self, event: Button.Pressed):
        event.stop()
        self.post_message(self.Cancel())

    @on(Button.Pressed, "#save")
    async def save(self, event: Button.Pressed):
        event.stop()
        is_valid = True
        data = {}
        for input in self.query(Input):
            if input.disabled:
                continue
            validation_result = input.validate(input.value)
            if validation_result and not validation_result.is_valid:
                is_valid = False
                self.show_validation_error(input, validation_result)

            if input.id:
                data[input.id] = input.value
        for select in self.query(Select):
            if select.id:
                data[select.id] = str(select.value) if not select.is_blank() else ""
        if is_valid:
            self.post_message(self.Save(object_id=self.object_id, data=data))

    def watch_form_title(self, new_title: str) -> None:
        try:
            self.query_one("#form-title", Label).update(new_title)
        except NoMatches:
            pass

    def show_validation_error(self, input: Input, validation_result):
        message = "\n".join(validation_result.failure_descriptions)  # type: ignore
        self.notify(
            f"{input.name}: {message.lower()}",
            title="Error",
            severity="error",
        )

    def reset(self):
        self.object_id = None
        for input_widget in self.query(Input):
            input_widget.value = ""
        for select_widget in self.query(Select):
            select_widget.clear()

    def load(self, object_id: str, data: dict[str, Any]):
        self.object_id = object_id
        log(data)
        for input_widget in self.query(Input):
            if input_widget.disabled:
                continue
            input_widget.value = data.get(input_widget.id, "")  # type: ignore
        for select_widget in self.query(Select):
            if select_widget.disabled:
                continue
            select_widget.value = data.get(select_widget.id, "")  # type: ignore
