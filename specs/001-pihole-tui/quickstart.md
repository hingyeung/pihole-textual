# Quickstart Guide: Pi-hole TUI Testing Scenarios

**Feature**: Pi-hole TUI Management Interface
**Date**: 2025-12-05
**Purpose**: Manual testing scenarios for validating Phase 1 features

## Prerequisites

**Before Testing**:
- Pi-hole v6.0+ installed and running
- Pi-hole admin password known
- Terminal emulator (80x24 minimum, 120x30 recommended)
- Python 3.8+ installed

**Test Pi-hole Setup**:
- Active DNS queries being processed (for realistic dashboard/query log)
- At least one domain in allowlist or blocklist (for domain management testing)
- 2FA/TOTP enabled OR disabled (test both scenarios if possible)

---

## User Story 1: Authentication & Connection

### Test Scenario 1.1: First-Time Login (No Saved Credentials)

**Goal**: Verify initial connection setup and authentication flow.

**Steps**:
1. Launch TUI: `python -m pihole_tui`
2. Observe: Login screen appears with connection settings form
3. Enter Pi-hole hostname/IP (e.g., `pi.hole` or `192.168.1.2`)
4. Enter port (default: `8080`)
5. Enter admin password
6. Select "Remember credentials" checkbox
7. Click "Connect" button

**Expected Results**:
- ✅ Connection settings screen displays all input fields
- ✅ Form validation prevents empty hostname/password
- ✅ Loading indicator appears during authentication
- ✅ On success: Dashboard appears within 3 seconds
- ✅ Connection status shows "Connected" in status bar
- ✅ Credentials saved in encrypted file (`~/.config/pihole-tui/connections.enc`)

**Error Cases**:
- Invalid hostname: "Unable to connect to Pi-hole. Check hostname/IP and port."
- Wrong password: "Authentication failed. Please check your password."
- Network timeout: "Connection timeout. Verify Pi-hole is reachable."

---

### Test Scenario 1.2: Login with 2FA/TOTP

**Goal**: Verify two-factor authentication flow.

**Prerequisites**: Pi-hole has 2FA enabled

**Steps**:
1. Launch TUI
2. Enter hostname, port, password
3. Click "Connect"
4. Observe: TOTP code input dialog appears
5. Enter 6-digit TOTP code from authenticator app
6. Click "Submit"

**Expected Results**:
- ✅ After initial password entry, TOTP dialog appears
- ✅ TOTP input accepts only 6 digits
- ✅ Invalid TOTP shows error: "Invalid authentication code. Please try again."
- ✅ Valid TOTP completes authentication and shows dashboard
- ✅ TOTP prompt reappears on next login if 2FA is enabled

---

### Test Scenario 1.3: Auto-Login with Saved Credentials

**Goal**: Verify remembered credentials work for subsequent launches.

**Prerequisites**: Credentials previously saved (Scenario 1.1 completed)

**Steps**:
1. Exit TUI (if running)
2. Launch TUI again: `python -m pihole_tui`
3. Observe: Auto-login attempt

**Expected Results**:
- ✅ Loading indicator shows "Connecting to [hostname]..."
- ✅ Dashboard appears within 3 seconds without login prompt
- ✅ Session automatically authenticated using saved credentials
- ✅ If credentials invalid (password changed), login screen appears with error

---

### Test Scenario 1.4: Session Renewal

**Goal**: Verify automatic session renewal prevents expiry.

**Prerequisites**: Authenticated and on dashboard

**Steps**:
1. Note session expiry time (default 300s validity)
2. Stay on dashboard for 4+ minutes (80% of validity)
3. Observe status bar

**Expected Results**:
- ✅ At ~4 minutes (80% of validity), session renewal occurs automatically
- ✅ No visible interruption or logout
- ✅ Status bar briefly shows "Renewing session..." indicator
- ✅ Countdown timer resets to 5 minutes
- ✅ If renewal fails, error notification appears and re-auth prompts

---

### Test Scenario 1.5: Connection Loss and Reconnect

**Goal**: Verify graceful handling of connection failures.

**Steps**:
1. Authenticate and view dashboard
2. Disconnect network OR stop Pi-hole service
3. Observe TUI behaviour
4. Wait for automatic reconnect OR manually trigger refresh
5. Restore network/service
6. Observe reconnection

**Expected Results**:
- ✅ Connection status changes to "Disconnected" in status bar (red indicator)
- ✅ Last successful data remains visible with "stale data" indicator
- ✅ Operations show error: "Connection lost. Retrying..."
- ✅ Auto-reconnect attempts every 10 seconds
- ✅ On reconnection: Status changes to "Connected", data refreshes
- ✅ If auto-reconnect fails after 3 attempts, user prompted to check connection

---

### Test Scenario 1.6: Multiple Pi-hole Instances

**Goal**: Verify management of multiple saved connections.

**Steps**:
1. From dashboard, press `Ctrl+P` (or menu: Settings → Connections)
2. Click "Add Connection"
3. Enter details for second Pi-hole instance
4. Save connection
5. Switch between connections using connection selector

**Expected Results**:
- ✅ Connection list shows all saved profiles
- ✅ Active connection highlighted
- ✅ Switching connections prompts: "Switch to [name]? Current session will end."
- ✅ After confirmation, TUI authenticates to new instance and loads its dashboard
- ✅ Each connection maintains separate session

---

## User Story 2: Dashboard & Statistics

### Test Scenario 2.1: Dashboard Display

**Goal**: Verify dashboard shows all statistics correctly.

**Steps**:
1. Authenticate successfully
2. Observe dashboard (default screen after login)
3. Review statistics panels

**Expected Results**:
- ✅ Dashboard loads within 2 seconds of authentication
- ✅ **Statistics displayed**:
  - Total queries today
  - Queries blocked today
  - Percentage blocked (with progress bar)
  - Domains on blocklists
  - Unique clients today
  - Clients ever seen
  - Queries forwarded vs cached (breakdown)
- ✅ **Query type distribution** (bar chart or table):
  - A, AAAA, PTR, SRV, ANY, TXT record counts
- ✅ **Reply type distribution**:
  - IP, CNAME, NODATA, NXDOMAIN counts
- ✅ **Blocking status** indicator (large, prominent):
  - Green "ENABLED" or Red "DISABLED"
- ✅ **Gravity last updated** timestamp displayed
- ✅ **Last update** timestamp shows when stats were fetched

---

### Test Scenario 2.2: Auto-Refresh

**Goal**: Verify dashboard auto-updates at configured interval.

**Steps**:
1. On dashboard, note current query count
2. Generate new DNS queries (browse websites on device using Pi-hole)
3. Wait for configured refresh interval (default 5 seconds)
4. Observe statistics update

**Expected Results**:
- ✅ Statistics refresh automatically without manual action
- ✅ Query count increases to reflect new queries
- ✅ Percentage blocked recalculates
- ✅ Last update timestamp changes
- ✅ Visual indicator (e.g., brief highlight) shows data refreshed

---

### Test Scenario 2.3: Manual Refresh

**Goal**: Verify user can trigger immediate refresh.

**Steps**:
1. On dashboard, press `F5` or click "Refresh" button
2. Observe loading state
3. Verify updated statistics

**Expected Results**:
- ✅ Loading indicator appears immediately
- ✅ Statistics fetch from API
- ✅ Dashboard updates within 1 second
- ✅ Last update timestamp changes to current time
- ✅ If refresh fails, error message displays but stale data remains visible

---

### Test Scenario 2.4: Configure Refresh Interval

**Goal**: Verify user can change auto-refresh rate.

**Steps**:
1. Press `Ctrl+,` or menu: Settings → Preferences
2. Navigate to "Dashboard refresh interval"
3. Change from 5s to 30s
4. Save preferences
5. Return to dashboard
6. Observe refresh behaviour

**Expected Results**:
- ✅ Preferences screen allows selection of 5s, 10s, 30s, 60s
- ✅ Setting saves and persists across restarts
- ✅ Dashboard now refreshes every 30 seconds
- ✅ Last update timestamp confirms new interval

---

## User Story 3: Query Log

### Test Scenario 3.1: View Query Log

**Goal**: Verify query log displays recent queries with details.

**Steps**:
1. From dashboard, press `Q` or navigate to "Query Log"
2. Observe query log screen

**Expected Results**:
- ✅ Query log screen loads within 2 seconds
- ✅ Recent 50 queries displayed in table format
- ✅ **Columns visible**:
  - Timestamp (relative: "5s ago", "2m ago")
  - Client IP/hostname
  - Domain queried
  - Query type (A, AAAA, etc.)
  - Status (icon + colour: green=allowed, red=blocked, blue=cached)
  - Reply type
  - Response time (ms)
- ✅ Queries sorted by timestamp (newest first)
- ✅ Colour coding makes blocked vs allowed immediately visible
- ✅ Real-time updates: New queries appear at top automatically

---

### Test Scenario 3.2: Filter by Status

**Goal**: Verify filtering queries by blocked/allowed status.

**Steps**:
1. On query log, locate filter bar at top
2. Select "Status" dropdown
3. Choose "Blocked only"
4. Observe filtered results

**Expected Results**:
- ✅ Only blocked queries displayed
- ✅ Filter applies within 500ms
- ✅ Query count updates to show filtered total
- ✅ Select "Allowed only": Only allowed queries shown
- ✅ Select "All": Full unfiltered log returns

---

### Test Scenario 3.3: Filter by Client

**Goal**: Verify filtering queries by specific client.

**Steps**:
1. On query log, note a client IP from displayed queries
2. In filter bar, enter client IP in "Client" field (e.g., `192.168.1.100`)
3. Press Enter or click "Apply"

**Expected Results**:
- ✅ Only queries from specified client displayed
- ✅ Client filter accepts IP addresses and hostnames
- ✅ Partial matches supported (e.g., `192.168` matches all IPs starting with that)
- ✅ Clear filter button resets to show all clients

---

### Test Scenario 3.4: Search by Domain

**Goal**: Verify searching for specific domains.

**Steps**:
1. On query log, locate "Search" field
2. Enter domain pattern (e.g., `google.com`)
3. Press Enter

**Expected Results**:
- ✅ Only queries matching domain pattern displayed
- ✅ Search supports wildcards (e.g., `*.google.com`)
- ✅ Search is case-insensitive
- ✅ Results update within 500ms
- ✅ Clear search shows all queries again

---

### Test Scenario 3.5: Time Range Filter

**Goal**: Verify filtering queries by time range.

**Steps**:
1. On query log, click "Time Range" dropdown
2. Select "Last hour"
3. Observe filtered results
4. Try other presets: "Last 24 hours", "Last 7 days"
5. Try "Custom range" and enter specific dates/times

**Expected Results**:
- ✅ Preset ranges filter correctly
- ✅ Custom range allows date/time picker
- ✅ Future dates rejected with validation error
- ✅ `from` must be before `until` timestamp
- ✅ Query log respects time filter, older queries not shown

---

### Test Scenario 3.6: Query Details View

**Goal**: Verify detailed information modal for selected query.

**Steps**:
1. On query log, click a query row (or press Enter on selected row)
2. Observe details modal/popup

**Expected Results**:
- ✅ Modal opens showing full query details
- ✅ **Details shown**:
  - Full timestamp (absolute time)
  - Client IP and hostname (if available)
  - Full domain name
  - Query type
  - Status with icon
  - Reply type
  - Response time
  - **If blocked**: Name of blocklist that blocked it
- ✅ Modal has "Close" button or press Esc to dismiss
- ✅ From modal, "Add to Allowlist" or "Add to Blocklist" buttons available

---

### Test Scenario 3.7: Pagination

**Goal**: Verify pagination for large query logs.

**Steps**:
1. On query log with >50 entries, scroll to bottom
2. Observe pagination controls
3. Click "Next Page" or press Page Down
4. Navigate through multiple pages

**Expected Results**:
- ✅ Initial page shows first 50 queries
- ✅ Page indicator shows "Page 1 of N"
- ✅ Scrolling to bottom loads next page automatically (virtual scrolling)
- ✅ Page navigation fast (<2 seconds per page)
- ✅ Can jump to specific page number
- ✅ Applied filters persist across pages

---

### Test Scenario 3.8: Export to CSV

**Goal**: Verify query log export functionality.

**Steps**:
1. On query log (with or without filters applied)
2. Press `Ctrl+E` or click "Export" button
3. Choose save location and filename
4. Save file
5. Open CSV in spreadsheet application

**Expected Results**:
- ✅ Export prompt appears with file save dialog
- ✅ Default filename includes date: `pihole-queries-2025-12-05.csv`
- ✅ Export processes within 5 seconds for up to 1000 queries
- ✅ CSV contains all columns: timestamp, client, domain, type, status, reply, response time
- ✅ Filtered results: Only visible (filtered) queries exported
- ✅ CSV properly formatted and opens in Excel/LibreOffice

---

### Test Scenario 3.9: Add Domain from Query Log

**Goal**: Verify quick action to add domain to allowlist/blocklist.

**Steps**:
1. On query log, select a blocked query
2. Right-click or press `A` (Add to Allowlist)
3. Confirm action in prompt
4. Navigate to Domain Management screen
5. Verify domain was added

**Expected Results**:
- ✅ Context menu or keyboard shortcut shows options:
  - "Add to Allowlist"
  - "Add to Blocklist"
- ✅ Confirmation prompt: "Add `domain.com` to Allowlist?"
- ✅ On confirm, success notification: "Added to Allowlist"
- ✅ Domain appears in allowlist with comment: "Added from query log"
- ✅ If domain already in list, notification: "Domain already in Allowlist"

---

## User Story 4: Blocking Control

### Test Scenario 4.1: Enable/Disable Blocking

**Goal**: Verify toggling Pi-hole blocking status.

**Steps**:
1. On dashboard, note current blocking status (Enabled)
2. Press `B` or click "Disable Blocking" button
3. Observe confirmation dialog
4. Select "Disable indefinitely"
5. Confirm action
6. Observe status change
7. Re-enable blocking

**Expected Results**:
- ✅ Confirmation dialog appears: "Disable Pi-hole blocking?"
- ✅ Options presented:
  - Indefinitely
  - Temporary (with duration selection)
  - Cancel
- ✅ After confirmation:
  - Blocking status changes to "DISABLED" (red indicator)
  - Dashboard statistics stop showing blocked queries
  - Status updates within 2 seconds
- ✅ Re-enable button available: "Enable Blocking"
- ✅ Clicking Enable re-enables immediately with confirmation

---

### Test Scenario 4.2: Temporary Disable with Timer

**Goal**: Verify countdown timer for temporary blocking disable.

**Steps**:
1. From dashboard, click "Disable Blocking"
2. In confirmation dialog, select "Temporary"
3. Choose "5 minutes" from preset durations
4. Confirm
5. Observe countdown timer

**Expected Results**:
- ✅ **Duration options available**:
  - 30 seconds
  - 1 minute
  - 5 minutes
  - 15 minutes
  - 30 minutes
  - 1 hour
  - Custom (enter specific seconds)
- ✅ After confirmation:
  - Status shows "DISABLED (Timer: 4:59)" in yellow
  - Countdown timer decrements every second
  - Timer displayed prominently on dashboard and status bar
- ✅ **When timer expires** (wait 5 minutes or test with 30-second timer):
  - Blocking automatically re-enables
  - Status changes to "ENABLED" (green)
  - Notification: "Blocking automatically re-enabled"

---

### Test Scenario 4.3: Cancel Timer Early

**Goal**: Verify manual re-enable cancels active timer.

**Steps**:
1. Disable blocking with 15-minute timer
2. Wait 1 minute (timer at ~14:00 remaining)
3. Click "Enable Blocking" button
4. Confirm

**Expected Results**:
- ✅ Enable button available even with active timer
- ✅ Confirmation prompt: "Enable blocking now? This will cancel the timer."
- ✅ On confirm:
  - Timer immediately cancelled
  - Blocking status changes to "ENABLED"
  - No waiting for timer expiry

---

### Test Scenario 4.4: Add Disable Reason/Comment

**Goal**: Verify optional comment for temporary disable.

**Steps**:
1. Click "Disable Blocking"
2. Select "Temporary" with 5-minute timer
3. In dialog, locate "Reason (optional)" field
4. Enter: "Troubleshooting Netflix connection"
5. Confirm

**Expected Results**:
- ✅ Optional text field for reason/comment visible
- ✅ Max length 200 characters
- ✅ Comment saved with disable action
- ✅ Comment visible in status tooltip: Hover over timer shows "Reason: Troubleshooting Netflix connection"
- ✅ Comment logged for audit (future enhancement, may not be visible in UI)

---

### Test Scenario 4.5: Keyboard Shortcut

**Goal**: Verify quick toggle via keyboard shortcut.

**Steps**:
1. From any screen, press `Ctrl+B` (blocking toggle shortcut)
2. Observe action
3. Press `Ctrl+B` again

**Expected Results**:
- ✅ Shortcut works from any screen (dashboard, query log, domains)
- ✅ First press: Confirmation to disable appears
- ✅ Second press after enabling: Confirmation to enable appears
- ✅ Shortcut provides fast access without navigating to dashboard

---

## User Story 5: Domain Management

### Test Scenario 5.1: View Allowlist

**Goal**: Verify viewing allowlist entries.

**Steps**:
1. From dashboard, press `D` or navigate to "Domains"
2. Observe domain management screen
3. Ensure "Allowlist" tab is selected

**Expected Results**:
- ✅ Domain management screen loads within 2 seconds
- ✅ Tabs visible: "Allowlist" and "Blocklist"
- ✅ Allowlist entries displayed in table:
  - Domain name
  - Enabled status (checkmark or toggle)
  - Comment
  - Date added
- ✅ Search bar at top for filtering domains
- ✅ "Add Domain" button visible
- ✅ If empty: Message "No allowlist entries. Add a domain to get started."

---

### Test Scenario 5.2: Add Domain to Allowlist

**Goal**: Verify adding new domain to allowlist.

**Steps**:
1. On Allowlist tab, click "Add Domain" button
2. Enter domain: `example.com`
3. Enter comment: "Allowed for testing"
4. Ensure "Enabled" checkbox is checked
5. Click "Save"

**Expected Results**:
- ✅ Add dialog opens with fields:
  - Domain (required)
  - Comment (optional)
  - Enabled (checkbox, default: checked)
- ✅ Domain validation prevents invalid formats
- ✅ On save:
  - Domain added to allowlist
  - Appears in table immediately
  - Success notification: "Domain added to Allowlist"
- ✅ API call completes within 2 seconds

---

### Test Scenario 5.3: Add Wildcard Domain

**Goal**: Verify wildcard pattern support.

**Steps**:
1. Click "Add Domain"
2. Enter wildcard: `*.cdn.example.com`
3. Enter comment: "Allow all CDN subdomains"
4. Save

**Expected Results**:
- ✅ Wildcard pattern accepted (`*.subdomain.com` format)
- ✅ Domain added successfully
- ✅ Wildcard displayed in list with asterisk visible
- ✅ Invalid wildcards rejected (e.g., `ex*.com`, `*.*.com`)

---

### Test Scenario 5.4: Edit Domain Entry

**Goal**: Verify editing existing domain properties.

**Steps**:
1. Select an existing domain from list
2. Click "Edit" button or press Enter
3. Change comment to "Updated comment"
4. Toggle "Enabled" status to disabled
5. Save changes

**Expected Results**:
- ✅ Edit dialog opens pre-filled with current values
- ✅ Can modify comment and enabled status
- ✅ Domain field may be read-only or editable (depends on API support)
- ✅ On save:
  - Changes reflected in list immediately
  - Success notification: "Domain updated"
- ✅ Disabled domains shown with greyed-out style or disabled indicator

---

### Test Scenario 5.5: Delete Domain Entry

**Goal**: Verify removing domain from list.

**Steps**:
1. Select a domain from list
2. Press `Delete` key or click "Delete" button
3. Observe confirmation dialog
4. Confirm deletion

**Expected Results**:
- ✅ Confirmation prompt: "Delete `example.com` from Allowlist?"
- ✅ Warning if domain is enabled: "This domain is currently enabled. Deleting will immediately affect blocking behaviour."
- ✅ On confirm:
  - Domain removed from list
  - Success notification: "Domain deleted"
  - List updates immediately
- ✅ Cannot be undone (warn user)

---

### Test Scenario 5.6: Search/Filter Domains

**Goal**: Verify searching domains in list.

**Steps**:
1. On Allowlist with multiple entries, locate search bar
2. Enter search term: `example`
3. Observe filtered results

**Expected Results**:
- ✅ Search filters list in real-time (as you type)
- ✅ Only domains matching search term displayed
- ✅ Search is case-insensitive
- ✅ Wildcards supported in search (e.g., `*.example`)
- ✅ Clear search button resets to show all domains

---

### Test Scenario 5.7: Enable/Disable Individual Entry

**Goal**: Verify toggling enabled status of single domain.

**Steps**:
1. Select a domain from list
2. Click toggle/checkbox next to domain or press Space
3. Observe status change

**Expected Results**:
- ✅ Toggle switches immediately
- ✅ API call updates Pi-hole configuration
- ✅ Visual feedback: Enabled=checkmark/green, Disabled=empty/grey
- ✅ Change persists after refresh
- ✅ Disabled domains still visible but marked as inactive

---

### Test Scenario 5.8: Bulk Enable/Disable

**Goal**: Verify bulk operations on multiple domains.

**Steps**:
1. Select multiple domains using checkboxes or `Shift+Click`
2. Click "Bulk Actions" dropdown
3. Select "Disable Selected"
4. Confirm bulk action

**Expected Results**:
- ✅ Multi-select checkboxes allow selecting multiple domains
- ✅ Bulk actions menu shows options:
  - Enable Selected
  - Disable Selected
  - Delete Selected
- ✅ Confirmation prompt shows count: "Disable 5 selected domains?"
- ✅ Progress indicator shows operation status
- ✅ On completion:
  - Success count displayed: "4 domains disabled, 1 failed"
  - Failed operations listed with errors
  - List updates to reflect changes

---

### Test Scenario 5.9: Bulk Delete

**Goal**: Verify deleting multiple domains at once.

**Steps**:
1. Select 3-5 domains from list
2. Click "Bulk Actions" → "Delete Selected"
3. Confirm deletion

**Expected Results**:
- ✅ Strong confirmation prompt: "Delete 5 selected domains? This cannot be undone."
- ✅ List of domains to be deleted shown for review
- ✅ On confirm:
  - Progress indicator during deletion
  - Domains removed from list
  - Success message: "5 domains deleted"
- ✅ If some fail: Partial success reported with error details

---

### Test Scenario 5.10: Import Domains from File

**Goal**: Verify bulk import functionality.

**Steps**:
1. Prepare text file with domains (one per line):
   ```
   example.com
   *.cdn.example.com
   test.example.com
   ```
2. On Allowlist, click "Import" button
3. Select file
4. Review preview of domains to import
5. Confirm import

**Expected Results**:
- ✅ File picker opens for selecting text file
- ✅ Supported formats: .txt, .csv
- ✅ Preview shows:
  - Total domains found
  - Valid domains (green checkmark)
  - Invalid domains (red X with reason)
  - Duplicates (yellow warning)
- ✅ Options:
  - Skip duplicates (checkbox, default: checked)
  - Enable imported domains (checkbox, default: checked)
- ✅ On import:
  - Progress bar shows import status
  - Result summary: "Added 45 domains, skipped 5 duplicates, failed 2 invalid"
  - Imported domains appear in list
- ✅ Import processes up to 100 domains within 10 seconds

---

### Test Scenario 5.11: Export Domains to File

**Goal**: Verify exporting domain list to file.

**Steps**:
1. On Allowlist (with entries), click "Export" button
2. Choose save location and filename
3. Save file
4. Open file in text editor

**Expected Results**:
- ✅ File save dialog with default name: `pihole-allowlist-2025-12-05.txt`
- ✅ Export completes within 3 seconds for up to 500 domains
- ✅ File format: One domain per line
- ✅ Optional: Include comments as line comments (`# comment`)
- ✅ Can re-import exported file

---

### Test Scenario 5.12: Switch Between Allowlist and Blocklist

**Goal**: Verify tab navigation between lists.

**Steps**:
1. View Allowlist tab
2. Click "Blocklist" tab
3. Observe blocklist entries
4. Add domain to blocklist
5. Switch back to Allowlist

**Expected Results**:
- ✅ Tabs switch instantly (<100ms)
- ✅ Each list maintains independent state (search, filters, page)
- ✅ Domain operations work identically on both lists
- ✅ Clear visual distinction which list is active (tab highlighting)
- ✅ Keyboard shortcut: `Ctrl+Tab` switches between lists

---

## Cross-Cutting Tests

### Test Scenario X.1: Keyboard Navigation

**Goal**: Verify all features accessible via keyboard.

**Steps**:
1. Launch TUI
2. Navigate through all screens using only keyboard
3. Perform actions using keyboard shortcuts

**Expected Results**:
- ✅ Tab key moves focus between elements
- ✅ Enter/Space activates buttons
- ✅ Arrow keys navigate lists/tables
- ✅ Escape closes dialogs
- ✅ All features have keyboard shortcuts (listed in help: `F1`)
- ✅ Shortcuts work from any screen

---

### Test Scenario X.2: Terminal Resize

**Goal**: Verify TUI adapts to terminal window size changes.

**Steps**:
1. Launch TUI with standard terminal size (120x30)
2. Resize terminal to minimum (80x24)
3. Resize to very large (200x60)

**Expected Results**:
- ✅ Layout adapts within 200ms of resize
- ✅ At 80x24 minimum:
  - All content remains readable
  - Scrollbars appear for overflow
  - No display corruption
- ✅ At large sizes:
  - Content expands to use space
  - Tables show more columns/rows
  - Statistics panels arrange optimally
- ✅ No crashes or hangs during rapid resizing

---

### Test Scenario X.3: Error Handling

**Goal**: Verify graceful error handling and user-friendly messages.

**Test Cases**:
1. **Network timeout**: Disconnect network mid-operation
   - ✅ Error: "Connection lost. Retrying..."
   - ✅ Auto-reconnect attempts

2. **Invalid API response**: Mock malformed JSON response
   - ✅ Error: "Unexpected response from Pi-hole. Please try again."
   - ✅ App remains functional

3. **Session expired**: Wait for session expiry without renewal
   - ✅ Prompt: "Session expired. Please log in again."
   - ✅ Re-auth without losing UI state

4. **Permission denied**: Try operation without proper permissions
   - ✅ Error: "Operation not permitted. Check Pi-hole admin rights."

5. **Rate limit**: Make rapid repeated requests
   - ✅ Warning: "Too many requests. Please wait [X] seconds."
   - ✅ Countdown shown until rate limit resets

**Expected**: All errors display user-friendly messages, log technical details, and provide recovery options.

---

### Test Scenario X.4: Performance with Large Datasets

**Goal**: Verify TUI remains responsive with large data volumes.

**Test Cases**:
1. **Query log with 10,000+ entries**:
   - ✅ Initial load <2 seconds
   - ✅ Pagination/scrolling smooth
   - ✅ Filtering <500ms

2. **Domain list with 500+ entries**:
   - ✅ List loads <2 seconds
   - ✅ Search real-time (<100ms per keystroke)
   - ✅ Bulk operations complete within acceptable time

3. **Long-running session (1+ hour)**:
   - ✅ Memory usage remains <150MB
   - ✅ No memory leaks
   - ✅ UI remains responsive

---

## Test Completion Checklist

**Phase 1 Features Complete When**:

- [ ] All User Story 1 scenarios pass (Authentication)
- [ ] All User Story 2 scenarios pass (Dashboard)
- [ ] All User Story 3 scenarios pass (Query Log)
- [ ] All User Story 4 scenarios pass (Blocking Control)
- [ ] All User Story 5 scenarios pass (Domain Management)
- [ ] All Cross-cutting scenarios pass (Keyboard, Resize, Errors, Performance)

**Known Limitations / Future Enhancements**:
- Blocklist management (external sources) - Out of Phase 1 scope
- Client statistics per device - Out of Phase 1 scope
- Historical trends/charts - Out of Phase 1 scope
- Theme customisation - Out of Phase 1 scope

**Test Environment Notes**:
- Test with active Pi-hole processing real queries for realistic data
- Test both 2FA enabled and disabled scenarios
- Test on different terminal emulators (iTerm2, Terminal.app, Windows Terminal, etc.)
- Test on minimum supported terminal size (80x24)

---

## Manual Testing Log Template

```
Date: _____________
Tester: _____________
Pi-hole Version: _____________
TUI Version: _____________

| Test ID | Scenario | Result | Notes |
|---------|----------|--------|-------|
| 1.1     | First-time login | ☐ PASS ☐ FAIL | |
| 1.2     | Login with 2FA | ☐ PASS ☐ FAIL | |
| ...     | ...              | ...            | |

Issues Found:
1. [Description]
2. [Description]
```
