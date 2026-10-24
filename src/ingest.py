import csv

from src.config import ROOT


FILES = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}


def missing_files():
    return [name for name in FILES.values() if not (ROOT / "data/raw" / name).is_file()]


def ingest():
    missing = missing_files()
    if missing:
        raise SystemExit("Missing Olist CSVs in data/raw/:\n" + "\n".join(f"- {name}" for name in missing))
    from src.db import engine
    from src.run_sql import run

    run(raw_only=True)
    db = engine()
    with db.begin() as conn:
        # All nine reloads commit together; an invalid file leaves prior data intact.
        conn.exec_driver_sql("TRUNCATE " + ", ".join(f"raw.{table}" for table in FILES))
        for table, name in FILES.items():
            path = ROOT / "data/raw" / name
            with path.open(newline="", encoding="utf-8-sig") as file:
                reader = csv.reader(file)
                header = next(reader)
                columns = conn.exec_driver_sql(
                    "SELECT column_name FROM information_schema.columns WHERE table_schema='raw' AND table_name=%s AND column_name <> '_loaded_at' ORDER BY ordinal_position",
                    (table,),
                ).scalars().all()
                if header != columns:
                    raise ValueError(f"{name}: columns differ from raw.{table}: {header} != {columns}")
                count = 0
                with conn.connection.cursor() as cursor:
                    with cursor.copy(f"COPY raw.{table} ({', '.join(columns)}) FROM STDIN") as copy:
                        for row in reader:
                            copy.write_row(row)
                            count += 1
                loaded = conn.exec_driver_sql(f"SELECT count(*) FROM raw.{table}").scalar_one()
                if loaded != count:
                    raise ValueError(f"{name}: CSV {count} rows, database {loaded} rows")
                print(f"{table}: {loaded} rows")


if __name__ == "__main__":
    ingest()
