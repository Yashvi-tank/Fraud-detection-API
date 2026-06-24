# Fraud Detection API

A production-quality **Fraud Detection API** that analyzes incoming financial transactions and determines whether they are potentially fraudulent. **Phase 1** delivers a rule-based fraud engine with PostgreSQL persistence. **Phase 1.5** adds pagination, filtering, sorting, and structured logging. **Phase 2** adds behavioral fraud detection using PostgreSQL transaction history. **Phase 3** introduces a hybrid Machine Learning fraud scoring layer using a Random Forest classifier.

## Project Overview

The API receives transaction data (amount, merchant, country, device), evaluates it against configurable fraud rules, persists the result in PostgreSQL, and returns a risk score with a classification (`SAFE`, `REVIEW`, or `SUSPICIOUS`).

### Phase 1 — Completed

- Rule-based fraud engine
- PostgreSQL persistence with SQLModel
- Alembic migrations
- FastAPI Swagger documentation
- Transaction creation via `POST /transactions/check`
- Transaction retrieval via `GET /transactions` and `GET /transactions/{id}`

### Phase 1.5 — Completed

- Paginated list endpoint with filters and sorting
- Standardized paginated response format
- Structured logging for fraud checks and database errors
- Expanded API test coverage

### Phase 2 — Completed

- Velocity detection (transaction burst analysis)
- Country change detection from user history
- Device history tracking (new device detection)
- User spending pattern anomaly detection
- Aggregated fraud reason reporting across static and behavioral rules

### Phase 3 — Completed

- Machine Learning fraud detection using a Random Forest classifier
- Standalone synthetic dataset generator (5,500+ samples)
- Full model training and evaluation pipeline
- Hybrid scoring blending rule-based and ML outputs: `final_score = min(100, rule_score + round(ml_probability * 20))`
- Persistence of ML fields (`fraud_probability`, `model_version`) in PostgreSQL with Alembic database migrations

### Fraud Rules (Phase 1 — Static)

| Rule | Condition | Points | Reason |
|------|-----------|--------|--------|
| 1 | `amount > 1000` | +30 | High transaction amount |
| 2 | `country != France` | +25 | Foreign transaction detected |
| 3 | `device_id` starts with `NEW` | +20 | Unrecognized device |

### Behavioral Rules (Phase 2)

| Rule | Condition | Default Points | Reason |
|------|-----------|----------------|--------|
| 4 | ≥ configured count in short window (default 2 min) | +20 | High transaction velocity detected |
| 5 | ≥ configured count in long window (default 10 min) | +15 | High transaction velocity detected |
| 6 | Country not in user's history | +20 | Transaction originated from unusual country |
| 7 | Device never used by user before | +15 | New device detected |
| 8 | Amount > multiplier × user average (min 3 prior tx) | +25 | Transaction amount significantly exceeds user history |

All behavioral thresholds are configurable via environment variables (see `.env.example`).

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
┌─────────────┐     ┌──────────────────┐     ┌─────────────────────────────┐
│  API Layer  │────▶│ Transaction      │────▶│ Static Fraud Engine         │
│ (FastAPI)   │     │ Service          │     │ (amount, country, device)   │
└─────────────┘     └────────┬─────────┘     └─────────────────────────────┘
                             │
                             ├────────────────▶ User History Service
                             │                         │
                             │                         ▼
                             │                  ┌─────────────────┐
                             │                  │   PostgreSQL    │
                             │                  │  (transactions) │
                             │                  └────────┬────────┘
                             │                           │
                             ▼                           │
                    ┌──────────────────┐                 │
                    │ Behavioral Fraud │◀────────────────┘
                    │ Engine           │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Score Aggregator │
                    │ (reasons + risk) │
                    └──────────────────┘
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
│   │   ├── fraud_engine.py          # Static rule evaluation + aggregation
│   │   ├── behavioral_fraud.py      # Behavioral rule evaluation
│   │   ├── user_history_service.py  # PostgreSQL history analysis
│   │   └── transaction_service.py
│   ├── ml/                      # Machine Learning scoring layer
│   │   ├── feature_engineering.py   # Feature extraction
│   │   ├── prediction_service.py    # Model serving and fallback
│   │   ├── generate_dataset.py      # Synthetic training dataset generator
│   │   └── train_model.py           # Model training pipeline
│   ├── api/
│   │   └── transactions.py      # Transaction endpoints
│   ├── utils/
│   │   └── logging.py           # Structured logging setup
│   └── tests/
│       ├── test_fraud_engine.py
│       ├── test_behavioral_fraud.py
│       ├── test_user_history_service.py
│       ├── test_ml.py               # ML-specific tests
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

### Local PostgreSQL Setup

1. Install PostgreSQL 14+ and ensure the server is running.
2. Create the application database:

```sql
CREATE DATABASE fraud_detection;
```

3. Copy `.env.example` to `.env` and set `DATABASE_URL`:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/fraud_detection
```

Adjust username, password, host, and port for your local instance.

### Database Migrations

Apply migrations before running the API locally:

```bash
alembic upgrade head
```

> On first run, tables are also created automatically via `init_db()` in the application lifespan. For production, prefer Alembic migrations.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application display name | `Fraud Detection API` |
| `APP_VERSION` | API version string | `1.0.0` |
| `DEBUG` | Enable SQL echo and debug logging | `false` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://postgres:postgres@localhost:5432/fraud_detection` |
| `VELOCITY_SHORT_WINDOW_MINUTES` | Short velocity window | `2` |
| `VELOCITY_SHORT_WINDOW_MAX_COUNT` | Max tx before short-window flag | `3` |
| `VELOCITY_SHORT_WINDOW_SCORE` | Risk points for short-window burst | `20` |
| `VELOCITY_LONG_WINDOW_MINUTES` | Long velocity window | `10` |
| `VELOCITY_LONG_WINDOW_MAX_COUNT` | Max tx before long-window flag | `5` |
| `VELOCITY_LONG_WINDOW_SCORE` | Risk points for long-window burst | `15` |
| `COUNTRY_CHANGE_SCORE` | Risk points for unusual country | `20` |
| `NEW_DEVICE_SCORE` | Risk points for unseen device | `15` |
| `SPENDING_ANOMALY_MIN_PRIOR_TRANSACTIONS` | Min history for spending check | `3` |
| `SPENDING_ANOMALY_MULTIPLIER` | Amount vs average multiplier | `3.0` |
| `SPENDING_ANOMALY_SCORE` | Risk points for spending anomaly | `25` |
| `ML_ENABLED` | Feature flag to enable/disable ML scoring | `true` |
| `ML_MODEL_PATH` | Path to persisted trained model file | `app/ml/models/fraud_model.joblib` |
| `ML_MODEL_METADATA_PATH` | Path to persisted model metadata | `app/ml/models/model_metadata.json` |
| `ML_WEIGHT` | Maximum points the ML layer can contribute | `20` |

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

### Non-Docker Local Server

Start the development server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open the interactive API documentation:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Machine Learning Pipeline (Phase 3)

The machine learning pipeline resides in `app/ml/` and runs independently of the FastAPI server.

1. **Generate the Training Dataset**:
   This generates a synthetic dataset containing 5,500+ transaction samples with realistic fraud correlations.
   ```bash
   python -m app.ml.generate_dataset
   ```
   Output is written to `app/ml/data/fraud_dataset.csv`.

2. **Train and Evaluate the Model**:
   This loads the generated dataset, trains a Random Forest model (primary) and a Logistic Regression model (for comparison), evaluates performance metrics (Accuracy, Precision, Recall, F1), and saves the best model.
   ```bash
   python -m app.ml.train_model
   ```
   Output artifacts:
   - Persisted Model: `app/ml/models/fraud_model.joblib`
   - Model Metadata: `app/ml/models/model_metadata.json`

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

### Check a Transaction (Suspicious Example)

Request:

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

Response:

```json
{
  "transaction_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "risk_score": 75,
  "status": "SUSPICIOUS",
  "reasons": [
    "High transaction amount",
    "Foreign transaction detected",
    "Unrecognized device"
  ],
  "fraud_probability": 0.0,
  "model_version": "mock_v1"
}
```

This transaction triggers all three static fraud rules for a total score of 75. Behavioral rules are skipped when the user has no prior transaction history.

### Check a Transaction (Behavioral Fraud Example)

After a user has established history in France, a high-value foreign transaction from a new device triggers both static and behavioral rules:

Request:

```bash
curl -X POST http://localhost:8000/transactions/check \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "combo_user",
    "amount": 2000,
    "merchant": "Foreign Luxury",
    "country": "Brazil",
    "device_id": "DEVICE_NEW"
  }'
```

Response (after 3 prior transactions for the same user, with a capped hybrid score):

```json
{
  "transaction_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "risk_score": 100,
  "status": "SUSPICIOUS",
  "reasons": [
    "High transaction amount",
    "Foreign transaction detected",
    "High transaction velocity detected",
    "Transaction originated from unusual country",
    "New device detected",
    "Transaction amount significantly exceeds user history"
  ],
  "fraud_probability": 0.0,
  "model_version": "mock_v1"
}
```

### List Transactions (Paginated)

```bash
curl "http://localhost:8000/transactions?page=1&page_size=10&sort_by=created_at&sort_order=desc"
```

```json
{
  "items": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "user_id": "user123",
      "amount": 1500.0,
      "merchant": "Amazon",
      "country": "Brazil",
      "device_id": "NEW_DEVICE_001",
      "risk_score": 75,
      "status": "SUSPICIOUS",
      "reasons": [
        "High transaction amount",
        "Foreign transaction detected",
        "Unrecognized device"
      ],
      "fraud_probability": 0.0,
      "model_version": "mock_v1",
      "created_at": "2026-06-16T12:00:00+00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

#### Optional Filters and Sorting

| Parameter | Description | Default |
|-----------|-------------|---------|
| `page` | Page number (1-based) | `1` |
| `page_size` | Items per page (max 100) | `10` |
| `status` | Filter by status (`SAFE`, `REVIEW`, `SUSPICIOUS`) | — |
| `user_id` | Filter by user identifier | — |
| `country` | Filter by country | — |
| `merchant` | Filter by merchant name | — |
| `sort_by` | `created_at`, `amount`, or `risk_score` | `created_at` |
| `sort_order` | `asc` or `desc` | `desc` |

Examples:

```bash
# Filter suspicious transactions for a user
curl "http://localhost:8000/transactions?status=SUSPICIOUS&user_id=user123"

# Sort by highest risk score
curl "http://localhost:8000/transactions?sort_by=risk_score&sort_order=desc&page_size=5"
```

### Get a Transaction by ID

```bash
curl http://localhost:8000/transactions/<transaction_id>
```

Returns `404` with a clear message when the transaction does not exist.

## Roadmap

### Future Enhancements

- [ ] JWT authentication and API key support
- [ ] Redis caching for hot user behavior profiles
- [ ] Request ID middleware and correlated structured logging
- [ ] Rate limiting on fraud check endpoint
- [ ] Real-time alerting for high-risk transactions
- [ ] Admin dashboard for rule tuning and case review
- [ ] CI/CD pipeline with automated migration checks

## License

MIT
