# Feature Specification: Pi-hole TUI Management Interface

**Feature Branch**: `001-pihole-tui`
**Created**: 2025-12-05
**Status**: Draft
**Input**: User description: "This project aims to create a comprehensive text-based user interface (TUI) using Python and Textual library for managing Pi-hole network-wide ad blocking. The interface will leverage Pi-hole's v6 REST API, which is embedded directly in the pihole-FTL binary."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Authenticate and Connect to Pi-hole (Priority: P1)

As a Pi-hole administrator, I need to securely authenticate with my Pi-hole instance so I can access management features without compromising security.

**Why this priority**: Authentication is the foundational requirement for all other features. Without secure access, no management operations can be performed. This is the critical first step that enables everything else.

**Independent Test**: Can be fully tested by attempting to connect with valid credentials (successful authentication and access granted) and invalid credentials (authentication rejected with clear error message).

**Acceptance Scenarios**:

1. **Given** user launches the TUI for the first time, **When** prompted for Pi-hole connection details, **Then** user can enter hostname/IP, port, and password
2. **Given** user enters valid credentials, **When** authentication is attempted, **Then** connection is established and user gains access to management features
3. **Given** user enters invalid credentials, **When** authentication is attempted, **Then** clear error message is displayed and user can retry
4. **Given** Pi-hole has two-factor authentication enabled, **When** user enters password, **Then** system prompts for TOTP code before granting access
5. **Given** user has successfully authenticated previously, **When** user launches the TUI again, **Then** saved credentials are used to reconnect automatically (if remember option was selected)
6. **Given** user is connected to Pi-hole, **When** session expires, **Then** system automatically renews session without user intervention
7. **Given** user wants to manage multiple Pi-hole instances, **When** configuring connections, **Then** user can save multiple connection profiles and switch between them
8. **Given** user is connected, **When** connection is lost, **Then** system displays clear connection status and attempts to reconnect automatically

---

### User Story 2 - View Dashboard and System Statistics (Priority: P2)

As a Pi-hole administrator, I need to view comprehensive real-time statistics and system status so I can monitor my network's ad-blocking performance and understand query patterns at a glance.

**Why this priority**: Core monitoring capability that provides visibility into Pi-hole's operation. After authentication, this is the primary view users need to assess system health and effectiveness. This is the central hub for all monitoring activities.

**Independent Test**: Can be fully tested by viewing the dashboard while Pi-hole processes queries and verifying that all statistics display correctly, update in real-time, and accurately reflect Pi-hole's current state.

**Acceptance Scenarios**:

1. **Given** user has authenticated successfully, **When** dashboard loads, **Then** user sees total queries today, queries blocked today, percentage blocked, number of domains on blocklists, and unique clients
2. **Given** user is viewing the dashboard, **When** new queries are processed, **Then** statistics update automatically within 5 seconds without manual refresh
3. **Given** user wants more detailed statistics, **When** viewing dashboard, **Then** user can see query distribution by type (A, AAAA, PTR, SRV, etc.) and reply types (NODATA, NXDOMAIN, CNAME, IP)
4. **Given** user wants to understand query handling, **When** viewing dashboard, **Then** user can see breakdown of queries forwarded vs cached
5. **Given** user wants current blocking status, **When** viewing dashboard, **Then** blocking status (enabled/disabled) is prominently displayed with visual indicator
6. **Given** user wants to see historical context, **When** viewing dashboard, **Then** user can see clients ever seen (lifetime) in addition to current active clients
7. **Given** user wants to verify blocklist currency, **When** viewing dashboard, **Then** last gravity update timestamp is displayed
8. **Given** dashboard data becomes stale, **When** user manually triggers refresh, **Then** all statistics are immediately updated from Pi-hole
9. **Given** user wants to customise update frequency, **When** configuring dashboard settings, **Then** user can select auto-refresh interval (5s, 10s, 30s, 60s, or manual only)

---

### User Story 3 - View Query Log and Filter Queries (Priority: P3)

As a Pi-hole administrator, I need to view recent DNS queries with detailed information and filter them by various criteria so I can investigate which domains are being blocked or allowed, troubleshoot connectivity issues, and understand client query patterns.

**Why this priority**: Critical troubleshooting tool that enables administrators to diagnose why specific domains are blocked or allowed. Essential for understanding Pi-hole behaviour and making informed decisions about domain management.

**Independent Test**: Can be fully tested by viewing the query log with live updates, applying various filters (status, client, domain, time range), and verifying that displayed queries match filter criteria and include all relevant details.

**Acceptance Scenarios**:

1. **Given** Pi-hole has processed queries, **When** user navigates to query log view, **Then** recent queries are displayed with timestamp, client identifier, domain queried, query type, status (blocked/allowed/forwarded/cached), reply type, and response time
2. **Given** user is viewing query log, **When** new queries are processed by Pi-hole, **Then** query log updates in real-time to show new entries
3. **Given** user wants to investigate blocking, **When** user filters by blocked queries only, **Then** only queries that were blocked are displayed
4. **Given** user wants to troubleshoot a specific device, **When** user filters by client IP or hostname, **Then** only queries from that client are displayed
5. **Given** user wants to find queries for a specific domain, **When** user searches for a domain pattern, **Then** only queries matching that pattern are displayed
6. **Given** user wants to investigate recent issues, **When** user selects time range filter, **Then** user can choose from preset ranges (last hour, 24 hours, 7 days) or specify custom range
7. **Given** user wants to understand query types, **When** user filters by query type, **Then** user can select specific DNS record types (A, AAAA, PTR, SRV, ANY, etc.)
8. **Given** user wants to sort results, **When** user clicks column headers, **Then** queries are sorted by that column (time, client, domain, or status)
9. **Given** user wants more details about a query, **When** user selects a query entry, **Then** detailed view shows complete query information including which blocklist blocked it (if applicable)
10. **Given** query log has many entries, **When** user scrolls through results, **Then** system loads additional pages without performance degradation
11. **Given** user wants to take action on a domain, **When** viewing query details, **Then** user can quickly add domain to allowlist or blocklist from context menu
12. **Given** user wants to analyse queries offline, **When** user requests export, **Then** current filtered query log can be exported to CSV format

---

### User Story 4 - Enable and Disable DNS Blocking (Priority: P4)

As a Pi-hole administrator, I need to quickly enable or disable DNS ad-blocking functionality so I can troubleshoot connectivity issues or temporarily allow all domains without permanently changing my configuration.

**Why this priority**: Critical operational control that administrators need frequently. When troubleshooting network issues, quickly disabling blocking helps identify whether Pi-hole is causing the problem. Must be easily accessible and reversible.

**Independent Test**: Can be fully tested by toggling blocking status and verifying that Pi-hole's blocking behaviour changes accordingly, with optional countdown timers working correctly for temporary disables.

**Acceptance Scenarios**:

1. **Given** Pi-hole blocking is currently enabled, **When** user selects disable action, **Then** blocking is disabled immediately and status indicator updates to show disabled state
2. **Given** user wants to temporarily disable blocking, **When** disabling, **Then** user can select from preset durations (30 seconds, 1 minute, 5 minutes, 15 minutes, 30 minutes, 1 hour) or enter custom duration
3. **Given** blocking is disabled with a timer, **When** countdown is active, **Then** remaining time is prominently displayed with visual countdown indicator
4. **Given** blocking is temporarily disabled, **When** timer expires, **Then** blocking is automatically re-enabled and user sees confirmation notification
5. **Given** Pi-hole blocking is currently disabled, **When** user selects enable action, **Then** blocking is re-enabled immediately (cancelling any active timer) and status indicator updates
6. **Given** user wants to record reason for disable, **When** disabling blocking, **Then** user can optionally enter a comment or reason (for audit purposes)
7. **Given** user wants to change blocking state, **When** initiating toggle action, **Then** confirmation dialog appears to prevent accidental changes
8. **Given** blocking status changes, **When** new state is applied, **Then** dashboard immediately reflects the new blocking status
9. **Given** user is performing quick troubleshooting, **When** viewing any screen, **Then** blocking toggle is accessible via keyboard shortcut for rapid access
10. **Given** network connection to Pi-hole fails during toggle, **When** operation cannot complete, **Then** error message is displayed and previous state is maintained

---

### User Story 5 - Manage Domain Allow and Block Lists (Priority: P5)

As a Pi-hole administrator, I need to add, remove, and manage specific domains on my allowlist (whitelist) and blocklist (blacklist) so I can customise blocking behaviour for domains that are incorrectly blocked or need explicit blocking.

**Why this priority**: Essential customisation capability that allows fine-grained control over blocking behaviour. Administrators frequently need to override blocklist decisions (allow incorrectly blocked domains) or explicitly block domains not on any blocklist.

**Independent Test**: Can be fully tested by adding domains to allowlist and blocklist, verifying they appear in the respective lists with correct enabled status and comments, and confirming that bulk operations work correctly.

**Acceptance Scenarios**:

1. **Given** user discovers a blocked domain that should be allowed, **When** user adds domain to allowlist, **Then** domain is immediately added and will no longer be blocked
2. **Given** user wants to explicitly block a domain, **When** user adds domain to blocklist, **Then** domain is immediately added and will be blocked even if not on any blocklist
3. **Given** user is managing domain lists, **When** user navigates to domain management view, **Then** user can switch between allowlist and blocklist tabs
4. **Given** user wants to view existing entries, **When** user selects allowlist or blocklist tab, **Then** all domains in that list are displayed with their status (enabled/disabled), comment, and added date
5. **Given** user wants to find a specific domain, **When** user enters search term, **Then** domain list is filtered to show only matching entries
6. **Given** user wants to temporarily disable a domain entry without deleting it, **When** user toggles domain status, **Then** domain is marked as disabled and Pi-hole no longer applies that rule
7. **Given** user wants to document why a domain was added, **When** adding or editing a domain, **Then** user can enter an optional comment/description
8. **Given** user wants to remove a domain from list, **When** user deletes domain entry, **Then** confirmation is requested and domain is removed from Pi-hole configuration
9. **Given** user adds a domain that already exists, **When** submission occurs, **Then** validation error prevents duplicate and user is notified
10. **Given** user enters malformed domain, **When** submission occurs, **Then** validation error is displayed with guidance on correct format
11. **Given** user wants to manage multiple domains efficiently, **When** user selects multiple entries, **Then** user can perform bulk operations (enable, disable, delete) on all selected domains
12. **Given** user has many domains to add, **When** user initiates bulk import, **Then** user can import domain list from file with validation feedback
13. **Given** user wants to backup domain lists, **When** user requests export, **Then** current allowlist or blocklist can be exported to file
14. **Given** domain list supports wildcards, **When** user adds wildcard pattern (e.g., *.example.com), **Then** pattern is validated and applied to all matching domains

---

### Edge Cases

- What happens when Pi-hole service is unreachable or returns errors (network failure, authentication issues, service restarts)?
- How does the system handle authentication session expiry during active use?
- What happens when user attempts operations while Pi-hole is updating or restarting?
- How does system behave when two-factor authentication is enabled but user doesn't have TOTP code available?
- What happens when saved credentials become invalid (password changed on Pi-hole)?
- How does the system handle very large query logs (100,000+ entries) without performance degradation?
- What happens when user scrolls quickly through paginated query results?
- How does system handle filtering and sorting operations on large datasets?
- What happens when terminal window is resized during operation?
- How does system adapt to very small terminal sizes (80x24) vs large terminals?
- What happens when blocking is disabled with a timer but user closes TUI before timer expires?
- How does system handle domain validation for international domain names (IDN/punycode)?
- What happens when user attempts to add domain that exists in both allowlist and blocklist?
- How does system handle bulk import of domains with mixed valid and invalid entries?
- What happens when export operations encounter file system permission errors?
- How does system behave when network latency to Pi-hole is very high (>2 seconds)?
- What happens when user attempts operations without proper authentication/authorization?

## Requirements *(mandatory)*

### Functional Requirements

**Authentication & Connection (User Story 1)**

- **FR-001**: System MUST prompt user for Pi-hole connection details (hostname/IP address and port) on first launch
- **FR-002**: System MUST authenticate users using password-based authentication
- **FR-003**: System MUST support two-factor authentication (TOTP) when enabled on Pi-hole
- **FR-004**: System MUST securely store connection credentials with encryption when user opts to remember credentials
- **FR-005**: System MUST allow configuration and management of multiple Pi-hole instance connection profiles
- **FR-006**: System MUST validate connection parameters before attempting authentication
- **FR-007**: System MUST display clear connection status indicator showing connected, disconnected, or connecting state
- **FR-008**: System MUST automatically renew authentication sessions before expiry to maintain continuous connection
- **FR-009**: System MUST automatically attempt to reconnect when connection is lost
- **FR-010**: System MUST provide clear error messages for authentication failures distinguishing between invalid credentials, network errors, and service unavailability

**Dashboard & Statistics (User Story 2)**

- **FR-011**: System MUST display current Pi-hole blocking status (enabled/disabled) prominently on dashboard
- **FR-012**: System MUST display key statistics: total queries today, queries blocked today, percentage blocked, domains on blocklists, and unique clients
- **FR-013**: System MUST display extended statistics: clients ever seen, queries forwarded vs cached, and last gravity update timestamp
- **FR-014**: System MUST display query distribution by DNS record type (A, AAAA, PTR, SRV, etc.)
- **FR-015**: System MUST display reply type distribution (NODATA, NXDOMAIN, CNAME, IP)
- **FR-016**: System MUST automatically refresh dashboard statistics at configurable intervals (5s, 10s, 30s, 60s)
- **FR-017**: System MUST allow users to manually trigger immediate dashboard refresh
- **FR-018**: System MUST display last update timestamp for dashboard data

**Query Log (User Story 3)**

- **FR-019**: System MUST display recent query log entries with timestamp, client identifier, domain, query type, status, reply type, and response time
- **FR-020**: System MUST update query log in real-time as new queries are processed
- **FR-021**: System MUST allow filtering queries by status (blocked, allowed, forwarded, cached)
- **FR-022**: System MUST allow filtering queries by client IP address or hostname
- **FR-023**: System MUST allow searching queries by domain name pattern
- **FR-024**: System MUST allow filtering queries by time range with preset options (last hour, 24 hours, 7 days) and custom range
- **FR-025**: System MUST allow filtering queries by DNS record type (A, AAAA, PTR, SRV, ANY, etc.)
- **FR-026**: System MUST allow filtering queries by reply type
- **FR-027**: System MUST allow sorting query log by timestamp, client, domain, or status
- **FR-028**: System MUST support pagination for query logs with large numbers of entries
- **FR-029**: System MUST display detailed query information when user selects an entry, including which blocklist blocked it
- **FR-030**: System MUST allow users to add query domains to allowlist or blocklist directly from query log
- **FR-031**: System MUST allow export of filtered query log to CSV format

**Blocking Control (User Story 4)**

- **FR-032**: System MUST allow users to enable Pi-hole blocking with immediate effect
- **FR-033**: System MUST allow users to disable Pi-hole blocking either indefinitely or for a specified duration
- **FR-034**: System MUST provide preset duration options for temporary disable (30s, 1m, 5m, 15m, 30m, 1h)
- **FR-035**: System MUST allow users to enter custom duration for temporary blocking disable
- **FR-036**: System MUST display countdown timer when blocking is temporarily disabled
- **FR-037**: System MUST automatically re-enable blocking when temporary disable timer expires
- **FR-038**: System MUST allow users to optionally enter reason/comment when disabling blocking
- **FR-039**: System MUST display confirmation dialog before changing blocking state
- **FR-040**: System MUST provide keyboard shortcut for quick access to blocking toggle
- **FR-041**: System MUST immediately update blocking status indicator across all views when state changes

**Domain Management (User Story 5)**

- **FR-042**: System MUST display allowlist (whitelist) entries with domain, enabled status, comment, and added date
- **FR-043**: System MUST display blocklist (blacklist) entries with domain, enabled status, comment, and added date
- **FR-044**: System MUST allow users to add domains to allowlist with immediate effect
- **FR-045**: System MUST allow users to add domains to blocklist with immediate effect
- **FR-046**: System MUST validate domain format before adding to lists
- **FR-047**: System MUST prevent duplicate domains within the same list
- **FR-048**: System MUST allow users to search and filter domain lists by domain name
- **FR-049**: System MUST allow users to enable or disable individual domain list entries
- **FR-050**: System MUST allow users to edit domain entry properties (comment, enabled status)
- **FR-051**: System MUST allow users to delete domain entries with confirmation
- **FR-052**: System MUST support bulk operations (enable, disable, delete) on multiple selected domains
- **FR-053**: System MUST support wildcard domain patterns (e.g., *.example.com)
- **FR-054**: System MUST allow bulk import of domains from file with validation
- **FR-055**: System MUST allow export of allowlist or blocklist to file

**General & Cross-Cutting**

- **FR-056**: System MUST provide keyboard navigation for all interface elements
- **FR-057**: System MUST handle terminal window resize events gracefully, adapting layout to available space
- **FR-058**: System MUST support minimum terminal size of 80x24 characters
- **FR-059**: System MUST display clear, actionable error messages for all failure scenarios
- **FR-060**: System MUST provide help screen or keyboard shortcut reference accessible from any view
- **FR-061**: System MUST persist user preferences (refresh intervals, saved connections, display settings) between sessions
- **FR-062**: System MUST validate all user input before submission
- **FR-063**: System MUST provide visual feedback for all user actions (loading states, progress indicators, confirmations)

### Key Entities

- **Connection Profile**: Represents a saved Pi-hole connection configuration; attributes include profile name, hostname/IP, port, saved credentials (encrypted), two-factor authentication enabled flag, last used timestamp
- **Authentication Session**: Represents an active authenticated session; attributes include session identifier, expiry timestamp, connection status, authentication method used
- **Dashboard Statistics**: Represents current Pi-hole metrics; attributes include total queries, blocked queries, percentage blocked, blocklist domain count, active clients, lifetime clients, queries forwarded, queries cached, last update timestamp, blocking status
- **Query Type Distribution**: Represents breakdown of DNS query types; attributes include query type (A, AAAA, PTR, SRV, etc.), count, percentage
- **Reply Type Distribution**: Represents breakdown of DNS reply types; attributes include reply type (NODATA, NXDOMAIN, CNAME, IP), count, percentage
- **Query Log Entry**: Represents a single DNS query; attributes include timestamp, client IP/hostname, queried domain, query type, status (blocked/allowed/forwarded/cached), reply type, response time in milliseconds, blocking list name (if blocked)
- **Blocking State**: Represents current blocking configuration; attributes include enabled/disabled status, temporary disable timer (if active), timer expiry timestamp, disable reason/comment
- **Domain List Entry**: Represents an allowlist or blocklist domain; attributes include domain pattern (supports wildcards), list type (allow/block), enabled status, comment/description, added timestamp, added by user
- **User Preferences**: Represents saved user settings; attributes include dashboard refresh interval, default filter settings, keyboard shortcuts customisation, terminal display preferences

## Success Criteria *(mandatory)*

### Measurable Outcomes

**Authentication & Connection**

- **SC-001**: Users can complete first-time connection setup (entering credentials and authenticating) in under 60 seconds
- **SC-002**: Users with saved credentials can launch TUI and auto-connect to Pi-hole in under 3 seconds
- **SC-003**: Authentication failures provide clear error messages within 2 seconds allowing users to identify and correct the issue
- **SC-004**: Session renewal occurs automatically without user interruption or visible connection loss
- **SC-005**: Users can configure and switch between multiple Pi-hole instances in under 30 seconds

**Dashboard & Monitoring**

- **SC-006**: Dashboard displays complete current statistics within 2 seconds of successful authentication
- **SC-007**: Dashboard statistics update automatically to reflect new data within configured refresh interval (default 5 seconds) with <100ms UI update latency
- **SC-008**: Users can identify Pi-hole blocking status (enabled/disabled) within 1 second of viewing dashboard
- **SC-009**: Manual dashboard refresh completes and displays updated data within 1 second

**Query Log**

- **SC-010**: Query log displays initial results within 2 seconds of navigation to query log view
- **SC-011**: Users can filter query logs containing 10,000+ entries with filter results appearing within 500ms
- **SC-012**: Real-time query log updates display new queries within 3 seconds of query processing by Pi-hole
- **SC-013**: Users can export filtered query log data (up to 1000 entries) in under 5 seconds
- **SC-014**: Query detail view opens in under 200ms providing complete query information

**Blocking Control**

- **SC-015**: Users can toggle Pi-hole blocking status (enable/disable) with change taking effect within 2 seconds
- **SC-016**: Temporary disable timer countdown updates with 1-second precision
- **SC-017**: Automatic re-enable occurs within 1 second of timer expiry
- **SC-018**: Blocking toggle is accessible via keyboard shortcut from any view in under 1 second

**Domain Management**

- **SC-019**: Users can add a single domain to allowlist or blocklist with change taking effect within 2 seconds
- **SC-020**: Domain list search/filter operations return results within 300ms for lists containing up to 1000 entries
- **SC-021**: Bulk operations on multiple domains (up to 50 selected) complete within 5 seconds
- **SC-022**: Bulk domain import validates and processes up to 100 domains per file within 10 seconds
- **SC-023**: Domain export generates file within 3 seconds for lists containing up to 500 entries

**General Usability**

- **SC-024**: 90% of Phase 1 operations (authenticate, view dashboard, toggle blocking, filter queries, add domain) can be completed without consulting help documentation
- **SC-025**: Application handles connection failures gracefully with clear error messages and recovery options (no crashes or unresponsive states)
- **SC-026**: Application adapts to terminal resize events within 200ms without display corruption or data loss
- **SC-027**: All operations are accessible via keyboard navigation with logical tab order
- **SC-028**: Application memory usage remains under 150MB during normal operation with typical usage patterns
- **SC-029**: Application starts and reaches authentication screen within 2 seconds on standard hardware

## Assumptions

- Pi-hole v6 is installed and running with REST API enabled
- Pi-hole v6 REST API provides authentication endpoint supporting password and TOTP
- Pi-hole administrator has valid authentication credentials (password, and TOTP if enabled)
- Network connectivity exists between TUI client and Pi-hole server with reasonable latency (<500ms for typical operations)
- Terminal emulator supports minimum 80x24 character display, with optimal experience at 120x30 or larger
- Terminal supports UTF-8 character encoding for proper display of domain names and UI elements
- Terminal supports colour display for status indicators (or gracefully degrades to monochrome)
- Users have basic familiarity with terminal interfaces and keyboard navigation
- Pi-hole v6 API provides necessary endpoints for Phase 1 features:
  - Authentication (POST /api/auth, DELETE /api/auth)
  - Statistics (GET /api/stats/summary, GET /api/stats/database/summary)
  - Blocking control (GET /api/dns/blocking, POST /api/dns/blocking)
  - Query log (GET /api/queries with pagination and filtering)
  - Domain lists (GET /api/domains, POST /api/domains, PUT /api/domains/{id}, DELETE /api/domains/{id}, PATCH /api/domains/{id})
- Application can store configuration files in user's home directory or standard application config location
- File system supports encrypted storage of credentials
- System provides standard file dialogs or command-line paths for import/export operations

## Out of Scope

The following capabilities are explicitly excluded from **Phase 1**:

**Pi-hole Installation & Configuration**
- Initial Pi-hole system installation or setup
- Advanced Pi-hole configuration (DHCP settings, DNS upstream providers, network configuration)
- Pi-hole system updates or upgrades
- FTL database management or maintenance

**Blocklist Management**
- Managing external blocklist sources (adding, removing, updating blocklist URLs)
- Viewing blocklist details beyond total domain counts shown on dashboard
- Creating or managing custom blocklist collections
- Gravity update operations (blocklist updates) - only displaying last update timestamp

**Client Management & Analytics**
- Per-client query statistics and analysis
- Client identification and naming
- Client groups or categories
- Client-specific blocking rules or policies

**Advanced Analytics**
- Historical data analysis and trends (beyond current day)
- Graphical charts and visualisations beyond basic statistics display
- Custom date ranges for statistical analysis
- Top domains and top blocked domains lists
- Top clients lists

**Network & System Management**
- Network diagnostic tools
- DNS server testing or validation
- System resource monitoring (CPU, memory, disk usage)
- Pi-hole service management (start, stop, restart)
- Log file management or viewing

**User & Security Management**
- User account creation or management
- Role-based access controls
- API token generation or management
- Audit logging of administrative actions
- Multi-user concurrent access management

**Advanced Features**
- Regular expression-based domain filtering
- CNAME inspection configuration
- Conditional forwarding rules
- Local DNS records management
- Custom DNS configuration
- Query reply modification or inspection

**Integration & Automation**
- External service integrations (email, notifications, webhooks)
- Scheduled operations or automation
- Backup and restore functionality
- Configuration import/export
- Third-party tool integration

**UI Customisation**
- Custom themes or colour schemes
- Custom dashboard layouts or widget arrangement
- Configurable column display or ordering
- Custom keyboard shortcut mapping (beyond defaults)

**Note**: These out-of-scope items may be considered for future phases. Phase 1 focuses on core monitoring and essential management features to establish the foundation of the TUI.
