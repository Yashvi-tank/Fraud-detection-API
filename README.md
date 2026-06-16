# Fraud Detection API

A production-quality **Fraud Detection API** that analyzes incoming financial transactions and determines whether they are potentially fraudulent. Phase 1 implements a **rule-based fraud engine** with a clean, modular architecture designed to support future capabilities such as JWT authentication, Redis caching, device/country tracking, machine learning prediction, and Docker deployment.

## Project Overview

The API receives transaction data (amount, merchant, country, device), evaluates it against configurable fraud rules, persists the result in PostgreSQL, and returns a risk score with a classification (`SAFE`, `REVIEW`, or `SUSPICIOUS`).

### Fraud Rules (Phase 1)

| Rule | Condition | Points | Reason |
|------|-----------|--------|--------|
| 1 | `amount > 1000` | +30 | High transaction amount |
| 2 | `country != France` | +25 | Foreign transaction detected |
| 3 | `device_id` starts with `NEW` | +20 | Unrecognized device |

### Risk Classification

| Score | Status |
|-------|--------|
| 0–30 | `SAFE` |
| 31–60 | `REVIEW` |
| 61+ | `SUSPICIOUS` |

## Architecture

```
Client Request
      │
      ▼
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  API Layer  │────▶│  Service Layer   │────▶│  Fraud Engine   │
│ (FastAPI)   │     │ (Transactions)   │     │ (Rule-based)    │
└─────────────┘     └────────┬─────────┘     └─────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │  (SQLModel)     │
                    └─────────────────┘
```

**Design principles:**

- **Separation of concerns** — routes delegate to services; fraud logic lives in a dedicated engine
- **Type safety** — Pydantic schemas and Python type hints throughout
- **Extensibility** — core modules (`config`, `database`, `services`) are ready for auth, caching, and ML layers

## Folder Structure

```
fraud-detection-api/
├── app/
│   ├── main.py                  # FastAPI application entry point
│   ├── core/
│   │   ├── config.py            # Environment-based settings
│   │   └── database.py          # Engine, session, and table init
│   ├── models/
│   │   └── transaction.py       # SQLModel Transaction table
│   ├── schemas/
│   │   └── transaction.py       # Pydantic request/response models
│   ├── services/
│   │   ├── fraud_engine.py      # Rule-based fraud evaluation
│   │   └── transaction_service.py
│   ├── api/
│   │   └── transactions.py      # Transaction endpoints
│   ├── utils/
│   └── tests/
│       ├── test_fraud_engine.py
│       └── test_api.py
├── alembic/                     # Database migrations
├── docker/
│   └── entrypoint.sh            # Wait for DB, run migrations, start API
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── requirements.txt
├── .env.example
├── .dockerignore
└── README.md
```

## Installation

### Prerequisites

- Python 3.12+ (for non-Docker local mode)
- PostgreSQL 14+ (for non-Docker local mode)
- Docker Desktop (recommended local mode)

### Setup

```bash
# Clone and enter the project
cd fraud-detection-api

# Create a virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate (Linux/macOS)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

### Database Setup

Create the PostgreSQL database:

```sql
CREATE DATABASE fraud_detection;
```

Apply migrations:

```bash
alembic upgrade head
```

> On first run, tables are also created automatically via `init_db()` in the application lifespan. For production, prefer Alembic migrations.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application display name | `Fraud Detection API` |
| `APP_VERSION` | API version string | `1.0.0` |
| `DEBUG` | Enable SQL echo logging | `false` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://postgres:postgres@localhost:5432/fraud_detection` |

Copy `.env.example` to `.env` and adjust values for your environment.

## Running Locally

### Docker (Recommended)

This starts both FastAPI and PostgreSQL, waits for DB readiness, runs Alembic migrations automatically, then starts the API.

```bash
# From project root
docker compose up --build
```

Access:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

Notes:

- API container uses Docker networking and connects to DB host `db` (not `localhost`).
- PostgreSQL data is persisted in the `postgres_data` Docker volume.
- To stop and remove containers:

```bash
docker compose down
```

To also remove the database volume:

```bash
docker compose down -v
```

Start the development server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open the interactive API documentation:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Run Tests

```bash
pytest app/tests -v
```

## API Examples

### Health Check

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "healthy"
}
```

### Check a Transaction

```bash
curl -X POST http://localhost:8000/transactions/check \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "amount": 1500,
    "merchant": "Amazon",
    "country": "Brazil",
    "device_id": "NEW_DEVICE_001"
  }'
```

```json
{
  "transaction_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "risk_score": 75,
  "status": "SUSPICIOUS",
  "reasons": [
    "High transaction amount",
    "Foreign transaction detected",
    "Unrecognized device"
  ]
}
```

### List All Transactions

```bash
curl http://localhost:8000/transactions
```

### Get a Transaction by ID

```bash
curl http://localhost:8000/transactions/<transaction_id>
```

## Roadmap

- [ ] JWT authentication
- [ ] Redis caching for device/country risk profiles
- [ ] Device and country tracking services
- [ ] ML-based fraud prediction
- [ ] Docker and CI/CD deployment

## License

MIT
