"""Build a self-contained dashboard from the public, aggregate extracts."""

import base64
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).parent
SOURCE = ROOT / "public_extracts"
names = ("monthly_state", "delivery_bins", "review_buckets", "categories",
         "seller_top20", "rfm_segments", "cohort_retention")
data = {name: json.loads(pd.read_csv(SOURCE / f"{name}.csv").to_json(orient="records"))
        for name in names}
monthly = pd.read_csv(SOURCE / "monthly_state.csv")
assert int(monthly.orders.sum()) == 96211
assert abs(monthly.revenue.sum() - 13181027.13) < 0.01
assert int(monthly.known_lateness_orders.sum()) == 96203

forecast = ROOT.parent / "reports/figures/revenue_forecast.png"
image = ("data:image/png;base64," + base64.b64encode(forecast.read_bytes()).decode()
         if forecast.exists() else "")
template = (ROOT / "dashboard.template.html").read_text()
output = (template.replace("__DASHBOARD_DATA__", json.dumps(data, ensure_ascii=False)
                           .replace("</", "<\\/"))
          .replace("__FORECAST_IMAGE__", image))
target = ROOT / "Olist_dashboard.html"
target.write_text(output)
print(f"Built {target} ({target.stat().st_size:,} bytes)")
