# Learning notes

## Phase 0: Reproducibility

The same `.env` names configure Docker and Python. A named Docker volume keeps the database between `make down` and `make up`. `make all` follows the pipeline order.

## Phase 1: Raw data and profiling

Raw tables keep CSV fields as text. This allows inspection before deciding how to cast values. A row count of 99 in a CSV and 98 in the database is an ingestion error; ingestion compares both counts and rolls back. The notebook reports nulls, duplicates, date ranges, and month counts.

## Phase 2: Staging

A staging view gives raw values consistent types and names. For example, `product_name_lenght` becomes `product_name_length`. Reviews can repeat per order, so the latest answered review is chosen; source rows remain in `raw` for audit.

## Phase 3: Star schema and grain

Grain says what one row represents. One `fact_orders` row is one order; one `fact_order_items` row is one purchased item. Dimensions add descriptive context, such as product category and customer state. Aggregating item revenue to order grain prevents duplicate order counts.

## Phase 4: Data quality

A primary key prevents duplicate fact rows; foreign keys prevent missing dimension references. The revenue check compares each order's stored `items_revenue` with the sum of its item prices. Missing items or payments are reported separately and remain visible.

## Phase 5: Window functions

`LAG(revenue)` reads the prior month's revenue without a self-join; the 3-month window averages the current and two previous months. `RANK()` orders categories by revenue within each year. `NTILE(4)` gives a relative seller revenue band.

## Phase 6: Statistics and forecasting

A p-value measures how surprising data this extreme would be under the null hypothesis; it is not the probability that the hypothesis is true. Effect size shows magnitude: rank-biserial near zero means little score separation even if p is small. MAPE compares forecast error with actual revenue; a simple seasonal-naive forecast is the baseline.

## Phase 7: Dashboard extracts

`orders_flat.csv` is one row per order, so KPI cards can count orders directly. Its `primary_category` is the highest-priced item's category, a simplification for category filtering. Category revenue charts use the item-grain category mart instead.

## Phase 8: Interpretation

Report numbers with their denominators and window. A historical association between delay and reviews does not show that delay alone caused a lower review.
