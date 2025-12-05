# Implementation Plan: Pi-hole TUI Management Interface

**Branch**: `001-pihole-tui` | **Date**: 2025-12-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-pihole-tui/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a comprehensive text-based user interface (TUI) for managing Pi-hole network-wide ad blocking, focusing on Phase 1 core features: secure authentication with session management and 2FA support, real-time dashboard with comprehensive statistics, live query log with advanced filtering and export, DNS blocking control with countdown timers, and domain allowlist/blocklist management with bulk operations. The TUI will leverage Pi-hole's v6 REST API using Python and the Textual framework to provide terminal-based access to essential Pi-hole management functions.

## Technical Context

**Language/Version**: Python 3.8+
**Primary Dependencies**: Textual (TUI framework based on Rich), httpx (async HTTP client), cryptography (credential encryption), toml/configparser (configuration management)
**Storage**: Local configuration files (encrypted credentials, user preferences) stored in user home directory (~/.config/pihole-tui/)
**Testing**: pytest (optional, focus on critical path integration tests per constitution)
**Target Platform**: Cross-platform terminal (Linux, macOS, Windows) with minimum 80x24 character display
**Project Type**: Single project (TUI application)
**Performance Goals**: Dashboard refresh <2s, filter operations <500ms, query log pagination <2s, UI responsiveness <200ms for resize/interactions
**Constraints**: Memory usage <150MB, session auto-renewal without user interruption, graceful degradation for network failures, support minimum terminal size 80x24
**Scale/Scope**: Single-user TUI application, manage multiple Pi-hole instances, handle query logs 10,000+ entries, support bulk operations up to 100 domains

**API Architecture**:
- **Base URL**: `http://pi.hole/api/` or `http://<pi-hole-ip>:8080/api/`
- **Authentication**: Session-based using SID (Session ID) obtained via POST to /api/auth
- **Response Format**: JSON for all endpoints
- **Session Management**: SID validity extends on each request; configurable timeout (default 300s)
- **HTTP Methods**: Standard REST (GET, POST, PUT, PATCH, DELETE)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Rapid Prototyping ✅ PASS

**Requirement**: Speed-to-market over perfection; working features over comprehensive documentation

**Assessment**: Phase 1 focuses on core features that deliver immediate value. Five user stories (P1-P5) are independently deliverable, enabling iterative validation. No extensive upfront design required - leverage Textual framework's existing patterns.

**Alignment**: Plan prioritises getting authentication + dashboard working quickly to validate the TUI approach, then incrementally adding features.

### II. Pragmatic Testing ✅ PASS

**Requirement**: Tests are OPTIONAL; manual testing acceptable; focus on critical paths only

**Assessment**: Testing strategy uses pytest for optional integration tests on critical paths (authentication, API communication). Manual testing is primary validation method per constitution. No unit test coverage requirements.

**Alignment**: Testing dependencies listed as optional. Constitution explicitly allows manual testing for personal research project.

### III. Simplicity First ✅ PASS

**Requirement**: YAGNI; avoid abstractions until patterns emerge; prefer straightforward solutions

**Assessment**: Single project structure. Direct API client using httpx (no repository pattern). Leverage Textual's built-in widgets before custom components. Local file storage for config (no database). Five focused features, no speculative functionality.

**Alignment**: No premature abstractions. Straightforward HTTP client → API → Textual UI flow. Configuration in simple encrypted files.

### IV. Textual-First Development ✅ PASS

**Requirement**: Follow Textual's reactive programming model; use built-in widgets; leverage framework patterns

**Assessment**: Primary dependency is Textual framework. Plan explicitly calls for using Textual's widgets (DataTable, Input, Button, etc.), Textual's message passing for component communication, and Textual's CSS for styling.

**Alignment**: Technical approach centers on Textual framework conventions rather than fighting the framework with custom implementations.

### V. Observable Behaviour ✅ PASS

**Requirement**: Focus on user-visible functionality; make state visible and debuggable; clear feedback for actions

**Assessment**: All five user stories focus on observable user outcomes (view dashboard, toggle blocking, filter queries, manage domains). Real-time updates, status indicators, and visual feedback are core requirements. Logging for troubleshooting included.

**Alignment**: Success criteria measured by user-observable behaviour (response times, visual updates, error messages) rather than internal metrics.

### Overall Assessment: ✅ ALL GATES PASSED

No constitution violations. Project structure, testing approach, and technical choices align with all five principles. Proceed to Phase 0 research.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
pihole-textual/
├── src/
│   ├── pihole_tui/
│   │   ├── __init__.py
│   │   ├── __main__.py           # Entry point (python -m pihole_tui)
│   │   ├── app.py                # Main Textual App class
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── client.py         # HTTP client (httpx) + session management
│   │   │   ├── auth.py           # Authentication endpoints
│   │   │   ├── stats.py          # Statistics endpoints
│   │   │   ├── queries.py        # Query log endpoints
│   │   │   ├── blocking.py       # Blocking control endpoints
│   │   │   └── domains.py        # Domain list endpoints
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── config.py         # Configuration models (connection profiles, prefs)
│   │   │   ├── session.py        # Session state model
│   │   │   ├── stats.py          # Statistics data models
│   │   │   ├── query.py          # Query log entry model
│   │   │   ├── blocking.py       # Blocking state model
│   │   │   └── domain.py         # Domain list entry model
│   │   ├── screens/
│   │   │   ├── __init__.py
│   │   │   ├── login.py          # Login/authentication screen
│   │   │   ├── dashboard.py      # Main dashboard screen
│   │   │   ├── query_log.py      # Query log viewer screen
│   │   │   ├── domains.py        # Domain management screen
│   │   │   └── settings.py       # Connection/preferences settings screen
│   │   ├── widgets/
│   │   │   ├── __init__.py
│   │   │   ├── stat_card.py      # Statistics display widget
│   │   │   ├── status_indicator.py # Blocking status widget
│   │   │   ├── query_table.py    # Query log data table
│   │   │   ├── domain_list.py    # Domain list widget
│   │   │   └── countdown_timer.py # Timer widget for temporary disable
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── config_manager.py # Config file read/write with encryption
│   │   │   ├── crypto.py         # Credential encryption utilities
│   │   │   ├── validators.py     # Domain validation, input validation
│   │   │   └── formatters.py     # Data formatters (time, percentages, etc.)
│   │   └── constants.py          # Constants (API paths, defaults, enums)
├── tests/                         # Optional tests per constitution
│   ├── integration/
│   │   ├── test_auth_flow.py     # Authentication integration test
│   │   └── test_api_client.py    # API client integration test
│   └── conftest.py               # pytest fixtures
├── pyproject.toml                # Project metadata & dependencies
├── README.md                     # Setup and usage instructions
└── .gitignore
```

**Structure Decision**: Single project structure selected. TUI application with clear separation of concerns:
- **api/**: Pi-hole REST API client modules (one per endpoint group)
- **models/**: Data models for configuration, session state, and API responses
- **screens/**: Textual screen components (one per major view)
- **widgets/**: Reusable Textual widgets (statistics cards, tables, indicators)
- **utils/**: Supporting utilities (config management, encryption, validation)

Entry point via `python -m pihole_tui` or installed console script. No web frontend or mobile components. Tests are optional and focused on integration paths (auth flow, API communication).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations detected. Complexity tracking not required.
