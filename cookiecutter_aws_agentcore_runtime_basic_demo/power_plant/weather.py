# -*- coding: utf-8 -*-

"""
A fake weather forecast, used as the agent's own (non-MCP) tool.

The result is deterministic for a location, so tests and demos are repeatable,
and it needs no network. Strands sends the returned model to the LLM as JSON.
"""

from __future__ import annotations

from .schemas import WeatherForecast

#: Possible conditions, picked by the location.
CONDITIONS: list[str] = ["sunny", "cloudy", "rain", "thunderstorm"]

#: Above this wind speed (m/s), climbing a turbine or a roof is not allowed.
MAX_SAFE_WIND_SPEED_MS: int = 12


def get_weather(lat: float, lon: float) -> WeatherForecast:
    """
    Get tomorrow's fake weather forecast for a location.

    ``safe_for_inspection`` is ``False`` on a thunderstorm or when the wind is
    above :data:`MAX_SAFE_WIND_SPEED_MS`.
    """
    # coordinates rounded to 0.1 degree, mixed so nearby sites differ
    seed = round(abs(lat) * 10) * 11 + round(abs(lon) * 10) * 5
    condition = CONDITIONS[seed % len(CONDITIONS)]
    wind_speed_ms = seed % 20
    temperature_c = 5 + seed % 30
    safe = condition != "thunderstorm" and wind_speed_ms <= MAX_SAFE_WIND_SPEED_MS
    return WeatherForecast(
        lat=lat,
        lon=lon,
        condition=condition,
        wind_speed_ms=wind_speed_ms,
        temperature_c=temperature_c,
        safe_for_inspection=safe,
    )
