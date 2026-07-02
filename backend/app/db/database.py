from collections.abc import Generator
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
SQLITE_PATH = DATA_DIR / "esg.sqlite"
DATABASE_URL = os.getenv("ESG_DATABASE_URL", f"sqlite:///{SQLITE_PATH.as_posix()}")


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def create_db_and_tables() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_job_card_columns()


def ensure_job_card_columns() -> None:
    required_columns = {
        "responsibilities_json": "TEXT DEFAULT '[]'",
        "requirements_json": "TEXT DEFAULT '[]'",
        "bonus_points_json": "TEXT DEFAULT '[]'",
        "skills_json": "TEXT DEFAULT '[]'",
        "field_sources_json": "TEXT DEFAULT '{}'",
        "evidence_json": "TEXT DEFAULT '{}'",
        "confidence": "VARCHAR(32) DEFAULT 'low'",
        "salary_range": "VARCHAR(120)",
        "salary_period": "VARCHAR(32)",
        "base_location": "VARCHAR(255)",
        "education_requirement": "VARCHAR(120)",
        "experience_requirement": "VARCHAR(120)",
        "is_pinned": "BOOLEAN DEFAULT 0",
        "sort_order": "INTEGER DEFAULT 0",
    }

    with engine.begin() as connection:
        existing_columns = {
            row[1] for row in connection.execute(text("PRAGMA table_info(job_cards)"))
        }

        for column_name, column_definition in required_columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    text(f"ALTER TABLE job_cards ADD COLUMN {column_name} {column_definition}")
                )


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
