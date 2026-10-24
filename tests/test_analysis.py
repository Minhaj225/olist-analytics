import numpy as np

from src.analysis.forecast import seasonal_naive, select_forecast
from src.analysis.hypothesis_tests import format_p, rank_biserial


def test_seasonal_naive_repeats_same_month_last_year():
    assert seasonal_naive(np.arange(1, 18), 3).tolist() == [6, 7, 8]


def test_rank_biserial_is_negative_when_first_group_scores_lower():
    assert rank_biserial([1, 1], [5, 5]) == -1.0


def test_forecast_uses_lower_holdout_error_for_future_values():
    winner, values = select_forecast([100, 100, 100], [90, 90, 90],
                                     [80, 80, 80], [110, 110, 110], [70, 70, 70])
    assert winner == "seasonal-naive baseline"
    assert values.tolist() == [110, 110, 110]


def test_underflowed_p_value_is_reported_as_bound():
    assert format_p(0.0) == "< 1e-300"
    assert format_p(0.05) == "= 0.05"
