# Build the Olist dashboard in Tableau Public

This guide starts after `make all` has finished. It builds the three pages in [the dashboard specification](DASHBOARD_SPEC.md) using Tableau Public in a desktop browser. You do not need to connect Tableau to PostgreSQL. Budget a few hours for a first build; save after each page.

## 1. Know what you are building

A **data source** is one CSV uploaded to Tableau. A **worksheet** is one chart or KPI card. A **dashboard** arranges several worksheets on a page. A **workbook** holds all the sources, worksheets, and dashboards.

The nine downloaded Olist CSVs are inputs to this project's pipeline. For Tableau, use the seven files already prepared in `dashboard/extracts/`:

| CSV | Use in this guide | Row meaning |
| --- | --- | --- |
| `orders_flat.csv` | Order KPI cards, state map, delivery histogram, review chart | One order |
| `kpi_monthly.csv` | Monthly revenue line | One month |
| `category_performance.csv` | Top categories and Pareto chart | One category in one year |
| `delivery_performance.csv` | Late rate by state | One state in one month |
| `seller_scorecard.csv` | Seller table | One seller for the full period |
| `customer_rfm.csv` | Customer segment charts | One customer for the full period |
| `cohort_retention.csv` | Retention heatmap | One cohort and month offset |

Keep these as **seven separate Tableau data sources**. Do not join the CSVs: their rows represent different things, and a join can multiply revenue or orders. The dashboard dates are January 2017 through August 2018. Money is Brazilian reais (BRL); revenue means delivered item price and excludes freight.

## 2. Open Tableau Public and add the files

1. Open [Tableau Public](https://public.tableau.com/) in a desktop browser, create a free account if needed, and sign in.
2. Open **My Profile → Create a Viz**. In **Files**, choose **Upload from Computer** and select `dashboard/extracts/orders_flat.csv`. Tableau's [web connection guide](https://help.tableau.com/current/online/en-us/creator_connect.htm) documents this path and CSV uploads.
3. On the **Data Source** page, inspect the column names. Go to **Sheet 1** at the bottom to start a worksheet.
4. Add each remaining CSV as a **new data source** in the same workbook: use **Data → New Data Source** or the new-data-source icon by the Data pane, choose **Files**, and upload the next file. Return to the sheet. Repeat until the Data pane lists all seven sources. When making a sheet, click the desired source name in the Data pane first.
5. Check field types on each source. Dates (`purchase_date`, `month`, `cohort_month`, `last_purchase`) should have a calendar icon. `is_late` should be Boolean. Amounts, counts, and rates should be numeric. If one was guessed as text, click its type icon in the Data Source page and choose the appropriate type. Keep IDs and two-letter state codes as text.
6. Save with **File → Save As**, using a name such as **Olist | Marketplace performance**. Tableau's [web authoring guide](https://help.tableau.com/current/pro/desktop/en-us/getstarted_web_authoring.htm) shows the worksheet, shelves, Marks card, dashboard button, and Save As flow.

**Before publishing:** Tableau Public workbooks and uploaded data are public and can be downloaded. Review the CSVs before saving there. The Olist source is a public, anonymized dataset, but `orders_flat.csv` still includes order IDs. See [Tableau's publishing notice](https://help.tableau.com/current/pro/desktop/en-us/publish_workbooks_tableaupublic.htm).

## 3. Make three reusable calculations

Select `orders_flat.csv` in the Data pane. Use **Analysis → Create Calculated Field** for each expression below. Give each field the shown name. Tableau documents [calculated fields](https://help.tableau.com/current/pro/desktop/en-us/calculations_calculatedfields.htm).

**AOV**

```tableau
SUM([items_revenue]) / COUNTD([order_id])
```

**Late Flag**

```tableau
IF ISNULL([is_late]) THEN NULL
ELSEIF [is_late] THEN 1
ELSE 0
END
```

**Lateness Bucket**

```tableau
IF ISNULL([days_vs_estimate]) THEN "Unknown"
ELSEIF [days_vs_estimate] < 0 THEN "Early"
ELSEIF [days_vs_estimate] = 0 THEN "On time"
ELSEIF [days_vs_estimate] <= 3 THEN "1–3 days late"
ELSE "4+ days late"
END
```

For every worksheet based on `orders_flat.csv`, drag `order_status` to **Filters** and select only **delivered**, unless a step says otherwise. A blank `is_late` stays blank; it is not counted as on time.

## 4. Build page 1: Executive Overview

### Five KPI cards

Create a new worksheet for each card with the **New Worksheet** button at the bottom. Select `orders_flat.csv`, apply the delivered filter, set the Marks type to **Text**, and drag the requested measure to **Text**. Rename each sheet by double-clicking its tab.

| Sheet name | Put on Text | Format | Expected full-period value |
| --- | --- | --- | --- |
| Revenue | `SUM(items_revenue)` | BRL currency, 2 decimals or millions | BRL 13,181,027.13 |
| Delivered orders | `COUNTD(order_id)` | Whole number | 96,211 |
| AOV | `AOV` | BRL currency | BRL 137.00 |
| Late rate | `AVG(Late Flag)` | Percentage, 1 decimal | 6.8% |
| Average review | `AVG(review_score)` | Number, 2 decimals | 4.16 / 5 |

For a KPI, click the pill menu if Tableau chooses the wrong aggregation. To format a number, right-click the field or axis, choose **Format** or **Default Properties → Number Format**, then set Currency, Percentage, or Number. Do not multiply `AVG(Late Flag)` by 100 before formatting it as a percentage.

### Monthly revenue line

1. New sheet; choose `kpi_monthly.csv`.
2. Drag `month` to **Columns**. Use a continuous month timeline, not a month name that mixes 2017 and 2018.
3. Drag `revenue` to **Rows** as **SUM**. Choose **Line** in Marks and format the axis as BRL.
4. Rename the sheet **Monthly revenue**. Its total across months should agree with the revenue card.

### Top 10 categories

1. New sheet; choose `category_performance.csv`.
2. Drag `category` to **Rows** and `revenue` to **Columns** as **SUM**; use horizontal bars.
3. Drag `category` to **Filters**, open the **Top** tab, select **By field → Top 10 by SUM(revenue)**. Sort descending by revenue.
4. Rename it **Top 10 categories**. This source has exact item-category revenue; the order source's `primary_category` is only an approximation for mixed-category orders.

### Revenue by state map

1. New sheet; choose `orders_flat.csv` and apply the delivered filter.
2. Right-click `customer_state` and choose **Geographic Role → State/Province**. Double-click `customer_state` to create a map; drag `SUM(items_revenue)` to **Color** and to **Tooltip**.
3. If Tableau marks Brazilian state codes as unknown, use **Map → Edit Locations**, set **Country/Region** to **Brazil**, and resolve remaining unknowns. Follow [Tableau's location guide](https://help.tableau.com/current/pro/desktop/en-us/maps_editlocation.htm). If the codes still will not map, make a sorted state bar chart with the same measure instead.
4. Rename the sheet **Revenue by state**.

### Assemble the page

1. Click **New Dashboard** at the bottom. Name it **1 | Executive Overview**.
2. Pick a desktop size around 1200 × 800 pixels. Drag the five KPI sheets into a top row; put the revenue line across the middle; put categories and the map below. Use tiled layout containers if alignment is difficult.
3. Add a **Text** object: “Delivered item revenue, January 2017–August 2018. Late rate uses 96,203 orders with known lateness; eight delivered orders lack delivery dates.”
4. Drag an **Image** object to the dashboard and insert `reports/figures/revenue_forecast.png`. Label it “Static forecast, generated outside Tableau; it does not change with dashboard filters.” Tableau documents [image objects and alt text](https://help.tableau.com/current/pro/desktop/en-us/dashboards_create.htm). The forecast is exploratory: its three-month holdout MAPE was 36.6%, and its shaded band is not a calibrated prediction interval.
5. Save.

## 5. Build page 2: Delivery and Satisfaction

### Late rate by state

1. Select `delivery_performance.csv`; create a calculated field named **Weighted Late Rate (%)**:

   ```tableau
   IF SUM([known_lateness_orders]) = 0 THEN NULL
   ELSE SUM([late_pct] * [known_lateness_orders]) / SUM([known_lateness_orders])
   END
   ```

2. Put `customer_state` on **Rows** and **Weighted Late Rate (%)** on **Columns**. Use bars and sort descending. Format as a regular number with one decimal and a % suffix; `late_pct` is already stored on a 0–100 scale, so Tableau's Percentage format would inflate it 100 times.
3. Rename the sheet **Late rate by state**.

### Delivery-day distribution

1. Select `orders_flat.csv`; apply the delivered filter.
2. Right-click `days_to_deliver` → **Create → Bins**. Start with a five-day bin size. Put the new bin field on **Columns** and `COUNTD(order_id)` on **Rows**; choose bars.
3. Rename it **Delivery days distribution**. Blank delivery days do not appear in the histogram. Tableau's [histogram guide](https://help.tableau.com/current/pro/desktop/en-us/buildexamples_histogram.htm) shows the same pattern.

### Reviews by lateness

1. Select `orders_flat.csv`; apply the delivered filter.
2. Put **Lateness Bucket** on **Columns** and `AVG(review_score)` on **Rows**; use bars. Order the buckets Early, On time, 1–3 days late, 4+ days late, Unknown.
3. Rename it **Review by lateness**. Keep **Unknown** visible so missing delivery dates are not hidden.

### Seller scorecard

1. Select `seller_scorecard.csv`. Put `seller_id` on **Rows**. Put `orders`, `revenue`, `late_pct`, `avg_review_score`, and `revenue_quartile` in the table, using **Measure Names/Measure Values** if Tableau shows only one measure initially.
2. Sort by `SUM(revenue)` descending and show the top 20 sellers to keep the table readable. Format `late_pct` as a regular number plus % because it is on a 0–100 scale.
3. Rename it **Seller scorecard**. It covers the full analysis window; it does not contain customer state or month.

Create dashboard **2 | Delivery and Satisfaction**. Place the state chart and histogram on top, reviews and the seller table below. Add a note that the seller table stays full-period when a state or date filter is used.

## 6. Build page 3: Customers and Products

### RFM customer segments

1. Select `customer_rfm.csv`. Create a bar chart with `segment` on **Rows** and `COUNTD(customer_unique_id)` on **Columns**. Name it **Customers by segment**.
2. Duplicate the sheet. Replace customer count with `SUM(monetary)`, then use the measure pill's **Quick Table Calculation → Percent of Total** and set **Compute Using → Table (Down)**. Name it **Revenue share by segment**. The percentages should total about 100%.

### Cohort retention heatmap

1. Select `cohort_retention.csv`. Put `cohort_month` on **Rows** and `months_since_first` on **Columns**. Make the month offset a **discrete dimension** if Tableau treats it as a continuous axis.
2. Choose **Square** in Marks. Put `AVG(retention_rate)` on **Color** and **Label**. Format this 0–1 value as a percentage.
3. Rename the sheet **Cohort retention**. Small values after month 0 are expected; the first month of a cohort is 100%.

### Category Pareto

1. Select `category_performance.csv`. Put `year` on **Filters** and select one year, because `cumulative_revenue_share` starts over each year.
2. Put `category` on **Columns**, sorted ascending by `MIN(revenue_rank)`. Put `SUM(revenue)` on **Rows**.
3. Drag `MAX(cumulative_revenue_share)` onto **Rows** beside revenue; open that pill's menu and choose **Dual Axis**. In the two Marks cards, set revenue to **Bar** and cumulative share to **Line**. Format the right axis as Percentage. Tableau's [web feature comparison](https://help.tableau.com/current/pro/desktop/en-us/server_desktop_web_edit_differences.htm) lists dual-axis formatting in web authoring.
4. Make the sheet wide enough to read. If labels crowd, filter `revenue_rank` to 1–20 and say “Top 20 shown; cumulative share is still measured against all categories.”
5. Rename it **Category Pareto**.

Create dashboard **3 | Customers and Products**. Put the two RFM charts together, with cohort retention below and the Pareto chart across the bottom. Add “RFM and seller results are fixed to the full analysis window” near the filters.

## 7. Add filters without changing what the charts mean

On an `orders_flat.csv` sheet, drag `purchase_date` to **Filters**, choose **Range of dates**, then show the filter. You can share it with other order-source sheets using the filter menu **Apply to Worksheets → All Using This Data Source**. Add `customer_state` the same way. Tableau explains [filter scope](https://help.tableau.com/current/pro/desktop/en-gb/filtering_global.htm).

Filters on one CSV do **not** automatically control sheets built from the other six CSVs. For the monthly trend, add its own `month` date filter; for late rate by state, add `month` and `customer_state` from `delivery_performance.csv`; for category charts, use `year` and `category` from `category_performance.csv`. State and category are absent from RFM, cohort, and seller extracts, so leave those charts labeled as full-period. Do not label a workbook filter “all pages” unless you have checked every sheet it changes.

If you use `primary_category` as an order-level filter, label it “primary category”: mixed-category orders are assigned to the highest-priced item only. Category revenue in `category_performance.csv` uses the actual items.

## 8. Check the finished dashboard

1. Clear optional filters and compare the five cards with the values in section 4. A mismatch usually means the delivered filter is missing, a field is being counted rather than summed, or a percentage was multiplied by 100 twice.
2. Confirm the monthly line spans January 2017–August 2018, the category chart has ten categories, and the map has Brazilian states or the stated bar-chart fallback.
3. Check the late-rate tooltip or page note says its denominator is **96,203**, while delivered orders are **96,211**.
4. Try a state and date filter, then inspect which sheets change. Keep “full-period” labels on sheets that stay fixed.
5. Save the workbook. In Tableau Public, copy the **Share** link from the published view and add it to the project README. Capture one screenshot per dashboard in `dashboard/screenshots/`.

Uploaded CSVs on Tableau Public are snapshots. After rerunning this project's pipeline, update the Tableau connection or re-upload the changed files and recheck the five cards; the public workbook does not automatically read the local CSVs. See [Tableau's data refresh guidance](https://help.tableau.com/current/online/en-us/creator_connect.htm).

## Is it okay to leave the data-quality warnings?

**Yes, for this historical dashboard, with the exclusions stated clearly.** Do not invent missing delivery dates, items, or payments. The warning total is not 776 bad sales: all **775 orders without items are not delivered** (603 unavailable, 164 canceled, 5 created, 2 invoiced, 1 shipped). The **one delivered order without a payment** was purchased on **2016-09-15**, outside this dashboard's analysis window. These records do not change the displayed delivered revenue or order count.

The **eight delivered orders without delivery dates** are within the analysis window. They remain in revenue, order count, and review measures, but cannot be called late or on time. The late rate therefore uses **96,203 known-lateness delivered orders**, rather than all 96,211 delivered orders. Show that denominator beside the late-rate KPI and avoid calling unknown dates “on time.” These eight records are roughly 0.008% of delivered orders, but their existence should still be visible.

This is acceptable for a descriptive portfolio analysis, not a rule to ignore future defects. The pipeline now has a **critical check for delivered orders without items**; any such order would make delivered revenue incomplete and stop the quality gate. If new missing-payment records enter the analysis window or missing delivery dates become material, investigate the source and revisit the dashboard before publishing updated figures. The detailed policy is in the [data dictionary](../docs/data_dictionary.md).
