import base64
import os
from pathlib import Path
import tempfile

TEST_DB_PATH = Path(tempfile.gettempdir()) / f"esg_test_{os.getpid()}.sqlite"
os.environ["ESG_DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["ESG_API_KEY_ENCRYPTION_KEY"] = base64.urlsafe_b64encode(b"0" * 32).decode(
    "utf-8",
)


def pytest_runtest_setup() -> None:
    from app.db.database import Base, create_db_and_tables, engine

    Base.metadata.drop_all(bind=engine)
    create_db_and_tables()
