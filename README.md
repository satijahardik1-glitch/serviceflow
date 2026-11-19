# ServiceFlow – Trusted Technician Marketplace

Home-services booking platform connecting customers with verified local technicians
(electricians, plumbers, AC repair, carpenters).

**Stack:** React + Vite + Tailwind · FastAPI + Pydantic · PostgreSQL + SQLAlchemy 2.0 + Alembic · JWT (bcrypt) with RBAC.

## Quick start (local, one command)

```bash
./run.sh        # builds the frontend, migrates + seeds a SQLite DB, serves everything at http://localhost:8000
```
Windows PowerShell steps are in "Manual local setup" below. Demo logins are in "Demo accounts".

## UI features

- **Dark mode** – toggle (🌙/☀️) in the navbar. Follows the OS setting by default, remembers the user's choice in `localStorage`, and is applied before first paint (no white flash). Implemented with Tailwind `darkMode: "class"`, a `ThemeContext`, and `dark:` variants on every component.
- **Responsive navbar** with a mobile menu, per-page browser-tab titles, scroll-to-top on navigation.
- **Error boundary** so an unexpected UI crash shows a friendly page instead of a blank screen.
- **Accessibility** – visible keyboard focus rings, `aria` labels on the theme switch/menu/star ratings, reduced-motion support.

## Production deployment

### Option A – Docker Compose (PostgreSQL + app)
```bash
cp .env.production.example .env        # fill in POSTGRES_PASSWORD, SECRET_KEY, ENCRYPTION_KEY, CORS_ORIGINS
docker compose up -d --build           # runs migrations automatically on start
docker compose exec app python create_admin.py --email you@company.com --name "Your Name"
```
Put a TLS-terminating reverse proxy (Caddy, nginx, a cloud load balancer) in front of port 8000 and serve over HTTPS.

### Option B – any PaaS (Render, Railway, Fly.io …)
Build with the included `Dockerfile` (it builds the frontend and the API into one image), attach a managed PostgreSQL, and set:

| Variable | Notes |
|---|---|
| `ENVIRONMENT` | `production` (enforces strong secrets, hides `/docs`, adds HSTS + CSP) |
| `DATABASE_URL` | `postgresql+psycopg2://user:pass@host:5432/db` |
| `SECRET_KEY` | ≥ 32 random chars. `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `ENCRYPTION_KEY` | Fernet key. `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` **Back it up** – losing it makes stored ID numbers unreadable |
| `CORS_ORIGINS` | Your public https origin(s), comma separated (no `*`) |
| `FORWARDED_ALLOW_IPS` | Your proxy's IP, so client IPs are read correctly for rate limiting |

The container runs `alembic upgrade head` on every start, then gunicorn with uvicorn workers (`WEB_CONCURRENCY`, default 2).
In production the app **refuses to start** with a weak/default `SECRET_KEY`, a missing `ENCRYPTION_KEY` or wildcard CORS, and `seed.py` refuses to run.
Create the first admin with `python create_admin.py`, never with seed data.

Probes: `GET /api/health` (liveness) · `GET /api/health/ready` (checks the database).

### Upgrading an existing install
```bash
pip install -r backend/requirements.txt
cd backend && alembic upgrade head     # migration 0002 encrypts any existing plaintext ID numbers
cd ../frontend && npm install && npm run build
```

## What "production-ready" covers here

| Area | Implementation |
|---|---|
| Sensitive data | ID numbers encrypted at rest (Fernet); technicians see only a masked value, admins see the full value and every admin view is logged |
| Auth | bcrypt, JWT (8h expiry by default), password must contain a letter + number, role checks on every endpoint |
| Abuse protection | Per-IP rate limits on login/register/diagnose, 15-minute lockout after 5 failed logins per account |
| Data integrity | Row-level `SELECT … FOR UPDATE` on the technician when booking/accepting, so overlapping jobs cannot be double-confirmed even under concurrent requests; one review per booking enforced by a unique constraint |
| Headers & errors | HSTS, CSP, nosniff, frame-deny, request IDs, structured request logging, no stack traces to clients |
| Scalability | Connection pooling, paginated list endpoints (`limit`/`offset`, `X-Total-Count`), asset caching |
| Operations | Alembic migrations, Docker image (non-root, healthcheck), docker-compose, GitHub Actions CI |
| Admin tooling | Manage categories and diagnosis rules (keywords, prices, durations, fallback) from the admin panel – no redeploy needed |
| Quality | 19 automated tests (auth, RBAC, diagnosis, matching, bookings, double-booking, encryption, admin, config safety); suite verified on SQLite **and** PostgreSQL |

### Known limitations (honest list)
- **Rate limiter is per process.** With several instances/workers each keeps its own counters; add a shared limiter (Redis / gateway / proxy) for strict global limits.
- **No email/SMS yet** – so no password reset, email verification or booking notifications. These need an SMTP/SMS provider.
- **Login token is kept in browser `localStorage`.** It is protected by a strict CSP, but httpOnly cookies + CSRF protection would be stronger.
- **"Proximity" is a city-name match**, not geo-distance. **No payments, chat or file upload** (ID *images*) yet.
- The Dockerfile and CI workflow could not be executed in the authoring sandbox; the same commands (migrations, gunicorn/uvicorn workers, tests on PostgreSQL) were run directly.

## Tests
```bash
cd backend
pip install -r requirements-dev.txt
pytest -q                                              # SQLite (fast)
TEST_DATABASE_URL=postgresql+psycopg2://user:pass@localhost/serviceflow_test pytest -q   # PostgreSQL (also runs the concurrency test)
```

## Project structure

```
serviceflow/
├── Dockerfile · docker-compose.yml · .env.production.example · run.sh
├── .github/workflows/ci.yml
├── backend/
│   ├── app/
│   │   ├── main.py            app, middleware (security headers, logging), health probes, SPA serving
│   │   ├── core/              config (validated) · security · crypto · ratelimit · pagination · deps (auth + RBAC)
│   │   ├── db/ · models/ · schemas/
│   │   ├── services/          diagnosis (rule engine) · matching (ranking) · ratings
│   │   └── routers/           auth · services · technicians · bookings · admin
│   ├── alembic/ (0001 schema, 0002 ID encryption) · seed.py (dev only) · create_admin.py
│   ├── tests/ · requirements.txt · requirements-dev.txt · .env.example
└── frontend/                  Vite + React + Tailwind
```

## Database schema

| Table | Key columns |
|---|---|
| `users` | id, name, email (unique), hashed_password, role (`customer`/`technician`/`admin`), phone, city, is_active |
| `technician_profiles` | id, user_id (1-1), bio, city, base_rate, experience_years, is_available, verification_status (`pending`/`verified`/`rejected`), id_document_type, id_document_number (**encrypted**), verification_note, avg_rating, review_count |
| `service_categories` | id, name, slug, description, icon |
| `technician_categories` | technician_id, category_id (many-to-many skills) |
| `diagnosis_rules` | id, category_id, symptom, keywords (csv), diagnosis, min_price, max_price, estimated_minutes, priority, is_default |
| `bookings` | id, customer_id, technician_id, category_id, problem_description, diagnosis, estimated_min/max_price, estimated_minutes, address, city, scheduled_at, status |
| `reviews` | id, booking_id (unique), customer_id, technician_id, rating 1-5, comment |
| `saved_technicians` | id, customer_id, technician_id (unique pair) |

Booking lifecycle: `pending → accepted → in_progress → completed`, or `rejected` / `cancelled`.

## Business logic
- **Diagnosis engine:** deterministic keyword scoring of description + selected symptoms against the category's rules (symptom chip +5, multi-word keyword +2, single keyword +1, priority as tie-breaker); no match → the category's fallback rule. The booking endpoint recomputes the estimate server-side.
- **Smart matching:** verified technicians with the skill, scored out of 100: rating 40 + same city 30 + available 20 + experience 10.
- **Privacy:** customer phone is shared with the technician only after acceptance; technicians are hidden from search until verified.

## Manual local setup (PostgreSQL)

Prerequisites: Python 3.11–3.12, Node 18+, PostgreSQL 14+.
```bash
psql -U postgres -c "CREATE DATABASE serviceflow;"
cd backend && python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env            # set DATABASE_URL and SECRET_KEY
alembic upgrade head && python seed.py
uvicorn app.main:app --reload --port 8000
# in another terminal
cd frontend && npm install && npm run dev        # http://localhost:5173 (proxies /api to :8000)
# or: npm run build  → the backend serves it at http://localhost:8000
```
(Python 3.13+ may lack prebuilt wheels for some pinned packages; use 3.12.)

## Demo accounts (dev only – from `seed.py`)

| Role | Email | Password |
|---|---|---|
| Admin | admin@serviceflow.com | `Admin@123` |
| Customer | neha@example.com / arjun@example.com | `Customer@123` |
| Technician (verified) | rajesh@ · amandeep@ · harpreet@ · gurpreet@ · manpreet@serviceflow.com | `Tech@1234` |
| Technician (pending / rejected) | sandeep@ / vikram@serviceflow.com | `Tech@1234` |

## API overview (all under `/api`; interactive docs at `/docs` outside production)

| Area | Endpoints |
|---|---|
| Auth | `POST /auth/register` · `POST /auth/login` · `GET /auth/me` |
| Services | `GET /services/categories` · `GET /services/symptoms` · `POST /services/diagnose` |
| Technicians | `GET /technicians/match` · `GET /technicians/{id}` · `GET/PUT /technicians/me` · `PATCH /technicians/me/availability` · `GET /technicians/saved` · `POST/DELETE /technicians/{id}/save` |
| Bookings | `POST /bookings` · `GET /bookings/mine` · `GET /bookings/{id}` · `PATCH /bookings/{id}/status` · `POST /bookings/{id}/review` |
| Admin | `GET /admin/metrics` · `/admin/users` · `/admin/technicians` · `/admin/bookings` (paginated) · `PATCH /admin/users/{id}/status` · `PATCH /admin/technicians/{id}/verification` · `POST/DELETE /admin/categories` · `GET/POST /admin/rules` · `PUT/DELETE /admin/rules/{id}` |
