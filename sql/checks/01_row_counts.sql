SELECT abs((SELECT count(*) FROM stg.orders) - (SELECT count(*) FROM dw.fact_orders))
     + abs((SELECT count(*) FROM stg.order_items) - (SELECT count(*) FROM dw.fact_order_items));
