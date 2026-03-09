"""Domains screen for managing Pi-hole allow and blocklists.

Implements:
- Tabbed view: Allowlist / Blocklist (T080-T082)
- Search/filter bar (T083)
- Add Domain dialog with validation + duplicate detection (T084-T086)
- Edit Domain dialog (T087)
- Delete confirmation dialog (T088)
- Bulk enable / disable / delete (T090-T091)
- Import from file with preview and skip-duplicates (T092-T093)
- Export to text file (T094)
- Ctrl+Tab to switch tabs (T095)
"""

import csv
import logging
from pathlib import Path
from typing import List, Optional, Set

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
    TabbedContent,
    TabPane,
)

from pihole_tui.api.client import NetworkError, PiHoleAPIError
from pihole_tui.api.domains import (
    add_domain,
    delete_domain,
    get_domains,
    patch_domain,
    update_domain,
)
from pihole_tui.constants import DomainListType
from pihole_tui.models.domain import (
    BulkDomainOperation,
    DomainAddRequest,
    DomainImportRequest,
    DomainImportResult,
    DomainListEntry,
    DomainListFilters,
    DomainListResponse,
    DomainUpdateRequest,
)
from pihole_tui.utils.validators import validate_domain
from pihole_tui.widgets.domain_list import DomainList

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------

class AddDomainDialog(ModalScreen):
    """Dialog for adding a new domain to the allow or blocklist.

    Dismisses with a ``DomainAddRequest`` on success, or ``None`` on cancel.
    Validates domain format and reports duplicates from an existing set.
    """

    DEFAULT_CSS = """
    AddDomainDialog { align: center middle; }

    AddDomainDialog #dialog {
        width: 60;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }

    AddDomainDialog #title {
        text-style: bold;
        text-align: center;
        width: 100%;
        padding-bottom: 1;
    }

    AddDomainDialog Label { padding-bottom: 0; }

    AddDomainDialog Input { width: 100%; margin-bottom: 1; }

    AddDomainDialog Select { width: 100%; margin-bottom: 1; }

    AddDomainDialog #error-msg {
        color: $error;
        height: 1;
        padding-bottom: 1;
    }

    AddDomainDialog #buttons {
        layout: horizontal;
        align: center middle;
        height: auto;
        width: 100%;
    }

    AddDomainDialog Button { margin: 0 1; }
    """

    def __init__(
        self,
        existing_domains: Optional[Set[str]] = None,
        initial_list_type: DomainListType = DomainListType.ALLOW,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._existing = existing_domains or set()
        self._initial_type = initial_list_type

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Add Domain", id="title")
            yield Label("Domain (e.g. example.com or *.example.com):")
            yield Input(placeholder="example.com", id="domain-input")
            yield Label("List:")
            yield Select(
                [("Allowlist", "0"), ("Blocklist", "1")],
                value=str(int(self._initial_type)),
                id="list-select",
            )
            yield Label("Comment (optional):")
            yield Input(placeholder="Optional note", id="comment-input")
            yield Checkbox("Enabled", value=True, id="enabled-check")
            yield Label("", id="error-msg")
            with Horizontal(id="buttons"):
                yield Button("Add", variant="primary", id="btn-add")
                yield Button("Cancel", variant="default", id="btn-cancel")

    @on(Button.Pressed, "#btn-add")
    def _add(self) -> None:
        domain = self.query_one("#domain-input", Input).value.strip().lower()
        comment = self.query_one("#comment-input", Input).value.strip() or None
        enabled = self.query_one("#enabled-check", Checkbox).value
        list_select = self.query_one("#list-select", Select)
        list_type = int(list_select.value) if list_select.value else 0
        error_label = self.query_one("#error-msg", Label)

        # Validation
        valid, err = validate_domain(domain)
        if not valid:
            error_label.update(err or "Invalid domain")
            return

        # Duplicate detection
        if domain in self._existing:
            error_label.update("Domain already exists in this list")
            return

        self.dismiss(
            DomainAddRequest(domain=domain, type=list_type, comment=comment, enabled=enabled)
        )

    @on(Input.Submitted)
    def _input_submitted(self) -> None:
        self._add()

    @on(Button.Pressed, "#btn-cancel")
    def _cancel(self) -> None:
        self.dismiss(None)


class EditDomainDialog(ModalScreen):
    """Dialog for editing the comment and enabled status of a domain.

    Dismisses with a ``DomainUpdateRequest`` on save, or ``None`` on cancel.
    """

    DEFAULT_CSS = """
    EditDomainDialog { align: center middle; }

    EditDomainDialog #dialog {
        width: 55;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }

    EditDomainDialog #title { text-style: bold; text-align: center; width: 100%; padding-bottom: 1; }
    EditDomainDialog #domain-display { color: $primary; text-style: bold; padding-bottom: 1; }
    EditDomainDialog Label { padding-bottom: 0; }
    EditDomainDialog Input { width: 100%; margin-bottom: 1; }

    EditDomainDialog #buttons {
        layout: horizontal;
        align: center middle;
        height: auto;
        width: 100%;
    }

    EditDomainDialog Button { margin: 0 1; }
    """

    def __init__(self, entry: DomainListEntry, **kwargs) -> None:
        super().__init__(**kwargs)
        self._entry = entry

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Edit Domain", id="title")
            yield Label(self._entry.domain, id="domain-display")
            yield Label("Comment:")
            yield Input(value=self._entry.comment or "", placeholder="Optional note", id="comment-input")
            yield Checkbox("Enabled", value=self._entry.enabled, id="enabled-check")
            with Horizontal(id="buttons"):
                yield Button("Save", variant="primary", id="btn-save")
                yield Button("Cancel", variant="default", id="btn-cancel")

    @on(Button.Pressed, "#btn-save")
    def _save(self) -> None:
        comment = self.query_one("#comment-input", Input).value.strip() or None
        enabled = self.query_one("#enabled-check", Checkbox).value
        self.dismiss(DomainUpdateRequest(comment=comment, enabled=enabled))

    @on(Button.Pressed, "#btn-cancel")
    def _cancel(self) -> None:
        self.dismiss(None)


class DeleteConfirmDialog(ModalScreen):
    """Confirm deletion of one or more domain entries.

    Dismisses with ``True`` to confirm or ``False`` to cancel.
    """

    DEFAULT_CSS = """
    DeleteConfirmDialog { align: center middle; }

    DeleteConfirmDialog #dialog {
        width: 50;
        height: auto;
        border: solid $error;
        background: $surface;
        padding: 1 2;
    }

    DeleteConfirmDialog #title { text-style: bold; text-align: center; width: 100%; padding-bottom: 1; }
    DeleteConfirmDialog #body { text-align: center; width: 100%; padding-bottom: 1; }

    DeleteConfirmDialog #buttons {
        layout: horizontal;
        align: center middle;
        height: auto;
        width: 100%;
    }

    DeleteConfirmDialog Button { margin: 0 1; }
    """

    def __init__(self, message: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Confirm Delete", id="title")
            yield Label(self._message, id="body")
            with Horizontal(id="buttons"):
                yield Button("Delete", variant="error", id="btn-confirm")
                yield Button("Cancel", variant="default", id="btn-cancel")

    @on(Button.Pressed, "#btn-confirm")
    def _confirm(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#btn-cancel")
    def _cancel(self) -> None:
        self.dismiss(False)


class ImportDialog(ModalScreen):
    """Import domains from a plain-text file (one domain per line).

    Dismisses with a ``DomainImportRequest`` or ``None`` on cancel.
    """

    DEFAULT_CSS = """
    ImportDialog { align: center middle; }

    ImportDialog #dialog {
        width: 65;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }

    ImportDialog #title { text-style: bold; text-align: center; width: 100%; padding-bottom: 1; }
    ImportDialog Label { padding-bottom: 0; }
    ImportDialog Input { width: 100%; margin-bottom: 1; }
    ImportDialog Select { width: 100%; margin-bottom: 1; }

    ImportDialog #preview {
        height: 8;
        border: solid $panel;
        background: $background;
        overflow-y: auto;
        margin-bottom: 1;
        padding: 0 1;
    }

    ImportDialog #error-msg { color: $error; height: 1; padding-bottom: 1; }

    ImportDialog #buttons {
        layout: horizontal;
        align: center middle;
        height: auto;
        width: 100%;
    }

    ImportDialog Button { margin: 0 1; }
    """

    def __init__(self, initial_list_type: DomainListType = DomainListType.ALLOW, **kwargs) -> None:
        super().__init__(**kwargs)
        self._initial_type = initial_list_type
        self._parsed_domains: List[str] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Import Domains from File", id="title")
            yield Label("File path (one domain per line):")
            yield Input(placeholder="/path/to/domains.txt", id="file-input")
            yield Button("Preview", variant="default", id="btn-preview")
            yield Label("Preview (first 20 domains):")
            yield Static("", id="preview")
            yield Label("Import into list:")
            yield Select(
                [("Allowlist", "0"), ("Blocklist", "1")],
                value=str(int(self._initial_type)),
                id="list-select",
            )
            yield Label("Comment to attach (optional):")
            yield Input(placeholder="Imported via TUI", id="comment-input")
            yield Checkbox("Skip duplicates (recommended)", value=True, id="skip-check")
            yield Label("", id="error-msg")
            with Horizontal(id="buttons"):
                yield Button("Import", variant="primary", id="btn-import")
                yield Button("Cancel", variant="default", id="btn-cancel")

    @on(Button.Pressed, "#btn-preview")
    def _preview(self) -> None:
        file_input = self.query_one("#file-input", Input)
        error_label = self.query_one("#error-msg", Label)
        preview_widget = self.query_one("#preview", Static)
        path = Path(file_input.value.strip())

        if not path.exists():
            error_label.update("File not found")
            return

        try:
            lines = path.read_text().splitlines()
            self._parsed_domains = [
                ln.strip().lower() for ln in lines if ln.strip() and not ln.startswith("#")
            ]
            if not self._parsed_domains:
                error_label.update("No valid domains found in file")
                return

            error_label.update("")
            preview_text = "\n".join(self._parsed_domains[:20])
            if len(self._parsed_domains) > 20:
                preview_text += f"\n… and {len(self._parsed_domains) - 20} more"
            preview_widget.update(preview_text)
        except OSError as e:
            error_label.update(f"Cannot read file: {e}")

    @on(Button.Pressed, "#btn-import")
    def _import(self) -> None:
        error_label = self.query_one("#error-msg", Label)
        if not self._parsed_domains:
            error_label.update("Preview the file first")
            return

        list_select = self.query_one("#list-select", Select)
        list_type = DomainListType(int(list_select.value) if list_select.value else 0)
        comment = self.query_one("#comment-input", Input).value.strip() or None
        skip = self.query_one("#skip-check", Checkbox).value

        self.dismiss(
            DomainImportRequest(
                domains=self._parsed_domains,
                list_type=list_type,
                skip_duplicates=skip,
                comment=comment,
            )
        )

    @on(Button.Pressed, "#btn-cancel")
    def _cancel(self) -> None:
        self.dismiss(None)


# ---------------------------------------------------------------------------
# Domains screen
# ---------------------------------------------------------------------------

class DomainsScreen(Screen):
    """Tabbed domain management screen (Allowlist / Blocklist).

    Keyboard shortcuts:
    - ``ctrl+tab`` / ``ctrl+shift+tab`` — switch tabs (T095)
    - ``a``                              — add domain
    - ``/``                              — focus search
    - ``ctrl+a``                         — select all (delegated to widget)
    - ``ctrl+d``                         — delete selected
    - ``ctrl+e``                         — export current list
    - ``ctrl+i``                         — import from file
    """

    BINDINGS = [
        ("ctrl+tab", "next_tab", "Next Tab"),
        ("ctrl+shift+tab", "prev_tab", "Prev Tab"),
        ("a", "add_domain", "Add"),
        ("/", "focus_search", "Search"),
        ("ctrl+d", "delete_selected", "Delete Selected"),
        ("ctrl+e", "export_list", "Export"),
        ("ctrl+i", "import_domains", "Import"),
        ("escape", "go_back", "Back"),
    ]

    DEFAULT_CSS = """
    DomainsScreen { layout: vertical; }

    DomainsScreen #toolbar {
        layout: horizontal;
        height: 5;
        background: $panel;
        padding: 1 1;
        align: left middle;
    }

    DomainsScreen #search-input {
        width: 30;
        margin: 0 1;
    }

    DomainsScreen #toolbar Button { margin: 0 1; }

    DomainsScreen #selection-info {
        width: 1fr;
        content-align: right middle;
        color: $text-muted;
        padding: 0 1;
    }

    DomainsScreen #bulk-bar {
        layout: horizontal;
        height: 5;
        background: $warning 20%;
        padding: 1 1;
        align: left middle;
        display: none;
    }

    DomainsScreen #bulk-bar.visible { display: block; }

    DomainsScreen #bulk-bar Button { margin: 0 1; }

    DomainsScreen TabbedContent { height: 1fr; }

    DomainsScreen TabPane { height: 1fr; padding: 0; }
    """

    def __init__(self, api_client, **kwargs) -> None:
        super().__init__(**kwargs)
        self.api_client = api_client
        self._allow_response: Optional[DomainListResponse] = None
        self._block_response: Optional[DomainListResponse] = None
        self._search_term: str = ""
        self._current_tab: DomainListType = DomainListType.ALLOW

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header()

        # Toolbar
        with Container(id="toolbar"):
            yield Button("+ Add", variant="primary", id="btn-add")
            yield Input(placeholder="Search domains…", id="search-input")
            yield Button("Search", id="btn-search")
            yield Label("", id="selection-info")

        # Bulk action bar (shown when rows are selected)
        with Container(id="bulk-bar"):
            yield Label("Selected: ", id="bulk-label")
            yield Button("Enable", variant="success", id="btn-bulk-enable")
            yield Button("Disable", variant="warning", id="btn-bulk-disable")
            yield Button("Delete", variant="error", id="btn-bulk-delete")
            yield Button("Clear", variant="default", id="btn-bulk-clear")

        # Tabbed content
        with TabbedContent(id="tabs"):
            with TabPane("Allowlist", id="tab-allow"):
                yield DomainList(id="domain-list-allow")
            with TabPane("Blocklist", id="tab-block"):
                yield DomainList(id="domain-list-block")

        yield Footer()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def on_mount(self) -> None:
        await self._load_current_tab()

    # ------------------------------------------------------------------
    # Tab switching — T095
    # ------------------------------------------------------------------

    def action_next_tab(self) -> None:
        tabs = self.query_one(TabbedContent)
        tabs.action_next_tab()

    def action_prev_tab(self) -> None:
        tabs = self.query_one(TabbedContent)
        tabs.action_previous_tab()

    @on(TabbedContent.TabActivated)
    async def _tab_activated(self, event: TabbedContent.TabActivated) -> None:
        # Use TabbedContent.active (the reactive) — more reliable than event.pane.id
        # which can be stale or None depending on the Textual version.
        active_pane_id = self.query_one("#tabs", TabbedContent).active or ""
        self._current_tab = DomainListType.BLOCK if "block" in active_pane_id else DomainListType.ALLOW
        # Clear selection when switching tabs
        self._update_bulk_bar(set())
        await self._load_current_tab()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    async def _load_current_tab(self) -> None:
        """Fetch and display entries for the active tab."""
        # Snapshot _current_tab immediately — self._current_tab can change while
        # we await the API response (race condition between on_mount and TabActivated),
        # which would cause the wrong widget to be updated.
        tab = self._current_tab

        filters = DomainListFilters(list_type=tab)
        try:
            response = await get_domains(self.api_client, filters)
            if tab == DomainListType.ALLOW:
                self._allow_response = response
                widget = self.query_one("#domain-list-allow", DomainList)
            else:
                self._block_response = response
                widget = self.query_one("#domain-list-block", DomainList)

            # Filter client-side since Pi-hole v6 has no search query param
            domains = response.domains
            if self._search_term:
                term = self._search_term.lower()
                domains = [d for d in domains if term in d.domain.lower()]

            widget.load_entries(domains)

            total = response.pagination.total_count
            shown = len(domains)
            if self._search_term and shown != total:
                self.query_one("#selection-info", Label).update(f"{shown}/{total} domain(s)")
            else:
                self.query_one("#selection-info", Label).update(f"{total} domain(s)")

        except (PiHoleAPIError, NetworkError) as e:
            self.notify(f"Failed to load domain list: {e.message}", severity="error", timeout=8)
        except Exception:
            logger.exception("Unexpected error loading domain list")
            self.notify("Failed to load domain list", severity="error", timeout=8)

    def _current_widget(self) -> DomainList:
        if self._current_tab == DomainListType.ALLOW:
            return self.query_one("#domain-list-allow", DomainList)
        return self.query_one("#domain-list-block", DomainList)

    def _existing_domains(self) -> Set[str]:
        """Return the set of domain strings already in the current list (for duplicate detection)."""
        response = self._allow_response if self._current_tab == DomainListType.ALLOW else self._block_response
        if response:
            return {e.domain for e in response.domains}
        return set()

    # ------------------------------------------------------------------
    # Toolbar / search
    # ------------------------------------------------------------------

    @on(Button.Pressed, "#btn-add")
    def _toolbar_add(self) -> None:
        self.action_add_domain()

    @on(Button.Pressed, "#btn-search")
    async def _toolbar_search(self) -> None:
        self._search_term = self.query_one("#search-input", Input).value.strip()
        await self._load_current_tab()

    @on(Input.Submitted, "#search-input")
    async def _search_submitted(self) -> None:
        self._search_term = self.query_one("#search-input", Input).value.strip()
        await self._load_current_tab()

    def action_focus_search(self) -> None:
        self.query_one("#search-input", Input).focus()

    # ------------------------------------------------------------------
    # Add Domain — T084, T085, T086
    # ------------------------------------------------------------------

    def action_add_domain(self) -> None:
        self.run_worker(self._add_domain_worker(), exclusive=True)

    async def _add_domain_worker(self) -> None:
        request: Optional[DomainAddRequest] = await self.app.push_screen(
            AddDomainDialog(
                existing_domains=self._existing_domains(),
                initial_list_type=self._current_tab,
            ),
            wait_for_dismiss=True,
        )
        if request is None:
            return

        try:
            entry = await add_domain(self.api_client, request)
            self.notify(f"Added: {entry.domain}", severity="information", timeout=4)
            await self._load_current_tab()
        except PiHoleAPIError as e:
            if e.status_code == 409:
                self.notify(f"Domain already exists: {request.domain}", severity="warning", timeout=6)
            else:
                self.notify(f"Failed to add domain: {e.message}", severity="error", timeout=8)
        except NetworkError as e:
            self.notify(f"Network error: {e.message}", severity="error", timeout=8)
        except Exception:
            logger.exception("Unexpected error adding domain")
            self.notify("Failed to add domain", severity="error", timeout=8)

    # ------------------------------------------------------------------
    # Edit Domain — T087
    # ------------------------------------------------------------------

    @on(DomainList.EditRequested)
    def _edit_requested(self, event: DomainList.EditRequested) -> None:
        self.run_worker(self._edit_domain_worker(event.entry), exclusive=True)

    async def _edit_domain_worker(self, entry: DomainListEntry) -> None:
        update: Optional[DomainUpdateRequest] = await self.app.push_screen(
            EditDomainDialog(entry),
            wait_for_dismiss=True,
        )
        if update is None:
            return

        try:
            updated = await update_domain(self.api_client, entry, update)
            self.notify(f"Updated: {updated.domain}", severity="information", timeout=4)
            await self._load_current_tab()
        except PiHoleAPIError as e:
            self.notify(f"Failed to update domain: {e.message}", severity="error", timeout=8)
        except NetworkError as e:
            self.notify(f"Network error: {e.message}", severity="error", timeout=8)
        except Exception:
            logger.exception("Unexpected error updating domain")
            self.notify("Failed to update domain", severity="error", timeout=8)

    # ------------------------------------------------------------------
    # Delete Domain — T088
    # ------------------------------------------------------------------

    @on(DomainList.DeleteRequested)
    def _delete_requested(self, event: DomainList.DeleteRequested) -> None:
        self.run_worker(self._delete_single_worker(event.entry), exclusive=True)

    async def _delete_single_worker(self, entry: DomainListEntry) -> None:
        confirmed = await self.app.push_screen(
            DeleteConfirmDialog(f"Delete '{entry.domain}'?"),
            wait_for_dismiss=True,
        )
        if not confirmed:
            return

        try:
            await delete_domain(self.api_client, entry)
            self.notify(f"Deleted: {entry.domain}", severity="information", timeout=4)
            await self._load_current_tab()
        except PiHoleAPIError as e:
            self.notify(f"Failed to delete: {e.message}", severity="error", timeout=8)
        except NetworkError as e:
            self.notify(f"Network error: {e.message}", severity="error", timeout=8)
        except Exception:
            logger.exception("Unexpected error deleting domain")
            self.notify("Failed to delete domain", severity="error", timeout=8)

    # ------------------------------------------------------------------
    # Toggle enabled/disabled (single row — T079)
    # ------------------------------------------------------------------

    @on(DomainList.ToggleRequested)
    def _toggle_requested(self, event: DomainList.ToggleRequested) -> None:
        self.run_worker(self._toggle_worker(event.entry), exclusive=False)

    async def _toggle_worker(self, entry: DomainListEntry) -> None:
        new_state = not entry.enabled
        try:
            await patch_domain(self.api_client, entry, new_state)
            state_str = "enabled" if new_state else "disabled"
            self.notify(f"{entry.domain} {state_str}", timeout=3)
            await self._load_current_tab()
        except (PiHoleAPIError, NetworkError) as e:
            self.notify(f"Toggle failed: {e.message}", severity="error", timeout=8)
        except Exception:
            logger.exception("Unexpected error toggling domain")
            self.notify("Toggle failed", severity="error", timeout=8)

    # ------------------------------------------------------------------
    # Multi-select / bulk actions — T089, T090, T091
    # ------------------------------------------------------------------

    @on(DomainList.SelectionChanged)
    def _selection_changed(self, event: DomainList.SelectionChanged) -> None:
        self._update_bulk_bar(event.selected_ids)

    def _update_bulk_bar(self, selected_ids: Set[int]) -> None:
        bulk_bar = self.query_one("#bulk-bar", Container)
        if selected_ids:
            bulk_bar.add_class("visible")
            self.query_one("#bulk-label", Label).update(f"Selected: {len(selected_ids)}  ")
        else:
            bulk_bar.remove_class("visible")

    @on(Button.Pressed, "#btn-bulk-enable")
    def _bulk_enable(self) -> None:
        entries = self._current_widget().get_selected_entries()
        if entries:
            self.run_worker(self._bulk_toggle_worker(entries, True), exclusive=False)

    @on(Button.Pressed, "#btn-bulk-disable")
    def _bulk_disable(self) -> None:
        entries = self._current_widget().get_selected_entries()
        if entries:
            self.run_worker(self._bulk_toggle_worker(entries, False), exclusive=False)

    @on(Button.Pressed, "#btn-bulk-delete")
    def _bulk_delete_btn(self) -> None:
        self.action_delete_selected()

    @on(Button.Pressed, "#btn-bulk-clear")
    def _bulk_clear(self) -> None:
        self._current_widget().clear_selection()
        self._update_bulk_bar(set())

    def action_delete_selected(self) -> None:
        entries = self._current_widget().get_selected_entries()
        if not entries:
            self.notify("No domains selected", severity="warning", timeout=3)
            return
        self.run_worker(self._bulk_delete_worker(entries), exclusive=True)

    async def _bulk_toggle_worker(
        self, entries: List[DomainListEntry], enabled: bool
    ) -> None:
        """Enable or disable multiple entries sequentially with progress notification."""
        state_str = "Enabling" if enabled else "Disabling"
        self.notify(f"{state_str} {len(entries)} domain(s)…", timeout=3)

        success = 0
        failed = 0
        for entry in entries:
            try:
                await patch_domain(self.api_client, entry, enabled)
                success += 1
            except Exception as e:
                logger.warning(f"Bulk toggle failed for {entry.domain}: {e}")
                failed += 1

        summary = f"{state_str.replace('ing', 'ed')} {success}/{len(entries)}"
        if failed:
            summary += f" ({failed} failed)"
            self.notify(summary, severity="warning", timeout=6)
        else:
            self.notify(summary, severity="information", timeout=4)

        self._current_widget().clear_selection()
        self._update_bulk_bar(set())
        await self._load_current_tab()

    async def _bulk_delete_worker(self, entries: List[DomainListEntry]) -> None:
        """Delete multiple entries after confirmation."""
        confirmed = await self.app.push_screen(
            DeleteConfirmDialog(f"Delete {len(entries)} selected domain(s)?"),
            wait_for_dismiss=True,
        )
        if not confirmed:
            return

        self.notify(f"Deleting {len(entries)} domain(s)…", timeout=3)
        success = 0
        failed = 0
        for entry in entries:
            try:
                await delete_domain(self.api_client, entry)
                success += 1
            except Exception as e:
                logger.warning(f"Bulk delete failed for {entry.domain}: {e}")
                failed += 1

        summary = f"Deleted {success}/{len(entries)}"
        if failed:
            summary += f" ({failed} failed)"
            self.notify(summary, severity="warning", timeout=6)
        else:
            self.notify(summary, severity="information", timeout=4)

        self._current_widget().clear_selection()
        self._update_bulk_bar(set())
        await self._load_current_tab()

    # ------------------------------------------------------------------
    # Import — T092, T093
    # ------------------------------------------------------------------

    def action_import_domains(self) -> None:
        self.run_worker(self._import_worker(), exclusive=True)

    async def _import_worker(self) -> None:
        request: Optional[DomainImportRequest] = await self.app.push_screen(
            ImportDialog(initial_list_type=self._current_tab),
            wait_for_dismiss=True,
        )
        if request is None:
            return

        result = DomainImportResult(total=len(request.domains))
        self.notify(f"Importing {result.total} domain(s)…", timeout=4)

        for raw_domain in request.domains:
            domain = raw_domain.strip().lower()
            if not domain:
                continue

            valid, _ = validate_domain(domain)
            if not valid:
                result.failed += 1
                result.errors.append(f"Invalid: {domain}")
                continue

            try:
                add_req = DomainAddRequest(
                    domain=domain,
                    type=int(request.list_type),
                    comment=request.comment,
                    enabled=True,
                )
                await add_domain(self.api_client, add_req)
                result.added += 1
            except PiHoleAPIError as e:
                if e.status_code == 409 and request.skip_duplicates:
                    result.skipped_duplicate += 1
                else:
                    result.failed += 1
                    result.errors.append(f"{domain}: {e.message}")
            except Exception as e:
                result.failed += 1
                result.errors.append(f"{domain}: {e}")

        summary = (
            f"Import done: {result.added} added, "
            f"{result.skipped_duplicate} skipped, {result.failed} failed"
        )
        severity = "warning" if result.failed else "information"
        self.notify(summary, severity=severity, timeout=8)
        await self._load_current_tab()

    # ------------------------------------------------------------------
    # Export — T094
    # ------------------------------------------------------------------

    def action_export_list(self) -> None:
        self.run_worker(self._export_worker(), exclusive=True)

    async def _export_worker(self) -> None:
        response = (
            self._allow_response
            if self._current_tab == DomainListType.ALLOW
            else self._block_response
        )
        if not response or not response.domains:
            self.notify("No domains to export", severity="warning", timeout=4)
            return

        list_name = "allowlist" if self._current_tab == DomainListType.ALLOW else "blocklist"
        export_path = Path.home() / f"pihole-{list_name}.txt"

        try:
            lines = [e.domain for e in response.domains]
            export_path.write_text("\n".join(lines) + "\n")
            self.notify(
                f"Exported {len(lines)} domain(s) to {export_path}",
                severity="information",
                timeout=6,
            )
        except OSError as e:
            self.notify(f"Export failed: {e}", severity="error", timeout=8)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def action_go_back(self) -> None:
        self.app.pop_screen()
