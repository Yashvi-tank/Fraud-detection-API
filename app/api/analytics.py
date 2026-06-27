"""Analytics API endpoints for dashboard visualization."""

from datetime import datetime, timedelta, UTC

from fastapi import APIRouter, Depends
from sqlmodel import Session, func, select

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.transaction import Transaction
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/summary",
    summary="Get aggregated summary statistics",
)
def get_summary(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return total, safe, suspicious counts, and average risk score."""
    total = session.exec(select(func.count(Transaction.id))).one() or 0
    safe = session.exec(select(func.count(Transaction.id)).where(Transaction.status == "SAFE")).one() or 0
    suspicious = session.exec(select(func.count(Transaction.id)).where(Transaction.status == "SUSPICIOUS")).one() or 0
    avg_score = session.exec(select(func.avg(Transaction.risk_score))).one() or 0.0

    return {
        "total_count": total,
        "safe_count": safe,
        "suspicious_count": suspicious,
        "average_risk_score": round(float(avg_score), 1) if avg_score else 0.0,
    }


@router.get(
    "/charts",
    summary="Get aggregated charts dataset",
)
def get_charts(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return dashboard datasets for risk distribution, activity timeline, probability histogram, and top risk countries.

    Performs in-memory grouping on fetch query to avoid database-specific dialect crashes (PostgreSQL vs SQLite).
    """
    transactions = session.exec(select(Transaction)).all()

    # 1. Risk distribution (Safe vs Review vs Suspicious status counts)
    status_counts = {"SAFE": 0, "REVIEW": 0, "SUSPICIOUS": 0}
    for tx in transactions:
        status_counts[tx.status] = status_counts.get(tx.status, 0) + 1
    risk_distribution = [
        {"status": "Safe", "value": status_counts["SAFE"]},
        {"status": "Review", "value": status_counts["REVIEW"]},
        {"status": "Suspicious", "value": status_counts["SUSPICIOUS"]},
    ]

    # 2. Daily Timeline (Last 30 Days)
    now = datetime.now(UTC)
    timeline_days = {}
    for i in range(29, -1, -1):
        day = (now - timedelta(days=i)).date()
        timeline_days[day] = {"date": day.isoformat(), "total": 0, "safe": 0, "suspicious": 0}

    for tx in transactions:
        tx_date = tx.created_at.date()
        if tx_date in timeline_days:
            timeline_days[tx_date]["total"] += 1
            if tx.status == "SAFE":
                timeline_days[tx_date]["safe"] += 1
            elif tx.status == "SUSPICIOUS":
                timeline_days[tx_date]["suspicious"] += 1

    timeline = list(timeline_days.values())

    # 3. Probability Distribution Bins (0.0-0.1 up to 0.9-1.0)
    bins = [0] * 10
    for tx in transactions:
        prob = tx.fraud_probability if tx.fraud_probability is not None else 0.0
        bin_idx = min(int(prob * 10), 9)
        bins[bin_idx] += 1
    probability_distribution = [
        {"bin": f"{i*10}-{(i+1)*10}%", "count": bins[i]}
        for i in range(10)
    ]

    # 4. Top Countries
    country_stats = {}
    for tx in transactions:
        c = tx.country
        if c not in country_stats:
            country_stats[c] = {"country": c, "suspicious_count": 0, "total_count": 0}
        country_stats[c]["total_count"] += 1
        if tx.status == "SUSPICIOUS":
            country_stats[c]["suspicious_count"] += 1

    # Sort countries by count of suspicious transactions first, then total count
    top_countries = sorted(
        country_stats.values(),
        key=lambda x: (x["suspicious_count"], x["total_count"]),
        reverse=True,
    )[:5]

    return {
        "risk_distribution": risk_distribution,
        "timeline": timeline,
        "probability_distribution": probability_distribution,
        "top_countries": top_countries,
    }
