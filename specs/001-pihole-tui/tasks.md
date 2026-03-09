# Tasks: Pi-hole TUI Management Interface

**Input**: Design documents from `/specs/001-pihole-tui/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Per project constitution, tests are OPTIONAL. Manual testing is primary validation method using quickstart.md scenarios. No test tasks included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/pihole_tui/` at repository root
- Paths shown below use actual project structure from plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialisation and basic structure

- [X] T001 Create pyproject.toml with project metadata, dependencies (textual, httpx, cryptography, pydantic, tomli), and entry point configuration
- [X] T002 [P] Create src/pihole_tui/__init__.py with package initialisation
- [X] T003 [P] Create src/pihole_tui/__main__.py as entry point for `python -m pihole_tui`
- [X] T004 [P] Create src/pihole_tui/constants.py with API paths, default values, and enums (QueryStatus, DomainListType, BulkOperationType)
- [X] T005 [P] Create .gitignore for Python project (exclude __pycache__, *.pyc, .env, dist/, build/, *.egg-info, .pytest_cache)
- [X] T006 [P] Create README.md with basic setup and usage instructions per constitution requirements
- [X] T007 [P] Create directory structure: src/pihole_tui/api/, src/pihole_tui/models/, src/pihole_tui/screens/, src/pihole_tui/widgets/, src/pihole_tui/utils/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 [P] Create src/pihole_tui/models/config.py with ConnectionProfile and UserPreferences models using Pydantic
- [X] T009 [P] Create src/pihole_tui/models/session.py with SessionState model for tracking active session
- [X] T010 [P] Create src/pihole_tui/utils/crypto.py with Fernet encryption/decryption functions for credential storage
- [X] T011 Create src/pihole_tui/utils/config_manager.py with methods to read/write config.toml and encrypted connections.enc file in ~/.config/pihole-tui/
- [X] T012 [P] Create src/pihole_tui/utils/validators.py with domain validation, IP validation, and input validation functions
- [X] T013 [P] Create src/pihole_tui/utils/formatters.py with time formatting, percentage formatting, and data display helpers
- [X] T014 Create src/pihole_tui/api/client.py with base HTTP client using httpx, session management, SID header handling, and auto-retry logic

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Authenticate and Connect to Pi-hole (Priority: P1) 🎯 MVP

**Goal**: Secure authentication with session management, 2FA support, multiple instance management, and auto-reconnect

**Independent Test**: Launch TUI, enter valid/invalid credentials, verify authentication success/failure, test 2FA flow, verify saved credentials auto-login, test session renewal

### Implementation for User Story 1

- [X] T015 [P] [US1] Create src/pihole_tui/models/__init__.py with model exports
- [X] T016 [P] [US1] Create src/pihole_tui/api/__init__.py with API client exports
- [X] T017 [P] [US1] Create src/pihole_tui/api/auth.py with authentication endpoints (POST /api/auth for login with password/TOTP, DELETE /api/auth for logout)
- [X] T018 [US1] Implement session renewal logic in src/pihole_tui/api/client.py with background task to renew at 80% of validity period
- [X] T019 [US1] Implement auto-reconnect logic in src/pihole_tui/api/client.py with exponential backoff for failed connections
- [X] T020 [P] [US1] Create src/pihole_tui/screens/__init__.py with screen exports
- [X] T021 [P] [US1] Create src/pihole_tui/screens/login.py with LoginScreen class implementing login form (hostname, port, password inputs, remember checkbox, connect button)
- [X] T022 [US1] Add TOTP dialog to src/pihole_tui/screens/login.py for two-factor authentication code input
- [X] T023 [P] [US1] Create src/pihole_tui/screens/settings.py with SettingsScreen for managing connection profiles and preferences
- [X] T024 [US1] Implement connection profile management in src/pihole_tui/screens/settings.py (add, edit, delete, switch between profiles)
- [X] T025 [P] [US1] Create src/pihole_tui/widgets/__init__.py with widget exports
- [X] T026 [P] [US1] Create src/pihole_tui/widgets/status_indicator.py with connection status widget showing connected/disconnected/connecting states with colour indicators
- [X] T027 [US1] Create src/pihole_tui/app.py with main Textual App class, implement startup flow (load saved credentials → auto-login OR show login screen)
- [X] T028 [US1] Implement status bar in src/pihole_tui/app.py showing connection status, current profile name, and session expiry
- [X] T029 [US1] Implement global error handling in src/pihole_tui/app.py for auth failures, network errors, and session expiry
- [X] T030 [US1] Update src/pihole_tui/__main__.py to create and run App instance

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently using quickstart.md scenarios 1.1-1.6

---

## Phase 4: User Story 2 - View Dashboard and System Statistics (Priority: P2)

**Goal**: Real-time dashboard with comprehensive statistics, auto-refresh, query/reply type distributions, and configurable update intervals

**Independent Test**: After authentication, verify dashboard displays all statistics, auto-updates every 5 seconds, manual refresh works, statistics match Pi-hole data, can configure refresh interval

### Implementation for User Story 2

- [X] T031 [P] [US2] Create src/pihole_tui/models/stats.py with DashboardStats, QueryTypeDistribution, and ReplyTypeDistribution models
- [X] T032 [P] [US2] Create src/pihole_tui/api/stats.py with statistics endpoints (GET /api/stats/summary, GET /api/stats/database/summary)
- [X] T033 [US2] Create src/pihole_tui/api/blocking.py with blocking status endpoint (GET /api/dns/blocking)
- [X] T034 [P] [US2] Create src/pihole_tui/widgets/stat_card.py with widget for displaying individual statistic panels (queries, blocked, percentage, clients, etc.)
- [X] T035 [US2] Implement query type distribution display in src/pihole_tui/widgets/stat_card.py using Textual's bar chart or table widgets
- [X] T036 [US2] Implement reply type distribution display in src/pihole_tui/widgets/stat_card.py
- [X] T037 [P] [US2] Create src/pihole_tui/screens/dashboard.py with DashboardScreen class and layout for statistics cards
- [X] T038 [US2] Implement statistics fetching in src/pihole_tui/screens/dashboard.py calling stats API endpoints
- [X] T039 [US2] Implement auto-refresh using Textual's set_interval() in src/pihole_tui/screens/dashboard.py with configurable interval (5s, 10s, 30s, 60s)
- [X] T040 [US2] Implement manual refresh action (F5 key or refresh button) in src/pihole_tui/screens/dashboard.py
- [X] T041 [US2] Display blocking status prominently in src/pihole_tui/screens/dashboard.py using status_indicator.py widget with green/red colour coding
- [X] T042 [US2] Display gravity last updated timestamp and last dashboard update time in src/pihole_tui/screens/dashboard.py
- [X] T043 [US2] Display queries forwarded vs cached breakdown in src/pihole_tui/screens/dashboard.py
- [X] T044 [US2] Implement refresh interval configuration in src/pihole_tui/screens/settings.py (preferences section)
- [X] T045 [US2] Update src/pihole_tui/app.py to show DashboardScreen as default screen after successful authentication

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Can authenticate and view live dashboard with all statistics.

---

## Phase 5: User Story 3 - View Query Log and Filter Queries (Priority: P3)

**Goal**: Live query log with real-time updates, advanced filtering (status, client, domain, time, type), pagination, CSV export, and quick actions

**Independent Test**: Navigate to query log, verify queries display with all details, apply filters (blocked only, specific client, domain search, time range), verify pagination, export to CSV, add domain from query to allowlist

### Implementation for User Story 3

- [X] T046 [P] [US3] Create src/pihole_tui/models/query.py with QueryLogEntry, QueryLogFilters, and QueryLogResponse models
- [X] T047 [P] [US3] Create src/pihole_tui/api/queries.py with query log endpoint (GET /api/queries with pagination and filtering parameters)
- [X] T048 [P] [US3] Create src/pihole_tui/widgets/query_table.py with custom DataTable widget for displaying query log entries with columns (timestamp, client, domain, type, status, reply, response time)
- [X] T049 [US3] Implement query status colour coding in src/pihole_tui/widgets/query_table.py (green=allowed, red=blocked, blue=cached, yellow=forwarded)
- [X] T050 [P] [US3] Create src/pihole_tui/screens/query_log.py with QueryLogScreen class and filter bar UI
- [X] T051 [US3] Implement status filter dropdown in src/pihole_tui/screens/query_log.py (All, Blocked, Allowed, Forwarded, Cached)
- [X] T052 [US3] Implement client filter input in src/pihole_tui/screens/query_log.py (IP address or hostname search)
- [X] T053 [US3] Implement domain search input in src/pihole_tui/screens/query_log.py (pattern matching with wildcard support)
- [X] T054 [US3] Implement time range filter in src/pihole_tui/screens/query_log.py with presets (last hour, 24h, 7 days) and custom range picker
- [X] T055 [US3] Implement query type filter in src/pihole_tui/screens/query_log.py (A, AAAA, PTR, SRV, ANY, etc.)
- [X] T056 [US3] Implement reply type filter in src/pihole_tui/screens/query_log.py (IP, CNAME, NODATA, NXDOMAIN)
- [X] T057 [US3] Implement column sorting in src/pihole_tui/widgets/query_table.py (click headers to sort by timestamp, client, domain, status)
- [X] T058 [US3] Implement pagination/virtual scrolling in src/pihole_tui/screens/query_log.py using API page/limit parameters
- [X] T059 [US3] Implement real-time updates in src/pihole_tui/screens/query_log.py using set_interval() to poll for new queries every 3-5 seconds
- [X] T060 [US3] Implement query details modal in src/pihole_tui/screens/query_log.py showing full query information including blocklist name
- [X] T061 [US3] Implement CSV export functionality in src/pihole_tui/screens/query_log.py (export currently filtered queries to file)
- [X] T062 [US3] Implement context menu in src/pihole_tui/widgets/query_table.py with "Add to Allowlist" and "Add to Blocklist" actions
- [X] T063 [US3] Update src/pihole_tui/app.py to add Query Log screen to navigation (keyboard shortcut Q)

**Checkpoint**: All three user stories (auth, dashboard, query log) should now be independently functional

---

## Phase 6: User Story 4 - Enable and Disable DNS Blocking (Priority: P4)

**Goal**: Quick toggle blocking on/off, temporary disable with countdown timers, preset/custom durations, optional reason tracking

**Independent Test**: Toggle blocking from dashboard, verify status changes immediately, set 5-minute timer and verify countdown, verify auto-enable when timer expires, test keyboard shortcut access

### Implementation for User Story 4

- [X] T064 [P] [US4] Create src/pihole_tui/models/blocking.py with BlockingState, BlockingToggleRequest models
- [X] T065 [P] [US4] Add POST /api/dns/blocking endpoint to src/pihole_tui/api/blocking.py for enabling/disabling with optional timer
- [X] T066 [P] [US4] Create src/pihole_tui/widgets/countdown_timer.py with timer widget displaying remaining time with visual countdown
- [X] T067 [US4] Implement blocking toggle action in src/pihole_tui/screens/dashboard.py with confirmation dialog
- [X] T068 [US4] Implement duration selection dialog in src/pihole_tui/screens/dashboard.py with preset options (30s, 1m, 5m, 15m, 30m, 1h) and custom duration input
- [X] T069 [US4] Implement optional reason/comment input in duration selection dialog in src/pihole_tui/screens/dashboard.py
- [X] T070 [US4] Implement countdown timer display in src/pihole_tui/screens/dashboard.py using countdown_timer.py widget with yellow status indicator
- [X] T071 [US4] Implement auto-enable logic in src/pihole_tui/screens/dashboard.py that re-enables blocking when timer expires with notification
- [X] T072 [US4] Implement manual re-enable action in src/pihole_tui/screens/dashboard.py that cancels active timer
- [X] T073 [US4] Update status_indicator.py widget to show three states: enabled (green), disabled (red), temp disabled with timer (yellow)
- [X] T074 [US4] Implement global keyboard shortcut (Ctrl+B) in src/pihole_tui/app.py for quick blocking toggle accessible from any screen
- [X] T075 [US4] Implement error handling in blocking toggle for network failures, maintaining previous state on error

**Checkpoint**: User Stories 1-4 complete. Can authenticate, view dashboard, query log, and control blocking with timers.

---

## Phase 7: User Story 5 - Manage Domain Allow and Block Lists (Priority: P5)

**Goal**: View/add/edit/delete domains on allowlist and blocklist, bulk operations, wildcard support, import/export

**Independent Test**: Navigate to domain management, view allowlist, add domain with comment, edit domain, delete domain, search domains, enable/disable individual entry, select multiple domains and perform bulk disable, import domains from file, export to file, test wildcard patterns

### Implementation for User Story 5

- [X] T076 [P] [US5] Create src/pihole_tui/models/domain.py with DomainListEntry, DomainListFilters, DomainListResponse, DomainAddRequest, DomainUpdateRequest, BulkDomainOperation, DomainImportRequest, DomainImportResult models
- [X] T077 [P] [US5] Create src/pihole_tui/api/domains.py with domain list endpoints (GET /api/domains, POST /api/domains, PUT /api/domains/{id}, DELETE /api/domains/{id}, PATCH /api/domains/{id})
- [X] T078 [P] [US5] Create src/pihole_tui/widgets/domain_list.py with custom widget displaying domain entries in table format with checkboxes for multi-select
- [X] T079 [US5] Implement domain status toggle (enable/disable) in src/pihole_tui/widgets/domain_list.py with visual indicators
- [X] T080 [P] [US5] Create src/pihole_tui/screens/domains.py with DomainsScreen class featuring tabbed view for Allowlist and Blocklist
- [X] T081 [US5] Implement allowlist tab in src/pihole_tui/screens/domains.py displaying allowlist entries using domain_list.py widget
- [X] T082 [US5] Implement blocklist tab in src/pihole_tui/screens/domains.py displaying blocklist entries using domain_list.py widget
- [X] T083 [US5] Implement search/filter bar in src/pihole_tui/screens/domains.py for filtering domains by pattern
- [X] T084 [US5] Implement "Add Domain" dialog in src/pihole_tui/screens/domains.py with domain input, comment input, enabled checkbox, and list type selection
- [X] T085 [US5] Implement domain validation in "Add Domain" dialog using validators.py (check domain format, wildcard patterns like *.example.com)
- [X] T086 [US5] Implement duplicate detection in "Add Domain" dialog showing error if domain already exists in list
- [X] T087 [US5] Implement "Edit Domain" dialog in src/pihole_tui/screens/domains.py for updating comment and enabled status
- [X] T088 [US5] Implement delete action in src/pihole_tui/screens/domains.py with confirmation dialog
- [X] T089 [US5] Implement multi-select functionality in src/pihole_tui/widgets/domain_list.py (checkboxes, Shift+Click, Ctrl+Click)
- [X] T090 [US5] Implement bulk actions menu in src/pihole_tui/screens/domains.py with Enable Selected, Disable Selected, Delete Selected options
- [X] T091 [US5] Implement bulk operation execution in src/pihole_tui/screens/domains.py with progress indicator and sequential API calls
- [X] T092 [US5] Implement import dialog in src/pihole_tui/screens/domains.py with file picker, preview, validation, and skip duplicates option
- [X] T093 [US5] Implement bulk import processing in src/pihole_tui/screens/domains.py (read file, validate each domain, call API sequentially, show result summary)
- [X] T094 [US5] Implement export functionality in src/pihole_tui/screens/domains.py to save current list to text file (one domain per line)
- [X] T095 [US5] Implement tab switching (Ctrl+Tab) between Allowlist and Blocklist in src/pihole_tui/screens/domains.py
- [X] T096 [US5] Update src/pihole_tui/app.py to add Domains screen to navigation (keyboard shortcut D)

**Checkpoint**: All five user stories should now be independently functional. Full Phase 1 feature set complete.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final polish

- [X] T097 [P] Implement help screen in src/pihole_tui/app.py showing keyboard shortcuts and basic usage (F1 to open)
- [ ] T098 [P] Implement graceful terminal resize handling in all screens ensuring layout adapts without corruption
- [ ] T099 [P] Add loading indicators to all API operations showing visual feedback during network requests
- [ ] T100 [P] Implement error notification system in src/pihole_tui/app.py for displaying user-friendly error messages with recovery options
- [ ] T101 [P] Add logging configuration in src/pihole_tui/app.py for debugging (log to ~/.config/pihole-tui/pihole-tui.log)
- [ ] T102 [P] Implement keyboard navigation improvements ensuring all features accessible via keyboard with logical tab order
- [ ] T103 Update README.md with complete setup instructions, dependencies installation, usage examples, and keyboard shortcuts
- [ ] T104 [P] Verify memory usage remains under 150MB during normal operation with large datasets
- [ ] T105 [P] Verify performance targets: dashboard refresh <2s, filter operations <500ms, pagination <2s, UI responsiveness <200ms
- [ ] T106 Run manual testing scenarios from quickstart.md for all user stories (US1-US5) and verify all acceptance criteria pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed) OR sequentially in priority order (P1 → P2 → P3 → P4 → P5)
  - Each story is independently testable after completion
- **Polish (Phase 8)**: Depends on desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 for authentication but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US1 for authentication, can use US5 integration but independently testable
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Requires US1 for authentication, displays on US2 dashboard but independently testable
- **User Story 5 (P5)**: Can start after Foundational (Phase 2) - Requires US1 for authentication, can be accessed from US3 but independently testable

### Within Each User Story

- Foundation tasks (models, API clients) before screen/widget tasks
- Screens before complex widget integration
- Core functionality before advanced features (e.g., basic list view before bulk operations)
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T002-T007)
- Foundational tasks marked [P] can run in parallel within phase 2 (T008-T013)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Within each user story, tasks marked [P] can run in parallel:
  - US1: T015-T016, T020-T021, T025-T026
  - US2: T031-T032, T034
  - US3: T046-T048, T050
  - US4: T064-T066
  - US5: T076-T078, T080
- Polish tasks (Phase 8) marked [P] can all run in parallel (T097-T105)

---

## Parallel Example: User Story 1

```bash
# Launch models, API client, and initial UI components together:
Task T015: Create src/pihole_tui/models/__init__.py
Task T016: Create src/pihole_tui/api/__init__.py
Task T020: Create src/pihole_tui/screens/__init__.py
Task T021: Create src/pihole_tui/screens/login.py (login form)
Task T025: Create src/pihole_tui/widgets/__init__.py
Task T026: Create src/pihole_tui/widgets/status_indicator.py

# Then sequential tasks that depend on above:
Task T017: Implement auth.py (depends on API structure)
Task T018: Session renewal (depends on client.py)
Task T022: TOTP dialog (depends on login.py existing)
# etc.
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2 Only)

1. Complete Phase 1: Setup (T001-T007)
2. Complete Phase 2: Foundational (T008-T014) - **CRITICAL - blocks all stories**
3. Complete Phase 3: User Story 1 Authentication (T015-T030)
4. **STOP and VALIDATE**: Test authentication flow using quickstart.md scenarios 1.1-1.6
5. Complete Phase 4: User Story 2 Dashboard (T031-T045)
6. **STOP and VALIDATE**: Test dashboard using quickstart.md scenarios 2.1-2.4
7. Deploy/demo MVP (authentication + dashboard = core value)

### Incremental Delivery (Recommended)

1. Complete Setup + Foundational → Foundation ready (T001-T014)
2. Add User Story 1 → Test independently → Deploy/Demo (authentication works!)
3. Add User Story 2 → Test independently → Deploy/Demo (dashboard visible!)
4. Add User Story 3 → Test independently → Deploy/Demo (query log working!)
5. Add User Story 4 → Test independently → Deploy/Demo (blocking control added!)
6. Add User Story 5 → Test independently → Deploy/Demo (domain management complete!)
7. Polish Phase → Final QA → Production release

Each story adds value without breaking previous stories. Can stop at any point with working features.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T014)
2. Once Foundational is done:
   - Developer A: User Story 1 (T015-T030)
   - Developer B: Can start User Story 2 models/API (T031-T033) in parallel
   - Once US1 complete, Developer B finishes US2 UI (T034-T045)
   - Developer C: Can start User Story 3 models/API (T046-T047) in parallel
3. Stories complete and integrate independently with authentication

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests are OPTIONAL per constitution - manual testing using quickstart.md is primary validation
- Commit after each task or logical group of parallel tasks
- Stop at any checkpoint to validate story independently using quickstart.md scenarios
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Constitution principle: Simplicity First - no premature abstractions, straightforward implementations
- Constitution principle: Observable Behaviour - focus on user-visible functionality

---

## Task Summary

**Total Tasks**: 106 tasks

**Phase Breakdown**:
- Phase 1 (Setup): 7 tasks
- Phase 2 (Foundational): 7 tasks (BLOCKING - must complete before user stories)
- Phase 3 (US1 - Auth): 16 tasks
- Phase 4 (US2 - Dashboard): 15 tasks
- Phase 5 (US3 - Query Log): 18 tasks
- Phase 6 (US4 - Blocking Control): 12 tasks
- Phase 7 (US5 - Domain Management): 21 tasks
- Phase 8 (Polish): 10 tasks

**Parallel Opportunities**: 23 tasks marked [P] can run in parallel with other tasks in same phase

**MVP Scope** (Minimum Viable Product): Phases 1-4 (T001-T045) = 45 tasks
- Delivers authentication + dashboard = core monitoring value
- Can validate TUI approach before building remaining features

**Independent Test Criteria**:
- US1: Can authenticate, save credentials, auto-login, handle 2FA, manage multiple instances
- US2: Dashboard displays all statistics, auto-refreshes, manual refresh works
- US3: Query log displays with all details, filtering works, export to CSV
- US4: Can toggle blocking, set timers, timers work correctly, keyboard shortcut accessible
- US5: Can view/add/edit/delete domains, bulk operations work, import/export successful

All tasks are immediately executable with specific file paths and clear descriptions. Ready for `/speckit.implement` or manual implementation.
