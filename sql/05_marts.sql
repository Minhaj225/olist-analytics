-- Marts use delivered purchases. Months with fewer than 500 orders are excluded
-- provisionally; profile the supplied CSVs before treating this as the final window.
DROP SCHEMA IF EXISTS mart CASCADE;
CREATE SCHEMA mart;

CREATE VIEW mart.analysis_months AS
SELECT date_trunc('month', purchase_at)::date AS month
FROM dw.fact_orders GROUP BY 1 HAVING count(*) >= 500;

CREATE VIEW mart.kpi_monthly AS
WITH monthly AS (
 SELECT date_trunc('month', o.purchase_at)::date AS month,
        count(*) orders, sum(o.items_revenue) revenue,
        sum(o.item_count) items, sum(o.freight_total) freight
 FROM dw.fact_orders o JOIN mart.analysis_months m ON m.month = date_trunc('month', o.purchase_at)::date
 WHERE o.order_status = 'delivered' GROUP BY 1
)
SELECT month, orders, revenue, revenue / nullif(orders,0) aov,
       items::numeric / nullif(orders,0) items_per_order,
       freight / nullif(revenue + freight,0) freight_share,
       (revenue / nullif(lag(revenue) OVER (ORDER BY month),0) - 1) mom_growth,
       avg(revenue) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) revenue_rolling_3m
FROM monthly;

CREATE VIEW mart.delivery_performance AS
SELECT date_trunc('month', o.purchase_at)::date AS month, c.state customer_state,
       count(*) delivered_orders, count(o.is_late) known_lateness_orders,
       avg(o.days_to_deliver) avg_days_to_deliver,
       100 * avg(o.is_late::integer) late_pct,
       avg(o.days_vs_estimate) FILTER (WHERE o.is_late) avg_delay_when_late,
       avg(o.review_score) avg_review_score
FROM dw.fact_orders o JOIN dw.dim_customer c USING (customer_unique_id)
JOIN mart.analysis_months m ON m.month = date_trunc('month', o.purchase_at)::date
WHERE o.order_status = 'delivered' GROUP BY 1,2;

CREATE VIEW mart.category_performance AS
WITH base AS (
 SELECT d.year, p.category, i.order_id, i.price, o.review_score
 FROM dw.fact_order_items i JOIN dw.fact_orders o USING (order_id)
 JOIN dw.dim_product p USING (product_id)
 JOIN dw.dim_date d ON d.date_key = i.purchase_date_key
 JOIN mart.analysis_months m ON m.month = date_trunc('month', o.purchase_at)::date
 WHERE o.order_status = 'delivered'
), totals AS (
 SELECT year, category, sum(price) revenue, count(DISTINCT order_id) orders
 FROM base GROUP BY year, category
), reviews AS (
 SELECT year, category, avg(review_score) avg_review_score
 FROM (SELECT DISTINCT year, category, order_id, review_score FROM base) one_review_per_order
 GROUP BY year, category
)
SELECT t.*, r.avg_review_score,
       rank() OVER (PARTITION BY t.year ORDER BY t.revenue DESC) revenue_rank,
       sum(t.revenue) OVER (PARTITION BY t.year ORDER BY t.revenue DESC, t.category ROWS UNBOUNDED PRECEDING)
       / nullif(sum(t.revenue) OVER (PARTITION BY t.year),0) cumulative_revenue_share
FROM totals t JOIN reviews r USING (year, category);

CREATE VIEW mart.seller_scorecard AS
WITH seller_orders AS (
 SELECT i.seller_id, i.order_id, sum(i.price) revenue,
        max(o.is_late::integer) is_late, max(o.review_score) review_score
 FROM dw.fact_order_items i JOIN dw.fact_orders o USING (order_id)
 JOIN mart.analysis_months m ON m.month = date_trunc('month', o.purchase_at)::date
 WHERE o.order_status = 'delivered' GROUP BY i.seller_id, i.order_id
), totals AS (
 SELECT seller_id, count(*) orders, sum(revenue) revenue,
        100 * avg(is_late) late_pct, avg(review_score) avg_review_score
 FROM seller_orders GROUP BY seller_id
)
SELECT *, ntile(4) OVER (ORDER BY revenue DESC) revenue_quartile FROM totals;

CREATE VIEW mart.cohort_retention AS
WITH purchases AS (
 SELECT customer_unique_id, date_trunc('month', purchase_at)::date AS month
 FROM dw.fact_orders o JOIN mart.analysis_months m ON m.month = date_trunc('month', o.purchase_at)::date
 WHERE order_status = 'delivered' GROUP BY 1,2
), cohorts AS (
 SELECT customer_unique_id, min(month) cohort_month FROM purchases GROUP BY 1
), cohort_sizes AS (
 SELECT cohort_month, count(*) cohort_size FROM cohorts GROUP BY 1
)
SELECT c.cohort_month,
       (extract(year FROM age(p.month, c.cohort_month)) * 12 + extract(month FROM age(p.month, c.cohort_month)))::integer months_since_first,
       s.cohort_size, count(*) active_customers,
       count(*)::numeric / s.cohort_size retention_rate
FROM purchases p JOIN cohorts c USING (customer_unique_id)
JOIN cohort_sizes s USING (cohort_month) GROUP BY 1,2,3;

CREATE VIEW mart.customer_rfm AS
WITH activity AS (
 SELECT customer_unique_id, max(purchase_at)::date last_purchase,
        count(*) frequency, sum(items_revenue) monetary
 FROM dw.fact_orders o JOIN mart.analysis_months m ON m.month = date_trunc('month', o.purchase_at)::date
 WHERE order_status = 'delivered' GROUP BY 1
), scores AS (
 SELECT a.*, (SELECT max(month) + interval '1 month' FROM mart.analysis_months)::date - last_purchase recency_days,
        ceil(5.0 * rank() OVER (ORDER BY last_purchase) / count(*) OVER ())::integer r_score,
        ceil(5.0 * rank() OVER (ORDER BY frequency) / count(*) OVER ())::integer f_score,
        ceil(5.0 * rank() OVER (ORDER BY monetary) / count(*) OVER ())::integer m_score
 FROM activity a
)
SELECT *, CASE WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions'
               WHEN m_score >= 4 THEN 'Big Spenders'
               WHEN r_score >= 4 THEN 'New'
               WHEN r_score <= 2 THEN 'Lost'
               ELSE 'At Risk' END segment
FROM scores;
