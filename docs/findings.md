# Findings

These findings were generated from the local Olist CSVs for the January 2017–August 2018 analysis window. Rerun `make analyze` after changing the source data.

## Headline KPIs

Delivered item revenue: BRL 13,181,027.13 across 96,211 orders; AOV: BRL 137.00; late rate: 6.8%; average review: 4.16/5. Evidence: `mart.kpi_monthly`, `dw.fact_orders`, and `reports/figures/monthly_revenue.png`. Recommendation: track these measures together each month so revenue growth is evaluated alongside delivery quality.

## Revenue forecast

Held out the last three complete analysis months. Seasonal-naive MAPE: 43.0%; Holt trend (insufficient training history for two seasonal cycles) MAPE: 36.6%. Lower-error choice: model. Next three model forecasts: BRL 851,017, BRL 823,289, BRL 795,562. The shaded band is ±1.96 training residual standard deviations, an approximation rather than a calibrated prediction interval. Evidence: `mart.kpi_monthly` and `reports/figures/revenue_forecast.png`. Recommendation: use the lower-error method for planning and refresh with recent data.

## RFM segments

2,789 of 93,104 customers (3.0%) made more than one delivered purchase in the analysis window.

- At Risk: 11,270 customers, 4.8% revenue share.
- Big Spenders: 36,104 customers, 73.9% revenue share.
- Champions: 1,189 customers, 2.4% revenue share.
- Lost: 22,963 customers, 9.8% revenue share.
- New: 21,578 customers, 9.1% revenue share.

Evidence: `mart.customer_rfm` and `reports/figures/rfm_segments.png`. Recommendation: prioritize customers with recent repeat purchases for retention outreach; treat the large frequency=1 group as acquisition-heavy evidence, not proven churn.

## Hypothesis tests

**H1.** H0: late and on-time review distributions are equal; H1: late reviews are lower. Mann–Whitney U=102,901,002, p < 1e-300, rank-biserial=-0.638; n=6,378/89,182, medians=1.0/5.0. Reviews are ordinal, so no normality assumption is used. Late deliveries are associated with lower reviews; inspect carrier and seller delays.

**H2.** H0: no monotonic delay/review association; H1: negative association. Spearman rho=-0.177, p < 1e-300, n=95,560. Ranks accommodate skew and tied review scores. Longer delays align with lower scores; monitor delay days.

**H3.** H0: order-value distributions are equal across payment types; H1: at least one differs. Kruskal–Wallis H=914.14, p = 7.58e-198, epsilon-squared=0.009; types=credit_card, boleto, voucher, debit_card, n=96,211. Groups have at least 20 orders; values are skewed. Payment types differ, but the effect is small; investigate mix before changing payment strategy.

Holm-adjusted pairwise differences: credit_card vs boleto, credit_card vs voucher, boleto vs voucher, credit_card vs debit_card, voucher vs debit_card.

Evidence: `dw.fact_orders` and `reports/figures/reviews_vs_lateness.png`. Associations do not establish causality.
