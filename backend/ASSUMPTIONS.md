# Freshers Party Backend — Part 8/8: Non-Goals & Assumptions

> Final specification part documenting what is **not** being built and key assumptions made during implementation (Parts 1–7).

---

## 9. Explicit Non-Goals

The following are **explicitly out of scope** for the Freshers Party backend:

### No Frontend
- No web UI, mobile app, or frontend code of any kind.
- API is designed for direct client consumption (web, mobile, QR code reader, admin dashboard).
- Clients are responsible for all presentation logic.

### No Cloud Deployment
- No cloud database (AWS RDS, Google Cloud SQL, etc.).
- No containerization (Docker, Kubernetes, Helm, etc.).
- No managed services (Lambda, Cloud Functions, App Engine, etc.).
- Single file-based SQLite database on the **same LAN laptop** as the deployment machine.

### No Message Broker / Async Processing
- No Celery, RabbitMQ, Kafka, or similar.
- No background task queue or job scheduling.
- All operations are synchronous request/response.

### No Advanced Authentication
- No OAuth/OpenID Connect for admin login.
- No LDAP, SAML, or enterprise identity providers.
- No social login (Google, GitHub, etc.).
- Username/password + JWT is sufficient for college event admins.

### No Rate Limiting or WAF Hardening
- No rate limit middleware (no per-IP request caps).
- No DDoS protection, bot detection, or Web Application Firewall (WAF) features.
- No IP allowlisting/blocklisting.
- Justification: LAN-only college event with ~500 concurrent users, not internet-facing.

### No Horizontal Scaling
- No replication, clustering, or multi-node deployment patterns.
- No load balancing across instances.
- Single-machine deployment is the target.
- Database (SQLite) is not designed for write-heavy multi-instance scenarios anyway.

### No Persistence Layer Abstraction
- No repository pattern, data mapper, or domain-driven design abstractions.
- ORM (SQLAlchemy) is used directly in services.

### No External Integrations
- No email notifications.
- No SMS voting.
- No third-party voting platforms.
- No integration with student management systems (though CSV import is manual).

---

## 10. Assumptions Made (Override-Able)

Below are key implementation choices made to remove ambiguity. Each can be overridden by providing explicit counter-requirements.

### A. Admin Authentication Method

**Assumption:** Admin authentication is **JWT-based** (stateless), not server-side sessions.

```python
# Implementation used:
- bcrypt password hashing on creation/update
- JWT token issued on login (HS256, 8-hour expiry)
- Token passed in Authorization: Bearer <token> header on protected endpoints
- Token verified on every admin request (no session store needed)
```

**Why:** JWT is stateless, works well on single machine, and doesn't require session storage infrastructure.

**Override:** If you want server-side sessions instead:
- Store session tokens in a sessions table
- Update admin_router.py: get_current_admin() to query sessions table
- Add session cleanup job or TTL mechanism

---

### B. QR Token Signing

**Assumption:** QR tokens (if generated) are signed using **HMAC-SHA256** with a shared secret from environment.

```python
# Implementation pattern:
token = base64(roll_number) + "." + base64(hmac_sha256(QR_TOKEN_SECRET, roll_number))
# Verification:
split token by "."
verify HMAC using hmac.compare_digest() for constant-time comparison
```

**Why:** HMAC is simple, fast, and doesn't require key rotation for short-lived tokens.

**Override:** If you want JWT-signed QR codes:
- Generate QR as JWT with {roll_number, iat, exp}
- Include in QR code content
- Verify on scanning with verify_admin_token() logic

---

### C. Password Hashing Algorithm

**Assumption:** Passwords are hashed using **bcrypt** with a cost factor of 12.

```python
# Implementation:
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Hashing: pwd_context.hash(password)  → automatic salt + cost 12
# Verify: pwd_context.verify(plain, hash) → constant-time comparison
```

**Why:** bcrypt includes salt by default, is OWASP-recommended, and is slow enough to resist brute force.

**Override:** If you want Argon2 instead:
- pip install passlib[argon2]
- Change schemes in CryptContext to ["argon2"]
- No code changes needed (passlib API is identical)

---

### D. Category as Free-Text (Not Enum/Table)

**Assumption:** The `category` field on Candidate and Vote is a free-text string validated against a **hardcoded list in code**, not a separate database table or strict enum.

```python
# Implementation pattern (in voting_service.py or routers):
VALID_CATEGORIES = [
    "Mister Freshers",
    "Fresherina", 
    "Best Dancer",
    "Most Talented",
]

# Validation on vote submission:
if vote_request.category not in VALID_CATEGORIES:
    raise ValueError("Invalid category")
```

**Why:** 
- For a single college event, categories rarely change mid-event.
- Avoids extra database joins.
- Easier to validate in code than querying a table every request.

**Override:** If you want a database-backed Category table:
- Create Category(id, name, description) model
- Add category_id (FK) to Candidate and Vote
- Update routers to validate category_id exists before vote submission
- Results query now joins Category to get name

---

### E. SQLite WAL Mode Enabled

**Assumption:** SQLite **Write-Ahead Logging (WAL)** mode is **enabled** on initialization.

```python
# Implementation (in database.py, after engine creation):
from sqlalchemy import event
from sqlalchemy.pool import Pool

@event.listens_for(Pool, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    if isinstance(dbapi_conn, sqlite3.Connection):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()
```

**Why:** WAL mode allows concurrent readers and writers without file-locking conflicts, essential for ~500 concurrent users voting simultaneously.

**Override:** If you want rollback journal mode (default):
- Remove the PRAGMA pragma listener
- SQLite reverts to default journal_mode=DELETE

---

### F. No Separate QR Code Generation Endpoint

**Assumption:** QR code generation is **not implemented** as a backend endpoint.

**Why:**
- Admin can use free online tools (qr-server.com, qrcode.io) to generate QR codes from roll numbers
- Keeps backend focused on voting logic, not image generation
- QR content is just: `{roll_number}` or `{roll_number}.{qr_token}` (simple strings)

**Override:** If you want a QR generation endpoint:
- pip install qrcode[pil]
- POST /api/admin/qr/{roll_number} → returns PNG/SVG with embedded roll number
- Integrate in admin dashboard

---

### G. Student Import is Manual (Not Streaming/Background)

**Assumption:** Student CSV import is **synchronous, manual CLI script**, not a background job or streaming endpoint.

```python
# Usage:
python scripts/import_students.py data/students.csv
# Output: "Imported: 500, Skipped (duplicate): 0, Skipped (invalid): 2"
```

**Why:**
- College event scenario: ~500–1000 students, import is one-time operation
- No need for job queue or progress tracking
- CSV file is uploaded/placed in data/ folder manually

**Override:** If you want HTTP-based import endpoint:
- POST /api/admin/import (multipart/form-data)
- Stream CSV rows, return summary as 200 response
- Update admin_router.py to add endpoint

---

### H. No Voter Eligibility Restrictions (Except eligible_to_vote Flag)

**Assumption:** Only check is the `Student.eligible_to_vote` boolean flag — no branch-based, year-based, or time-window restrictions.

**Why:** Keeps voting logic simple. College admins can set eligible_to_vote=False to exclude specific students.

**Override:** If you want role-based voting (e.g., only second-year students can vote):
- Add role/branch/year validation in voting_service.verify_vote_eligibility()
- Update Student model with role field if needed
- Add where clause to vote eligibility check

---

### I. No Persistence of Votes Across Voting Sessions

**Assumption:** Votes are permanent once cast — no "clear votes and start over" feature (though admins can manually delete vote records).

**Why:**
- College event has one voting window
- Admins can run SQL directly on freshers.db to delete votes if needed
- No API endpoint for bulk vote deletion (deliberate friction)

**Override:** If you want a "reset voting" admin endpoint:
- POST /api/admin/votes/reset?category=Mister%20Freshers
- Deletes all votes in that category after admin confirmation
- Log deletion event to audit trail (if added)

---

### J. No Audit Trail / Logging

**Assumption:** No persistent audit log of admin actions (login, candidate creation, vote deletion, etc.).

**Why:** College event is low-stakes and transparent; admins are trusted. Add if needed.

**Override:** If you want audit logging:
- Create AuditLog(id, admin_id, action, timestamp, details_json) model
- Add logging to every admin endpoint
- Provide GET /api/admin/audit endpoint
- Update admin_router.py with logging calls

---

### K. No Vote Encryption in Database

**Assumption:** Votes are stored **plaintext** in the Vote table (voter_id, candidate_id, category, created_at).

**Why:**
- Database is on a single trusted LAN machine
- Admins have direct access to freshers.db file anyway
- Encryption would complicate testing and auditing

**Override:** If you want encrypted vote storage:
- Add app/security.py functions: encrypt_vote(data), decrypt_vote(data)
- Use Fernet (symmetric encryption from cryptography library)
- Store encrypted blob in Vote table
- Decrypt on retrieval (minimal performance impact for 500 votes)

---

### L. No Real-Time Voting UI State Sync

**Assumption:** Results are **polled** (client requests GET /api/voting/results), not pushed via WebSocket.

**Why:** Simpler backend, no connection state management, sufficient for college event.

**Override:** If you want real-time results:
- Add FastAPI WebSocket endpoint: WS /api/voting/results/stream?category=...
- Broadcast vote counts to all connected clients on every new vote
- Requires connection manager (see FastAPI WebSocket docs)
- Frontend handles reconnection logic

---

## Summary Table

| Component | Assumption | Override |
|-----------|-----------|----------|
| Admin Auth | JWT (stateless) | Server-side sessions |
| QR Tokens | HMAC-SHA256 | JWT-signed QR codes |
| Passwords | bcrypt | Argon2 |
| Categories | Hardcoded list in code | Database-backed table |
| SQLite | WAL mode enabled | Journal mode (default) |
| QR Generation | None (use online tools) | HTTP endpoint |
| Student Import | Manual CLI script | HTTP streaming endpoint |
| Eligibility | Only eligible_to_vote flag | Branch/year/time-window checks |
| Vote Persistence | Permanent (no reset API) | Add reset endpoint + audit trail |
| Audit Trail | None | Persistent action log |
| Vote Encryption | Plaintext in DB | Fernet encryption |
| Results Updates | Polled (HTTP) | WebSocket push |

---

## Affected Files (If Overriding Assumptions)

| Assumption | Files to Modify |
|-----------|-----------------|
| Admin Auth | `app/security.py`, `app/routers/admin_router.py` |
| QR Tokens | `app/security.py` |
| Passwords | `app/security.py` |
| Categories | `app/models.py`, `app/schemas.py`, `app/routers/voting_router.py` |
| SQLite WAL | `app/database.py` |
| Student Import | `scripts/import_students.py` or new `app/routers/admin_router.py` endpoint |
| Eligibility | `app/services/voting_service.py` |
| Vote Persistence | `app/routers/admin_router.py` |
| Audit Trail | Create `app/models.py` + new route |
| Vote Encryption | `app/security.py`, `app/models.py` |
| Results Updates | `app/main.py`, new WebSocket endpoint |

---

## Build Verification Checklist (All 8 Parts)

Run these to verify implementation completeness:

### Part 1: Foundation ✓
```bash
ls -la app/
# Verify: __init__.py, main.py, models.py, schemas.py, database.py, security.py
# Verify: routers/, services/, scripts/ directories exist
```

### Part 2: Data Models ✓
```bash
python -c "from app.models import Student, Candidate, Vote, AdminUser, Event; print('All models import OK')"
# Verify: 5 models with proper constraints, indexes, foreign keys
```

### Part 3: Security ✓
```bash
python -c "from app.security import hash_password, verify_password, create_admin_token; print('Security OK')"
# Verify: bcrypt hashing, JWT tokens, QR token signing
```

### Part 4-5: API Contracts ✓
```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/pass/verify -H "Content-Type: application/json" -d '{"identifier_type":"roll_number","value":"24ME001"}'
# Verify: All endpoints return proper responses
```

### Part 6: Student Import ✓
```bash
python scripts/import_students.py data/sample_students.csv
# Verify: Summary printed, DB populated
```

### Part 7: Testing ✓
```bash
pytest tests/ -v
# Verify: All 65+ tests pass
```

### Part 8: Non-Goals & Assumptions ✓
```bash
cat ASSUMPTIONS.md
# Verify: All 12 assumptions documented and overrideable
```

---

## Example: Overriding Assumption D (Categories as Database Table)

### Current (Assumption D):
```python
# In voting_router.py
VALID_CATEGORIES = ["Mister Freshers", "Fresherina", "Best Dancer"]
if vote_request.category not in VALID_CATEGORIES:
    raise ValueError("Invalid category")
```

### Override:
1. Add Category model to models.py:
```python
class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
```

2. Update Vote/Candidate:
```python
class Candidate(Base):
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category")

class Vote(Base):
    category_id = Column(Integer, ForeignKey("categories.id"))
```

3. Update routers:
```python
# In voting_router.py
category = db.query(Category).filter(Category.id == vote_request.category_id).first()
if not category:
    raise HTTPException(status_code=400, detail="Invalid category")
```

---

## Questions & Override Process

**To override any assumption:**

1. State the assumption number/letter (e.g., "Override Assumption C: Argon2 instead of bcrypt")
2. Provide new implementation requirement
3. Agent updates affected files and tests
4. Verify with: `pytest tests/ -v` and manual endpoint testing

**Example request:**
> "Override Assumption K: Implement vote encryption with Fernet. Votes in DB should be encrypted, decrypted on results retrieval."

---

**(End of Part 8/8 — Full specification complete)**

All 8 parts now delivered:
- ✅ Part 1: Foundation (repository structure, normalization rules)
- ✅ Part 2: Data Models (5 ORM models, schemas)
- ✅ Part 3: Security (bcrypt, JWT, QR tokens)
- ✅ Part 4: API Contracts (Pass & Voting endpoints)
- ✅ Part 5: API Contracts (Admin & Events endpoints)
- ✅ Part 6: Student Import Script (flexible CSV, idempotent)
- ✅ Part 7: Testing & Build Order (65+ tests, build order verification)
- ✅ Part 8: Non-Goals & Assumptions (this document)
