SELECT count(*) FROM dw.fact_orders WHERE item_count = 0 OR primary_payment_type IS NULL;
