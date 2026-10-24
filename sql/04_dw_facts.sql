-- fact_orders grain: one source order, including orders without items or payments.
CREATE TABLE dw.fact_orders (
 order_id text PRIMARY KEY,
 customer_unique_id text NOT NULL REFERENCES dw.dim_customer(customer_unique_id),
 purchase_date_key integer NOT NULL REFERENCES dw.dim_date(date_key),
 purchase_at timestamp NOT NULL, approved_at timestamp, delivered_at timestamp,
 estimated_at timestamp, order_status text NOT NULL,
 item_count integer NOT NULL, items_revenue numeric(14,2) NOT NULL,
 freight_total numeric(14,2) NOT NULL, payment_total numeric(14,2) NOT NULL,
 primary_payment_type text, max_installments integer,
 review_score integer, approval_lag_hours numeric, days_to_deliver numeric,
 days_vs_estimate integer, is_late boolean
);
-- Aggregations remain left joined so missing items/payments stay visible as zero.
WITH items AS (
 SELECT order_id, count(*) item_count, sum(price) items_revenue, sum(freight_value) freight_total
 FROM stg.order_items GROUP BY order_id
), payments AS (
 SELECT order_id, sum(payment_value) payment_total, max(payment_installments) max_installments
 FROM stg.order_payments GROUP BY order_id
), payment_rank AS (
 SELECT order_id, payment_type,
        row_number() OVER (PARTITION BY order_id ORDER BY sum(payment_value) DESC NULLS LAST, payment_type) rn
 FROM stg.order_payments GROUP BY order_id, payment_type
)
INSERT INTO dw.fact_orders
SELECT o.order_id, c.customer_unique_id, to_char(o.purchase_at, 'YYYYMMDD')::integer,
       o.purchase_at, o.approved_at, o.delivered_at, o.estimated_at, o.order_status,
       coalesce(i.item_count, 0), coalesce(i.items_revenue, 0), coalesce(i.freight_total, 0),
       coalesce(p.payment_total, 0), pr.payment_type, p.max_installments, r.review_score,
       extract(epoch FROM (o.approved_at - o.purchase_at)) / 3600,
       extract(epoch FROM (o.delivered_at - o.purchase_at)) / 86400,
       o.delivered_at::date - o.estimated_at::date,
       CASE WHEN o.delivered_at IS NOT NULL AND o.estimated_at IS NOT NULL
            THEN o.delivered_at::date > o.estimated_at::date END
FROM stg.orders o JOIN stg.customers c USING (customer_id)
LEFT JOIN items i USING (order_id)
LEFT JOIN payments p USING (order_id)
LEFT JOIN payment_rank pr ON pr.order_id = o.order_id AND pr.rn = 1
LEFT JOIN stg.order_reviews r ON r.order_id = o.order_id;
CREATE INDEX fact_orders_customer_idx ON dw.fact_orders(customer_unique_id);
CREATE INDEX fact_orders_date_idx ON dw.fact_orders(purchase_date_key);
CREATE INDEX fact_orders_status_idx ON dw.fact_orders(order_status);

-- fact_order_items grain: one (order_id, order_item_id) pair.
CREATE TABLE dw.fact_order_items (
 order_id text NOT NULL REFERENCES dw.fact_orders(order_id), order_item_id integer NOT NULL,
 purchase_date_key integer NOT NULL REFERENCES dw.dim_date(date_key),
 customer_unique_id text NOT NULL REFERENCES dw.dim_customer(customer_unique_id),
 product_id text NOT NULL REFERENCES dw.dim_product(product_id),
 seller_id text NOT NULL REFERENCES dw.dim_seller(seller_id),
 price numeric(14,2) NOT NULL, freight_value numeric(14,2) NOT NULL,
 item_total numeric(14,2) GENERATED ALWAYS AS (price + freight_value) STORED,
 PRIMARY KEY (order_id, order_item_id)
);
INSERT INTO dw.fact_order_items (order_id, order_item_id, purchase_date_key, customer_unique_id, product_id, seller_id, price, freight_value)
SELECT i.order_id, i.order_item_id, o.purchase_date_key, o.customer_unique_id,
       i.product_id, i.seller_id, i.price, i.freight_value
FROM stg.order_items i JOIN dw.fact_orders o USING (order_id);
CREATE INDEX fact_items_product_idx ON dw.fact_order_items(product_id);
CREATE INDEX fact_items_seller_idx ON dw.fact_order_items(seller_id);
CREATE INDEX fact_items_date_idx ON dw.fact_order_items(purchase_date_key);
