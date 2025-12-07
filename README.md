# Pi-hole TUI

A comprehensive terminal user interface (TUI) for managing Pi-hole network-wide ad blocking.

## Features

- **Secure Authentication**: Connect to Pi-hole with session management and 2FA support
- **Real-time Dashboard**: View comprehensive statistics with auto-refresh
- **Query Log Viewer**: Browse and filter DNS queries with advanced search
- **Blocking Control**: Enable/disable DNS blocking with countdown timers
- **Domain Management**: Manage allowlist and blocklist with bulk operations

## Requirements

- Python 3.8 or higher
- Pi-hole v6.0 or higher with REST API enabled
- Terminal with minimum 80x24 character display

## Installation

### From Source

```bash
# Clone the repository
git clone <repository-url>
cd pihole-textual

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Development Installation

```bash
# Install with development dependencies
pip install -e ".[dev]"
```

## Usage

### Launch the TUI

```bash
# Using the installed command
pihole-tui

# Or using Python module
python -m pihole_tui
```

### First-Time Setup

1. Launch the TUI
2. Enter your Pi-hole hostname/IP address and port (default: 8080)
3. Enter your admin password
4. Optionally enable "Remember credentials" for auto-login
5. If 2FA is enabled, enter your TOTP code when prompted

### Keyboard Shortcuts

- `Q` - Navigate to Query Log
- `D` - Navigate to Domain Management
- `S` - Open Settings
- `Ctrl+B` - Quick toggle blocking on/off
- `F1` - Help screen
- `F5` - Manual refresh (on dashboard)
- `Ctrl+C` - Exit application
- `Tab` - Navigate between fields
- `Ctrl+Tab` - Switch between tabs (in domain management)

## Configuration

Configuration files are stored in:
- Linux/macOS: `~/.config/pihole-tui/`
- Windows: `%APPDATA%\pihole-tui\`

### Files

- `config.toml` - User preferences (refresh intervals, display settings)
- `connections.enc` - Encrypted connection profiles (credentials stored securely)
- `pihole-tui.log` - Application logs for debugging

## Manual Testing

See `specs/001-pihole-tui/quickstart.md` for comprehensive manual testing scenarios covering all features.

## Development

### Project Structure

```
src/pihole_tui/
├── api/          # Pi-hole REST API client modules
├── models/       # Data models (Pydantic)
├── screens/      # Textual screen components
├── widgets/      # Reusable UI widgets
└── utils/        # Utilities (config, crypto, validation)
```

### Running Tests (Optional)

```bash
# Tests are optional per project constitution
pytest
```

## Performance Targets

- Dashboard refresh: < 2 seconds
- Filter operations: < 500ms
- Query log pagination: < 2 seconds
- UI responsiveness: < 200ms for resize/interactions
- Memory usage: < 150MB during normal operation

## Troubleshooting

### Connection Issues

- Verify Pi-hole is accessible at the configured hostname/port
- Check that Pi-hole API is enabled (v6+ required)
- Ensure your admin password is correct

### Session Expiry

- Sessions auto-renew every 4 minutes (at 80% of validity period)
- If session expires, you'll be prompted to re-authenticate

### Logs

Check `~/.config/pihole-tui/pihole-tui.log` for detailed error messages.

## License

MIT
