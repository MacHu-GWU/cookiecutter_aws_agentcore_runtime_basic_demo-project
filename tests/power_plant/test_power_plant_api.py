# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant import api


def test():
    _ = api
    _ = api.Base
    _ = api.Site
    _ = api.Asset
    _ = api.Technician
    _ = api.SiteTechnician
    _ = api.create_db_engine
    _ = api.load_seed_data
    _ = api.SiteInfo
    _ = api.AssetInfo
    _ = api.TechnicianInfo
    _ = api.SiteDetail
    _ = api.TechnicianDetail
    _ = api.WeatherForecast
    _ = api.list_sites
    _ = api.list_assets
    _ = api.get_site
    _ = api.get_technician
    _ = api.get_weather
    _ = api.SiteAgentRequest
    _ = api.SiteAgentResponse


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.api",
        preview=False,
    )
