from datetime import date

import pytest

from src.water_prediction import build_seven_day_forecast


def test_forecast_returns_seven_days_and_respects_capacity():
    df = build_seven_day_forecast(
        current_storage_l=800,
        storage_capacity_l=1000,
        daily_base_inflow_l=100,
        daily_demand_l=150,
        rainfall_mm=[0, 10, 0, 5, 0, 0, 2],
        rainfall_capture_l_per_mm=2,
        start_date=date(2026, 1, 1),
    )
    assert len(df) == 7
    assert df.iloc[0]["Forecast storage (L)"] == 750
    assert df["Forecast storage (L)"].between(0, 1000).all()


def test_invalid_rainfall_length_is_rejected():
    with pytest.raises(ValueError, match="seven"):
        build_seven_day_forecast(
            current_storage_l=100,
            storage_capacity_l=200,
            daily_base_inflow_l=10,
            daily_demand_l=10,
            rainfall_mm=[0, 0],
        )


def test_storage_above_capacity_is_rejected():
    with pytest.raises(ValueError, match="cannot exceed"):
        build_seven_day_forecast(
            current_storage_l=201,
            storage_capacity_l=200,
            daily_base_inflow_l=10,
            daily_demand_l=10,
            rainfall_mm=[0] * 7,
        )
