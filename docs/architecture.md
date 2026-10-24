# Architecture

```mermaid
flowchart LR
  CSV[Olist CSVs] --> RAW[raw text tables]
  RAW --> STG[stg typed and deduplicated views]
  STG --> DW[dw star schema]
  DW --> MART[mart analysis views]
  MART --> CSVX[dashboard CSV extracts]
  CSVX --> BI[Tableau Public or Power BI]
  DW --> PY[Python statistics and forecast]
  PY --> F[findings and figures]
```

The SQL runner applies files in numeric order in one transaction. Rebuilding replaces the warehouse and marts; a failed build rolls back. Ingestion truncates and reloads all raw tables in one transaction.

```mermaid
erDiagram
  dim_date ||--o{ fact_orders : purchase_date_key
  dim_customer ||--o{ fact_orders : customer_unique_id
  fact_orders ||--o{ fact_order_items : order_id
  dim_date ||--o{ fact_order_items : purchase_date_key
  dim_customer ||--o{ fact_order_items : customer_unique_id
  dim_product ||--o{ fact_order_items : product_id
  dim_seller ||--o{ fact_order_items : seller_id
```

`fact_orders` has one row per source order. `fact_order_items` has one row per `(order_id, order_item_id)`. Customer identity uses `customer_unique_id`; the source `customer_id` identifies an order-specific customer record.
