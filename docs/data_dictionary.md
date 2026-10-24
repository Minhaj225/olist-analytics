# Data dictionary and profiling decisions

The nine source CSVs were profiled locally on 24 October 2026. The marts include months with at least 500 source orders, yielding a contiguous **January 2017–August 2018** analysis window (20 months). January 2017 has 800 orders and August 2018 has 6,512; the sparse edge months outside this window have 1–324 orders. The full source purchase range is 4 September 2016 to 17 October 2018. Run `notebooks/01_eda.ipynb` again if the CSVs change.

All source columns are stored as `text` in `raw`, plus `_loaded_at timestamptz`. The typed names below are staging view columns; the warehouse preserves these meanings.

| Source file / raw table | Raw columns (all text) | Staging columns and types |
|---|---|---|
| `olist_customers_dataset.csv` / `customers` | `customer_id`, `customer_unique_id`, `customer_zip_code_prefix`, `customer_city`, `customer_state` | `customer_id text`, `customer_unique_id text`, `zip_prefix integer`, `city text`, `state text` |
| `olist_geolocation_dataset.csv` / `geolocation` | `geolocation_zip_code_prefix`, `geolocation_lat`, `geolocation_lng`, `geolocation_city`, `geolocation_state` | `zip_prefix integer`, `lat numeric`, `lng numeric`, `city text`, `state text` |
| `olist_order_items_dataset.csv` / `order_items` | `order_id`, `order_item_id`, `product_id`, `seller_id`, `shipping_limit_date`, `price`, `freight_value` | `order_id text`, `order_item_id integer`, `product_id text`, `seller_id text`, `shipping_limit_at timestamp`, `price numeric(14,2)`, `freight_value numeric(14,2)` |
| `olist_order_payments_dataset.csv` / `order_payments` | `order_id`, `payment_sequential`, `payment_type`, `payment_installments`, `payment_value` | `order_id text`, `payment_sequential integer`, `payment_type text`, `payment_installments integer`, `payment_value numeric(14,2)` |
| `olist_order_reviews_dataset.csv` / `order_reviews` | `review_id`, `order_id`, `review_score`, `review_comment_title`, `review_comment_message`, `review_creation_date`, `review_answer_timestamp` | `review_id text`, `order_id text`, `review_score integer`, `review_creation_at timestamp`, `review_answer_at timestamp` |
| `olist_orders_dataset.csv` / `orders` | `order_id`, `customer_id`, `order_status`, `order_purchase_timestamp`, `order_approved_at`, `order_delivered_carrier_date`, `order_delivered_customer_date`, `order_estimated_delivery_date` | `order_id text`, `customer_id text`, `order_status text`, `purchase_at timestamp`, `approved_at timestamp`, `carrier_at timestamp`, `delivered_at timestamp`, `estimated_at timestamp` |
| `olist_products_dataset.csv` / `products` | `product_id`, `product_category_name`, `product_name_lenght`, `product_description_lenght`, `product_photos_qty`, `product_weight_g`, `product_length_cm`, `product_height_cm`, `product_width_cm` | `product_id text`, `category text`, `product_name_length integer`, `product_description_length integer`, `photo_count integer`, `weight_g numeric`, `length_cm numeric`, `height_cm numeric`, `width_cm numeric` |
| `olist_sellers_dataset.csv` / `sellers` | `seller_id`, `seller_zip_code_prefix`, `seller_city`, `seller_state` | `seller_id text`, `zip_prefix integer`, `city text`, `state text` |
| `product_category_name_translation.csv` / `category_translation` | `product_category_name`, `product_category_name_english` | `category_name text`, `category_english text` |

## Warehouse grains and measures

| Table | Grain / key | Main fields |
|---|---|---|
| `dw.dim_date` | One calendar date / `date_key` | date, year, quarter, month, month_name, week, day_of_week, is_weekend |
| `dw.dim_customer` | One real person / `customer_unique_id` | city, state, region from latest order location |
| `dw.dim_product` | One product / `product_id` | category, weight, dimensions, photo_count |
| `dw.dim_seller` | One seller / `seller_id` | city, state |
| `dw.fact_orders` | One order / `order_id` | item_count, items_revenue, freight_total, payment_total, payment type, review, delivery measures |
| `dw.fact_order_items` | One item / `(order_id, order_item_id)` | price, freight_value, generated item_total, date/customer/product/seller keys |

## Known quirks and decisions

- `customer_id` is an order-level record key. Customer retention and RFM use `customer_unique_id`.
- Raw reviews are retained. Staging keeps one review per order: latest answer timestamp, then creation timestamp, then greatest review ID. Duplicate review IDs can therefore remain in raw without multiplying orders.
- Geolocation staging chooses one deterministic row per ZIP prefix; it is not used in warehouse measures, so duplicated geography cannot multiply facts.
- Product categories use the English translation when present, then Portuguese, then `unknown`.
- Delivery timestamps remain null for undelivered orders. `is_late` is null when actual or estimated delivery is missing.
- An order without items or payments stays in `fact_orders` with zero sums. There are 775 orders without items: 603 unavailable, 164 canceled, 5 created, 2 invoiced, and 1 shipped. None is delivered. One delivered order has no payment, but its purchase date is 2016-09-15, outside the January 2017–August 2018 analysis window. `warn_missing_items_payments.sql` reports all 776 rows; `08_delivered_without_items.sql` is a critical check that fails if a delivered order has no items.
- Delivered orders with missing delivery dates or delivery before purchase are reported by `warn_delivery_dates.sql`, not silently removed. There are 8 delivered orders without a delivery timestamp and none with delivery before purchase. The 8 are included in delivered revenue and order counts, but excluded from late-rate calculations because `is_late` is null. The late-rate denominator is 96,203 known-lateness delivered orders, versus 96,211 delivered orders in the analysis window.
- Revenue is item price for delivered orders, excluding freight and canceled orders. In the analysis window, 2,789 of 93,104 customers (3.0%) have more than one delivered purchase.
- The 500-order cutoff selects the observed contiguous January 2017–August 2018 window. It is an explicit analytical choice, not a source-data correction.

## Observed source profile

| Raw table | Rows | Duplicate complete rows | Notable nulls / dates |
|---|---:|---:|---|
| customers | 99,441 | 0 | No null source columns |
| geolocation | 1,000,163 | 261,831 | 981,148 repeated ZIP prefixes; no null source columns |
| order_items | 112,650 | 0 | No null source columns; shipping limit dates extend to 9 April 2020 |
| order_payments | 103,886 | 0 | No null source columns |
| order_reviews | 99,224 | 0 | 87,656 null titles; 58,247 null messages; 814 repeated review IDs and 547 orders with multiple reviews |
| orders | 99,441 | 0 | 160 null approval times, 1,783 null carrier times, 2,965 null customer delivery times |
| products | 32,951 | 0 | 610 null categories and name/description/photo fields; 2 null weights/dimensions |
| sellers | 3,095 | 0 | No null source columns |
| category_translation | 71 | 0 | No null source columns |

Thirteen non-null product category names lack an English translation, so staging retains Portuguese. Date ranges and per-column distributions are generated by the notebook into local `data/profile.json` (ignored by Git).
