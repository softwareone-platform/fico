from rich.style import Style
from textual import on
from textual.app import ComposeResult
from textual.containers import Grid, Horizontal
from textual.keys import Keys
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Footer,
    Label,
    Markdown,
    TabbedContent,
    TabPane,
    TextArea,
)
from textual.widgets.text_area import TextAreaTheme
from tree_sitter import Language
from tree_sitter_rql import HIGHLIGHTS_QUERY, language

rqleditor_theme = TextAreaTheme(
    name="rqleditor",
    syntax_styles={
        "operator": Style(color="yellow"),
        "keyword": Style(color="blue"),
        "variable": Style(color="green"),
        "constant.builtin": Style(color="cyan"),
        "constant.numeric": Style(color="white", bold=True),
        "string": Style(color="#c88e32"),
    },
)


class RQLEditor(ModalScreen[str]):
    CSS = """
    RQLEditor {
        align: center middle;
    }
    RQLEditor > Grid {
        grid-size: 1 3;
        grid-rows: 3 1fr 3;
        grid-gutter: 1;
        padding: 1;
        width: 80;
        height: 32;
        border: thick $background 80%;
        background: $surface;
    }
    RQLEditor > Grid > TextArea {
        width: 80;
        height: 30;
    }
    RQLEditor > Grid > Label {
        height: 1fr;
        width: 1fr;
        content-align: center middle;
        background: $panel;
        color: $foreground;
        text-style: bold;
    }
    RQLEditor > Grid > Horizontal {
        align-horizontal: right;
    }
    #apply {
        margin-right: 1;
    }
    """

    BINDINGS = [
        (Keys.Escape, "dismiss", "Close"),
    ]

    def __init__(self, text: str | None, help_text: str | None = None):
        super().__init__()
        self.text_area = self.setup_text_area(text)
        self.help_text = help_text

    def setup_text_area(self, text) -> TextArea:
        ta = TextArea.code_editor(text or "")
        ta.register_theme(rqleditor_theme)
        ta.register_language("rql", Language(language()), HIGHLIGHTS_QUERY)
        ta.theme = "rqleditor"
        ta.language = "rql"
        return ta

    def compose(self) -> ComposeResult:
        with Grid():
            yield Label("Enter RQL Query")
            with TabbedContent():
                with TabPane("Editor"):
                    yield self.text_area
                with TabPane("Help"):
                    yield Markdown(
                        self.help_text, open_links=False
                    )
            with Horizontal():
                yield Button("Apply", variant="primary", id="apply")
                yield Button("Clear", id="clear")
        yield Footer()

    @on(Button.Pressed)
    def button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "clear":
            self.text_area.text = ""
            return
        self.dismiss(self.text_area.text)

    def action_dismiss(self):
        self.dismiss("")
