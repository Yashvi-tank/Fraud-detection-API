#!/bin/sh
set -e

echo "Waiting for PostgreSQL to be ready..."
python - <<'PY'
import os
import time
import psycopg

database_url = os.getenv("DATABASE_URL", "")
# psycopg connect expects postgresql://, while SQLAlchemy uses postgresql+psycopg://
database_url = database_url.replace("+psycopg", "")

for attempt in range(60):
    try:
        with psycopg.connect(database_url, connect_timeout=2):
            print("PostgreSQL is ready.")
            break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("PostgreSQL did not become ready in time.")
PY

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
