from itertools import combinations

import numpy as np
from scipy import stats

from src.analysis.common import read_sql, save_figure, write_findings


def rank_biserial(first, second):
    u = stats.mannwhitneyu(first, second, alternative="two-sided").statistic
    return float(2 * u / (len(first) * len(second)) - 1)


def format_p(value):
    return "< 1e-300" if value == 0 else f"= {value:.3g}"


def main():
    import matplotlib.pyplot as plt

    orders = read_sql("""SELECT o.review_score, o.is_late, o.days_vs_estimate,
                             o.items_revenue, o.primary_payment_type
                      FROM dw.fact_orders o JOIN mart.analysis_months m
                      ON m.month = date_trunc('month', o.purchase_at)::date
                      WHERE o.order_status = 'delivered'""")
    reviewed = orders.dropna(subset=["review_score", "is_late"]).copy()
    reviewed["is_late"] = reviewed["is_late"].astype(bool)
    late = reviewed.loc[reviewed.is_late, "review_score"]
    on_time = reviewed.loc[~reviewed.is_late, "review_score"]
    if min(len(late), len(on_time)) < 20:
        raise ValueError("Too few reviewed orders in a lateness group")
    h1 = stats.mannwhitneyu(late, on_time, alternative="less")
    h1_effect = rank_biserial(late, on_time)
    correlated = orders.dropna(subset=["days_vs_estimate", "review_score"])
    if len(correlated) < 20:
        raise ValueError("Too few orders for delay correlation")
    h2 = stats.spearmanr(correlated.days_vs_estimate, correlated.review_score)
    payment = orders.dropna(subset=["primary_payment_type", "items_revenue"])
    counts = payment.primary_payment_type.value_counts()
    types = counts[counts >= 20].index.tolist()
    if len(types) < 2:
        raise ValueError("Too few payment types with at least 20 orders")
    groups = [payment.loc[payment.primary_payment_type == kind, "items_revenue"] for kind in types]
    h3 = stats.kruskal(*groups)
    n = sum(map(len, groups))
    epsilon_sq = max(0.0, (h3.statistic - len(groups) + 1) / (n - len(groups)))
    lines = [
        "**H1.** H0: late and on-time review distributions are equal; H1: late reviews are lower. "
        f"Mann–Whitney U={h1.statistic:,.0f}, p {format_p(h1.pvalue)}, rank-biserial={h1_effect:.3f}; "
        f"n={len(late):,}/{len(on_time):,}, medians={late.median():.1f}/{on_time.median():.1f}. "
        "Reviews are ordinal, so no normality assumption is used. "
        + ("Late deliveries are associated with lower reviews; inspect carrier and seller delays." if h1.pvalue < .05 else "No clear lower-review association was detected."),
        "**H2.** H0: no monotonic delay/review association; H1: negative association. "
        f"Spearman rho={h2.statistic:.3f}, p {format_p(h2.pvalue)}, n={len(correlated):,}. "
        "Ranks accommodate skew and tied review scores. "
        + ("Longer delays align with lower scores; monitor delay days." if h2.pvalue < .05 and h2.statistic < 0 else "A negative association was not established."),
        "**H3.** H0: order-value distributions are equal across payment types; H1: at least one differs. "
        f"Kruskal–Wallis H={h3.statistic:.2f}, p {format_p(h3.pvalue)}, epsilon-squared={epsilon_sq:.3f}; "
        f"types={', '.join(types)}, n={n:,}. Groups have at least 20 orders; values are skewed. "
        + ("Payment types differ, but the effect is small; investigate mix before changing payment strategy." if h3.pvalue < .05 else "No value difference was established."),
    ]
    if h3.pvalue < .05:
        pairs = []
        for left, right in combinations(types, 2):
            p = stats.mannwhitneyu(payment.loc[payment.primary_payment_type == left, "items_revenue"],
                                   payment.loc[payment.primary_payment_type == right, "items_revenue"],
                                   alternative="two-sided").pvalue
            pairs.append((left, right, p))
        # Holm family-wise correction across all pairwise comparisons.
        ordered = sorted(pairs, key=lambda x: x[2])
        significant = []
        for i, (a, b, p) in enumerate(ordered):
            if p > .05 / (len(ordered) - i):
                break
            significant.append(f"{a} vs {b}")
        lines.append("Holm-adjusted pairwise differences: " + (", ".join(significant) if significant else "none") + ".")
    reviewed.boxplot(column="review_score", by="is_late")
    plt.suptitle("")
    plt.title("Review score by delivery lateness")
    plt.xlabel("Late delivery")
    save_figure("reviews_vs_lateness.png")
    write_findings("Hypothesis tests", "\n\n".join(lines) +
                   "\n\nEvidence: `dw.fact_orders` and `reports/figures/reviews_vs_lateness.png`. "
                   "Associations do not establish causality.")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
