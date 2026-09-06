# SmartCivicAI — Errors Found & Fixed, Test Report

I set the whole stack up for real (installed Postgres, created the DB, installed
backend deps in a venv, ran Alembic migrations, ran the seed script, booted the
live API server, and built the React frontend) and drove it with real HTTP
requests rather than just reading the code. Six real bugs were found and fixed.

## Bugs found and fixed

### 1. Language enum mismatch — every user/complaint insert failed (critical)
`backend/app/models/user.py` and `backend/app/models/complaint.py` declared
`Enum(LanguageCode, ...)` without `values_callable`. SQLAlchemy's default
behavior for a Python `enum.Enum` is to store the member **name** (`"EN"`),
but the hand-written Alembic migration created the Postgres enum type using
the member **value** (`"en"`). Every attempt to insert a user or a complaint
raised `invalid input value for enum language_code: "EN"`.

**Fix:** added `values_callable=lambda e: [x.value for x in e]` to both
`Enum(LanguageCode, ...)` column definitions.

### 2. bcrypt / passlib incompatibility
`requirements.txt` pinned `bcrypt==4.2.1`, but `passlib==1.7.4` reads
`bcrypt.__about__.__version__`, an attribute bcrypt removed in 4.1+.
Hashing/verifying still worked, but every single call logged a full
spurious traceback (`(trapped) error reading bcrypt version`).

**Fix:** pinned `bcrypt==4.0.1` in `requirements.txt`, documented why.

### 3. `.local` demo emails rejected by validation — nobody could log in (critical)
Every seeded demo account (`admin@smartcivicai.local`,
`officer@smartcivicai.local`, `citizen@smartcivicai.local`) used a reserved
IANA special-use TLD. Pydantic's `EmailStr` (via `email_validator`) rejects
`.local` addresses **regardless of the deliverability check**, so the
documented demo credentials returned `422 Unprocessable Entity` on login —
i.e. the credentials in every doc file didn't actually work.

**Fix:** renamed the domain to `smartcivicai.gov.in` in `app/seed.py` and
across `docs/BUILD_STATUS.md`, `docs/running-frontend.md`,
`docs/testing-guide.md`. Verified the frontend's role-based login routing
doesn't depend on the email domain (it reads the `role` field from the API
response), so this was safe to change.

### 4. Unsafe email defaults caused ~10s hangs on every complaint action
`backend/.env.example` — the file the project tells you to `cp` to `.env` —
shipped `EMAIL_ENABLED=true` with a placeholder password
(`YOUR_GMAIL_APP_PASSWORD`, which is non-empty and so passes the "is a
password configured" check). Result: a fresh setup silently attempted a
real SMTP connection to `smtp.gmail.com` on every complaint submission /
status change / officer assignment, each one blocking for the full 10s
timeout before failing. Every other optional integration in this project
(AI provider, CV provider, prediction provider, seed-on-start) defaults to
off; email didn't.

**Fix:** defaulted `EMAIL_ENABLED=false` in `backend/.env.example` and in
`Settings.EMAIL_ENABLED` (`app/core/config.py`). (The root-level
`.env.example` and `docker-compose.yml` already had the correct default —
only the backend-local file and the class default were wrong.)

### 5. Debug logging flooded output from third-party libraries
`DEBUG=true` (the default) set the **root** logger to `DEBUG`, so
`python-multipart` dumped raw byte-range tracing for every single field of
every file upload. Not a functional bug, but made real logs unreadable.

**Fix:** kept the root logger at `INFO`, scoped `DEBUG` to the app's own
`smartcivicai` logger, and explicitly set `python_multipart`/`multipart`
loggers to `WARNING`.

### 6. Backend Docker image targeted an unverified Python version
`backend/Dockerfile` targeted `python:3.14-slim`, called out in the
project's own docs as a real availability risk (3.14 is very new; some
wheels/mirrors may lag). Since I verified this exact codebase runs cleanly
end-to-end on Python 3.12.3 with zero code changes, I removed the
documented risk rather than leaving it as a caveat.

**Fix:** pinned `FROM python:3.12-slim` in `backend/Dockerfile`, updated
the corresponding note in `requirements.txt`.

## What was tested (and passed) after the fixes

**Auth:** register (incl. duplicate-email 409, weak-password 422), login for
all 3 roles, `GET/PATCH /auth/me`, refresh-token flow (incl. invalid-token
401).

**Complaints:** submission with image upload, AI demo pipeline
(classify → priority → route → citizen response), status-transition graph
(rejects invalid jumps like `PENDING → RESOLVED`), officer accept (incl. a
genuine 409 when a second officer tries to accept an already-claimed
complaint), resolve-with-remarks, citizen feedback (incl. ownership
enforcement — 403 for a non-owner).

**Admin:** AI override (module/category/priority/department) with
per-field audit logging, department & category CRUD, officer account
creation, user activation/deactivation (incl. blocked self-deactivation,
and a deactivated user can't log in), full RBAC enforcement (403s where
expected).

**Analytics:** all 15 documented endpoints return `200` with sane data.

**Other:** notifications (list, unread-count), audit-log listing.

**Frontend:** `npm install` and `npm run build` both succeed cleanly.
Cross-checked every API call in every `src/services/*.js` file — path,
HTTP method, and request-body field names — against the live backend route
table and Pydantic schemas: zero mismatches found. Traced routing
(`App.jsx` + `ProtectedRoute.jsx`) against every page component that
exists: fully wired, no dead links or missing routes.

**Docker:** `docker-compose.yml` validates as well-formed YAML with the
three expected services and volumes; `docker-entrypoint.sh` passes
`sh -n`. Could not run `docker compose up` itself — no Docker daemon in
this sandbox.

## Known, expected non-issues (not bugs)

- Real SMTP delivery fails in this sandbox because outbound network is
  restricted to an allowlist that doesn't include `smtp.gmail.com` — but
  `send_email()` catches this and degrades gracefully exactly as designed
  (the triggering request still succeeds).
- YOLOv8 civic-issue detection and the XGBoost/sklearn prediction models
  are demo-mode by default and require you to supply trained
  weights/enough data respectively — this is intentional and documented,
  not a bug.

## Demo credentials (all use password `Demo@1234`)

- Admin: `admin@smartcivicai.gov.in`
- Officer: `officer@smartcivicai.gov.in`
- Citizen: `citizen@smartcivicai.gov.in`

## To run it yourself

```bash
cd backend
python -m venv venv && source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL if your Postgres creds differ
alembic upgrade head
python -m app.seed     # optional — creates demo accounts + ~60 sample complaints
uvicorn app.main:app --reload

# in a second terminal
cd frontend
npm install
cp .env.example .env
npm run dev
```
