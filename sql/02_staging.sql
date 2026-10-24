-- Each view retains its source entity grain. Reviews and geography use a documented single-row rule.
CREATE OR REPLACE VIEW stg.customers AS
SELECT trim(customer_id) customer_id, trim(customer_unique_id) customer_unique_id,
       nullif(trim(customer_zip_code_prefix), '')::integer zip_prefix,
       nullif(trim(customer_city), '') city, nullif(trim(customer_state), '') state
FROM raw.customers;

CREATE OR REPLACE VIEW stg.geolocation AS
SELECT zip_prefix, lat, lng, city, state FROM (
 SELECT nullif(trim(geolocation_zip_code_prefix), '')::integer zip_prefix,
        nullif(trim(geolocation_lat), '')::numeric lat,
        nullif(trim(geolocation_lng), '')::numeric lng,
        nullif(trim(geolocation_city), '') city,
        nullif(trim(geolocation_state), '') state,
        row_number() OVER (PARTITION BY nullif(trim(geolocation_zip_code_prefix), '')::integer ORDER BY geolocation_state, geolocation_city, geolocation_lat, geolocation_lng) rn
 FROM raw.geolocation
) x WHERE rn = 1;

CREATE OR REPLACE VIEW stg.orders AS
SELECT trim(order_id) order_id, trim(customer_id) customer_id, trim(order_status) order_status,
       nullif(order_purchase_timestamp, '')::timestamp purchase_at,
       nullif(order_approved_at, '')::timestamp approved_at,
       nullif(order_delivered_carrier_date, '')::timestamp carrier_at,
       nullif(order_delivered_customer_date, '')::timestamp delivered_at,
       nullif(order_estimated_delivery_date, '')::timestamp estimated_at
FROM raw.orders;

CREATE OR REPLACE VIEW stg.order_items AS
SELECT trim(order_id) order_id, nullif(order_item_id, '')::integer order_item_id,
       trim(product_id) product_id, trim(seller_id) seller_id,
       nullif(shipping_limit_date, '')::timestamp shipping_limit_at,
       nullif(price, '')::numeric(14,2) price,
       nullif(freight_value, '')::numeric(14,2) freight_value
FROM raw.order_items;

CREATE OR REPLACE VIEW stg.order_payments AS
SELECT trim(order_id) order_id, nullif(payment_sequential, '')::integer payment_sequential,
       nullif(trim(payment_type), '') payment_type,
       nullif(payment_installments, '')::integer payment_installments,
       nullif(payment_value, '')::numeric(14,2) payment_value
FROM raw.order_payments;

-- Latest answered review wins per order; review_id breaks timestamp ties.
CREATE OR REPLACE VIEW stg.order_reviews AS
SELECT review_id, order_id, review_score, review_creation_at, review_answer_at FROM (
 SELECT trim(review_id) review_id, trim(order_id) order_id,
        nullif(review_score, '')::integer review_score,
        nullif(review_creation_date, '')::timestamp review_creation_at,
        nullif(review_answer_timestamp, '')::timestamp review_answer_at,
        row_number() OVER (PARTITION BY order_id ORDER BY nullif(review_answer_timestamp, '')::timestamp DESC NULLS LAST, nullif(review_creation_date, '')::timestamp DESC NULLS LAST, review_id DESC) rn
 FROM raw.order_reviews
) x WHERE rn = 1;

CREATE OR REPLACE VIEW stg.products AS
SELECT trim(p.product_id) product_id,
       coalesce(nullif(trim(t.product_category_name_english), ''), nullif(trim(p.product_category_name), ''), 'unknown') category,
       nullif(p.product_name_lenght, '')::integer product_name_length,
       nullif(p.product_description_lenght, '')::integer product_description_length,
       nullif(p.product_photos_qty, '')::integer photo_count,
       nullif(p.product_weight_g, '')::numeric weight_g,
       nullif(p.product_length_cm, '')::numeric length_cm,
       nullif(p.product_height_cm, '')::numeric height_cm,
       nullif(p.product_width_cm, '')::numeric width_cm
FROM raw.products p LEFT JOIN raw.category_translation t USING (product_category_name);

CREATE OR REPLACE VIEW stg.sellers AS
SELECT trim(seller_id) seller_id, nullif(trim(seller_zip_code_prefix), '')::integer zip_prefix,
       nullif(trim(seller_city), '') city, nullif(trim(seller_state), '') state
FROM raw.sellers;

CREATE OR REPLACE VIEW stg.category_translation AS
SELECT trim(product_category_name) category_name, trim(product_category_name_english) category_english
FROM raw.category_translation;
