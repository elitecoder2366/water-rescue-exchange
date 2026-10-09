"""Seven-day water availability forecasting with manual inputs and Open-Meteo rainfall."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd
import requests


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_rainfall_forecast(
    latitude: float,
    longitude: float,
    *,
    timeout: int = 12,
) -> pd.DataFrame:
    """Fetch daily precipitation forecasts from Open-Meteo (no API key required)."""
    if not -90 <= float(latitude) <= 90:
        raise ValueError("Latitude must be between -90 and 90.")
    if not -180 <= float(longitude) <= 180:
        raise ValueError("Longitude must be between -180 and 180.")

    response = requests.get(
        OPEN_METEO_URL,
        params={
            "latitude": float(latitude),
            "longitude": float(longitude),
            "daily": "precipitation_sum",
            "forecast_days": 7,
            "timezone": "auto",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    daily = payload.get("daily", {})
    dates = daily.get("time", [])
    rain = daily.get("precipitation_sum", [])
    if not dates or len(dates) != len(rain):
        raise ValueError("Weather service returned incomplete daily rainfall data.")
    return pd.DataFrame({
        "Date": pd.to_datetime(dates),
        "Forecast rainfall (mm)": [max(0.0, float(x or 0.0)) for x in rain],
    })


def build_seven_day_forecast(
    *,
    current_storage_l: float,
    storage_capacity_l: float,
    daily_base_inflow_l: float,
    daily_demand_l: float,
    rainfall_mm: list[float],
    rainfall_capture_l_per_mm: float = 0.0,
    start_date: date | None = None,
) -> pd.DataFrame:
    """Simple transparent water-balance forecast; all storage quantities are litres."""
    values = {
        "current storage": current_storage_l,
        "storage capacity": storage_capacity_l,
        "daily inflow": daily_base_inflow_l,
        "daily demand": daily_demand_l,
        "rainfall capture factor": rainfall_capture_l_per_mm,
    }
    for label, value in values.items():
        if float(value) < 0:
            raise ValueError(f"{label.capitalize()} cannot be negative.")
    if storage_capacity_l <= 0:
        raise ValueError("Storage capacity must be greater than zero.")
    if current_storage_l > storage_capacity_l:
        raise ValueError("Current storage cannot exceed storage capacity.")
    if len(rainfall_mm) != 7:
        raise ValueError("Exactly seven daily rainfall values are required.")
    if any(float(x) < 0 for x in rainfall_mm):
        raise ValueError("Rainfall values cannot be negative.")

    day = start_date or date.today()
    storage = float(current_storage_l)
    rows: list[dict[str, Any]] = []
    for i, rainfall in enumerate(rainfall_mm):
        rainfall_inflow = float(rainfall) * float(rainfall_capture_l_per_mm)
        total_inflow = float(daily_base_inflow_l) + rainfall_inflow
        raw_storage = storage + total_inflow - float(daily_demand_l)
        overflow = max(0.0, raw_storage - float(storage_capacity_l))
        storage = min(float(storage_capacity_l), max(0.0, raw_storage))
        shortage = max(0.0, -raw_storage)
        rows.append({
            "Date": day + timedelta(days=i + 1),
            "Forecast rainfall (mm)": round(float(rainfall), 2),
            "Estimated inflow (L)": round(total_inflow, 2),
            "Expected demand (L)": round(float(daily_demand_l), 2),
            "Forecast storage (L)": round(storage, 2),
            "Storage available (%)": round(storage / float(storage_capacity_l) * 100, 1),
            "Potential overflow (L)": round(overflow, 2),
            "Estimated unmet demand (L)": round(shortage, 2),
        })
    return pd.DataFrame(rows)
