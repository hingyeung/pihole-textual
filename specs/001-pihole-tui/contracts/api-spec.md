# API Contract Specification: Pi-hole v6 REST API

**Feature**: Pi-hole TUI Management Interface
**API Version**: Pi-hole v6.0+
**Base URL**: `http://pi.hole/api/` or `http://<pi-hole-ip>:8080/api/`
**Authentication**: Session-based (SID header)
**Response Format**: JSON

## Authentication Endpoints

### POST /api/auth

Authenticate with Pi-hole and obtain session ID.

**Request**:
```json
{
  "password": "string",
  "totp": "string"  // Optional, required if 2FA enabled
}
```

**Response** (200 OK):
```json
{
  "session": {
    "sid": "string",  // Session ID for subsequent requests
    "validity": 300   // Session validity in seconds
  }
}
```

**Errors**:
- `401 Unauthorized`: Invalid password
- `403 Forbidden`: Invalid TOTP code (if 2FA enabled)
- `429 Too Many Requests`: Rate limit exceeded

**Usage**:
- Store `sid` for authentication in subsequent requests
- Calculate expiry: `current_time + validity seconds`
- Include in header: `X-FTL-SID: <sid>` for all authenticated requests

---

### DELETE /api/auth

Logout and invalidate session.

**Headers**:
```
X-FTL-SID: <session-id>
```

**Response** (200 OK):
```json
{
  "success": true
}
```

**Errors**:
- `401 Unauthorized`: Invalid or expired SID

---

## Statistics Endpoints

### GET /api/stats/summary

Get summary statistics for dashboard.

**Headers**:
```
X-FTL-SID: <session-id>
```

**Response** (200 OK):
```json
{
  "queries": {
    "total": 15420,
    "blocked": 3254,
    "percent_blocked": 21.1
  },
  "clients": {
    "active": 12,
    "ever_seen": 45
  },
  "domains_on_blocklist": 1245678,
  "queries_forwarded": 8532,
  "queries_cached": 6888,
  "query_types": {
    "A": 8234,
    "AAAA": 5123,
    "PTR": 1245,
    "SRV": 234,
    "ANY": 123,
    "TXT": 461
  },
  "reply_types": {
    "IP": 11234,
    "CNAME": 2341,
    "NODATA": 1234,
    "NXDOMAIN": 611
  },
  "gravity_last_updated": 1733425200  // Unix timestamp
}
```

**Errors**:
- `401 Unauthorized`: Invalid or expired SID

---

### GET /api/stats/database/summary

Get database-level statistics (clients ever seen, historical data).

**Headers**:
```
X-FTL-SID: <session-id>
```

**Response** (200 OK):
```json
{
  "clients_ever_seen": 45,
  "total_queries_all_time": 1245678,
  "database_size_mb": 234.5
}
```

**Errors**:
- `401 Unauthorized`: Invalid or expired SID

---

## Blocking Control Endpoints

### GET /api/dns/blocking

Get current blocking status.

**Headers**:
```
X-FTL-SID: <session-id>
```

**Response** (200 OK):
```json
{
  "blocking": true,  // true=enabled, false=disabled
  "timer": null      // null if permanent, timestamp if temporary disable
}
```

**Errors**:
- `401 Unauthorized`: Invalid or expired SID

---

### POST /api/dns/blocking

Enable or disable DNS blocking.

**Headers**:
```
X-FTL-SID: <session-id>
```

**Request**:
```json
{
  "blocking": false,  // true=enable, false=disable
  "timer": 300        // Optional: duration in seconds for temporary disable
}
```

**Response** (200 OK):
```json
{
  "blocking": false,
  "timer": 1733425500  // Unix timestamp when timer expires (if timer set)
}
```

**Errors**:
- `401 Unauthorized`: Invalid or expired SID
- `400 Bad Request`: Invalid timer value

**Notes**:
- If `timer` is provided, blocking will auto-enable after timer expires
- Timer extends session validity
- If `blocking=true`, any active timer is cancelled

---

## Query Log Endpoints

### GET /api/queries

Get query log with pagination and filtering.

**Headers**:
```
X-FTL-SID: <session-id>
```

**Query Parameters**:
- `from`: Unix timestamp (optional) - Start of time range
- `until`: Unix timestamp (optional) - End of time range
- `blocked`: boolean (optional) - Filter by blocked status (true/false/omit for all)
- `client`: string (optional) - Filter by client IP or hostname
- `domain`: string (optional) - Filter by domain pattern
- `query_type`: string (optional) - Filter by query type (A, AAAA, etc.)
- `page`: integer (default: 1) - Page number (1-indexed)
- `limit`: integer (default: 50, max: 100) - Items per page

**Example**:
```
GET /api/queries?blocked=true&client=192.168.1.100&page=1&limit=50
```

**Response** (200 OK):
```json
{
  "queries": [
    {
      "id": 12345,
      "timestamp": 1733425200,
      "client": {
        "ip": "192.168.1.100",
        "hostname": "johns-laptop"
      },
      "domain": "ads.example.com",
      "query_type": "A",
      "status": "blocked",
      "reply_type": "IP",
      "response_time_ms": 12,
      "blocklist": "StevenBlack's list"
    },
    {
      "id": 12344,
      "timestamp": 1733425195,
      "client": {
        "ip": "192.168.1.101",
        "hostname": null
      },
      "domain": "example.com",
      "query_type": "AAAA",
      "status": "allowed",
      "reply_type": "IP",
      "response_time_ms": 45,
      "blocklist": null
    }
  ],
  "pagination": {
    "total_count": 15420,
    "page": 1,
    "page_size": 50,
    "total_pages": 309
  }
}
```

**Status Values**:
- `allowed`: Query was allowed
- `blocked`: Query was blocked by blocklist
- `forwarded`: Query forwarded to upstream DNS
- `cached`: Query answered from cache

**Errors**:
- `401 Unauthorized`: Invalid or expired SID
- `400 Bad Request`: Invalid query parameters

---

## Domain List Endpoints

### GET /api/domains

Get domain list entries (allowlist or blocklist).

**Headers**:
```
X-FTL-SID: <session-id>
```

**Query Parameters**:
- `type`: integer (required) - 0=allowlist, 1=blocklist
- `search`: string (optional) - Search pattern
- `enabled`: boolean (optional) - Filter by enabled status
- `page`: integer (default: 1) - Page number
- `limit`: integer (default: 50, max: 100) - Items per page

**Example**:
```
GET /api/domains?type=0&page=1&limit=50
```

**Response** (200 OK):
```json
{
  "domains": [
    {
      "id": 123,
      "domain": "example.com",
      "type": 0,
      "enabled": true,
      "comment": "Allow for work purposes",
      "date_added": 1733425200
    },
    {
      "id": 124,
      "domain": "*.cdn.example.com",
      "type": 0,
      "enabled": true,
      "comment": "Wildcard for CDN",
      "date_added": 1733425300
    }
  ],
  "pagination": {
    "total_count": 45,
    "page": 1,
    "page_size": 50,
    "total_pages": 1
  }
}
```

**Errors**:
- `401 Unauthorized`: Invalid or expired SID
- `400 Bad Request`: Invalid type parameter (must be 0 or 1)

---

### POST /api/domains

Add new domain to allowlist or blocklist.

**Headers**:
```
X-FTL-SID: <session-id>
```

**Request**:
```json
{
  "domain": "example.com",
  "type": 0,           // 0=allowlist, 1=blocklist
  "comment": "Optional comment",
  "enabled": true
}
```

**Response** (201 Created):
```json
{
  "id": 125,
  "domain": "example.com",
  "type": 0,
  "enabled": true,
  "comment": "Optional comment",
  "date_added": 1733425400
}
```

**Errors**:
- `401 Unauthorized`: Invalid or expired SID
- `400 Bad Request`: Invalid domain format or type
- `409 Conflict`: Domain already exists in this list

---

### PUT /api/domains/{id}

Update existing domain entry.

**Headers**:
```
X-FTL-SID: <session-id>
```

**Path Parameters**:
- `id`: integer - Domain entry ID

**Request** (all fields optional, provide only fields to update):
```json
{
  "domain": "updated-example.com",
  "comment": "Updated comment",
  "enabled": false
}
```

**Response** (200 OK):
```json
{
  "id": 125,
  "domain": "updated-example.com",
  "type": 0,
  "enabled": false,
  "comment": "Updated comment",
  "date_added": 1733425400
}
```

**Errors**:
- `401 Unauthorized`: Invalid or expired SID
- `404 Not Found`: Domain ID not found
- `400 Bad Request`: Invalid domain format

---

### DELETE /api/domains/{id}

Remove domain from list.

**Headers**:
```
X-FTL-SID: <session-id>
```

**Path Parameters**:
- `id`: integer - Domain entry ID

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Domain removed successfully"
}
```

**Errors**:
- `401 Unauthorized`: Invalid or expired SID
- `404 Not Found`: Domain ID not found

---

### PATCH /api/domains/{id}

Partial update (commonly used for enable/disable).

**Headers**:
```
X-FTL-SID: <session-id>
```

**Path Parameters**:
- `id`: integer - Domain entry ID

**Request**:
```json
{
  "enabled": false
}
```

**Response** (200 OK):
```json
{
  "id": 125,
  "domain": "example.com",
  "type": 0,
  "enabled": false,
  "comment": "Optional comment",
  "date_added": 1733425400
}
```

**Errors**:
- `401 Unauthorized`: Invalid or expired SID
- `404 Not Found`: Domain ID not found

---

## Common Response Patterns

### Success Response

```json
{
  "success": true,
  "data": { /* endpoint-specific data */ }
}
```

### Error Response

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    /* Optional additional error context */
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `authentication_required` | 401 | No SID provided or SID invalid |
| `session_expired` | 401 | SID expired, re-authentication required |
| `forbidden` | 403 | Authenticated but operation not permitted |
| `not_found` | 404 | Resource not found |
| `validation_error` | 400 | Invalid request parameters |
| `conflict` | 409 | Resource already exists |
| `rate_limit_exceeded` | 429 | Too many requests |
| `server_error` | 500 | Internal Pi-hole error |

---

## Authentication Header

All authenticated endpoints require session ID in header:

```
X-FTL-SID: <session-id>
```

Example:
```
GET /api/stats/summary HTTP/1.1
Host: pi.hole
X-FTL-SID: abc123def456
```

---

## Pagination Pattern

Endpoints returning lists use consistent pagination:

**Request Parameters**:
- `page`: integer (1-indexed, default: 1)
- `limit`: integer (items per page, default: 50, max: 100)

**Response Structure**:
```json
{
  "data": [ /* array of items */ ],
  "pagination": {
    "total_count": 1000,
    "page": 1,
    "page_size": 50,
    "total_pages": 20
  }
}
```

---

## Rate Limiting

Pi-hole API implements rate limiting to prevent abuse:

- **Authentication**: 5 attempts per minute per IP
- **General API**: 100 requests per minute per session
- **Bulk operations**: 10 requests per minute per session

**Rate Limit Headers** (included in responses):
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1733425500
```

If rate limit exceeded, API returns `429 Too Many Requests` with `Retry-After` header.

---

## Timeouts and Retries

**Recommended Client Behavior**:
- **Connect timeout**: 5 seconds
- **Read timeout**: 30 seconds
- **Retry strategy**: Exponential backoff for 5xx errors and network errors
- **Max retries**: 3 attempts
- **Backoff**: 1s, 2s, 4s between retries

**Session Renewal**:
- Renew session at 80% of validity period
- If renewal fails, attempt re-authentication
- Maximum session validity: 300 seconds (5 minutes)

---

## Domain Validation Rules

When adding/updating domains:

**Valid Formats**:
- Standard domain: `example.com`
- Subdomain: `sub.example.com`
- Wildcard: `*.example.com` (matches all subdomains)

**Invalid Formats**:
- IP addresses: `192.168.1.1` (use clients for IP filtering)
- Partial wildcards: `ex*.com` (only `*.domain` supported)
- Invalid characters: domains with spaces, special chars
- Empty strings or whitespace only

**Validation**:
- Domain length: 1-253 characters
- Label length: 1-63 characters per label
- Characters: alphanumeric, hyphens, dots only
- Must not start/end with hyphen or dot

---

## Implementation Notes for Client

1. **Session Management**:
   - Store SID securely (encrypted if persisted)
   - Track expiry and renew proactively
   - Handle 401 by attempting renewal, then re-auth if renewal fails

2. **Error Handling**:
   - Distinguish between auth errors (401), validation errors (400), and server errors (500)
   - Provide user-friendly messages for common errors
   - Log full error details for debugging

3. **Pagination**:
   - Calculate total pages: `ceil(total_count / page_size)`
   - Implement virtual scrolling for large datasets
   - Cache pages to reduce API calls

4. **Real-time Updates**:
   - Poll endpoints at configurable intervals
   - Use query parameter filters to fetch only new data where possible
   - Implement debouncing for user-triggered filters

5. **Bulk Operations**:
   - No native bulk API support - make sequential requests
   - Show progress indicator for operations on multiple items
   - Continue on error, report failures at end

6. **Offline Handling**:
   - Detect network errors vs API errors
   - Show clear connection status
   - Cache last successful data for display with "stale" indicator
