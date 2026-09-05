# Freshers Party Backend Setup

## 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## 2. Set Up Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

**Generate secure keys:**
```bash
# On Linux/Mac:
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Edit `.env` and set:
- `SECRET_KEY` — strong random string for JWT signing (copy the output above)
- `QR_TOKEN_SECRET` — strong random string for QR token HMAC (another random string)
- `ADMIN_JWT_EXPIRY_HOURS` — how long JWT tokens last (default: 8 hours)

## 3. Create Admin User

**Interactive mode (prompts for username & password):**
```bash
python scripts/create_admin.py
```

**Command-line mode:**
```bash
python scripts/create_admin.py --username admin_user --password secure_password
```

The password is hashed immediately with bcrypt and stored in the database. **You only need to do this once per admin account.**

## 4. Run the Server

```bash
uvicorn app.main:app --reload
```

Server runs at `http://localhost:8000`
- Health check: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

## 5. Import Students (Optional)

Import students from a CSV file:

```bash
python scripts/import_students.py path/to/students.csv
```

**CSV Format:**
- Required columns: `Roll Number` (or `Roll No`, `roll_number`), `Name`
- Optional columns: `Branch`, `Year`
- Case/space-insensitive header matching

**Example CSV:**
```
Roll Number,Name,Branch,Year
24ME001,Rahul Kumar,Mechanical,1
24ME002,Priya Singh,Mechanical,1
24CS001,Amit Patel,Computer Science,1
```

**Features:**
- ✓ Flexible column header matching (case-insensitive)
- ✓ Idempotent (skips duplicates on re-run)
- ✓ Normalizes roll numbers (uppercase, trimmed)
- ✓ Skips rows with missing roll number or name
- ✓ Prints summary: Imported, Skipped (duplicate), Skipped (invalid)

**Sample import:**
```bash
python scripts/import_students.py data/sample_students.csv
```

## 6. API Usage

### Health Check
```bash
curl http://localhost:8000/health
```

### Admin Login
```bash
curl -X POST http://localhost:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin_user","password":"secure_password"}'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 28800
}
```

### Use Token for Admin Endpoints
```bash
curl -H "Authorization: Bearer <access_token>" http://localhost:8000/api/admin/votes
```

For all API endpoints, see [API.md](API.md).

## 7. Run Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Suite
```bash
pytest tests/test_student_lookup.py     # Student normalization & lookup
pytest tests/test_pass_verification.py  # Pass endpoint tests
pytest tests/test_voting.py             # Voting endpoint tests
pytest tests/test_admin.py              # Admin authentication & endpoints
pytest tests/test_import.py             # CSV import script
```

### Run with Verbose Output
```bash
pytest -v
```

### Run and Stop on First Failure
```bash
pytest -x
```

For detailed testing guide, see [TESTING.md](TESTING.md).

---

## Security Notes

- **Never commit `.env`** — add it to `.gitignore`
- **SECRET_KEY and QR_TOKEN_SECRET** remain the same across restarts (tokens stay valid)
- **JWT tokens expire after 8 hours** — admin must log in again after expiry
- **Passwords are hashed** with bcrypt — plaintext is never stored
- Admin IDs and secrets are never returned in API responses
