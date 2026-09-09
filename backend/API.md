# Freshers Party Backend — API Documentation

> API endpoints for Pass, Voting, Admin, and Events management.

---

## Base URL
```
http://localhost:8000
```

## Health Check
```
GET /health → { "status": "ok" }
```

---

## Pass Verification (Student Lookup)

### POST /api/pass/verify
Lookup a student by roll number or name.

**Request:**
```json
{
  "identifier_type": "roll_number" | "name",
  "value": "24ME001"
}
```

**Response (200):**
```json
{
  "valid": true,
  "student": {
    "roll_number": "24ME001",
    "name": "Rahul Kumar"
  }
}
```

or (ambiguous name):
```json
{
  "valid": false,
  "reason": "multiple_students_found",
  "message": "Multiple students have this name. Please enter your roll number."
}
```

or (not found):
```json
{
  "valid": false,
  "reason": "student_not_found",
  "message": "Student not registered."
}
```

---

## Voting

### GET /api/voting/candidates
Get all active candidates.

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "Candidate A",
    "category": "Mister Freshers",
    "photo": "url_or_null"
  }
]
```

### POST /api/voting/verify
Verify eligibility to vote (pre-flight check).

**Request:**
```json
{
  "roll_number": "24ME001",
  "name": "Rahul Kumar",
  "category": "Mister Freshers"
}
```

**Response (200):**
```json
{
  "valid": true,
  "already_voted": false
}
```

or:
```json
{
  "valid": false,
  "reason": "identity_mismatch" | "student_not_found" | "not_eligible",
  "message": "..."
}
```

### POST /api/voting/vote
Submit a vote.

**Request:**
```json
{
  "roll_number": "24ME001",
  "name": "Rahul Kumar",
  "candidate_id": 1,
  "category": "Mister Freshers"
}
```

**Response (200 — success):**
```json
{
  "success": true
}
```

**Response (200 — failure):**
```json
{
  "success": false,
  "reason": "already_voted" | "student_not_found" | "identity_mismatch" | "not_eligible" | "invalid_candidate",
  "message": "..."
}
```

### GET /api/voting/results?category=Mister%20Freshers
Get voting results for a category.

**Response (200):**
```json
{
  "category": "Mister Freshers",
  "results": [
    {
      "candidate_id": 1,
      "name": "Candidate A",
      "votes": 183
    }
  ]
}
```

Results sorted by votes descending.

---

## Admin (All Require Bearer Token)

**Authorization Header:**
```
Authorization: Bearer <jwt_token>
```

Invalid/missing token → `401 Unauthorized`

### POST /api/admin/login
Authenticate as admin and get JWT token.

**Request:**
```json
{
  "username": "admin_user",
  "password": "secure_password"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 28800
}
```

**Response (401):**
```json
{
  "detail": "Invalid username or password"
}
```

### GET /api/admin/votes
Get all votes with voter and candidate details.

**Response (200):**
```json
[
  {
    "voter_name": "Rahul Kumar",
    "voter_roll_number": "24ME001",
    "candidate_name": "Candidate A",
    "category": "Mister Freshers",
    "created_at": "2024-01-15T10:30:00"
  }
]
```

Sorted by `created_at` descending (most recent first).

### POST /api/admin/candidates
Create a new candidate.

**Request:**
```json
{
  "name": "Candidate B",
  "category": "Miss Freshers",
  "photo": "url_or_null"
}
```

**Response (200):**
```json
{
  "id": 2,
  "name": "Candidate B",
  "category": "Miss Freshers",
  "photo": null,
  "active": true
}
```

### PATCH /api/admin/candidates/{id}
Update a candidate.

**Request (any subset):**
```json
{
  "name": "Updated Name",
  "active": false
}
```

**Response (200):**
```json
{
  "id": 2,
  "name": "Updated Name",
  "category": "Miss Freshers",
  "photo": null,
  "active": false
}
```

**Response (404):**
```json
{
  "detail": "Candidate not found"
}
```

### POST /api/admin/events
Create a new event.

**Request:**
```json
{
  "name": "Freshers Party",
  "description": "Welcome event for new students",
  "start_time": "2024-01-20T18:00:00",
  "end_time": "2024-01-20T22:00:00"
}
```

**Response (200):**
```json
{
  "id": 1,
  "name": "Freshers Party",
  "description": "Welcome event for new students",
  "start_time": "2024-01-20T18:00:00",
  "end_time": "2024-01-20T22:00:00",
  "winner": null
}
```

### POST /api/admin/events/{event_id}/winner
Set the winner for an event.

**Request:**
```json
{
  "winner": "Candidate A"
}
```

**Response (200):**
```json
{
  "id": 1,
  "name": "Freshers Party",
  "description": "...",
  "start_time": "...",
  "end_time": "...",
  "winner": "Candidate A"
}
```

**Response (404):**
```json
{
  "detail": "Event not found"
}
```

---

## Events (Public)

### GET /api/events
Get all events.

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "Freshers Party",
    "description": "...",
    "start_time": "...",
    "end_time": "...",
    "winner": null
  }
]
```

### GET /api/events/{event_id}
Get a single event by ID.

**Response (200):**
```json
{
  "id": 1,
  "name": "Freshers Party",
  "description": "...",
  "start_time": "...",
  "end_time": "...",
  "winner": null
}
```

**Response (404):**
```json
{
  "detail": "Event not found"
}
```

---

## Error Handling

- **Invalid request body** → `422 Unprocessable Entity`
- **Unauthorized (missing/invalid token)** → `401 Unauthorized`
- **Resource not found** → `404 Not Found`
- **Business logic failure** → `200 OK` with `success: false` or `valid: false`
- **Server error** → `500 Internal Server Error` (generic, no traceback)

---

## Authentication

Admin endpoints require a valid JWT token in the `Authorization` header:
```
Authorization: Bearer <access_token>
```

- Token valid for **8 hours** (configurable via `ADMIN_JWT_EXPIRY_HOURS` env var)
- Get token via `POST /api/admin/login`
- Token expires after set duration; login again to get a new one
