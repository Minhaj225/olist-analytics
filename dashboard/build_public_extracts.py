"""Build aggregate-only CSVs for a public Tableau workbook."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).parent
SOURCE = ROOT / "extracts"
OUTPUT = ROOT / "public_extracts"


def main():
    OUTPUT.mkdir(exist_ok=True)
    orders = pd.read_csv(SOURCE / "orders_flat.csv")
    orders = orders.loc[orders.order_status.eq("delivered")].copy()
    orders["month"] = orders.purchase_date.str[:7] + "-01"
    orders["review_sum"] = orders.review_score.fillna(0)
    orders["review_count"] = orders.review_score.notna().astype(int)
    orders["late_orders"] = orders.is_late.eq(True).astype(int)
    orders["known_lateness_orders"] = orders.is_late.notna().astype(int)

    by_state = orders.groupby(["month", "customer_state"], as_index=False).agg(
        orders=("order_id", "size"), revenue=("items_revenue", "sum"),
        review_sum=("review_sum", "sum"), review_count=("review_count", "sum"),
        late_orders=("late_orders", "sum"),
        known_lateness_orders=("known_lateness_orders", "sum"),
    )
    by_state.to_csv(OUTPUT / "monthly_state.csv", index=False, float_format="%.4f")

    days = orders.loc[orders.days_to_deliver.notna(), ["month", "customer_state", "days_to_deliver"]].copy()
    days["days_bin"] = (days.days_to_deliver.clip(lower=0, upper=80) // 5 * 5).astype(int)
    days.groupby(["month", "customer_state", "days_bin"], as_index=False).size().rename(
        columns={"size": "orders"}
    ).to_csv(OUTPUT / "delivery_bins.csv", index=False)

    delay = orders.days_vs_estimate
    orders["lateness_bucket"] = "Unknown"
    orders.loc[delay.lt(0), "lateness_bucket"] = "Early"
    orders.loc[delay.eq(0), "lateness_bucket"] = "On time"
    orders.loc[delay.gt(0) & delay.le(3), "lateness_bucket"] = "1–3 days late"
    orders.loc[delay.gt(3), "lateness_bucket"] = "4+ days late"
    orders.groupby(["month", "customer_state", "lateness_bucket"], as_index=False).agg(
        review_sum=("review_sum", "sum"), review_count=("review_count", "sum")
    ).to_csv(OUTPUT / "review_buckets.csv", index=False, float_format="%.4f")

    pd.read_csv(SOURCE / "category_performance.csv").to_csv(
        OUTPUT / "categories.csv", index=False
    )
    sellers = pd.read_csv(SOURCE / "seller_scorecard.csv").nlargest(20, "revenue").copy()
    sellers.insert(0, "seller_rank", range(1, len(sellers) + 1))
    sellers.drop(columns="seller_id").to_csv(OUTPUT / "seller_top20.csv", index=False)

    rfm = pd.read_csv(SOURCE / "customer_rfm.csv")
    rfm.groupby("segment", as_index=False).agg(
        customers=("customer_unique_id", "size"), revenue=("monetary", "sum")
    ).to_csv(OUTPUT / "rfm_segments.csv", index=False, float_format="%.4f")
    pd.read_csv(SOURCE / "cohort_retention.csv").to_csv(
        OUTPUT / "cohort_retention.csv", index=False
    )

    assert by_state.orders.sum() == 96211
    assert abs(by_state.revenue.sum() - 13181027.13) < 0.01
    assert by_state.known_lateness_orders.sum() == 96203
    assert not any("id" in column.lower() for path in OUTPUT.glob("*.csv")
                   for column in pd.read_csv(path, nrows=0).columns)
    print(f"Built seven aggregate CSVs in {OUTPUT}")


if __name__ == "__main__":
    main()
