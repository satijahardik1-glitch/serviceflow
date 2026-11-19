#!/usr/bin/env bash
# One-command local launcher: builds the frontend, sets up the backend, serves everything on :8000
set -e
cd "$(dirname "$0")"

( cd frontend && npm install --no-audit --no-fund && npm run build )

cd backend
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt

# No .env yet? Use a zero-setup SQLite database so no PostgreSQL is needed for a quick look.
if [ ! -f .env ]; then
  echo "DATABASE_URL=sqlite:///./serviceflow.db" > .env
  echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(48))')" >> .env
  echo "CORS_ORIGINS=http://localhost:8000,http://localhost:5173" >> .env
  echo "RATE_LIMIT_ENABLED=true" >> .env
fi

alembic upgrade head
python seed.py
echo; echo "ServiceFlow running at http://localhost:8000"; echo
uvicorn app.main:app --host 0.0.0.0 --port 8000
