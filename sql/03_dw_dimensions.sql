-- Grain: one date, one real customer, one product, and one seller per dimension row.
-- Rebuild within the runner's single transaction, so failed builds roll back together.
DROP SCHEMA IF EXISTS dw CASCADE;
CREATE SCHEMA dw;

CREATE TABLE dw.dim_date (
 date_key integer PRIMARY KEY, date date NOT NULL UNIQUE, year integer NOT NULL,
 quarter integer NOT NULL, month integer NOT NULL, month_name text NOT NULL,
 week integer NOT NULL, day_of_week integer NOT NULL, is_weekend boolean NOT NULL
);
INSERT INTO dw.dim_date
SELECT to_char(d, 'YYYYMMDD')::integer, d::date, extract(year FROM d)::integer,
       extract(quarter FROM d)::integer, extract(month FROM d)::integer,
       trim(to_char(d, 'Month')), extract(week FROM d)::integer,
       extract(isodow FROM d)::integer, extract(isodow FROM d) IN (6,7)
FROM generate_series((SELECT min(purchase_at)::date FROM stg.orders),
                     (SELECT max(purchase_at)::date FROM stg.orders), interval '1 day') d;

CREATE TABLE dw.dim_customer (
 customer_unique_id text PRIMARY KEY, city text, state text, region text
);
-- Latest order gives a stable single location when a customer moved.
INSERT INTO dw.dim_customer
SELECT customer_unique_id, city, state,
 CASE WHEN state IN ('AC','AM','AP','PA','RO','RR','TO') THEN 'North'
      WHEN state IN ('AL','BA','CE','MA','PB','PE','PI','RN','SE') THEN 'Northeast'
      WHEN state IN ('DF','GO','MS','MT') THEN 'Central-West'
      WHEN state IN ('ES','MG','RJ','SP') THEN 'Southeast'
      WHEN state IN ('PR','RS','SC') THEN 'South' ELSE 'Unknown' END
FROM (
 SELECT c.*, row_number() OVER (PARTITION BY c.customer_unique_id ORDER BY o.purchase_at DESC NULLS LAST, c.customer_id DESC) rn
 FROM stg.customers c LEFT JOIN stg.orders o USING (customer_id)
) x WHERE rn = 1;

CREATE TABLE dw.dim_product (
 product_id text PRIMARY KEY, category text NOT NULL, weight_g numeric,
 length_cm numeric, height_cm numeric, width_cm numeric, photo_count integer
);
INSERT INTO dw.dim_product
SELECT product_id, category, weight_g, length_cm, height_cm, width_cm, photo_count FROM stg.products;
CREATE INDEX dim_product_category_idx ON dw.dim_product(category);

CREATE TABLE dw.dim_seller (seller_id text PRIMARY KEY, city text, state text);
INSERT INTO dw.dim_seller SELECT seller_id, city, state FROM stg.sellers;
CREATE INDEX dim_customer_state_idx ON dw.dim_customer(state);
CREATE INDEX dim_seller_state_idx ON dw.dim_seller(state);
