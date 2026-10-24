SELECT (SELECT count(*) FROM dw.fact_orders WHERE review_score NOT BETWEEN 1 AND 5 AND review_score IS NOT NULL)
     + (SELECT count(*) FROM dw.fact_order_items WHERE price < 0 OR freight_value < 0);
