# Project Plan: E-commerce Analytics Pipeline + Dashboard (Olist)

> Hand this file to Claude Code as the project brief. Work through the phases in order, finish each phase's "Done when" checks before moving on, and commit after each phase.

## 1. Goal and context

Build an end-to-end analytics project that turns raw e-commerce CSVs into a clean PostgreSQL warehouse, runs statistical and predictive analysis on top, and feeds a BI dashboard (Tableau Public or Power BI) with business KPIs and written recommendations.

This is a **resume project for a Data Analyst Trainee role** (SQL/Python pipelines, statistical tests, ML/forecasting, dashboards, clear business communication). The owner is a CS student who is **new to data warehousing, window functions, and statistical testing**, so:

- Keep the design simple and readable. No over-engineering (no Airflow, no dbt, no Spark).
- Maintain `docs/LEARNING.md`: after each phase, add a short plain-language explanation of the concepts used (e.g. star schema, grain, window functions, p-values, effect size) with one small example from this project.
- Comment SQL files so each transformation's purpose is clear.
- Explain non-obvious choices in the commit message or docs, not just in code.

## 2. Tech stack

| Layer | Choice |
|---|---|
| Database | PostgreSQL 16 in Docker (docker-compose) |
| Language | Python 3.11+ |
| Libraries | pandas, SQLAlchemy 2.x, psycopg (v3), scipy, statsmodels, scikit-learn, matplotlib/seaborn, pytest, python-dotenv |
| SQL | Plain `.sql` files, run in order by a Python runner |
| BI | Tableau Public (works on any OS) or Power BI Desktop (Windows only), built by the owner from CSV extracts this project generates |
| Tooling | Makefile for common commands, `.env` for config |

## 3. Dataset

**Brazilian E-Commerce Public Dataset by Olist** (Kaggle). About 100k orders, Sep 2016 to Oct 2018.

The owner must download it manually from Kaggle (login required) and place the CSVs in `data/raw/`. Do not try to scrape it. If the files are missing, stop and print a clear message listing the expected files:

- `olist_customers_dataset.csv`
- `olist_geolocation_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `olist_orders_dataset.csv`
- `olist_products_dataset.csv`
- `olist_sellers_dataset.csv`
- `product_category_name_translation.csv`

Known data quirks to handle (verify each during profiling, don't assume):

- Product columns are misspelled in the source (`product_name_lenght`, `product_description_lenght`). Rename in staging.
- `customer_id` is unique per order; `customer_unique_id` identifies the actual person. Use `customer_unique_id` for any customer-level analysis.
- `order_reviews` can contain duplicate `review_id`s and multiple reviews per order. Define and document a dedupe rule (e.g. keep the latest review per order).
- `geolocation` has many duplicate zip prefixes. Aggregate to one row per zip prefix or leave it out of the warehouse if unused.
- Delivery timestamps are null for non-delivered orders.
- Some orders have no items or no payments. Report counts; do not silently drop.
- Early (2016) and late (late 2018) months are sparse. Determine the reliable analysis window from profiling (expected roughly Jan 2017 to Aug 2018) and document the cutoff.
- Some product categories lack English translations. Fall back to the Portuguese name, or `unknown`.

## 4. Repository structure

```
olist-analytics/
├── README.md
├── PLAN.md
├── Makefile
├── docker-compose.yml
├── .env.example
├── .gitignore                # ignore data/raw, .env, extracts if large
├── requirements.txt
├── data/
│   └── raw/                  # owner places CSVs here (gitignored)
├── sql/
│   ├── 00_schemas.sql        # create schemas: raw, stg, dw, mart
│   ├── 01_raw_tables.sql
│   ├── 02_staging.sql
│   ├── 03_dw_dimensions.sql
│   ├── 04_dw_facts.sql
│   ├── 05_marts.sql
│   └── checks/               # SQL data-quality assertions
├── src/
│   ├── config.py             # reads .env
│   ├── db.py                 # SQLAlchemy engine helper
│   ├── ingest.py             # CSV -> raw.*
│   ├── run_sql.py            # runs sql files in order
│   ├── quality_checks.py     # runs checks, fails loudly
│   ├── analysis/
│   │   ├── kpis.py
│   │   ├── hypothesis_tests.py
│   │   ├── forecast.py
│   │   └── rfm.py
│   └── export_extracts.py    # mart tables -> dashboard/extracts/*.csv
├── notebooks/
│   └── 01_eda.ipynb          # profiling + exploratory analysis
├── tests/
├── dashboard/
│   ├── DASHBOARD_SPEC.md     # pages, charts, KPI definitions
│   ├── extracts/             # CSVs for Tableau/Power BI
│   └── screenshots/          # added by owner
├── docs/
│   ├── LEARNING.md
│   ├── data_dictionary.md
│   ├── architecture.md       # includes a Mermaid diagram
│   └── findings.md           # business findings + recommendations
└── reports/
    └── figures/              # saved charts from analysis
```

## 5. Phases

### Phase 0: Project scaffolding
- Create the repo structure above, `requirements.txt` (pinned versions), `.gitignore`, `.env.example` (DB host, port, name, user, password), and a `docker-compose.yml` running Postgres with a named volume.
- Create a `Makefile` with targets: `up`, `down`, `ingest`, `build` (run all SQL), `check`, `analyze`, `export`, `test`, `all`.
- Write a first `README.md` skeleton (title, one-paragraph summary, "how to run" placeholder).

**Done when:** `make up` starts Postgres, and a small script can connect and run `SELECT 1`.

### Phase 1: Ingestion and profiling
- `ingest.py` loads each CSV into `raw.<table>` with no business logic. Use `COPY` or `to_sql` with chunking. Keep raw columns as loaded; add `_loaded_at` timestamp.
- Make ingestion **idempotent** (truncate and reload, so rerunning does not duplicate rows).
- Log row counts per table and compare to CSV row counts.
- In `notebooks/01_eda.ipynb`, profile every table: nulls, duplicates, date ranges, distributions, and the quirks listed in section 3. Write the findings into `docs/data_dictionary.md` and note the chosen analysis window.

**Done when:** `make ingest` is re-runnable, row counts match the CSVs, and the data dictionary lists every table, column, type, and known quirk.

### Phase 2: Staging layer (`stg`)
- One staging table or view per raw table: cast types (timestamps, numerics), trim strings, rename misspelled columns, standardize category names, apply the dedupe rules, and join the category translation.
- Keep staging one-to-one with source entities. No aggregation here.

**Done when:** all `stg.*` objects exist, have correct types, and have no duplicate primary keys.

### Phase 3: Warehouse (`dw`), star schema
Design with explicit **grain** documented at the top of each SQL file.

Dimensions:
- `dw.dim_date` (generate a calendar covering the data range: date_key, date, year, quarter, month, month_name, week, day_of_week, is_weekend)
- `dw.dim_customer` (one row per `customer_unique_id`: city, state, region)
- `dw.dim_product` (product_id, English category, weight, dimensions, photo count)
- `dw.dim_seller` (seller_id, city, state)

Facts:
- `dw.fact_order_items`: grain = one row per order item. Keys to all dimensions, `price`, `freight_value`, `item_total`.
- `dw.fact_orders`: grain = one row per order. Customer key, purchase date key, status, item count, items revenue, freight total, payment total, primary payment type, max installments, review score, `approval_lag_hours`, `days_to_deliver`, `days_vs_estimate` (positive = late), `is_late`.

Add primary keys, foreign keys, and indexes on join and filter columns.

**Done when:** fact row counts reconcile to staging, no orphan foreign keys, and a sample query joining fact to all dimensions returns sensible results.

### Phase 4: Data quality checks
Create `sql/checks/*.sql` and `quality_checks.py`. Each check returns failing rows or a count, and the runner exits non-zero on failure. Include at least:
- Primary key uniqueness on every dw table
- No null keys in facts
- `items_revenue` in `fact_orders` reconciles to the sum of `fact_order_items.price` per order
- Delivered orders have a delivery date; delivery date is not before purchase date (report violations, don't hide them)
- Row-count reconciliation between layers
- Review scores within 1 to 5
- Non-negative prices and freight

Document known, accepted exceptions in `docs/data_dictionary.md`.

**Done when:** `make check` prints a pass/fail table and fails the process if any critical check fails.

### Phase 5: Marts (`mart`)
Build analysis-ready tables or views using **CTEs and window functions** (comment each so the owner can learn from them):
- `mart.kpi_monthly`: orders, revenue, AOV, items per order, freight share, MoM growth (`LAG`), and a 3-month rolling average
- `mart.delivery_performance`: by month and customer state: avg days to deliver, % late, avg delay when late, avg review score
- `mart.category_performance`: revenue, orders, avg review, revenue rank within the year (`RANK`/`DENSE_RANK`), and cumulative revenue share for a Pareto chart
- `mart.seller_scorecard`: orders, revenue, late rate, avg review, with a quartile band (`NTILE`)
- `mart.cohort_retention`: first-purchase month cohort vs months since first purchase, using `customer_unique_id`. **Note:** repeat purchase rate in this dataset is very low (a few percent). Report that honestly as a finding (acquisition-heavy, weak retention) instead of padding the chart.
- `mart.customer_rfm`: recency, frequency, monetary per customer with segment labels (see Phase 6)

**Done when:** each mart returns plausible numbers that match a manual spot-check query against the fact tables.

### Phase 6: Python analytics layer
All scripts must be reproducible, save charts to `reports/figures/`, and write key numbers to `docs/findings.md`.

1. **KPIs** (`kpis.py`): reproduce headline KPIs in pandas and assert they match the SQL marts (cross-validation).
2. **Hypothesis tests** (`hypothesis_tests.py`). For each: state H0/H1, check assumptions (distribution shape, sample sizes), choose the appropriate test, report p-value **and effect size**, and write a one-sentence business interpretation.
   - H1: Late-delivered orders have lower review scores than on-time orders (Mann-Whitney U, since scores are ordinal; effect size such as rank-biserial or Cliff's delta).
   - H2: Delivery delay (days) is negatively correlated with review score (Spearman).
   - H3: Order value differs across payment types (Kruskal-Wallis, with post-hoc comparisons if significant).
   - H4 (optional): Freight cost share differs across customer regions.
3. **RFM segmentation** (`rfm.py`): score R, F, M (quantile-based; because most customers have F=1, handle ties sensibly and document it), assign segments (e.g. Champions, Big Spenders, New, At Risk, Lost), and save segment sizes and revenue share.
4. **Forecast** (`forecast.py`): forecast monthly revenue over the reliable window. Hold out the last 3 complete months, compare a **seasonal-naive baseline vs Holt-Winters** (statsmodels), and report MAPE for both. If the series is too short for seasonality, say so and use a simpler method. Plot actual vs forecast with an interval.
5. **Optional delivery-risk flag**: a logistic regression (or gradient boosting) predicting `is_late` from order attributes (state, seller state, freight, weight, purchase month), with a train/test split, ROC-AUC, and a feature-importance chart. Keep this clearly secondary to the SQL and dashboard work.

**Done when:** each analysis runs from a single command, outputs figures plus numbers, and `docs/findings.md` contains the interpreted results.

### Phase 7: Dashboard extracts and spec
- `export_extracts.py` writes each mart (and a flat denormalized `orders_flat.csv` for easy BI use) to `dashboard/extracts/` with consistent column naming and ISO dates.
- Write `dashboard/DASHBOARD_SPEC.md` describing the dashboard the owner will build manually in Tableau Public or Power BI:
  - **Page 1, Executive Overview:** KPI cards (revenue, orders, AOV, % late, avg review), monthly revenue trend with the forecast, top 10 categories, revenue by state map.
  - **Page 2, Delivery and Satisfaction:** % late by state, delivery days distribution, review score by lateness bucket, seller scorecard table.
  - **Page 3, Customers and Products:** RFM segment sizes and revenue share, cohort retention view, Pareto of category revenue.
  - Filters: date range, state, category. Each KPI card must include its **exact definition** and the source column or table.
  - Recommended color/layout notes and a list of calculated fields to create.

**Done when:** `make export` regenerates all CSVs and the spec lists exactly which extract feeds which chart.

### Phase 8: Documentation and polish
- `docs/architecture.md`: Mermaid diagram of raw → stg → dw → mart → extracts/dashboard, plus the star schema diagram (ERD).
- `docs/findings.md`: 4 to 6 findings, each with the evidence (number or chart), the business implication, and a concrete recommendation (e.g. "Late deliveries in state X drive Y points lower reviews, so prioritize carrier or seller fixes there").
- `README.md`: problem statement, architecture diagram, stack, quick start (`make all`), key findings summary with 2 to 3 headline numbers, dashboard screenshots (added by owner) or link to the Tableau Public page, project structure, and limitations (single dataset, low repeat purchases, historical data).
- `tests/`: pytest tests for pure-Python functions (RFM scoring, delay calculations, KPI assertions) and a test that runs quality checks against the built database.
- Optional: a GitHub Actions workflow that runs `pytest` and linting on push.

**Done when:** a fresh clone plus downloaded CSVs plus `make all` reproduces everything, and README instructions work as written.

## 6. Working rules for Claude Code

1. Work phase by phase. After each phase, run its checks, update `docs/LEARNING.md`, and commit with a clear message (`phase-3: build star schema`).
2. Never hardcode credentials. Use `.env`; commit only `.env.example`.
3. Never silently drop or fix bad data. Log counts and document each decision in the data dictionary.
4. Prefer clear, readable SQL (CTEs, consistent naming, comments) over clever one-liners.
5. Make every script re-runnable without manual cleanup.
6. When a choice has real trade-offs (e.g. the review dedupe rule, the analysis window), pick a sensible default, document the reasoning, and flag it in the phase summary.
7. If something blocks progress (missing CSVs, Docker not installed), stop and report exactly what is needed.
8. At the end of each phase, give a 3 to 5 line summary: what was built, what was verified, and what the owner should review.

## 7. Manual steps for the owner (Claude Code cannot do these)

- [ ] Install Docker and Python 3.11+
- [ ] Download the Olist dataset from Kaggle into `data/raw/`
- [ ] Build the dashboard in Tableau Public or Power BI following `dashboard/DASHBOARD_SPEC.md`
- [ ] Save dashboard screenshots to `dashboard/screenshots/` and publish the Tableau Public link (if used)
- [ ] Read `docs/LEARNING.md` after each phase and be ready to explain every SQL query and test choice in an interview
- [ ] Push to GitHub with a clean commit history and a polished README

## 8. Interview talking points (fill in at the end)

- The business question and the three most important findings
- Why this star schema design and what the grain of each fact table is
- One data quality issue found, and how it was handled
- Why Mann-Whitney instead of a t-test for review scores
- How the forecast was validated against a baseline
- What you would do next with more time or data
