"""Building blocks of the interactive data editor.

Every widget here is spec-driven (see modules.editor.schema): rows and
sections know how to render, edit and serialise their own value, and nothing
about the resume structure itself.

Navigation model: every interactive line is a `Row` (focusable). Arrows and
w/s move focus between rows; space/enter activates the focused row (expand a
section, edit a value, toggle a checkbox). Keys a row does not handle bubble
up to its parent section, which implements list-level actions (add, delete,
move between skill columns).
"""

from __future__ import annotations

from typing import Iterable

from rich.markup import escape
from rich.text import Text
from textual import events
from textual.containers import Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Static

from modules.editor.schema import (
    DictSpec, FieldSpec, LeveledDictSpec, MultiChoiceSpec, ObjListSpec,
    StrListSpec, pretty,
)

NOT_SET = "[red]NOT SET[/]"
LEVEL_COLORS = {"low": "red", "mid": "yellow", "high": "green"}


def markup(text: str) -> Text:
    """Rich markup -> Text.

    Textual 8 parses plain strings with its own Content markup, which folds
    whitespace; going through rich.Text keeps spacing exactly as written.
    """
    return Text.from_markup(text)


class DataChanged(Message):
    """Posted when the user changes any value; bubbles up to the app."""


def focus_neighbor(current: Widget, removing: Widget) -> None:
    """Move focus to the nearest widget outside the subtree being removed."""
    chain = current.screen.focus_chain
    if current not in chain:
        return
    index = chain.index(current)
    for candidate in chain[index + 1:] + chain[:index][::-1]:
        if removing not in candidate.ancestors_with_self:
            candidate.focus()
            return


def input_focused(widget: Widget) -> bool:
    """True while an inline Input is being edited somewhere on screen.

    Keys that an Input handles through bindings (arrows, backspace, ...) are
    resolved only after the event bubbles unhandled to the app, so ancestor
    key handlers must stay out of the way while an edit is in progress.
    """
    return isinstance(widget.screen.focused, Input)


class Row(Widget, can_focus=True):
    """A focusable interactive line.

    Note: Textual dispatches `on_key` for every class in the MRO, so the
    handler is defined here once; subclasses hook in via `_row_key`.
    """

    DEFAULT_CSS = """
    Row {
        height: auto;
        width: 1fr;
        padding: 0 1;
    }
    Row:focus, Row:focus-within {
        background: magenta 20%;
    }
    """

    async def activate(self) -> None:
        """Space/enter action."""

    async def _row_key(self, event: events.Key) -> bool:
        """Subclass hook; return True if the key was consumed."""
        return False

    async def on_key(self, event: events.Key) -> None:
        if await self._row_key(event):
            event.stop()
            event.prevent_default()
            return
        key = event.key
        if key in ("up", "w"):
            self.screen.focus_previous()
        elif key in ("down", "s"):
            self.screen.focus_next()
        elif key in ("space", "enter"):
            await self.activate()
        else:
            return
        event.stop()
        event.prevent_default()


class EditableRow(Row):
    """A row with a text value edited in-place through an inline Input."""

    DEFAULT_CSS = """
    EditableRow {
        layout: horizontal;
    }
    EditableRow > .field-label {
        width: auto;
    }
    EditableRow > .field-value {
        width: 1fr;
        height: auto;
    }
    EditableRow > Input, EditableRow > Input:focus {
        width: 1fr;
        height: 1;
        border: none;
        padding: 0;
        background: magenta 35%;
    }
    """

    def __init__(self, value: str = "", label: str | None = None,
                 bullet: bool = False, owner=None,
                 discard_if_empty: bool = False) -> None:
        super().__init__()
        self.value = value
        self.field_label = label
        self.bullet = bullet
        self.owner = owner
        self.discard_if_empty = discard_if_empty
        self.editing = False

    def compose(self):
        if self.bullet:
            yield Static(markup("[cyan]•[/] "), classes="field-label")
        elif self.field_label is not None:
            yield Static(markup(f"[cyan]{escape(self.field_label)}[/]: "), classes="field-label")
        yield Static(self._value_text(), classes="field-value")

    def _value_text(self) -> Text:
        return markup(escape(self.value) if self.value.strip() else NOT_SET)

    async def activate(self) -> None:
        await self.start_edit()

    async def start_edit(self) -> None:
        if self.editing:
            return
        self.editing = True
        self.query_one(".field-value").display = False
        editor = Input(value=self.value, select_on_focus=False)
        await self.mount(editor)
        editor.focus()
        editor.cursor_position = len(editor.value)

    async def _finish_edit(self, commit: bool, refocus: bool = True) -> None:
        if not self.editing:
            return
        self.editing = False
        editor = self.query_one(Input)
        new_value = editor.value
        await editor.remove()
        display = self.query_one(".field-value", Static)
        display.display = True
        changed = commit and new_value != self.value
        if changed:
            self.value = new_value
            display.update(self._value_text())
        if self.discard_if_empty and not self.value.strip() and self.owner is not None:
            await self.owner.discard_row(self, changed=changed, refocus=refocus)
            return
        if changed:
            self.post_message(DataChanged())
        if refocus:
            self.focus()

    async def on_input_blurred(self, event: Input.Blurred) -> None:
        event.stop()
        await self._finish_edit(commit=True, refocus=False)

    async def _row_key(self, event: events.Key) -> bool:
        if self.editing:
            # enter/escape end the edit; up/down must not navigate away.
            # Everything else keeps bubbling so the Input's own bindings
            # (arrows, backspace, home/end, ...) still work.
            if event.key == "enter":
                await self._finish_edit(commit=True)
            elif event.key == "escape":
                await self._finish_edit(commit=False)
            elif event.key not in ("up", "down"):
                return False
            return True
        if event.key == "delete" and self.owner is not None:
            await self.owner.discard_row(self, changed=bool(self.value.strip()))
            return True
        return False

    def get_value(self) -> str:
        return self.value


class AddRow(Row):
    """The trailing "+ add ..." action line of a growable list."""

    def __init__(self, caption: str, owner) -> None:
        super().__init__()
        self.caption = caption
        self.owner = owner

    def render(self):
        return markup(f"[green]+[/] [dim]{escape(self.caption)}[/]")

    async def activate(self) -> None:
        await self.owner.add_entry()


class SectionHeader(Row):
    """The collapsible title line of a Section."""

    def __init__(self, section: "Section") -> None:
        super().__init__()
        self.section = section

    def render(self):
        return markup(self.section.header_markup())

    async def activate(self) -> None:
        self.section.toggle()

    async def _row_key(self, event: events.Key) -> bool:
        if event.key == "delete":
            return await self.section.on_delete_key()
        return False


class Section(Vertical):
    """A collapsible group: a header row plus an indented body."""

    DEFAULT_CSS = """
    Section {
        height: auto;
        width: 1fr;
    }
    Section > .section-body {
        height: auto;
        width: 1fr;
        padding: 0 0 0 3;
    }
    """

    def __init__(self, collapsed: bool = True) -> None:
        super().__init__()
        self.collapsed = collapsed
        self._header = SectionHeader(self)
        self._body = Vertical(*self.body_widgets(), classes="section-body")
        self._body.display = not collapsed

    def body_widgets(self) -> Iterable[Widget]:
        return []

    def compose(self):
        yield self._header
        yield self._body

    def title(self) -> str:
        return ""

    def count(self) -> int:
        return 0

    def header_markup(self) -> str:
        arrow = "▸" if self.collapsed else "▾"
        return f"[magenta]{arrow}[/] [bold cyan]{escape(self.title())}[/] [dim]({self.count()})[/]"

    def toggle(self) -> None:
        self.collapsed = not self.collapsed
        self._body.display = not self.collapsed
        self._header.refresh()

    def refresh_header(self) -> None:
        self._header.refresh()

    async def on_delete_key(self) -> bool:
        return False


class StrListSection(Section):
    """A growable list of plain strings."""

    def __init__(self, spec: StrListSpec, values: list) -> None:
        self.spec = spec
        self._initial = ["" if v is None else str(v) for v in (values or [])]
        super().__init__()

    def body_widgets(self):
        self._add = AddRow("add item", self)
        rows = [EditableRow(value, bullet=True, owner=self, discard_if_empty=True)
                for value in self._initial]
        return [*rows, self._add]

    def rows(self) -> list[EditableRow]:
        return [w for w in self._body.children
                if isinstance(w, EditableRow) and not w._pruning]

    def title(self) -> str:
        return self.spec.label

    def count(self) -> int:
        return len(self.rows()) if self._body.children else len(self._initial)

    async def add_entry(self) -> None:
        if self.collapsed:
            self.toggle()
        row = EditableRow("", bullet=True, owner=self, discard_if_empty=True)
        await self._body.mount(row, before=self._add)
        self.refresh_header()
        await row.start_edit()

    async def discard_row(self, row, changed: bool = True, refocus: bool = True) -> None:
        if refocus:
            focus_neighbor(self.screen.focused or row, removing=row)
        # Not awaited: this may run from a handler inside the removed subtree,
        # and awaiting the removal of your own ancestor deadlocks the pump.
        row.remove()
        self.refresh_header()
        if changed:
            self.post_message(DataChanged())

    async def on_key(self, event: events.Key) -> None:
        if event.key == "n" and not input_focused(self):
            event.stop()
            await self.add_entry()

    def get_value(self) -> list[str]:
        return [row.value for row in self.rows()]


class ItemSection(Section):
    """One collapsible record inside an ObjListSection."""

    def __init__(self, owner: "ObjListSection", item: dict, collapsed: bool = True) -> None:
        self.owner = owner
        self.field_rows = {
            f: EditableRow("" if item.get(f) is None else str(item.get(f)), label=pretty(f))
            for f in owner.spec.item_fields
        }
        super().__init__(collapsed=collapsed)

    def body_widgets(self):
        return list(self.field_rows.values())

    def header_markup(self) -> str:
        arrow = "▸" if self.collapsed else "▾"
        title_row = self.field_rows.get(self.owner.spec.title_field)
        if title_row is not None and title_row.value.strip():
            title = escape(title_row.value)
        else:
            title = "[dim italic]new entry[/]"
        return f"[magenta]{arrow}[/] [cyan]{self.item_index()}.[/] {title}"

    def item_index(self) -> int:
        try:
            return self.owner.items().index(self) + 1
        except ValueError:
            return len(self.owner.items()) + 1

    def first_row(self) -> EditableRow | None:
        return next(iter(self.field_rows.values()), None)

    async def on_delete_key(self) -> bool:
        await self.owner.remove_item(self)
        return True

    def on_data_changed(self, message: DataChanged) -> None:
        self.refresh_header()  # the title field may have changed; keep bubbling

    def get_value(self) -> dict:
        return {f: row.value for f, row in self.field_rows.items()}


class ObjListSection(Section):
    """A growable list of records (education, work experience, ...)."""

    def __init__(self, spec: ObjListSpec, items: list) -> None:
        self.spec = spec
        self._initial = [item for item in (items or []) if isinstance(item, dict)]
        super().__init__()

    def body_widgets(self):
        self._add = AddRow("add entry", self)
        return [*(ItemSection(self, item) for item in self._initial), self._add]

    def items(self) -> list[ItemSection]:
        return [w for w in self._body.children
                if isinstance(w, ItemSection) and not w._pruning]

    def title(self) -> str:
        return self.spec.label

    def count(self) -> int:
        return len(self.items()) if self._body.children else len(self._initial)

    def refresh_items(self) -> None:
        for item in self.items():
            item.refresh_header()

    async def add_entry(self) -> None:
        if self.collapsed:
            self.toggle()
        item = ItemSection(self, {}, collapsed=False)
        await self._body.mount(item, before=self._add)
        self.refresh_header()
        self.refresh_items()
        self.post_message(DataChanged())
        first = item.first_row()
        if first is not None:
            first.focus()
            await first.start_edit()

    async def remove_item(self, item: ItemSection) -> None:
        focus_neighbor(self.screen.focused or item, removing=item)
        # Not awaited: usually called from the removed item's own header,
        # and awaiting the removal of your own ancestor deadlocks the pump.
        item.remove()
        self.refresh_header()
        self.refresh_items()
        self.post_message(DataChanged())

    async def on_key(self, event: events.Key) -> None:
        if event.key == "n" and not input_focused(self):
            event.stop()
            await self.add_entry()

    def get_value(self) -> list[dict]:
        return [item.get_value() for item in self.items()]


class DictSection(Section):
    """A fixed mapping of scalar values."""

    def __init__(self, spec: DictSpec, value: dict) -> None:
        self.spec = spec
        self.field_rows = {
            f: EditableRow("" if value.get(f) is None else str(value.get(f)), label=pretty(f))
            for f in spec.fields
        }
        super().__init__()

    def body_widgets(self):
        return list(self.field_rows.values())

    def title(self) -> str:
        return self.spec.label

    def count(self) -> int:
        return len(self.field_rows)

    def get_value(self) -> dict:
        return {f: row.value for f, row in self.field_rows.items()}


class ChoiceRow(Row):
    """Checkboxes on a single line; left/right or a/d move between options."""

    def __init__(self, spec: MultiChoiceSpec, value: list) -> None:
        super().__init__()
        self.spec = spec
        self.selected = [v for v in (value or []) if v in spec.options]
        self.cursor = 0

    def render(self):
        parts = [f"[cyan]{escape(self.spec.label)}[/]:"]
        for index, option in enumerate(self.spec.options):
            mark = "[green]x[/]" if option in self.selected else " "
            cell = f"\\[{mark}] {escape(option)}"
            if index == self.cursor and self.has_focus:
                cell = f"[reverse]{cell}[/]"
            parts.append(cell)
        return markup("  ".join(parts))

    async def activate(self) -> None:
        option = self.spec.options[self.cursor]
        if option in self.selected:
            self.selected.remove(option)
        else:
            self.selected.append(option)
        self.post_message(DataChanged())
        self.refresh()

    async def _row_key(self, event: events.Key) -> bool:
        key = event.key
        if key in ("left", "a"):
            self.cursor = max(0, self.cursor - 1)
        elif key in ("right", "d"):
            self.cursor = min(len(self.spec.options) - 1, self.cursor + 1)
        else:
            return False
        self.refresh()
        return True

    def on_focus(self, event: events.Focus) -> None:
        self.refresh()

    def on_blur(self, event: events.Blur) -> None:
        self.refresh()

    def get_value(self) -> list[str]:
        return [option for option in self.spec.options if option in self.selected]


class SkillColumn(Vertical):
    """One level column of a SkillsSection."""

    DEFAULT_CSS = """
    SkillColumn {
        width: 1fr;
        height: auto;
    }
    SkillColumn > .skill-column-title {
        height: 1;
        padding: 0 1;
    }
    """

    def __init__(self, section: "SkillsSection", level: str, names: list[str]) -> None:
        self.section = section
        self.level = level
        self._initial = names
        super().__init__()

    def compose(self):
        color = LEVEL_COLORS.get(self.level, "cyan")
        yield Static(markup(f"[bold {color}]{escape(self.level.upper())}[/]"),
                     classes="skill-column-title")
        for name in self._initial:
            yield EditableRow(name, bullet=True, owner=self, discard_if_empty=True)
        self._add = AddRow("add skill", self)
        yield self._add

    def rows(self) -> list[EditableRow]:
        return [w for w in self.children
                if isinstance(w, EditableRow) and not w._pruning]

    def count(self) -> int:
        return len(self.rows()) if self.children else len(self._initial)

    def focusables(self) -> list[Row]:
        return [w for w in self.children if isinstance(w, Row) and not w._pruning]

    async def add_entry(self) -> None:
        row = EditableRow("", bullet=True, owner=self, discard_if_empty=True)
        await self.mount(row, before=self._add)
        self.section.refresh_header()
        await row.start_edit()

    async def discard_row(self, row, changed: bool = True, refocus: bool = True) -> None:
        if refocus:
            focus_neighbor(self.screen.focused or row, removing=row)
        # Not awaited: may run from a handler inside the removed subtree.
        row.remove()
        self.section.refresh_header()
        if changed:
            self.post_message(DataChanged())

    async def move_row(self, row: EditableRow, delta: int) -> None:
        target = self.section.column_neighbor(self, delta)
        if target is None:
            return
        clone = EditableRow(row.value, bullet=True, owner=target, discard_if_empty=True)
        await target.mount(clone, before=target._add)
        row.remove()
        clone.focus()
        self.post_message(DataChanged())

    def focus_adjacent(self, delta: int) -> None:
        target = self.section.column_neighbor(self, delta)
        if target is None:
            return
        current = self.focusables()
        focused = self.screen.focused
        # find index of focused in current by identity to satisfy type checkers
        index = next((i for i, w in enumerate(current) if w is focused), 0)
        targets = target.focusables()
        if targets:
            targets[min(index, len(targets) - 1)].focus()

    async def on_key(self, event: events.Key) -> None:
        if input_focused(self):
            return
        key = event.key
        if key in ("left", "a"):
            self.focus_adjacent(-1)
        elif key in ("right", "d"):
            self.focus_adjacent(1)
        elif key in ("shift+left", "shift+right"):
            focused = self.screen.focused
            if not isinstance(focused, EditableRow) or focused not in self.rows():
                return
            await self.move_row(focused, -1 if key == "shift+left" else 1)
        elif key == "n":
            await self.add_entry()
        else:
            return
        event.stop()
        event.prevent_default()


class SkillsSection(Section):
    """name -> level mapping shown as one column per level."""

    DEFAULT_CSS = """
    SkillsSection > .section-body {
        layout: horizontal;
    }
    """

    def __init__(self, spec: LeveledDictSpec, value: dict) -> None:
        self.spec = spec
        buckets: dict[str, list[str]] = {level: [] for level in spec.levels}
        fallback = spec.levels[len(spec.levels) // 2]
        for name, level in (value or {}).items():
            buckets[level if level in buckets else fallback].append(str(name))
        self._buckets = buckets
        super().__init__()

    def body_widgets(self):
        self.columns = [SkillColumn(self, level, names)
                        for level, names in self._buckets.items()]
        return self.columns

    def title(self) -> str:
        return self.spec.label

    def count(self) -> int:
        return sum(column.count() for column in self.columns)

    def column_neighbor(self, column: SkillColumn, delta: int) -> SkillColumn | None:
        index = self.columns.index(column) + delta
        if 0 <= index < len(self.columns):
            return self.columns[index]
        return None

    async def on_key(self, event: events.Key) -> None:
        if event.key == "n" and not input_focused(self):
            event.stop()
            if self.collapsed:
                self.toggle()
            await self.columns[0].add_entry()

    def get_value(self) -> dict[str, str]:
        return {row.value: column.level
                for column in self.columns
                for row in column.rows() if row.value.strip()}


def build_field_widget(spec: FieldSpec, value) -> Widget:
    """Create the editor widget for a field spec and its current value."""
    if isinstance(spec, MultiChoiceSpec):
        return ChoiceRow(spec, value or [])
    if isinstance(spec, LeveledDictSpec):
        return SkillsSection(spec, value or {})
    if isinstance(spec, ObjListSpec):
        return ObjListSection(spec, value or [])
    if isinstance(spec, StrListSpec):
        return StrListSection(spec, value or [])
    if isinstance(spec, DictSpec):
        return DictSection(spec, value or {})
    return EditableRow("" if value is None else str(value), label=spec.label)
