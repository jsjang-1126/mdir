from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from textual import events, on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import DataTable, Footer, Static

from mdir import __version__
from mdir.bookmarks import add_bookmark, load_bookmarks, remove_bookmark
from mdir.operations import OperationError, copy_item, delete, mkdir, move_item, rename
from mdir.preview import PreviewPane, is_text_file
from mdir.input_mode import switch_to_english_input
from mdir.shell_history import add_command
from mdir.shell_runner import run_shell_command
from mdir.themes import MDIR_THEMES
from mdir.widgets import CenterModal, ChoiceModal, FilePanel, InputModal, ShellModal, ShellOutputModal


class MdirApp(App):
    """Two-panel terminal file explorer."""

    CSS_PATH = "mdir.tcss"
    TITLE = "mdir"

    BINDINGS = [
        Binding("tab", "switch_panel", "Panel", priority=True),
        Binding("enter", "open_entry", "Open"),
        Binding("backspace,u", "go_up", "Up dir", priority=True),
        Binding("f2", "rename_entry", "Rename"),
        Binding("f5", "copy_entry", "Copy"),
        Binding("f6", "move_entry", "Move"),
        Binding("f7", "mkdir_entry", "Mkdir"),
        Binding("f8", "delete_entry", "Delete"),
        Binding("slash", "search_panel", "Search"),
        Binding("b", "bookmark_menu", "Bookmark"),
        Binding("g", "goto_bookmark", "Go mark"),
        Binding("p", "toggle_preview", "Preview"),
        Binding("v", "edit_vim", "Vim"),
        Binding("n", "edit_nano", "Nano"),
        Binding("s", "shell_panel", "Shell"),
        Binding("r", "refresh_panels", "Refresh"),
        Binding("q", "quit_or_dismiss", "Quit"),
    ]

    def __init__(self, start_path: Path | None = None) -> None:
        super().__init__()
        home = (start_path or Path.cwd()).expanduser().resolve()
        self._left_path = home
        self._right_path = home
        self._active_panel_id = "left-panel"
        self._modal_return_panel_id = "left-panel"
        self._shell_output_mode = False

    def set_shell_output_mode(self, active: bool) -> None:
        """Disable terminal mouse tracking while shell output modal is open."""
        self._shell_output_mode = active
        driver = self._driver
        if driver is None:
            return
        if active:
            if hasattr(driver, "_disable_mouse_support"):
                driver._disable_mouse_support()
            self.capture_mouse(None)
        else:
            if hasattr(driver, "_enable_mouse_support"):
                driver._enable_mouse_support()
            switch_to_english_input()

    def compose(self) -> ComposeResult:
        with Horizontal(id="main-layout"):
            with Horizontal(id="panels"):
                yield FilePanel("left-panel", self._left_path)
                yield FilePanel("right-panel", self._right_path)
            yield PreviewPane(id="preview-pane")
        yield Static("", id="status-bar")
        yield Static(self._help_text(), id="help-bar")
        yield Footer()

    def on_mount(self) -> None:
        self.set_timer(0.05, switch_to_english_input)
        for theme in MDIR_THEMES:
            self.register_theme(theme)
        self._set_active_panel("left-panel")
        self._update_status("Ready")

    def _help_text(self) -> str:
        return (
            "Tab:panel  Enter:open  u:up  s:shell  v:vim  n:nano  F2:rename  F5:copy  F6:move  "
            "F7:mkdir  F8:del  /:search  b:bookmark  g:goto  p:preview  q:quit"
        )

    def _panel(self, panel_id: str) -> FilePanel:
        return self.query_one(f"#{panel_id}", FilePanel)

    def active_panel(self) -> FilePanel:
        return self._panel(self._active_panel_id)

    def inactive_panel(self) -> FilePanel:
        other = "right-panel" if self._active_panel_id == "left-panel" else "left-panel"
        return self._panel(other)

    def _set_active_panel(self, panel_id: str) -> None:
        self._active_panel_id = panel_id
        for pid in ("left-panel", "right-panel"):
            self._panel(pid).active = pid == panel_id
        table = self.query_one(f"#{panel_id}-table", DataTable)
        self.set_focus(table)

    def restore_panel_after_modal(self, panel_id: str) -> None:
        """Return keyboard focus after the last modal closes."""

        def restore() -> None:
            if self._modal_open():
                return
            self._set_active_panel(panel_id)

        self.call_later(restore)
        self.set_timer(0.05, restore)

    def _update_status(self, message: str) -> None:
        panel = self.active_panel()
        entry = panel.selected_entry
        suffix = ""
        if entry:
            suffix = (
                f"  |  {entry.icon} {entry.name}"
                f"  {entry.size_text}"
                f"  {entry.modified_detail_text}"
                f"  {entry.perm_text}"
            )
        self.query_one("#status-bar", Static).update(
            f"mdir v{__version__}  |  {panel.current_path}{suffix}  |  {message}"
        )

    def _update_preview(self, entry_path: Path | None) -> None:
        self.query_one("#preview-pane", PreviewPane).show_path(entry_path)

    def _modal_mount(self, widget: InputModal | ChoiceModal | ShellModal | ShellOutputModal) -> None:
        if not self._modal_open():
            self._modal_return_panel_id = self._active_panel_id
        self.mount(CenterModal(widget, self._modal_return_panel_id))

    @on(FilePanel.SelectionChanged)
    def on_panel_selection(self, event: FilePanel.SelectionChanged) -> None:
        if event.panel.id != self._active_panel_id:
            event.panel.claim_active()
        entry = event.entry
        path = None if entry is None or entry.name == ".." else entry.path
        self._update_preview(path)
        self._update_status("")

    @on(FilePanel.Activated)
    def on_panel_activated(self, event: FilePanel.Activated) -> None:
        if event.entry.is_dir:
            return
        self._open_file(event.entry.path)

    def _modal_open(self) -> bool:
        return bool(self.query("CenterModal"))

    def _guard_modal(self) -> bool:
        return self._modal_open()

    def _dismiss_shell_ui(self) -> bool:
        if self.query("ShellOutputModal"):
            self.query_one(ShellOutputModal).action_dismiss_output()
            return True
        if self.query("ShellModal"):
            self.query_one(ShellModal).action_cancel_shell()
            return True
        return False

    def action_quit_or_dismiss(self) -> None:
        if self._dismiss_shell_ui():
            return
        if self._guard_modal():
            return
        self.exit()

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape" and self._dismiss_shell_ui():
            event.stop()

    def action_switch_panel(self) -> None:
        if self._guard_modal():
            return
        other = "right-panel" if self._active_panel_id == "left-panel" else "left-panel"
        self._set_active_panel(other)
        self._update_status("Switched panel")

    def action_go_up(self) -> None:
        if self._guard_modal():
            return
        self.active_panel().go_up()
        self._update_status("Up")

    def action_open_entry(self) -> None:
        if self._guard_modal():
            return
        panel = self.active_panel()
        entry = panel.selected_entry
        if entry is None:
            return
        if entry.name == ".." or entry.is_dir:
            panel.activate_selection()
            self._update_status("Entered directory")
            return
        self._open_file(entry.path)

    def _selected_text_file(self) -> Path | None:
        panel = self.active_panel()
        entry = panel.selected_entry
        if entry is None or entry.name == ".." or entry.is_dir:
            self._update_status("Select a text file")
            return None
        if not is_text_file(entry.path):
            self._update_status("Not a text file")
            return None
        return entry.path

    def _edit_in_terminal(self, path: Path, editor: str) -> None:
        if shutil.which(editor) is None:
            self._update_status(f"{editor} not installed")
            return

        with self.suspend():
            subprocess.call([editor, str(path)])

        switch_to_english_input()
        self.active_panel().refresh_listing()
        self.inactive_panel().refresh_listing()
        self._update_status(f"Closed {editor}: {path.name}")

    def _run_shell_command(self, folder: Path, command: str) -> None:
        add_command(folder, command)

        if not self._modal_open():
            self._modal_return_panel_id = self._active_panel_id
        self.mount(
            CenterModal(
                ShellOutputModal(folder, command, output=None),
                self._modal_return_panel_id,
                block_mouse=True,
            )
        )
        short = command if len(command) <= 50 else command[:47] + "..."
        self._update_status(f"Shell running: {short}")
        self._execute_shell_command(folder, command)

    @work(thread=True, exclusive=True)
    def _execute_shell_command(self, folder: Path, command: str) -> None:
        _code, output = run_shell_command(folder, command)
        self.call_from_thread(self._finish_shell_command, folder, command, output)

    def _finish_shell_command(self, folder: Path, command: str, output: str) -> None:
        try:
            modal = self.query_one(ShellOutputModal)
            modal.set_output(output)
        except Exception:
            self.set_shell_output_mode(False)

        self.active_panel().refresh_listing()
        self.inactive_panel().refresh_listing()
        short = command if len(command) <= 50 else command[:47] + "..."
        self._update_status(f"Shell done: {short}")

    def action_shell_panel(self) -> None:
        if self._guard_modal():
            return
        folder = self.active_panel().current_path

        def on_execute(command: str) -> None:
            self._run_shell_command(folder, command)

        self._modal_mount(
            ShellModal(
                folder,
                on_execute=on_execute,
                on_cancel=lambda: self._update_status("Shell cancelled"),
            )
        )

    def action_edit_vim(self) -> None:
        if self._guard_modal():
            return
        path = self._selected_text_file()
        if path is not None:
            self._edit_in_terminal(path, "vim")

    def action_edit_nano(self) -> None:
        if self._guard_modal():
            return
        path = self._selected_text_file()
        if path is not None:
            self._edit_in_terminal(path, "nano")

    @work(thread=True)
    def _open_file(self, path: Path) -> None:
        try:
            subprocess.Popen(
                ["xdg-open", str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.call_from_thread(self._update_status, f"Opened {path.name}")
        except OSError as exc:
            self.call_from_thread(self._update_status, f"Open failed: {exc}")

    def action_refresh_panels(self) -> None:
        self.active_panel().refresh_listing()
        self.inactive_panel().refresh_listing()
        self._update_status("Refreshed")

    def action_toggle_preview(self) -> None:
        visible = self.query_one("#preview-pane", PreviewPane).toggle()
        self._update_status("Preview on" if visible else "Preview off")

    def _require_entry(self):
        panel = self.active_panel()
        entry = panel.selected_entry
        if entry is None or entry.name == "..":
            self._update_status("Nothing selected")
            raise OperationError("No selection")
        return panel, entry

    def action_copy_entry(self) -> None:
        try:
            _panel, entry = self._require_entry()
            dest = self.inactive_panel().current_path
            target = copy_item(entry.path, dest)
            self.inactive_panel().refresh_listing()
            self._update_status(f"Copied to {target}")
        except OperationError as exc:
            self._update_status(str(exc))

    def action_move_entry(self) -> None:
        try:
            panel, entry = self._require_entry()
            dest = self.inactive_panel().current_path
            target = move_item(entry.path, dest)
            panel.refresh_listing()
            self.inactive_panel().refresh_listing()
            self._update_status(f"Moved to {target}")
        except OperationError as exc:
            self._update_status(str(exc))

    def action_delete_entry(self) -> None:
        try:
            panel, entry = self._require_entry()
        except OperationError:
            return

        label = entry.name
        choices = [("y", f"Delete {label}"), ("n", "Cancel")]

        def on_pick(key: str, _value: str) -> None:
            if key != "y":
                self._update_status("Delete cancelled")
                return
            try:
                delete(entry.path)
                panel.refresh_listing()
                self._update_status(f"Deleted {label}")
            except OperationError as exc:
                self._update_status(str(exc))

        self._modal_mount(ChoiceModal(f"Delete {label}?", choices, on_pick=on_pick))

    def action_mkdir_entry(self) -> None:
        panel = self.active_panel()

        def on_submit(value: str) -> None:
            try:
                created = mkdir(panel.current_path, value)
                panel.refresh_listing()
                self._update_status(f"Created {created.name}")
            except OperationError as exc:
                self._update_status(str(exc))

        self._modal_mount(InputModal("New directory name", placeholder="folder-name", on_submit=on_submit))

    def action_rename_entry(self) -> None:
        try:
            panel, entry = self._require_entry()
        except OperationError:
            return

        def on_submit(value: str) -> None:
            try:
                target = rename(entry.path, value)
                panel.refresh_listing()
                self._update_status(f"Renamed to {target.name}")
            except OperationError as exc:
                self._update_status(str(exc))

        self._modal_mount(InputModal("Rename", initial=entry.name, on_submit=on_submit))

    def action_search_panel(self) -> None:
        panel = self.active_panel()

        def on_submit(value: str) -> None:
            panel.filter_text = value.strip()
            self._update_status("Filter applied" if panel.filter_text else "Filter cleared")

        def on_cancel() -> None:
            panel.filter_text = ""
            self._update_status("Filter cleared")

        self._modal_mount(
            InputModal(
                "Filter files",
                placeholder="type to filter",
                initial=panel.filter_text,
                on_submit=on_submit,
                on_cancel=on_cancel,
            )
        )

    def action_bookmark_menu(self) -> None:
        if self._guard_modal():
            return
        panel = self.active_panel()
        choices = [
            ("a", f"Add bookmark for {panel.current_path}"),
            ("d", "Delete bookmark"),
            ("c", "Cancel"),
        ]

        def on_pick(key: str, _value: str) -> None:
            if key == "a":
                self._prompt_add_bookmark(panel.current_path)
            elif key == "d":
                self._prompt_delete_bookmark()
            elif key == "c":
                self._update_status("Cancelled")

        self._modal_mount(ChoiceModal("Bookmarks", choices, on_pick=on_pick))

    def _prompt_add_bookmark(self, path: Path) -> None:
        def on_submit(value: str) -> bool:
            name = value.strip()
            if not name:
                return False
            add_bookmark(name, str(path))
            self._update_status(f"Bookmarked '{name}'")
            return True

        self._modal_mount(
            InputModal(
                "Bookmark name",
                placeholder="work, downloads, ...",
                hint="Type a name, then press Enter to save. Esc cancels.",
                on_submit=on_submit,
            )
        )

    def _prompt_delete_bookmark(self) -> None:
        bookmarks = load_bookmarks()
        if not bookmarks:
            self._update_status("No bookmarks")
            return
        choices = [(name, path) for name, path in bookmarks.items()]
        choices.append(("c", "Cancel"))

        def on_pick(key: str, _value: str) -> None:
            if key == "c":
                return
            remove_bookmark(key)
            self._update_status(f"Removed bookmark '{key}'")

        self._modal_mount(ChoiceModal("Delete bookmark", choices, on_pick=on_pick))

    def action_goto_bookmark(self) -> None:
        if self._guard_modal():
            return
        bookmarks = load_bookmarks()
        if not bookmarks:
            self._update_status("No bookmarks")
            return
        choices = [(name, path) for name, path in bookmarks.items()]
        choices.append(("c", "Cancel"))

        def on_pick(key: str, value: str) -> None:
            if key == "c":
                return
            self.active_panel().set_path(Path(value))
            self._update_status(f"Jumped to '{key}'")

        self._modal_mount(ChoiceModal("Go to bookmark", choices, on_pick=on_pick))


def run(start_path: Path | None = None) -> None:
    MdirApp(start_path).run()
