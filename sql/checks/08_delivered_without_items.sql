SELECT count(*) FROM dw.fact_orders
WHERE order_status = 'delivered' AND item_count = 0;
