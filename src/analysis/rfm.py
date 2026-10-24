import numpy as np

from src.analysis.common import read_sql, save_figure, write_findings


def score_customers(customers):
    scored = customers.copy()
    for column, ascending, target in (
        ("recency_days", False, "r_score"),
        ("frequency", True, "f_score"),
        ("monetary", True, "m_score"),
    ):
        # Equal source values get the same rank, critical for frequency=1 ties.
        scored[target] = np.ceil(5 * scored[column].rank(method="min", ascending=ascending, pct=True)).astype(int)
    scored["segment"] = np.select(
        [
            (scored.r_score >= 4) & (scored.f_score >= 4),
            scored.m_score >= 4,
            scored.r_score >= 4,
            scored.r_score <= 2,
        ],
        ["Champions", "Big Spenders", "New", "Lost"],
        default="At Risk",
    )
    return scored


def main():
    import matplotlib.pyplot as plt

    customers = read_sql("SELECT * FROM mart.customer_rfm")
    scored = score_customers(customers)
    for column in ("r_score", "f_score", "m_score", "segment"):
        assert scored[column].equals(customers[column]), f"Python/SQL RFM mismatch: {column}"
    summary = scored.groupby("segment").agg(customers=("customer_unique_id", "size"), revenue=("monetary", "sum"))
    summary["revenue_share"] = summary.revenue / summary.revenue.sum()
    repeat_customers = int((scored.frequency > 1).sum())
    summary.customers.plot.bar(title="Customers by RFM segment")
    plt.ylabel("Customers")
    save_figure("rfm_segments.png")
    lines = [f"- {segment}: {row.customers:,.0f} customers, {row.revenue_share:.1%} revenue share."
             for segment, row in summary.iterrows()]
    write_findings("RFM segments", f"{repeat_customers:,} of {len(scored):,} customers "
                   f"({repeat_customers / len(scored):.1%}) made more than one delivered purchase in the analysis window.\n\n" +
                   "\n".join(lines) +
                   "\nEvidence: `mart.customer_rfm` and `reports/figures/rfm_segments.png`. "
                   "Recommendation: prioritize customers with recent repeat purchases for retention outreach; "
                   "treat the large frequency=1 group as acquisition-heavy evidence, not proven churn.")
    print(summary)


if __name__ == "__main__":
    main()
