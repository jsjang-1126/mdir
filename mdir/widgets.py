from __future__ import annotations

from pathlib import Path

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import DataTable, Input, Label, Static

from mdir.models import FileEntry, list_directory


class FilePanel(Vertical):
    """Single directory browser panel."""

    DEFAULT_CSS = """
    FilePanel {
        width: 1fr;
        height: 1fr;
        min-height: 1;
        layout: vertical;
        border: solid $accent;
        padding: 0 1;
    }

    FilePanel.active {
        border: heavy $success;
    }

    FilePanel > .panel-path {
        height: 1;
        color: $text-muted;
        text-style: bold;
        overflow: hidden;
    }

    FilePanel DataTable {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("up,k", "cursor_up", "Up", show=False),
        Binding("down,j", "cursor_down", "Down", show=False),
        Binding("pageup", "page_up", "Page Up", show=False),
        Binding("pagedown", "page_down", "Page Down", show=False),
        Binding("home", "scroll_home", "Home", show=False),
        Binding("end", "scroll_end", "End", show=False),
        Binding("enter", "open_selected", "Open", show=False, priority=True),
    ]

    class Activated(Message):
        def __init__(self, panel: FilePanel, entry: FileEntry) -> None:
            super().__init__()
            self.panel = panel
            self.entry = entry

    class SelectionChanged(Message):
        def __init__(self, panel: FilePanel, entry: FileEntry | None) -> None:
            super().__init__()
            self.panel = panel
            self.entry = entry

    active: reactive[bool] = reactive(False)
    current_path: reactive[Path] = reactive(Path.home())
    filter_text: reactive[str] = reactive("")

    def __init__(self, panel_id: str, start_path: Path | None = None, **kwargs) -> None:
        super().__init__(id=panel_id, **kwargs)
        self._entries: list[FileEntry] = []
        self._table: DataTable | None = None
        self._initial_path = (start_path or Path.home()).expanduser().resolve()

    def compose(self) -> ComposeResult:
        yield Label(str(self._initial_path), classes="panel-path")
        yield DataTable(id=f"{self.id}-table", zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        self._table = self.query_one(DataTable)
        table = self._table
        table.add_columns("Name", "Size", "Modified", "Perm")
        table.fixed_columns = 1
        table.cursor_type = "row"
        self.current_path = self._initial_path

    def watch_active(self, active: bool) -> None:
        self.set_class(active, "active")

    def watch_current_path(self, _path: Path) -> None:
        if not self.is_attached:
            return
        self.query_one(".panel-path", Label).update(str(self.current_path))
        self.refresh_listing()

    def watch_filter_text(self, _text: str) -> None:
        if not self.is_attached:
            return
        self.refresh_listing()

    @property
    def selected_entry(self) -> FileEntry | None:
        if self._table is None:
            return None
        if self._table.cursor_row is None:
            return None
        row = self._table.cursor_row
        if row < 0 or row >= len(self._entries):
            return None
        return self._entries[row]

    def refresh_listing(self) -> None:
        if self._table is None:
            return

        table = self._table
        cursor_row = table.cursor_row or 0
        all_entries = list_directory(self.current_path)
        needle = self.filter_text.casefold()
        if needle:
            self._entries = [
                e
                for e in all_entries
                if needle in e.name.casefold() or (e.name == ".." and ".." in needle)
            ]
        else:
            self._entries = all_entries

        table.clear()
        for entry in self._entries:
            name = Text(f"{entry.icon} {entry.name}")
            if entry.is_dir and entry.name != "..":
                name.stylize("bold cyan")
            table.add_row(
                name,
                entry.size_text,
                entry.modified_text,
                entry.perm_text,
            )

        if self._entries:
            table.move_cursor(row=min(cursor_row, len(self._entries) - 1))
        self.post_message(self.SelectionChanged(self, self.selected_entry))

    def set_path(self, path: Path) -> None:
        resolved = path.expanduser().resolve()
        if resolved.is_dir():
            self.current_path = resolved

    def go_up(self) -> None:
        parent = self.current_path.parent
        if parent != self.current_path:
            self.current_path = parent

    def activate_selection(self) -> None:
        entry = self.selected_entry
        if entry is None:
            return
        if entry.name == ".." or entry.is_dir:
            self.set_path(entry.path)
            return
        self.post_message(self.Activated(self, entry))

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.control is not self._table:
            return
        self.post_message(self.SelectionChanged(self, self.selected_entry))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.control is not self._table:
            return
        event.stop()
        self.activate_selection()

    def action_open_selected(self) -> None:
        self.activate_selection()

    def action_cursor_up(self) -> None:
        if self._table:
            self._table.action_cursor_up()

    def action_cursor_down(self) -> None:
        if self._table:
            self._table.action_cursor_down()

    def action_page_up(self) -> None:
        if self._table:
            self._table.action_page_up()

    def action_page_down(self) -> None:
        if self._table:
            self._table.action_page_down()

    def action_scroll_home(self) -> None:
        if self._table:
            self._table.action_scroll_home()

    def action_scroll_end(self) -> None:
        if self._table:
            self._table.action_scroll_end()

    def focus_table(self) -> None:
        if self.id and self.app:
            self.app.query_one(f"#{self.id}-table", DataTable).focus()


class CenterModal(Container):
    """Full-screen transparent overlay that centers a dialog."""

    DEFAULT_CSS = """
    CenterModal {
        layer: overlay;
        width: 100%;
        height: 100%;
        align: center middle;
    }
    """

    def __init__(self, dialog: Vertical, return_panel_id: str) -> None:
        super().__init__()
        self._dialog = dialog
        self._return_panel_id = return_panel_id

    def compose(self) -> ComposeResult:
        yield self._dialog


def _close_modal_dialog(dialog: Vertical) -> None:
    host = dialog.parent
    return_panel_id = None
    if isinstance(host, CenterModal):
        return_panel_id = host._return_panel_id
        host.remove()
    elif dialog.is_attached:
        dialog.remove()

    app = dialog.app
    if app and return_panel_id and hasattr(app, "restore_panel_after_modal"):
        app.restore_panel_after_modal(return_panel_id)


class InputModal(Vertical):
    """Small centered prompt for names and search."""

    can_focus = True

    DEFAULT_CSS = """
    InputModal {
        width: 60;
        height: auto;
        max-width: 90%;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    InputModal .modal-title {
        text-style: bold;
        margin-bottom: 1;
    }

    InputModal .modal-hint {
        color: $text-muted;
        margin-top: 1;
    }

    InputModal .modal-error {
        color: $error;
        margin-top: 1;
        min-height: 1;
    }
    """

    def __init__(
        self,
        title: str,
        placeholder: str = "",
        initial: str = "",
        hint: str = "",
        on_submit=None,
        on_cancel=None,
    ) -> None:
        super().__init__()
        self._title = title
        self._placeholder = placeholder
        self._initial = initial
        self._hint = hint
        self._on_submit = on_submit
        self._on_cancel = on_cancel
        self._error = ""

    def compose(self) -> ComposeResult:
        yield Label(self._title, classes="modal-title")
        yield Input(placeholder=self._placeholder, value=self._initial)
        if self._hint:
            yield Label(self._hint, classes="modal-hint")
        yield Label("", classes="modal-error", id="modal-error")

    def on_mount(self) -> None:
        self.call_after_refresh(self._focus_input)

    def _focus_input(self) -> None:
        self.query_one(Input).focus()

    def _show_error(self, message: str) -> None:
        self._error = message
        self.query_one("#modal-error", Label).update(message)

    def _close(self) -> None:
        _close_modal_dialog(self)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        if self._on_submit and self._on_submit(event.value) is False:
            self._show_error("Name cannot be empty.")
            self._focus_input()
            return
        self._close()

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            event.stop()
            if self._on_cancel:
                self._on_cancel()
            self._close()


class ChoiceModal(Vertical):
    """Pick one item from a vertical list."""

    can_focus = True

    BINDINGS = [
        Binding("enter", "confirm_choice", "Select", show=False, priority=True),
        Binding("escape", "cancel_choice", "Cancel", show=False, priority=True),
    ]

    DEFAULT_CSS = """
    ChoiceModal {
        width: 60;
        height: auto;
        max-height: 80%;
        max-width: 90%;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
        overflow-y: auto;
    }

    ChoiceModal .modal-title {
        text-style: bold;
        margin-bottom: 1;
    }

    ChoiceModal .choice-item {
        padding: 0 1;
    }

    ChoiceModal .choice-item.highlighted {
        background: $accent 40%;
    }

    ChoiceModal .choice-item:hover {
        background: $accent 20%;
    }
    """

    def __init__(
        self,
        title: str,
        choices: list[tuple[str, str]],
        on_pick=None,
        on_cancel=None,
    ) -> None:
        super().__init__()
        self._title = title
        self._choices = choices
        self._index = 0
        self._on_pick = on_pick
        self._on_cancel = on_cancel

    def compose(self) -> ComposeResult:
        yield Label(self._title, classes="modal-title")
        for index, (key, value) in enumerate(self._choices):
            yield Static(
                f"[{key}] {value}",
                classes="choice-item",
                id=f"choice-{index}",
            )

    def on_mount(self) -> None:
        self._highlight()
        self.focus()

    def _highlight(self) -> None:
        for index in range(len(self._choices)):
            item = self.query_one(f"#choice-{index}", Static)
            item.set_class(index == self._index, "highlighted")

    def _close(self) -> None:
        _close_modal_dialog(self)

    def _pick(self, key: str, value: str) -> None:
        if self._on_pick:
            self._on_pick(key, value)
        self._close()

    def action_confirm_choice(self) -> None:
        key, value = self._choices[self._index]
        self._pick(key, value)

    def action_cancel_choice(self) -> None:
        if self._on_cancel:
            self._on_cancel()
        self._close()

    def on_click(self, event: events.Click) -> None:
        widget = event.widget
        if not isinstance(widget, Static) or "choice-item" not in widget.classes:
            return
        widget_id = widget.id or ""
        if not widget_id.startswith("choice-"):
            return
        index = int(widget_id.split("-", 1)[1])
        key, value = self._choices[index]
        self._pick(key, value)

    def on_key(self, event: events.Key) -> None:
        if event.key == "up":
            event.stop()
            self._index = max(0, self._index - 1)
            self._highlight()
            return
        if event.key == "down":
            event.stop()
            self._index = min(len(self._choices) - 1, self._index + 1)
            self._highlight()
            return
        if event.character and len(event.character) == 1 and event.character.isprintable():
            for index, (key, _) in enumerate(self._choices):
                if key.lower() == event.character.lower():
                    _, value = self._choices[index]
                    self._pick(key, value)
                    return
