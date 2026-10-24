SELECT (SELECT count(*) - count(DISTINCT date_key) FROM dw.dim_date)
     + (SELECT count(*) - count(DISTINCT customer_unique_id) FROM dw.dim_customer)
     + (SELECT count(*) - count(DISTINCT product_id) FROM dw.dim_product)
     + (SELECT count(*) - count(DISTINCT seller_id) FROM dw.dim_seller)
     + (SELECT count(*) - count(DISTINCT order_id) FROM dw.fact_orders)
     + (SELECT count(*) - count(DISTINCT (order_id, order_item_id)) FROM dw.fact_order_items);
