"""The Textual application that hosts the data editor widgets."""

from __future__ import annotations

import json
from pathlib import Path

from rich.markup import escape
from rich.text import Text
from textual.app import App
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from modules.editor.schema import build_specs
from modules.editor.widgets import DataChanged, EditableRow, Row, build_field_widget

LEGEND = """\
[bold magenta]Navigate[/]
 [cyan]↑ ↓ · w s[/]    Fields
 [cyan]← → · a d[/]    Columns

[bold magenta]Edit[/]
 [cyan]Space·Enter[/]  Interact
 [cyan]Enter[/]        Confirm
 [cyan]Esc[/]          Cancel

[bold magenta]Lists[/]
 [cyan]N[/]            Add entry
 [cyan]Del[/]          Delete
 [cyan]Shift ← →[/]    Move skill

[bold magenta]File[/]
 [cyan]Ctrl+S[/]       Save
 [cyan]Ctrl+X[/]       Exit\
"""


class ExitConfirmScreen(ModalScreen[str]):
    """Asks whether to save before exiting with unsaved changes."""

    CSS = """
    ExitConfirmScreen {
        align: center middle;
    }
    #dialog {
        width: auto;
        height: auto;
        max-width: 70;
        border: round yellow;
        border-title-color: yellow;
        border-title-style: bold;
        padding: 1 2;
        background: $surface;
    }
    #dialog-buttons {
        width: auto;
        height: auto;
        margin-top: 1;
    }
    #dialog-buttons Button {
        margin-right: 2;
    }
    """

    BINDINGS = [
        Binding("y", "choose('save')", "save & exit"),
        Binding("n", "choose('discard')", "discard"),
        Binding("escape", "choose('cancel')", "cancel"),
        Binding("left", "app.focus_previous", show=False),
        Binding("right", "app.focus_next", show=False),
    ]

    def __init__(self, file_name: str) -> None:
        super().__init__()
        self.file_name = file_name

    def compose(self):
        dialog = Vertical(id="dialog")
        dialog.border_title = "Unsaved changes"
        with dialog:
            yield Static(Text.from_markup(
                f"Save changes to [bold cyan]{escape(self.file_name)}[/] before exiting?"
            ))
            with Horizontal(id="dialog-buttons"):
                yield Button("Save & exit (y)", variant="success", id="save")
                yield Button("Discard (n)", variant="error", id="discard")
                yield Button("Cancel (esc)", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#save").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id)

    def action_choose(self, choice: str) -> None:
        self.dismiss(choice)


class EditorApp(App[None]):
    """Interactive editor for a resume data file."""

    CSS = """
    Screen {
        layout: horizontal;
    }
    #fields {
        width: 1fr;
        border: round magenta;
        border-title-color: magenta;
        border-title-style: bold;
        border-subtitle-color: yellow;
        padding: 1 2;
        scrollbar-size-vertical: 1;
    }
    #sidebar {
        width: 30;
        border: round blue;
        border-title-color: blue;
        border-title-style: bold;
        padding: 1 2;
    }
    """

    BINDINGS = [
        Binding("ctrl+s", "save", "Save", priority=True),
        Binding("ctrl+x", "request_quit", "Exit", priority=True),
        Binding("ctrl+q", "request_quit", "Exit", show=False, priority=True),
    ]

    dirty = reactive(False)

    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = Path(path)
        with open(self.path, encoding="utf-8") as f:
            self.data = json.load(f)
        self.specs = build_specs(self.data)
        self.saved = False
        self._field_widgets: list[tuple[str, object]] = []

    def compose(self):
        fields = VerticalScroll(id="fields")
        fields.can_focus = False
        fields.border_title = escape(self.path.stem)
        with fields:
            for spec in self.specs:
                widget = build_field_widget(spec, self.data.get(spec.key))
                self._field_widgets.append((spec.key, widget))
                yield widget
        sidebar = Static(Text.from_markup(LEGEND), id="sidebar")
        sidebar.border_title = "Keys"
        yield sidebar

    def on_mount(self) -> None:
        rows = self.query(Row)
        if rows:
            rows.first().focus()

    def watch_dirty(self, dirty: bool) -> None:
        try:
            fields = self.query_one("#fields")
        except Exception:
            return
        if dirty:
            fields.border_subtitle = "[bold yellow]● unsaved[/]"
        elif self.saved:
            fields.border_subtitle = "[green]saved[/]"
        else:
            fields.border_subtitle = ""

    def on_data_changed(self, message: DataChanged) -> None:
        self.dirty = True

    async def action_save(self) -> None:
        for row in self.query(EditableRow):
            if row.editing:
                await row._finish_edit(commit=True)
        data = {key: widget.get_value() for key, widget in self._field_widgets}  # type: ignore
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        self.saved = True
        self.dirty = False
        self.watch_dirty(False)
        self.notify(f"Saved {self.path.name}", timeout=2)

    def action_request_quit(self) -> None:
        if len(self.screen_stack) > 1:
            return
        if not self.dirty:
            self.exit()
            return
        self.push_screen(ExitConfirmScreen(self.path.name), self._on_exit_choice)

    def _on_exit_choice(self, choice: str | None) -> None:
        if choice == "save":
            async def save_and_exit() -> None:
                await self.action_save()
                self.exit()
            self.run_worker(save_and_exit())
        elif choice == "discard":
            self.exit()


def run_editor(path: Path) -> bool:
    """Open the TUI editor for a data file; returns True if it was saved."""
    app = EditorApp(path)
    app.run()
    return app.saved
