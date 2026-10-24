from src.config import ROOT
from src.db import engine


def check():
    failures = []
    with engine().connect() as conn:
        for path in sorted((ROOT / "sql/checks").glob("*.sql")):
            count = conn.exec_driver_sql(path.read_text()).scalar_one()
            warning = path.name.startswith("warn_")
            status = "WARN" if count and warning else "FAIL" if count else "PASS"
            print(f"{status:4} {path.stem:42} {count}")
            if count and not warning:
                failures.append(path.stem)
    if failures:
        raise SystemExit("Critical checks failed: " + ", ".join(failures))


if __name__ == "__main__":
    check()
