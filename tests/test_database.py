import os

import pytest


def test_quality_checks_against_built_database():
    pytest.importorskip("sqlalchemy")
    from sqlalchemy.exc import OperationalError
    from src.config import ROOT
    from src.db import engine
    from src.quality_checks import check

    if not os.getenv("POSTGRES_PASSWORD") and not (ROOT / ".env").exists():
        pytest.skip("No local PostgreSQL configuration")
    try:
        with engine().connect() as conn:
            conn.exec_driver_sql("SELECT 1")
    except OperationalError as exc:
        pytest.skip(f"PostgreSQL unavailable: {exc}")
    with engine().connect() as conn:
        conn.exec_driver_sql("SELECT 1 FROM dw.fact_orders LIMIT 1")
    check()
