import pandas as pd

from datetime import datetime

from src.analysis.kpis import calculate_kpis, delivery_delay_days
from src.analysis.rfm import score_customers


def test_kpis_exclude_undelivered_revenue():
    orders = pd.DataFrame({
        "order_status": ["delivered", "canceled"],
        "items_revenue": [100.0, 900.0],
        "is_late": [True, False],
        "review_score": [3, 5],
    })
    result = calculate_kpis(orders)
    assert result["revenue"] == 100.0
    assert result["orders"] == 1
    assert result["aov"] == 100.0
    assert result["late_pct"] == 100.0


def test_rfm_ties_do_not_split_equal_frequencies():
    customers = pd.DataFrame({
        "customer_unique_id": ["a", "b", "c"],
        "recency_days": [5, 50, 150],
        "frequency": [1, 1, 2],
        "monetary": [100.0, 200.0, 300.0],
    })
    scored = score_customers(customers)
    assert scored.loc[scored.customer_unique_id == "a", "f_score"].item() == scored.loc[scored.customer_unique_id == "b", "f_score"].item()
    assert scored.loc[scored.customer_unique_id == "c", "f_score"].item() > scored.loc[scored.customer_unique_id == "a", "f_score"].item()
    assert scored.loc[scored.customer_unique_id == "a", "r_score"].item() > scored.loc[scored.customer_unique_id == "c", "r_score"].item()
    assert scored.r_score.tolist() == [5, 4, 2]
    assert scored.f_score.tolist() == [2, 2, 5]
    assert scored.m_score.tolist() == [2, 4, 5]


def test_delivery_delay_uses_calendar_days():
    assert delivery_delay_days(datetime(2020, 1, 2, 1), datetime(2020, 1, 1, 23)) == 1
    assert delivery_delay_days(None, datetime(2020, 1, 1)) is None
