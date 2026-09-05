# Freshers Party Backend — Testing Guide

> Comprehensive test suite for all components (Parts 1–6 of the spec).

---

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_student_lookup.py
pytest tests/test_voting.py
pytest tests/test_admin.py
```

### Run Specific Test Class or Function

```bash
pytest tests/test_student_lookup.py::TestNormalization
pytest tests/test_student_lookup.py::TestNormalization::test_normalize_roll_uppercase
```

### Run with Verbose Output

```bash
pytest -v
```

### Run and Stop on First Failure

```bash
pytest -x
```

### Run with Coverage Report

```bash
pytest --cov=app --cov-report=html
```

---

## Test Suite Overview

### 1. Student Lookup Tests (`test_student_lookup.py`)
Tests for `student_service.py` — normalization and matching logic.

**Test Coverage:**
- ✅ Roll number normalization (uppercase, whitespace trimming)
- ✅ Name normalization (whitespace trimming, case-insensitive matching)
- ✅ Student lookup by roll number (exact, normalized, not found)
- ✅ Student lookup by name (unique, case-insensitive, ambiguous, not found)
- ✅ Student identity verification (roll + name validation)

**Acceptance Criteria Met:**
- [ ] Roll lookup: `24ME001`, `24me001`, `" 24me001 "` all resolve to the same student.
- [ ] Name lookup: `Rahul Kumar`, `rahul kumar`, `" Rahul Kumar "` all resolve the same way.
- [ ] Two students sharing a name → no data leaked.
- [ ] Unknown roll number and unknown name both → `student_not_found`.

---

### 2. Pass Verification Tests (`test_pass_verification.py`)
Tests for `/api/pass/verify` endpoint — student lookup via API.

**Test Coverage:**
- ✅ Lookup by roll number (found, not found, normalized variants)
- ✅ Lookup by name (unique, not found, case-insensitive)
- ✅ Ambiguous name handling (multiple_students_found, no data leak)
- ✅ Response format validation

**Endpoints Tested:**
- `POST /api/pass/verify`

---

### 3. Voting Tests (`test_voting.py`)
Tests for voting endpoints — candidates, verification, vote submission, results.

**Test Coverage:**
- ✅ Get candidates (active only, no voter info)
- ✅ Voting eligibility verification (eligible, identity mismatch, not found, not eligible)
- ✅ Vote submission (success, identity mismatch, student not found, duplicate vote same category)
- ✅ Vote in different categories (allowed after voting in one category)
- ✅ Invalid candidate handling (inactive, wrong category)
- ✅ Voting results (empty, sorted by votes descending, no voter info)

**Endpoints Tested:**
- `GET /api/voting/candidates`
- `POST /api/voting/verify`
- `POST /api/voting/vote`
- `GET /api/voting/results?category=...`

**Acceptance Criteria Met:**
- [ ] Voting: correct roll + correct name → success.
- [ ] Voting: correct roll + wrong name → `identity_mismatch`.
- [ ] Voting: unknown roll → `student_not_found`, regardless of name.
- [ ] First vote in a category → success; second vote same category → `already_voted`; vote in different category → success.
- [ ] Public results contain only `candidate_id`, `name`, `votes` — assert no voter fields present.

---

### 4. Admin Tests (`test_admin.py`)
Tests for admin authentication and admin endpoints.

**Test Coverage:**
- ✅ Admin login (valid credentials, invalid password, invalid username)
- ✅ Admin authentication on endpoints (no token, invalid token, garbage token, malformed header)
- ✅ Admin vote records (empty, with data, voter/candidate info included)
- ✅ Candidate management (create, update, update not found)
- ✅ Event management (create, set winner, set winner not found)

**Endpoints Tested:**
- `POST /api/admin/login`
- `GET /api/admin/votes`
- `POST /api/admin/candidates`
- `PATCH /api/admin/candidates/{id}`
- `POST /api/admin/events`
- `POST /api/admin/events/{event_id}/winner`

**Acceptance Criteria Met:**
- [ ] Admin routes reject requests with no token and with a garbage token (`401` in both cases).

---

### 5. Events Tests (`test_events.py`)
Tests for public events endpoints.

**Test Coverage:**
- ✅ Get all events
- ✅ Get single event (found, not found)
- ✅ Event structure validation

**Endpoints Tested:**
- `GET /api/events`
- `GET /api/events/{event_id}`

---

### 6. CSV Import Tests (`test_import.py`)
Tests for student import script (`scripts/import_students.py`).

**Test Coverage:**
- ✅ Basic import (CSV → SQLite)
- ✅ Idempotent import (duplicate detection on re-run)
- ✅ Flexible header matching (case/space-insensitive)
- ✅ Invalid row handling (missing roll or name, skipped)
- ✅ Roll number normalization during import
- ✅ Missing required column detection (abort with error)

**Acceptance Criteria Met:**
- [ ] Student import done when script runs against sample CSV and summary counts correct on re-run (0 new, N duplicates).

---

## Acceptance Criteria Checklist (Part 7/8)

Run all tests to verify:

- [ ] Roll lookup: `24ME001`, `24me001`, `" 24me001 "` all resolve to the same student.
- [ ] Name lookup: `Rahul Kumar`, `rahul kumar`, `" Rahul Kumar "` all resolve the same way.
- [ ] Two students sharing a name → `multiple_students_found`, no student data leaked.
- [ ] Unknown roll number and unknown name both → `student_not_found`.
- [ ] Voting: correct roll + correct name → success.
- [ ] Voting: correct roll + wrong name → `identity_mismatch`.
- [ ] Voting: unknown roll → `student_not_found`, regardless of name.
- [ ] First vote in a category → success; second vote same category → `already_voted`; vote in a different category → success.
- [ ] Public results contain only `candidate_id`, `name`, `votes` — assert no voter fields present.
- [ ] Restarting the app (new process, same `freshers.db`) preserves students and votes.
- [ ] Admin routes reject requests with no token and with a garbage token (`401` in both cases).

---

## Build Order Completion

Check off each stage as it passes tests:

1. **Student import** 
   - Run: `pytest tests/test_import.py`
   - Done when: Idempotent re-run shows 0 new, N duplicates

2. **Student lookup** 
   - Run: `pytest tests/test_student_lookup.py`
   - Done when: All normalization + matching tests pass

3. **Pass verification endpoint** 
   - Run: `pytest tests/test_pass_verification.py`
   - Done when: Exact spec match including ambiguous-name case

4. **Candidates** 
   - Run: `pytest tests/test_voting.py::TestVotingCandidates`
   - Done when: Model exists, active-only endpoint works

5. **Voting identity verification** 
   - Run: `pytest tests/test_voting.py::TestVotingVerification`
   - Done when: Uses student_service matching logic

6. **Vote submission** 
   - Run: `pytest tests/test_voting.py::TestVoteSubmission`
   - Done when: Full validation chain + unique constraint + transactions work

7. **Public results** 
   - Run: `pytest tests/test_voting.py::TestVotingResults::test_results_no_voter_info`
   - Done when: No voter identity leakage assertion passes

8. **Admin auth** 
   - Run: `pytest tests/test_admin.py::TestAdminLogin -k login`
   - Done when: bcrypt + JWT working, `/api/admin/login` works

9. **Admin vote records** 
   - Run: `pytest tests/test_admin.py::TestAdminVotes`
   - Done when: Joined voter/candidate info returned, admin-only enforced

10. **Events/winners** 
    - Run: `pytest tests/test_admin.py::TestAdminEvents`
    - Done when: CRUD operations work as specified

11. **Full test pass** 
    - Run: `pytest` (all tests)
    - Done when: All tests pass, including persistence checks

---

## Test Database

Tests use an **in-memory SQLite database** (`:memory:`) for isolation and speed.

- Each test function gets a fresh database (via `test_db` fixture)
- No files created on disk
- Fixtures create sample data automatically (students, candidates, admin user)

---

## Fixtures

Available in `tests/conftest.py`:

| Fixture | Purpose |
|---------|---------|
| `test_db` | Fresh in-memory SQLite database |
| `client` | FastAPI test client with test DB |
| `admin_user` | Pre-created test admin (username: testadmin, password: testpassword) |
| `admin_token` | Valid JWT token for test admin |
| `sample_students` | 4 test students (including 2 with same name) |
| `sample_candidates` | 4 test candidates (including 1 inactive) |

---

## Example: Running a Single Acceptance Criterion

**Roll lookup normalization:**
```bash
pytest tests/test_student_lookup.py::TestNormalization::test_normalize_roll_uppercase -v
pytest tests/test_student_lookup.py::TestNormalization::test_normalize_roll_strip_whitespace -v
pytest tests/test_student_lookup.py::TestStudentLookup::test_find_by_roll_normalized -v
pytest tests/test_pass_verification.py::TestPassVerification::test_lookup_by_roll_normalized -v
```

**Duplicate vote prevention:**
```bash
pytest tests/test_voting.py::TestVoteSubmission::test_vote_duplicate_same_category -v
```

**Admin authentication:**
```bash
pytest tests/test_admin.py::TestAdminAuthentication -v
```

---

## CI/CD Integration

To integrate with CI/CD (GitHub Actions, GitLab CI, etc.):

```yaml
# Example for GitHub Actions
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=app --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

---

## Troubleshooting

**Import Error: `app` not found**
- Make sure you're running pytest from the `backend/` directory
- Verify `backend/app/__init__.py` exists

**Database lock error**
- Using on-disk SQLite for tests? Switch to `:memory:` (default in conftest.py)

**Token not in fixtures?**
- Call `client.post("/api/admin/login", ...)` to get token, or use `admin_token` fixture

---

*Last updated: 2026-09-05 (Part 7/8 — Testing complete)*
