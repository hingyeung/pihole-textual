# Technical Research: Pi-hole TUI Management Interface

**Feature**: Pi-hole TUI Management Interface
**Date**: 2025-12-05
**Purpose**: Document technical decisions and research findings for Phase 1 implementation

## TUI Framework Selection

### Decision: Textual

**Rationale**:
- **Modern Python TUI framework**: Built on Rich library, provides reactive programming model with async support
- **Widget library**: Comprehensive built-in widgets (DataTable, Input, Button, Header, Footer, etc.) reduce custom component development
- **CSS-like styling**: Textual CSS system allows separation of style from logic
- **Active development**: Well-maintained with strong community support and documentation
- **Terminal compatibility**: Works across platforms (Linux, macOS, Windows) with graceful degradation
- **Message-driven architecture**: Fits reactive pattern needed for real-time updates (dashboard stats, query log)

**Alternatives Considered**:
- **curses/ncurses**: Too low-level, would require significant custom widget development
- **urwid**: Mature but less modern API, lacks built-in async support
- **blessed**: Simpler but limited widget library, would need more custom development
- **Rich alone**: Great for static rendering but lacks interactive TUI components

## HTTP Client Selection

### Decision: httpx

**Rationale**:
- **Async support**: Native async/await for non-blocking API calls (essential for responsive TUI with real-time updates)
- **Modern API**: Similar to requests but with async capabilities
- **HTTP/2 support**: Future-proof for potential Pi-hole API upgrades
- **Connection pooling**: Efficient for multiple API calls with session reuse
- **Type hints**: Better IDE support and type safety

**Alternatives Considered**:
- **requests**: Synchronous only, would block TUI during API calls
- **aiohttp**: More low-level, httpx provides better high-level API similar to requests
- **urllib**: Standard library but too low-level for this use case

## Credential Encryption

###Decision: cryptography library (Fernet symmetric encryption)

**Rationale**:
- **Standard library**: Widely used, well-audited encryption library
- **Symmetric encryption**: Appropriate for local credential storage (no key exchange needed)
- **Fernet recipe**: Simple, secure encryption with authentication (AES 128 in CBC mode with HMAC)
- **Key derivation**: Use PBKDF2 to derive encryption key from user's Pi-hole password or system-specific key
- **File-based storage**: Encrypted credentials in `~/.config/pihole-tui/connections.enc`

**Alternatives Considered**:
- **keyring/keychain**: System keychain integration complex, platform-dependent
- **plaintext**: Unacceptable security risk
- **Base64 encoding**: Not encryption, provides no security

## Configuration Storage

### Decision: TOML format with encrypted credential section

**Rationale**:
- **Human-readable**: Easy to edit for non-sensitive settings (refresh intervals, display preferences)
- **Python support**: toml library for parsing, simple to work with
- **Separate encrypted file**: Store encrypted credentials in separate `.enc` file for security
- **Location**: `~/.config/pihole-tui/` follows XDG Base Directory specification
- **Structure**:
  - `config.toml`: Non-sensitive preferences (refresh rates, UI settings)
  - `connections.enc`: Encrypted connection profiles (hostname, port, password, SID)

**Alternatives Considered**:
- **JSON**: Less human-readable, no comment support
- **INI**: Less structured, harder to represent nested data
- **YAML**: Overkill for simple config, security concerns with parsing

## Session Management Strategy

### Decision: Background auto-renewal with SID caching

**Rationale**:
- **SID validity**: Pi-hole sessions expire but extend on use (default 300s timeout)
- **Auto-renewal**: Background task checks SID expiry and renews before timeout (at 80% of validity period)
- **Graceful degradation**: If renewal fails, prompt for re-authentication without losing UI state
- **Multiple instances**: Support multiple saved connections, active session tracked per profile
- **Implementation**: Textual's `set_interval()` for periodic renewal checks

**Alternatives Considered**:
- **Manual renewal**: Poor UX, interrupts user workflow
- **Renew on every request**: Unnecessary API overhead
- **No renewal**: Sessions would expire frequently, requiring frequent re-login

## Real-time Updates Approach

### Decision: Polling with configurable intervals

**Rationale**:
- **Pi-hole API**: No WebSocket or SSE support, polling is only option for real-time updates
- **Configurable intervals**: User-selectable (5s, 10s, 30s, 60s) balances responsiveness vs API load
- **Screen-specific polling**: Only active screen polls (dashboard polls stats, query log polls queries)
- **Efficient filtering**: Use API query parameters to fetch only new/changed data where supported
- **Implementation**: Textual's reactive properties and `set_interval()` for scheduled updates

**Alternatives Considered**:
- **WebSockets**: Not supported by Pi-hole v6 API
- **Long polling**: Not supported by Pi-hole v6 API
- **Event-driven**: Would require Pi-hole API changes

## Data Model Strategy

### Decision: Pydantic models for validation and serialisation

**Rationale**:
- **Type safety**: Pydantic enforces types at runtime, catches API response inconsistencies
- **Validation**: Automatic validation of API responses and user input
- **JSON serialisation**: Built-in JSON encoding/decoding for API communication
- **IDE support**: Type hints improve autocomplete and error detection
- **Documentation**: Models serve as self-documenting contracts for data structures

**Alternatives Considered**:
- **dataclasses**: Less validation, no automatic JSON handling
- **Plain dicts**: No type safety, error-prone
- **attrs**: Good alternative but Pydantic more common in API-heavy projects

## Query Log Pagination Strategy

### Decision: Server-side pagination with virtual scrolling

**Rationale**:
- **API support**: Pi-hole /api/queries supports `page` and `limit` parameters
- **Memory efficiency**: Load only visible page of queries (default 50 per page)
- **Virtual scrolling**: Textual DataTable supports lazy loading, fetch pages as user scrolls
- **Filter preservation**: Apply filters server-side via API parameters (blocked, client, time range)
- **Performance**: Handles large query logs (10,000+ entries) without loading all into memory

**Alternatives Considered**:
- **Client-side pagination**: Would require fetching entire log, memory-intensive
- **Infinite scroll with local cache**: Complex caching logic, potential stale data issues
- **Fixed page size**: Less flexible, virtual scrolling provides better UX

## Domain Bulk Operations Strategy

### Decision: Sequential API calls with progress indication

**Rationale**:
- **API limitation**: Pi-hole API doesn't support bulk domain operations in single request
- **User feedback**: Progress bar shows operation status during bulk add/delete/enable/disable
- **Error handling**: Continue on individual failures, report errors at end
- **Transaction safety**: Each API call is independent, partial completion is acceptable
- **Limit**: Cap bulk operations at 100 domains to prevent API overload

**Alternatives Considered**:
- **Parallel requests**: Risk overwhelming Pi-hole API, no rate limiting info available
- **Single large payload**: API doesn't support bulk operations
- **Background processing**: Adds complexity, user needs immediate feedback

## Error Handling Philosophy

### Decision: User-friendly messages with fallback states

**Rationale**:
- **Constitution principle**: Observable behaviour over internal correctness
- **Clear errors**: Translate API errors to actionable user messages (eg. "Connection failed. Check Pi-hole address and port." vs raw httpx exception)
- **Graceful degradation**: Show last successful data with "stale data" indicator if refresh fails
- **Retry logic**: Automatic retry for transient failures (network timeouts) with exponential backoff
- **Logging**: Detailed errors logged for troubleshooting, concise messages shown to user

**Alternatives Considered**:
- **Silent failures**: Poor UX, user unaware of issues
- **Technical error messages**: Confusing for non-technical users
- **Aggressive retries**: Could hammer failing API

## Development Dependencies

### Core Dependencies:
- **textual**: TUI framework (version >=0.40.0 for latest features)
- **httpx**: Async HTTP client
- **cryptography**: Credential encryption
- **pydantic**: Data validation and modelling
- **tomli/toml**: TOML configuration parsing (tomli for Python <3.11, toml for >=3.11)

### Optional Dependencies:
- **pytest**: Integration testing (per constitution, optional)
- **pytest-asyncio**: Async test support
- **rich**: Enhanced terminal output (already dependency of textual)

### Development Tools:
- **black**: Code formatting (if desired)
- **mypy**: Type checking (optional, for type safety verification)

## Summary of Key Decisions

| Area | Decision | Primary Rationale |
|------|----------|-------------------|
| TUI Framework | Textual | Modern reactive framework with built-in widgets and async support |
| HTTP Client | httpx | Async support essential for non-blocking API calls |
| Encryption | Fernet (cryptography) | Secure symmetric encryption for local credential storage |
| Configuration | TOML + encrypted file | Human-readable config, secure credential storage |
| Session Management | Auto-renewal with caching | Transparent renewal prevents session expiry interruptions |
| Real-time Updates | Polling (configurable) | Only option given Pi-hole API capabilities |
| Data Models | Pydantic | Type safety and validation for API interactions |
| Pagination | Server-side with virtual scroll | Memory efficient, handles large datasets |
| Bulk Operations | Sequential with progress | User feedback, handles API limitations |
| Error Handling | User-friendly with fallback | Constitution principle: observable behaviour |

## Risk Mitigation

**Risk**: Pi-hole API changes breaking client compatibility
- **Mitigation**: Graceful error handling, version checking on connect (future enhancement)

**Risk**: Credential encryption key loss
- **Mitigation**: Warn user about key backup, provide clear re-setup flow

**Risk**: Poor performance with large query logs
- **Mitigation**: Server-side pagination, configurable page size, efficient filtering

**Risk**: Session expiry during critical operations
- **Mitigation**: Auto-renewal before expiry, re-auth prompt if operation fails

**Risk**: Network latency making TUI unresponsive
- **Mitigation**: Async operations, loading indicators, timeout configuration

## Future Considerations (Out of Phase 1 Scope)

- WebSocket support if Pi-hole API adds real-time capabilities
- Offline mode with cached data
- Multiple Pi-hole instance aggregated dashboard
- Plugin system for custom widgets
- Theme customisation beyond Textual defaults

These are explicitly deferred per constitution's YAGNI principle - implement only when proven necessary.
