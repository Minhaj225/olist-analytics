SELECT (SELECT count(*) FROM dw.fact_orders o LEFT JOIN dw.dim_customer c USING (customer_unique_id) WHERE c.customer_unique_id IS NULL)
     + (SELECT count(*) FROM dw.fact_order_items i LEFT JOIN dw.dim_product p USING (product_id) WHERE p.product_id IS NULL)
     + (SELECT count(*) FROM dw.fact_order_items i LEFT JOIN dw.dim_seller s USING (seller_id) WHERE s.seller_id IS NULL);
