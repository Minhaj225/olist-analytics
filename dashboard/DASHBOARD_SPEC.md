# Dashboard specification

Build these pages manually in Tableau Public or Power BI from `dashboard/extracts/`. Use a light background, one dark text color, blue for revenue, and amber for late deliveries. Display the analysis window on every page.

## Page 1: Executive Overview

| Visual | Extract | Exact definition |
|---|---|---|
| Revenue card | `orders_flat.csv` | Sum `items_revenue` where `order_status = delivered`; BRL, excludes freight |
| Orders card | `orders_flat.csv` | Count `order_id` where delivered |
| AOV card | `orders_flat.csv` | Revenue / delivered orders |
| Late rate card | `orders_flat.csv` | Average of `is_late` for delivered orders with known lateness; 96,203 of 96,211 delivered orders |
| Average review card | `orders_flat.csv` | Average `review_score` for delivered orders with a review |
| Monthly revenue and forecast | `kpi_monthly.csv` plus `reports/figures/revenue_forecast.png` | `month`, `revenue`; forecast shown as an image or recreated from reported numbers |
| Top 10 categories | `category_performance.csv` | Sum `revenue` by `category` across years; top 10 |
| Revenue by state map | `orders_flat.csv` | Sum delivered `items_revenue` by `customer_state` |

## Page 2: Delivery and Satisfaction

| Visual | Extract | Definition |
|---|---|---|
| Late rate by state | `delivery_performance.csv` | Weighted average `late_pct` using `known_lateness_orders` |
| Delivery days distribution | `orders_flat.csv` | Histogram of `days_to_deliver` for delivered orders |
| Review by lateness bucket | `orders_flat.csv` | Average `review_score` grouped by `is_late` and `days_vs_estimate` bucket |
| Seller scorecard | `seller_scorecard.csv` | `orders`, `revenue`, `late_pct`, `avg_review_score`, `revenue_quartile` |

## Page 3: Customers and Products

| Visual | Extract | Definition |
|---|---|---|
| RFM segment sizes and revenue share | `customer_rfm.csv` | Count `customer_unique_id`, sum `monetary` by `segment` |
| Cohort retention | `cohort_retention.csv` | `retention_rate` by `cohort_month` and `months_since_first` |
| Category Pareto | `category_performance.csv` | `revenue` bars and `cumulative_revenue_share` line by `year`, ordered by `revenue_rank` |

## Filters and calculated fields

Use date range on month or purchase date, customer state on order-level and delivery visuals, and category on category visuals. `orders_flat.primary_category` permits an approximate category filter on order-level visuals: multi-category orders count under their highest-priced item. Label this explicitly. Marts have different grains, so do not sum `late_pct` or `retention_rate` across rows without their denominators.

- `AOV = SUM(items_revenue) / COUNT(order_id)` after filtering to delivered orders.
- `Late % = AVG(Late Flag)` formatted as a percentage, where `Late Flag` is 1 for late, 0 for on time, and null for unknown; use only delivered orders.
- `Freight share = SUM(freight_total) / (SUM(items_revenue) + SUM(freight_total))`.
- Lateness buckets from `days_vs_estimate`: early (<0), on time (=0), 1–3 days late, 4+ days late.

Add screenshots to `dashboard/screenshots/` and a public link to the README after publishing. Tableau Public may expose uploaded row-level extract data; publish only if that is acceptable for this public dataset.

For click-by-click Tableau Public instructions and the data-quality interpretation, see [the beginner guide](TABLEAU_BEGINNER_GUIDE.md).
