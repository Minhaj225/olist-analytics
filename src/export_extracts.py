from src.analysis.common import read_sql
from src.config import ROOT


MARTS = (
    "kpi_monthly", "delivery_performance", "category_performance",
    "seller_scorecard", "cohort_retention", "customer_rfm",
)


def export():
    target = ROOT / "dashboard/extracts"
    target.mkdir(parents=True, exist_ok=True)
    for name in MARTS:
        frame = read_sql(f"SELECT * FROM mart.{name}")
        frame.to_csv(target / f"{name}.csv", index=False, date_format="%Y-%m-%d")
        print(f"{name}: {len(frame)} rows")
    # One row per order; primary category is the highest-priced item, so order KPIs never multiply.
    flat = read_sql("""
        SELECT o.order_id, o.purchase_at::date purchase_date, o.order_status,
               c.state customer_state, c.region customer_region, p.category primary_category,
               o.items_revenue, o.freight_total, o.payment_total, o.item_count,
               o.primary_payment_type, o.review_score, o.days_to_deliver,
               o.days_vs_estimate, o.is_late
        FROM dw.fact_orders o JOIN dw.dim_customer c USING (customer_unique_id)
        JOIN mart.analysis_months m ON m.month = date_trunc('month', o.purchase_at)::date
        LEFT JOIN LATERAL (
            SELECT dp.category FROM dw.fact_order_items i
            JOIN dw.dim_product dp USING (product_id)
            WHERE i.order_id = o.order_id
            ORDER BY i.price DESC, i.order_item_id LIMIT 1
        ) p ON true
    """)
    flat.to_csv(target / "orders_flat.csv", index=False, date_format="%Y-%m-%d")
    print(f"orders_flat: {len(flat)} rows")


if __name__ == "__main__":
    export()
