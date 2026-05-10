import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ── Database URL ──────────────────────────────
# Reads from environment variable if set (Render/production)
# Falls back to local PostgreSQL if not set
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://agripulse_msax_user:lmhqZ7JAcogclpdvMJnTeNMmkxpFAOrm@dpg-d80aohfaqgkc739vnfbg-a/agripulse_msax"
    #"postgresql://postgres:bloodbird@localhost:5432/agripulse"  # ← change yourpassword
)

# Render gives postgres:// but SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ── Engine ────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True  # checks connection health before use
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
