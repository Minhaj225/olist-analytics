import argparse

from src.config import ROOT
from src.db import engine


def run(raw_only=False):
    files = sorted((ROOT / "sql").glob("[0-9][0-9]_*.sql"))
    if raw_only:
        files = files[:2]
    db = engine()
    with db.begin() as conn:
        for path in files:
            conn.exec_driver_sql(path.read_text())
            print(f"Applied {path.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", action="store_true")
    run(parser.parse_args().raw)
