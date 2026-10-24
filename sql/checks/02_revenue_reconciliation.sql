SELECT count(*) FROM dw.fact_orders o
LEFT JOIN (SELECT order_id, sum(price) revenue FROM dw.fact_order_items GROUP BY 1) i USING (order_id)
WHERE o.items_revenue <> coalesce(i.revenue, 0);
