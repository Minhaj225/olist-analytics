SELECT (SELECT count(*) FROM dw.fact_orders WHERE order_id IS NULL OR customer_unique_id IS NULL OR purchase_date_key IS NULL)
     + (SELECT count(*) FROM dw.fact_order_items WHERE order_id IS NULL OR order_item_id IS NULL OR product_id IS NULL OR seller_id IS NULL OR customer_unique_id IS NULL OR purchase_date_key IS NULL);
