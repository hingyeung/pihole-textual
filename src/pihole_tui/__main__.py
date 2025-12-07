"""Entry point for running pihole-tui as a module.

Usage:
    python -m pihole_tui
"""

import sys


def main():
    """Main entry point for the application."""
    try:
        from pihole_tui.app import PiHoleTUI

        app = PiHoleTUI()
        app.run()
    except KeyboardInterrupt:
        print("\nExiting Pi-hole TUI...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting Pi-hole TUI: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
