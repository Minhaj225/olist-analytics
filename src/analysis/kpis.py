import pandas as pd

from src.analysis.common import read_sql, save_figure, write_findings


def delivery_delay_days(delivered, estimated):
    if pd.isna(delivered) or pd.isna(estimated):
        return None
    return (delivered.date() - estimated.date()).days


def calculate_kpis(orders):
    delivered = orders.loc[orders.order_status == "delivered"]
    count = len(delivered)
    return {
        "revenue": float(delivered.items_revenue.sum()),
        "orders": count,
        "aov": float(delivered.items_revenue.mean()) if count else 0.0,
        "late_pct": float(delivered.is_late.dropna().mean() * 100) if delivered.is_late.notna().any() else 0.0,
        "avg_review": float(delivered.review_score.mean()) if delivered.review_score.notna().any() else 0.0,
    }


def main():
    import matplotlib.pyplot as plt

    orders = read_sql("""SELECT o.* FROM dw.fact_orders o JOIN mart.analysis_months m
                          ON m.month = date_trunc('month', o.purchase_at)::date""")
    monthly = read_sql("SELECT * FROM mart.kpi_monthly ORDER BY month")
    kpis = calculate_kpis(orders)
    for row in orders.loc[orders.delivered_at.notna() & orders.estimated_at.notna()].head(100).itertuples():
        assert delivery_delay_days(row.delivered_at, row.estimated_at) == row.days_vs_estimate
    assert abs(kpis["revenue"] - float(monthly.revenue.sum())) < 0.01
    assert kpis["orders"] == int(monthly.orders.sum())
    assert abs(kpis["aov"] - kpis["revenue"] / kpis["orders"]) < 0.01
    plt.plot(pd.to_datetime(monthly.month), monthly.revenue)
    plt.title("Monthly delivered item revenue")
    plt.ylabel("BRL")
    save_figure("monthly_revenue.png")
    write_findings("Headline KPIs", (
        f"Delivered item revenue: BRL {kpis['revenue']:,.2f} across {kpis['orders']:,} orders; "
        f"AOV: BRL {kpis['aov']:,.2f}; late rate: {kpis['late_pct']:.1f}%; "
        f"average review: {kpis['avg_review']:.2f}/5. "
        "Evidence: `mart.kpi_monthly`, `dw.fact_orders`, and `reports/figures/monthly_revenue.png`. "
        "Recommendation: track these measures together each month so revenue growth is evaluated alongside delivery quality."
    ))
    print(kpis)


if __name__ == "__main__":
    main()
