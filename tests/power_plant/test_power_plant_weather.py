# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.weather import (
    get_weather,
)


def test_get_weather_is_deterministic():
    assert get_weather(35.05, -117.6) == get_weather(35.05, -117.6)


def test_get_weather_safe():
    weather = get_weather(33.8, -115.4)  # site S-02
    assert weather["condition"] == "sunny"
    assert weather["safe_for_inspection"] is True


def test_get_weather_too_windy():
    """Site S-03 is the demo's unsafe case: sunny but too windy."""
    weather = get_weather(41.1, -105.9)
    assert weather["wind_speed_ms"] == 16
    assert weather["safe_for_inspection"] is False


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.weather",
        preview=False,
    )
