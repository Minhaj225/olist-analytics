SELECT (SELECT count(*) - count(DISTINCT order_id) FROM stg.orders)
     + (SELECT count(*) - count(DISTINCT customer_id) FROM stg.customers)
     + (SELECT count(*) - count(DISTINCT product_id) FROM stg.products)
     + (SELECT count(*) - count(DISTINCT seller_id) FROM stg.sellers)
     + (SELECT count(*) - count(DISTINCT (order_id, order_item_id)) FROM stg.order_items)
     + (SELECT count(*) - count(DISTINCT (order_id, payment_sequential)) FROM stg.order_payments)
     + (SELECT count(*) - count(DISTINCT order_id) FROM stg.order_reviews)
     + (SELECT count(*) - count(DISTINCT zip_prefix) FROM stg.geolocation)
     + (SELECT count(*) - count(DISTINCT category_name) FROM stg.category_translation);
