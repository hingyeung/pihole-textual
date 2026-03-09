"""Domain list widget for displaying allow/blocklist entries.

Provides a DataTable-based widget with:
- Per-row enable/disable toggling
- Multi-select via Space bar, Shift+Click row selection
- Messages emitted for toggle, select, and context actions
"""

from typing import Dict, List, Optional, Set

from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import DataTable, Static

from pihole_tui.models.domain import DomainListEntry


class DomainList(Static):
    """Scrollable table of domain list entries with multi-select support.

    Messages posted:
    - ``DomainList.ToggleRequested``  — user wants to flip enabled for one row
    - ``DomainList.SelectionChanged`` — selected set changed
    - ``DomainList.EditRequested``    — user pressed Enter on a row
    - ``DomainList.DeleteRequested``  — user pressed Delete/Backspace on a row
    """

    DEFAULT_CSS = """
    DomainList {
        height: 1fr;
        width: 100%;
    }

    DomainList DataTable {
        height: 1fr;
        width: 100%;
    }
    """

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    class ToggleRequested(Message):
        """User wants to toggle enabled/disabled for a domain entry."""

        def __init__(self, entry: DomainListEntry) -> None:
            super().__init__()
            self.entry = entry

    class SelectionChanged(Message):
        """The set of selected domain IDs changed."""

        def __init__(self, selected_ids: Set[int]) -> None:
            super().__init__()
            self.selected_ids = selected_ids

    class EditRequested(Message):
        """User wants to edit a domain entry."""

        def __init__(self, entry: DomainListEntry) -> None:
            super().__init__()
            self.entry = entry

    class DeleteRequested(Message):
        """User wants to delete a domain entry."""

        def __init__(self, entry: DomainListEntry) -> None:
            super().__init__()
            self.entry = entry

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    selected_ids: reactive[Set[int]] = reactive(set, always_update=True)

    def __init__(self, entries: Optional[List[DomainListEntry]] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._entries: List[DomainListEntry] = entries or []
        # Map row_key → entry id for fast lookup
        self._row_key_to_id: Dict[str, int] = {}
        self._id_to_entry: Dict[int, DomainListEntry] = {}
        self.selected_ids = set()

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        table: DataTable = DataTable(cursor_type="row", zebra_stripes=True)
        table.add_columns("✓", "Domain", "Status", "Comment", "Added")
        yield table

    def on_mount(self) -> None:
        self._populate()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def load_entries(self, entries: List[DomainListEntry]) -> None:
        """Replace the displayed entries with a new list.

        Args:
            entries: New domain list entries to display.
        """
        self._entries = entries
        self._populate()

    def get_entry(self, domain_id: int) -> Optional[DomainListEntry]:
        """Return the entry for a given domain id, or None."""
        return self._id_to_entry.get(domain_id)

    def get_selected_entries(self) -> List[DomainListEntry]:
        """Return all currently selected entries."""
        return [self._id_to_entry[i] for i in self.selected_ids if i in self._id_to_entry]

    def clear_selection(self) -> None:
        """Deselect all rows."""
        self.selected_ids = set()
        self._refresh_checkboxes()

    def select_all(self) -> None:
        """Select all displayed rows."""
        self.selected_ids = {e.id for e in self._entries}
        self._refresh_checkboxes()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _populate(self) -> None:
        """Clear and re-populate the DataTable from current entries."""
        table = self.query_one(DataTable)
        table.clear()
        self._row_key_to_id.clear()
        self._id_to_entry.clear()
        self.selected_ids = set()

        for entry in self._entries:
            self._id_to_entry[entry.id] = entry
            row_key = str(entry.id)
            self._row_key_to_id[row_key] = entry.id

            checkbox = "☑" if entry.id in self.selected_ids else "☐"
            status = "[green]Enabled[/green]" if entry.enabled else "[red]Disabled[/red]"
            comment = entry.comment or ""
            added = (
                entry.date_added_dt.strftime("%Y-%m-%d") if entry.date_added_dt else "—"
            )
            table.add_row(checkbox, entry.domain, status, comment, added, key=row_key)

    def _refresh_checkboxes(self) -> None:
        """Update only the checkbox column without full repopulate."""
        table = self.query_one(DataTable)
        for row_key, domain_id in self._row_key_to_id.items():
            checkbox = "☑" if domain_id in self.selected_ids else "☐"
            try:
                table.update_cell(row_key, "✓", checkbox)
            except Exception:
                pass  # Row may not exist yet during population

    def _entry_from_cursor(self) -> Optional[DomainListEntry]:
        """Return the entry at the current cursor row."""
        table = self.query_one(DataTable)
        if table.cursor_row < 0 or table.cursor_row >= len(table.rows):
            return None
        try:
            row_key = list(table.rows.keys())[table.cursor_row]
            domain_id = self._row_key_to_id.get(str(row_key.value))
            if domain_id is None:
                return None
            return self._id_to_entry.get(domain_id)
        except (IndexError, AttributeError):
            return None

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Enter pressed on a row — emit EditRequested."""
        domain_id = self._row_key_to_id.get(str(event.row_key.value))
        if domain_id is not None:
            entry = self._id_to_entry.get(domain_id)
            if entry:
                self.post_message(self.EditRequested(entry))

    def on_key(self, event) -> None:
        """Handle keyboard shortcuts for the domain list."""
        table = self.query_one(DataTable)

        if event.key == "space":
            # Toggle selection for the current row
            entry = self._entry_from_cursor()
            if entry:
                new_selected = set(self.selected_ids)
                if entry.id in new_selected:
                    new_selected.discard(entry.id)
                else:
                    new_selected.add(entry.id)
                self.selected_ids = new_selected
                self._refresh_checkboxes()
                self.post_message(self.SelectionChanged(self.selected_ids))
            event.stop()

        elif event.key == "t":
            # Toggle enabled/disabled for the current row
            entry = self._entry_from_cursor()
            if entry:
                self.post_message(self.ToggleRequested(entry))
            event.stop()

        elif event.key in ("delete", "backspace"):
            entry = self._entry_from_cursor()
            if entry:
                self.post_message(self.DeleteRequested(entry))
            event.stop()

        elif event.key == "ctrl+a":
            self.select_all()
            self.post_message(self.SelectionChanged(self.selected_ids))
            event.stop()

        elif event.key == "escape":
            self.clear_selection()
            self.post_message(self.SelectionChanged(self.selected_ids))
            event.stop()
