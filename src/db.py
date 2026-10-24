from sqlalchemy import create_engine

from src.config import database_url


def engine():
    return create_engine(database_url(), pool_pre_ping=True)


if __name__ == "__main__":
    with engine().connect() as conn:
        print("PostgreSQL SELECT 1:", conn.exec_driver_sql("SELECT 1").scalar_one())
