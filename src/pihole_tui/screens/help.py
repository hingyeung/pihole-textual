"""Help screen showing keyboard shortcuts and basic usage."""

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


_HELP_TEXT = """\
[bold]Global[/bold]

  [cyan]F1[/cyan]          This help screen
  [cyan]D[/cyan]           Domain management
  [cyan]Q[/cyan]           Query log
  [cyan]S[/cyan]           Settings
  [cyan]Ctrl+B[/cyan]      Toggle DNS blocking on/off
  [cyan]Ctrl+Q[/cyan]      Quit

[bold]Dashboard[/bold]

  [cyan]F5[/cyan]          Refresh statistics
  [cyan]Escape[/cyan]      Go back

[bold]Query Log[/bold]

  [cyan]Enter[/cyan]       View query details
  [cyan]E[/cyan]           Export filtered queries to CSV
  [cyan]Escape[/cyan]      Go back

[bold]Domain Management[/bold]

  [cyan]A[/cyan]           Add domain
  [cyan]/[/cyan]           Focus search field
  [cyan]T[/cyan]           Toggle enabled/disabled on selected row
  [cyan]Space[/cyan]       Select/deselect row
  [cyan]Ctrl+A[/cyan]      Select all
  [cyan]Ctrl+D[/cyan]      Delete selected
  [cyan]Ctrl+E[/cyan]      Export current list to file
  [cyan]Ctrl+I[/cyan]      Import domains from file
  [cyan]Ctrl+Tab[/cyan]    Switch between Allowlist / Blocklist
  [cyan]Escape[/cyan]      Go back

[bold]Dialogs[/bold]

  [cyan]Enter[/cyan]       Confirm / submit
  [cyan]Escape[/cyan]      Cancel
"""


class HelpScreen(ModalScreen):
    """Modal help screen showing keyboard shortcuts."""

    DEFAULT_CSS = """
    HelpScreen { align: center middle; }

    HelpScreen #dialog {
        width: 60;
        height: auto;
        max-height: 80%;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }

    HelpScreen #title {
        text-style: bold;
        text-align: center;
        width: 100%;
        padding-bottom: 1;
        color: $primary;
    }

    HelpScreen #content {
        height: auto;
        max-height: 30;
        overflow-y: auto;
    }

    HelpScreen #close-btn {
        margin-top: 1;
        width: 100%;
        align: center middle;
    }
    """

    BINDINGS = [("escape,f1", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Keyboard Shortcuts", id="title")
            with VerticalScroll(id="content"):
                yield Static(_HELP_TEXT)
            yield Button("Close  [Esc]", variant="primary", id="close-btn")

    def on_button_pressed(self) -> None:
        self.dismiss()
