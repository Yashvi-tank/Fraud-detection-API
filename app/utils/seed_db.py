"""Database seeding utility to populate realistic test data."""

import random
from datetime import datetime, timedelta, UTC
from sqlmodel import Session, delete, select

from app.core.database import engine
from app.core.security import hash_password
from app.models.transaction import Transaction
from app.models.user import User

MERCHANTS = [
    "Amazon", "Walmart", "eBay", "Target", "Best Buy",
    "Apple Store", "Luxury Goods", "Crypto Exchange", "Wire Transfer",
    "Gambling Site", "Grocery", "Gas Station", "Restaurant",
    "Travel Agency", "Electronics Store"
]

COUNTRIES = [
    "France", "Germany", "Brazil", "USA", "UK",
    "Nigeria", "China", "India", "Russia", "Japan"
]


def seed_database() -> None:
    """Clear database and seed users and transactions."""
    with Session(engine) as session:
        print("Cleaning up existing database tables...")
        session.exec(delete(Transaction))
        session.exec(delete(User))
        session.commit()

        print("Creating demo user...")
        demo_pwd = hash_password("demo-password")
        demo_user = User(
            username="demo",
            hashed_password=demo_pwd,
            created_at=datetime.now(UTC) - timedelta(days=31),
        )
        session.add(demo_user)

        # Create a few other users to mix in
        other_users = []
        for i in range(1, 6):
            username = f"user_{100 + i}"
            pwd = hash_password(f"password_{i}")
            user = User(
                username=username,
                hashed_password=pwd,
                created_at=datetime.now(UTC) - timedelta(days=30),
            )
            session.add(user)
            other_users.append(username)

        session.commit()
        print("Users successfully seeded.")

        print("Seeding transaction history...")
        now = datetime.now(UTC)
        transactions: list[Transaction] = []

        # We will generate ~150 transactions over the last 30 days.
        # Most transactions will belong to 'demo' to establish history and patterns.
        # We will manually create some high-fidelity fraud burst patterns and single outliers.

        # --- PART 1: Normal legitimate transactions for 'demo' ---
        # Demo usually transacts in France, low amounts, amazon/grocery/restaurants.
        for i in range(100):
            # Spread over the last 30 days
            days_ago = random.uniform(0.1, 30)
            tx_time = now - timedelta(days=days_ago)

            amount = round(random.uniform(5.0, 150.0), 2)
            merchant = random.choices(
                MERCHANTS,
                weights=[15, 10, 10, 10, 8, 8, 2, 1, 1, 1, 15, 10, 8, 1, 5],
                k=1
            )[0]
            country = "France"
            device_id = "DEVICE_DEMO_1"

            # Low risk
            risk_score = 0
            reasons = []
            status = "SAFE"
            fraud_probability = round(random.uniform(0.00, 0.08), 4)

            tx = Transaction(
                user_id="demo",
                amount=amount,
                merchant=merchant,
                country=country,
                device_id=device_id,
                risk_score=risk_score,
                status=status,
                reasons=reasons,
                fraud_probability=fraud_probability,
                model_version="v1",
                created_at=tx_time,
            )
            transactions.append(tx)

        # --- PART 2: Legitimate transactions for other users ---
        for username in other_users:
            # Each other user gets ~8 random SAFE transactions in their default countries
            default_country = random.choice(COUNTRIES)
            device_id = f"DEVICE_{username.upper()}"
            for _ in range(8):
                days_ago = random.uniform(1, 30)
                tx_time = now - timedelta(days=days_ago)
                amount = round(random.uniform(10.0, 200.0), 2)
                merchant = random.choice(["Amazon", "Grocery", "Restaurant", "Gas Station"])

                # Some foreign rule flags might apply if not France, but they remain SAFE or REVIEW
                risk_score = 0
                reasons = []
                if default_country != "France":
                    risk_score += 25
                    reasons.append("Foreign transaction detected")

                status = "SAFE" if risk_score <= 30 else "REVIEW"
                fraud_probability = round(random.uniform(0.01, 0.12), 4)

                tx = Transaction(
                    user_id=username,
                    amount=amount,
                    merchant=merchant,
                    country=default_country,
                    device_id=device_id,
                    risk_score=risk_score,
                    status=status,
                    reasons=reasons,
                    fraud_probability=fraud_probability,
                    model_version="v1",
                    created_at=tx_time,
                )
                transactions.append(tx)

        # --- PART 3: Simulated suspicious anomalies for 'demo' ---
        # 1. Suspicious outlier: Large luxury transaction from Brazil, unrecognized device
        tx_time_outlier = now - timedelta(days=12, hours=3)
        tx_outlier = Transaction(
            user_id="demo",
            amount=3499.99,
            merchant="Luxury Goods",
            country="Brazil",
            device_id="NEW_DEVICE_ANDR_99",
            risk_score=100,  # 30 (high amount) + 25 (foreign country) + 20 (unrecognized device) + 20 (country anomaly) + 25 (spending) + 19 (ML) = 139 -> capped at 100
            status="SUSPICIOUS",
            reasons=[
                "High transaction amount",
                "Foreign transaction detected",
                "Unrecognized device",
                "Transaction originated from unusual country",
                "New device detected",
                "Transaction amount significantly exceeds user history",
                "ML model flagged as suspicious (probability: 0.95)"
            ],
            fraud_probability=0.9521,
            model_version="v1",
            created_at=tx_time_outlier,
        )
        transactions.append(tx_outlier)

        # 2. Velocity burst anomaly: 6 rapid transactions in 5 minutes (triggers velocity rules)
        tx_time_base = now - timedelta(days=5, hours=14)
        for i in range(6):
            tx_time = tx_time_base + timedelta(seconds=i * 45)
            # High frequency small transactions on a Gambling Site
            amount = round(random.uniform(20.0, 50.0), 2)
            merchant = "Gambling Site"
            country = "France"
            device_id = "DEVICE_DEMO_1"

            # Accumulating risk
            reasons = ["High transaction velocity detected"]
            risk_score = 20  # base velocity
            if i >= 3:
                risk_score += 15  # long window velocity boost
            # ML starts flagging these as suspicious probability builds up
            prob = 0.35 + (i * 0.10)
            ml_boost = round(prob * 20)
            risk_score += ml_boost
            if prob >= 0.50:
                reasons.append(f"ML model flagged as suspicious (probability: {prob:.2f})")

            status = "REVIEW" if risk_score <= 60 else "SUSPICIOUS"

            tx = Transaction(
                user_id="demo",
                amount=amount,
                merchant=merchant,
                country=country,
                device_id=device_id,
                risk_score=risk_score,
                status=status,
                reasons=reasons,
                fraud_probability=round(prob, 4),
                model_version="v1",
                created_at=tx_time,
            )
            transactions.append(tx)

        # 3. Country anomaly: Transaction from Nigeria using a new device
        tx_time_nigeria = now - timedelta(days=19, hours=8)
        tx_nigeria = Transaction(
            user_id="demo",
            amount=420.00,
            merchant="Wire Transfer",
            country="Nigeria",
            device_id="NEW_IPHONE_XX",
            risk_score=95,  # 25 (foreign) + 20 (unrecognized device) + 20 (country anomaly) + 15 (new device) + 15 (ML boost 0.75 * 20) = 95
            status="SUSPICIOUS",
            reasons=[
                "Foreign transaction detected",
                "Unrecognized device",
                "Transaction originated from unusual country",
                "New device detected",
                "ML model flagged as suspicious (probability: 0.75)"
            ],
            fraud_probability=0.7482,
            model_version="v1",
            created_at=tx_time_nigeria,
        )
        transactions.append(tx_nigeria)

        # 4. Review anomalies: Borderline scores (e.g. amount > 1000 in France, or Foreign country but no other issues)
        # 4a. High amount in France
        transactions.append(Transaction(
            user_id="demo",
            amount=1200.00,
            merchant="Apple Store",
            country="France",
            device_id="DEVICE_DEMO_1",
            risk_score=34,  # 30 (high amount) + 4 (ML boost 0.2)
            status="REVIEW",
            reasons=["High transaction amount"],
            fraud_probability=0.2012,
            model_version="v1",
            created_at=now - timedelta(days=22, hours=2),
        ))

        # 4b. Germany transaction (foreign, but not country anomaly since Germany is near, or first time)
        transactions.append(Transaction(
            user_id="demo",
            amount=85.00,
            merchant="Restaurant",
            country="Germany",
            device_id="DEVICE_DEMO_1",
            risk_score=49,  # 25 (foreign) + 20 (country change anomaly) + 4 (ML boost)
            status="REVIEW",
            reasons=["Foreign transaction detected", "Transaction originated from unusual country"],
            fraud_probability=0.2215,
            model_version="v1",
            created_at=now - timedelta(days=25, hours=5),
        ))

        # --- PART 4: Some fraud occurrences in other users ---
        # User 103 gets hit with major fraud
        transactions.append(Transaction(
            user_id="user_103",
            amount=8200.00,
            merchant="Crypto Exchange",
            country="Russia",
            device_id="NEW_DEVICE_UNKNOWN",
            risk_score=100,  # 30 + 25 + 20 + 20 + 25 + 20 = 140 capped to 100
            status="SUSPICIOUS",
            reasons=[
                "High transaction amount",
                "Foreign transaction detected",
                "Unrecognized device",
                "Transaction originated from unusual country",
                "New device detected",
                "Transaction amount significantly exceeds user history",
                "ML model flagged as suspicious (probability: 0.99)"
            ],
            fraud_probability=0.9912,
            model_version="v1",
            created_at=now - timedelta(days=8, hours=23),
        ))

        # User 104 gets hit with a Review transaction
        transactions.append(Transaction(
            user_id="user_104",
            amount=150.00,
            merchant="Target",
            country="USA",
            device_id="DEVICE_NEW_MOTO",
            risk_score=57,  # 25 (foreign) + 20 (unrecognized device) + 12 (ML)
            status="REVIEW",
            reasons=["Foreign transaction detected", "Unrecognized device"],
            fraud_probability=0.5843,
            model_version="v1",
            created_at=now - timedelta(days=15, hours=10),
        ))

        # Add all transactions
        print(f"Adding {len(transactions)} transactions to session...")
        session.add_all(transactions)
        session.commit()
        print("Transactions successfully seeded.")
        print("Database seeding completed successfully!")


if __name__ == "__main__":
    seed_database()
