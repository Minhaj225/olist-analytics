SELECT count(*) FROM dw.fact_orders
WHERE (order_status = 'delivered' AND delivered_at IS NULL)
   OR (delivered_at IS NOT NULL AND delivered_at < purchase_at);
