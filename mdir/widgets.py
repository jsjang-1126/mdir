from __future__ import annotations

from pathlib import Path

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, ScrollableContainer, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import DataTable, Input, Label, Static

from mdir.models import FileEntry, list_directory
from mdir.shell_history import get_history, remove_command_at


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

    def claim_active(self) -> None:
        """Tell the app this panel is active (mouse click / table focus)."""
        app = self.app
        if app is None or not self.id:
            return
        set_active = getattr(app, "_set_active_panel", None)
        if callable(set_active):
            set_active(self.id)

    def on_click(self, event: events.Click) -> None:
        self.claim_active()

    def on_descendant_focus(self, event: events.DescendantFocus) -> None:
        if event.control is self._table:
            self.claim_active()


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

    def __init__(self, dialog: Vertical, return_panel_id: str, *, block_mouse: bool = False) -> None:
        super().__init__()
        self._dialog = dialog
        self._return_panel_id = return_panel_id
        self._block_mouse = block_mouse

    def compose(self) -> ComposeResult:
        yield self._dialog

    def _stop_mouse(self, event: events.Event) -> None:
        event.stop()

    def on_mouse_down(self, event: events.MouseDown) -> None:
        if self._block_mouse:
            self._stop_mouse(event)

    def on_mouse_up(self, event: events.MouseUp) -> None:
        if self._block_mouse:
            self._stop_mouse(event)

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if self._block_mouse:
            self._stop_mouse(event)

    def on_mouse_scroll_down(self, event: events.MouseScrollDown) -> None:
        if self._block_mouse:
            self._stop_mouse(event)

    def on_mouse_scroll_up(self, event: events.MouseScrollUp) -> None:
        if self._block_mouse:
            self._stop_mouse(event)

    def on_mouse_scroll_left(self, event: events.MouseScrollLeft) -> None:
        if self._block_mouse:
            self._stop_mouse(event)

    def on_mouse_scroll_right(self, event: events.MouseScrollRight) -> None:
        if self._block_mouse:
            self._stop_mouse(event)


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


class ShellCommandInput(Input):
    """Shell command line; Esc closes the shell modal."""

    def on_key(self, event: events.Key) -> None:
        if event.key != "escape":
            return
        event.stop()
        parent = self.parent
        while parent is not None and not isinstance(parent, ShellModal):
            parent = parent.parent
        if isinstance(parent, ShellModal):
            parent.action_cancel_shell()


class ShellModal(Vertical):
    """Run a shell command in the active panel directory."""

    can_focus = True

    BINDINGS = [
        Binding("escape", "cancel_shell", "Cancel", show=False, priority=True),
        Binding("tab", "toggle_focus", "Focus", show=False, priority=True),
    ]

    DEFAULT_CSS = """
    ShellModal {
        width: 72;
        height: auto;
        max-height: 85%;
        max-width: 95%;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    ShellModal .modal-title {
        text-style: bold;
        margin-bottom: 1;
    }

    ShellModal .modal-hint {
        color: $text-muted;
        margin: 1 0;
    }

    ShellModal .history-list {
        height: auto;
        max-height: 14;
        overflow-y: auto;
        border: solid $panel;
        padding: 0 1;
        margin-bottom: 1;
    }

    ShellModal .history-empty {
        color: $text-muted;
        padding: 0 1;
    }

    ShellModal .history-item {
        padding: 0 1;
    }

    ShellModal .history-item.highlighted {
        background: $accent 40%;
    }

    ShellModal .history-item:hover {
        background: $accent 20%;
    }

    ShellModal .modal-error {
        color: $error;
        min-height: 1;
    }
    """

    def __init__(
        self,
        folder: Path,
        on_execute=None,
        on_cancel=None,
    ) -> None:
        super().__init__()
        self._folder = folder
        self._commands = get_history(folder)
        self._index = max(0, len(self._commands) - 1)
        self._history_focus = bool(self._commands)
        self._on_execute = on_execute
        self._on_cancel = on_cancel

    def compose(self) -> ComposeResult:
        yield Label(f"Shell — {self._folder}", classes="modal-title")
        with Vertical(id="history-list", classes="history-list"):
            yield from self._compose_history_items()
        yield Label(
            "↑↓ history  Enter run  Del remove  Tab input  Esc close",
            classes="modal-hint",
        )
        yield ShellCommandInput(placeholder="shell command...", id="shell-input")
        yield Label("", classes="modal-error", id="shell-error")

    def _compose_history_items(self) -> ComposeResult:
        if not self._commands:
            yield Label("(no history yet)", classes="history-empty")
            return
        for index, command in enumerate(self._commands):
            yield Static(command, classes="history-item", id=f"history-{index}")

    def on_mount(self) -> None:
        self._highlight_history()
        self.call_after_refresh(self._apply_focus)

    def _apply_focus(self) -> None:
        if self._history_focus and self._commands:
            self.focus()
            return
        self.query_one("#shell-input", Input).focus()

    def _highlight_history(self) -> None:
        if not self._commands:
            return
        for index in range(len(self._commands)):
            item = self.query_one(f"#history-{index}", Static)
            item.set_class(index == self._index, "highlighted")

    def _rebuild_history(self) -> None:
        container = self.query_one("#history-list", Vertical)
        container.remove_children()
        for widget in self._compose_history_items():
            container.mount(widget)
        if self._commands:
            self._index = min(self._index, len(self._commands) - 1)
            self._history_focus = True
        else:
            self._index = 0
            self._history_focus = False
        self._highlight_history()
        self._apply_focus()

    def _show_error(self, message: str) -> None:
        self.query_one("#shell-error", Label).update(message)

    def _close(self) -> None:
        _close_modal_dialog(self)

    def _execute(self, command: str) -> None:
        command = command.strip()
        if not command:
            self._show_error("Command cannot be empty.")
            self.query_one("#shell-input", Input).focus()
            return
        callback = self._on_execute
        self._close()
        if callback:
            callback(command)

    def action_cancel_shell(self) -> None:
        if self._on_cancel:
            self._on_cancel()
        self._close()

    def action_toggle_focus(self) -> None:
        if not self._commands:
            self.query_one("#shell-input", Input).focus()
            return
        self._history_focus = not self._history_focus
        self._apply_focus()

    def _delete_selected(self) -> None:
        if not self._commands:
            return
        remove_command_at(self._folder, self._index)
        self._commands = get_history(self._folder)
        self._rebuild_history()
        self.query_one("#shell-error", Label).update("")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "shell-input":
            return
        event.stop()
        self._execute(event.value)

    def on_click(self, event: events.Click) -> None:
        widget = event.widget
        if not isinstance(widget, Static) or "history-item" not in widget.classes:
            return
        widget_id = widget.id or ""
        if not widget_id.startswith("history-"):
            return
        index = int(widget_id.split("-", 1)[1])
        self._index = index
        self._history_focus = True
        self._highlight_history()
        self._execute(self._commands[index])

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            event.stop()
            self.action_cancel_shell()
            return

        input_widget = self.query_one("#shell-input", Input)
        if input_widget.has_focus:
            if event.key == "up" and not input_widget.value:
                event.stop()
                if self._commands:
                    self._history_focus = True
                    self._index = len(self._commands) - 1
                    self._highlight_history()
                    self.focus()
                return
            return

        if not self._commands:
            return

        if event.key == "up":
            event.stop()
            self._index = max(0, self._index - 1)
            self._highlight_history()
            return
        if event.key == "down":
            event.stop()
            if self._index >= len(self._commands) - 1:
                self._history_focus = False
                input_widget.focus()
                return
            self._index = min(len(self._commands) - 1, self._index + 1)
            self._highlight_history()
            return
        if event.key == "enter":
            event.stop()
            self._execute(self._commands[self._index])
            return
        if event.key == "delete":
            event.stop()
            self._delete_selected()
            return


class ShellOutputModal(Vertical):
    """Scrollable shell command output."""

    can_focus = True
    can_focus_children = False

    BINDINGS = [
        Binding("q", "dismiss_output", "Close", show=False, priority=True),
        Binding("escape", "dismiss_output", "Close", show=False, priority=True),
        Binding("up,k", "scroll_output_up", "Up", show=False, priority=True),
        Binding("down,j", "scroll_output_down", "Down", show=False, priority=True),
        Binding("pageup", "scroll_output_page_up", "Page Up", show=False, priority=True),
        Binding("pagedown", "scroll_output_page_down", "Page Down", show=False, priority=True),
    ]

    DEFAULT_CSS = """
    ShellOutputModal {
        width: 90%;
        height: 85%;
        max-width: 120;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    ShellOutputModal .output-title {
        text-style: bold;
        margin-bottom: 1;
    }

    ShellOutputModal .output-meta {
        color: $text-muted;
        margin-bottom: 1;
    }

    ShellOutputModal #output-scroll {
        height: 1fr;
        min-height: 10;
        overflow-y: auto;
        border: solid $panel;
        background: $background;
        padding: 0 1;
    }

    ShellOutputModal .output-body {
        width: 1fr;
        height: auto;
    }

    ShellOutputModal .output-footer {
        height: 1;
        color: $warning;
        text-style: bold;
        margin-top: 1;
        background: $panel;
        padding: 0 1;
    }
    """

    _FOOTER_READY = "↑↓ j/k  PgUp/PgDn: scroll   q / Esc: close"
    _FOOTER_WAIT = "Running command... please wait"

    def __init__(self, folder: Path, command: str, output: str | None = None) -> None:
        super().__init__()
        self._folder = folder
        self._command = command
        self._output = output
        self._ready = output is not None

    def compose(self) -> ComposeResult:
        yield Label(f"$ {self._command}", classes="output-title")
        yield Label(str(self._folder), classes="output-meta")
        with ScrollableContainer(id="output-scroll", can_focus=False):
            text = self._output if self._output is not None else "Running command, please wait..."
            yield Static(text, classes="output-body", id="output-text")
        footer = self._FOOTER_READY if self._ready else self._FOOTER_WAIT
        yield Label(footer, classes="output-footer", id="output-footer")

    def on_mount(self) -> None:
        app = self.app
        if hasattr(app, "set_shell_output_mode"):
            app.set_shell_output_mode(True)
        self.focus()
        if self._ready:
            self.call_after_refresh(self._mark_ready)

    def on_unmount(self) -> None:
        app = self.app
        if hasattr(app, "set_shell_output_mode"):
            app.set_shell_output_mode(False)

    def set_output(self, output: str) -> None:
        self._output = output
        self.query_one("#output-text", Static).update(output)
        self.query_one("#output-footer", Label).update(self._FOOTER_READY)
        self._ready = False
        self.call_after_refresh(self._mark_ready)

    def _mark_ready(self) -> None:
        self._ready = True
        self.focus()

    def _output_scroll(self) -> ScrollableContainer:
        return self.query_one("#output-scroll", ScrollableContainer)

    def action_scroll_output_up(self) -> None:
        if not self._ready:
            return
        self._output_scroll().scroll_up(animate=False, force=True)

    def action_scroll_output_down(self) -> None:
        if not self._ready:
            return
        self._output_scroll().scroll_down(animate=False, force=True)

    def action_scroll_output_page_up(self) -> None:
        if not self._ready:
            return
        self._output_scroll().scroll_page_up(animate=False, force=True)

    def action_scroll_output_page_down(self) -> None:
        if not self._ready:
            return
        self._output_scroll().scroll_page_down(animate=False, force=True)

    def action_dismiss_output(self) -> None:
        _close_modal_dialog(self)

    def on_key(self, event: events.Key) -> None:
        if event.key in ("q", "escape"):
            event.stop()
            if self._ready or self._output is None:
                self.action_dismiss_output()
            return
        if not self._ready:
            return
        if event.key in ("up", "k"):
            event.stop()
            self.action_scroll_output_up()
            return
        if event.key in ("down", "j"):
            event.stop()
            self.action_scroll_output_down()
            return
        if event.key == "pageup":
            event.stop()
            self.action_scroll_output_page_up()
            return
        if event.key == "pagedown":
            event.stop()
            self.action_scroll_output_page_down()
            return

    def _stop_mouse(self, event: events.Event) -> None:
        event.stop()

    def on_mouse_down(self, event: events.MouseDown) -> None:
        self._stop_mouse(event)

    def on_mouse_up(self, event: events.MouseUp) -> None:
        self._stop_mouse(event)

    def on_mouse_move(self, event: events.MouseMove) -> None:
        self._stop_mouse(event)

    def on_mouse_scroll_down(self, event: events.MouseScrollDown) -> None:
        self._stop_mouse(event)

    def on_mouse_scroll_up(self, event: events.MouseScrollUp) -> None:
        self._stop_mouse(event)

    def on_mouse_scroll_left(self, event: events.MouseScrollLeft) -> None:
        self._stop_mouse(event)

    def on_mouse_scroll_right(self, event: events.MouseScrollRight) -> None:
        self._stop_mouse(event)
