import numpy as np

from src.analysis.common import read_sql, save_figure, write_findings


def seasonal_naive(values, horizon):
    values = np.asarray(values, dtype=float)
    if len(values) < 12:
        raise ValueError("Seasonal naive needs at least 12 observed months")
    return values[-12:][:horizon]


def mape(actual, predicted):
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    return float(np.mean(np.abs((actual - predicted) / actual)) * 100)


def select_forecast(actual, baseline_holdout, model_holdout, baseline_future, model_future):
    if mape(actual, baseline_holdout) <= mape(actual, model_holdout):
        return "seasonal-naive baseline", np.asarray(baseline_future, dtype=float)
    return "model", np.asarray(model_future, dtype=float)


def main():
    import matplotlib.pyplot as plt
    import pandas as pd
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    monthly = read_sql("SELECT month, revenue FROM mart.kpi_monthly ORDER BY month")
    if len(monthly) < 15 or (monthly.revenue <= 0).any():
        raise ValueError("Need at least 15 consecutive positive-revenue months for a 3-month holdout")
    month = pd.to_datetime(monthly.month)
    if not (month.diff().dropna().dt.days.between(28, 31)).all():
        raise ValueError("Analysis months are not consecutive")
    series = monthly.revenue.to_numpy(dtype=float)
    train, actual = series[:-3], series[-3:]
    baseline = seasonal_naive(train, 3)
    seasonal = len(train) >= 24
    model = ExponentialSmoothing(train, trend="add", seasonal="add" if seasonal else None,
                                 seasonal_periods=12 if seasonal else None).fit(optimized=True)
    fitted = np.maximum(0, np.asarray(model.forecast(3)))
    baseline_error, model_error = mape(actual, baseline), mape(actual, fitted)
    final = ExponentialSmoothing(series, trend="add", seasonal="add" if len(series) >= 24 else None,
                                 seasonal_periods=12 if len(series) >= 24 else None).fit(optimized=True)
    winner, next_values = select_forecast(actual, baseline, fitted, seasonal_naive(series, 3),
                                          np.maximum(0, np.asarray(final.forecast(3))))
    residuals = series[12:] - series[:-12] if winner == "seasonal-naive baseline" else series - np.asarray(final.fittedvalues)
    residual_sigma = float(np.std(residuals, ddof=1))
    future_month = pd.date_range(month.iloc[-1] + pd.offsets.MonthBegin(1), periods=3, freq="MS")
    plt.plot(month, series, label="Actual")
    plt.plot(month.iloc[-3:], baseline, label="Seasonal-naive holdout")
    plt.plot(month.iloc[-3:], fitted, label="Model holdout")
    plt.plot(future_month, next_values, label=f"{winner} forecast")
    plt.fill_between(future_month, np.maximum(0, next_values - 1.96 * residual_sigma),
                     next_values + 1.96 * residual_sigma, alpha=.2, label="Approx. residual band")
    plt.legend()
    plt.ylabel("BRL")
    plt.title("Revenue forecast with 3-month holdout")
    save_figure("revenue_forecast.png")
    method = "seasonal Holt–Winters" if seasonal else "Holt trend (insufficient training history for two seasonal cycles)"
    write_findings("Revenue forecast", (
        f"Held out the last three complete analysis months. Seasonal-naive MAPE: {baseline_error:.1f}%; "
        f"{method} MAPE: {model_error:.1f}%. Lower-error choice: {winner}. "
        f"Next three {winner} forecasts: {', '.join(f'BRL {v:,.0f}' for v in next_values)}. "
        "The shaded band is ±1.96 training residual standard deviations, an approximation rather than a calibrated prediction interval. "
        "Evidence: `mart.kpi_monthly` and `reports/figures/revenue_forecast.png`. "
        "Recommendation: use the lower-error method for planning and refresh with recent data."
    ))
    print(f"Seasonal-naive MAPE {baseline_error:.1f}%; {method} MAPE {model_error:.1f}%")


if __name__ == "__main__":
    main()
