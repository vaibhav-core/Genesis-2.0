# Freshers Party Backend — Project Status

> Multi-part specification implementation progress (Parts 1–6/8 complete)

---

## Completion Status

### ✅ Part 1/8: Foundation
- [x] Repository structure created
- [x] Canonical normalization rules defined
- [x] Single source of truth for student matching (student_service.py)

### ✅ Part 2/8: Data Models
- [x] SQLAlchemy models: Student, Candidate, Vote, AdminUser, Event
- [x] Proper indexes, constraints, foreign keys
- [x] Pydantic schemas for all models

### ✅ Part 3/8: Security Model
- [x] Password hashing with bcrypt
- [x] JWT token creation/verification (8-hour expiry)
- [x] QR token HMAC signing
- [x] Admin creation script
- [x] Environment variable configuration

### ✅ Part 4/8: API Contracts (Pass & Voting)
- [x] `POST /api/pass/verify` — student lookup by roll/name
- [x] `GET /api/voting/candidates` — list active candidates
- [x] `POST /api/voting/verify` — eligibility check
- [x] `POST /api/voting/vote` — vote submission with full validation
- [x] `GET /api/voting/results` — results sorted by votes
- [x] Voting service with IntegrityError handling for race conditions

### ✅ Part 5/8: API Contracts (Admin & Events)
- [x] `POST /api/admin/login` — JWT authentication
- [x] `GET /api/admin/votes` — all votes with details
- [x] `POST /api/admin/candidates` — create candidate
- [x] `PATCH /api/admin/candidates/{id}` — update candidate
- [x] `POST /api/admin/events` — create event
- [x] `POST /api/admin/events/{event_id}/winner` — set winner
- [x] `GET /api/events` — list all events
- [x] `GET /api/events/{event_id}` — get single event
- [x] Bearer token authentication on all admin routes

### ✅ Part 6/8: Student Import Script
- [x] CSV import with flexible header matching
- [x] Idempotent (skips duplicates)
- [x] Skips invalid rows (missing roll/name)
- [x] Normalization applied
- [x] Summary printing

### ⏳ Part 7/8: Testing (Next)

### ⏳ Part 8/8: Non-goals/Assumptions (Next)

---

## Project Structure

```
Genesis-2.0/backend/
├── app/
│   ├── __init__.py
│   ├── main.py                          (FastAPI app setup)
│   ├── database.py                      (SQLAlchemy engine, SessionLocal)
│   ├── models.py                        (Student, Candidate, Vote, AdminUser, Event)
│   ├── schemas.py                       (Pydantic models for API)
│   ├── security.py                      (Password hashing, JWT, QR tokens)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── pass_router.py               (Student lookup endpoints)
│   │   ├── voting_router.py             (Voting endpoints)
│   │   ├── admin_router.py              (Admin endpoints + login)
│   │   └── events_router.py             (Public events endpoints)
│   └── services/
│       ├── __init__.py
│       ├── student_service.py           (Normalization & student lookup)
│       ├── voting_service.py            (Vote validation & submission)
│       └── admin_service.py             (Admin operations)
├── scripts/
│   ├── create_admin.py                  (Create admin users)
│   └── import_students.py               (CSV → SQLite import)
├── data/
│   ├── freshers.db                      (SQLite DB, created at runtime)
│   └── sample_students.csv              (Example for testing)
├── tests/                               (To be implemented)
├── .env.example                         (Environment variable template)
├── .gitignore                           (Excludes .env, .db, __pycache__, etc.)
├── requirements.txt                     (Python dependencies)
├── API.md                               (API documentation with examples)
├── SETUP.md                             (Setup & usage guide)
└── README.md                            (This file)
```

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create .env
```bash
cp .env.example .env
# Edit .env and set SECRET_KEY, QR_TOKEN_SECRET
```

### 3. Create Admin User
```bash
python scripts/create_admin.py
# Or: python scripts/create_admin.py --username admin --password pass
```

### 4. Run Server
```bash
uvicorn app.main:app --reload
# Server at http://localhost:8000
```

### 5. Import Students (Optional)
```bash
python scripts/import_students.py data/sample_students.csv
```

### 6. Test API
```bash
# Login
curl -X POST http://localhost:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"pass"}'

# Get votes (with token)
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/admin/votes
```

---

## Key Design Decisions

### Normalization
- **Single source of truth:** `student_service.py` (imported by pass_router and voting_router)
- Roll number: `strip().upper()`
- Name: `strip()`, case-insensitive comparison with `casefold()`

### Voting Validation
- **Order:** identity → eligibility → candidate → existing vote
- **Fail fast:** return first applicable error
- **Race condition handling:** IntegrityError caught on insert, treated as `already_voted`

### Authentication
- **Admin login:** username + password → JWT token (8-hour expiry)
- **Protected routes:** Bearer token in `Authorization` header
- **No IDs in responses:** only for internal use

### Data Persistence
- SQLite at `data/freshers.db`
- Never committed to repo
- Survives server restarts
- No external DB, no Docker

### Error Responses
- **Pass/Voting endpoints:** 200 OK with `valid: false` or `success: false` (business logic failures)
- **Admin endpoints:** 401 for auth failures, 404 for not found
- **Invalid requests:** 422 Unprocessable Entity
- **Server errors:** 500 with generic message (no traceback)

---

## Testing Strategy (Part 7/8)

Tests should cover:
1. Student normalization & lookup (duplicate names, missing students)
2. Voting validation (duplicate votes, identity mismatch, ineligible voters)
3. Admin authentication (valid/invalid tokens, expired tokens)
4. Candidate CRUD operations
5. Event management
6. CSV import (duplicates, invalid rows, flexible headers)
7. Race conditions (concurrent vote attempts)

---

## Next Steps (Parts 7–8)

### Part 7: Testing
- Unit tests for services
- Integration tests for API endpoints
- Test fixtures for sample data

### Part 8: Non-goals/Assumptions
- Scale & load testing
- Deployment guide
- Assumptions document

---

## API Endpoints Summary

See [API.md](API.md) for full documentation.

### Pass
- `POST /api/pass/verify`

### Voting
- `GET /api/voting/candidates`
- `POST /api/voting/verify`
- `POST /api/voting/vote`
- `GET /api/voting/results?category=...`

### Admin (Bearer token required)
- `POST /api/admin/login`
- `GET /api/admin/votes`
- `POST /api/admin/candidates`
- `PATCH /api/admin/candidates/{id}`
- `POST /api/admin/events`
- `POST /api/admin/events/{event_id}/winner`

### Events (Public)
- `GET /api/events`
- `GET /api/events/{event_id}`

### Health
- `GET /health`

---

## Database Schema

### students
- id (PK)
- roll_number (UNIQUE, indexed)
- name (indexed, not unique)
- branch (nullable)
- year (nullable)
- eligible_to_vote (default: True)

### candidates
- id (PK)
- name
- category (indexed)
- photo (nullable)
- active (default: True)

### votes
- id (PK)
- voter_id (FK → students.id)
- candidate_id (FK → candidates.id)
- category
- created_at (default: now)
- **Constraint:** UNIQUE(voter_id, category)

### admin_users
- id (PK)
- username (UNIQUE)
- password_hash

### events
- id (PK)
- name
- description (nullable)
- start_time (nullable)
- end_time (nullable)
- winner (nullable)

---

## Environment Variables

See `.env.example` for all options.

- `SECRET_KEY` — JWT signing secret (required)
- `QR_TOKEN_SECRET` — QR token HMAC secret (required)
- `ADMIN_JWT_EXPIRY_HOURS` — token lifetime (default: 8)
- `DATABASE_URL` — SQLite path (default: `sqlite:///./data/freshers.db`)

---

## Dependencies

See `requirements.txt`:
- FastAPI 0.104.1
- SQLAlchemy 2.0.23
- Uvicorn 0.24.0
- passlib[bcrypt] 1.7.4
- PyJWT 2.8.1
- python-dotenv 1.0.0
- Pydantic 2.5.0
- python-multipart 0.0.6

---

*Last updated: 2026-09-05 (Parts 1–6 complete)*
