# -*- coding: utf-8 -*-

"""
The seed data of the power plant database: 4 tables as lists of dicts, loaded by
:func:`~cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.orm.load_seed_data`.

- ``SITES`` 1:N ``ASSETS`` (by ``site_id``).
- ``SITES`` N:M ``TECHNICIANS`` (through ``SITE_TECHNICIANS``).

This subpackage is copied into the AgentCore runtimes, so it imports only the
standard library and packages of the ``agentcore`` dependency group (SQLAlchemy),
never config, ``one``, or cdk: callers pass it an engine.
"""

# fmt: off
#: Power plant sites. ``kind`` is ``solar`` or ``wind``.
SITES: list[dict] = [
    {"id": "S-01", "name": "Sunrise Valley", "kind": "solar", "lat": 35.05, "lon": -117.60, "capacity_mw": 120},
    {"id": "S-02", "name": "Desert Mirror", "kind": "solar", "lat": 33.80, "lon": -115.40, "capacity_mw": 250},
    {"id": "S-03", "name": "Ridge Wind", "kind": "wind", "lat": 41.10, "lon": -105.90, "capacity_mw": 300},
    {"id": "S-04", "name": "Coastal Breeze", "kind": "wind", "lat": 27.80, "lon": -97.40, "capacity_mw": 180},
    {"id": "S-05", "name": "Prairie Sun", "kind": "solar", "lat": 38.50, "lon": -98.30, "capacity_mw": 90},
]

#: Equipment at a site. Each asset belongs to exactly one site.
ASSETS: list[dict] = [
    {"id": "A-01", "site_id": "S-01", "kind": "inverter", "model": "SunPower X-500"},
    {"id": "A-02", "site_id": "S-01", "kind": "inverter", "model": "SunPower X-500"},
    {"id": "A-03", "site_id": "S-01", "kind": "transformer", "model": "GridMax T-20"},
    {"id": "A-04", "site_id": "S-02", "kind": "inverter", "model": "SolarEdge Pro 1000"},
    {"id": "A-05", "site_id": "S-02", "kind": "transformer", "model": "GridMax T-40"},
    {"id": "A-06", "site_id": "S-03", "kind": "turbine", "model": "Vestas V150"},
    {"id": "A-07", "site_id": "S-03", "kind": "turbine", "model": "Vestas V150"},
    {"id": "A-08", "site_id": "S-03", "kind": "turbine", "model": "Vestas V150"},
    {"id": "A-09", "site_id": "S-04", "kind": "turbine", "model": "GE Cypress 6.1"},
    {"id": "A-10", "site_id": "S-04", "kind": "turbine", "model": "GE Cypress 6.1"},
    {"id": "A-11", "site_id": "S-05", "kind": "inverter", "model": "SMA Sunny Central"},
    {"id": "A-12", "site_id": "S-05", "kind": "transformer", "model": "GridMax T-20"},
]

#: Field technicians who inspect sites.
TECHNICIANS: list[dict] = [
    {"id": "T-01", "name": "Alice Chen", "skill": "solar"},
    {"id": "T-02", "name": "Bob Martinez", "skill": "wind"},
    {"id": "T-03", "name": "Carol Singh", "skill": "electrical"},
    {"id": "T-04", "name": "Dan Okafor", "skill": "wind"},
]

#: Which technician is assigned to which site (many-to-many link table).
SITE_TECHNICIANS: list[dict] = [
    {"site_id": "S-01", "technician_id": "T-01"},
    {"site_id": "S-01", "technician_id": "T-03"},
    {"site_id": "S-02", "technician_id": "T-01"},
    {"site_id": "S-03", "technician_id": "T-02"},
    {"site_id": "S-03", "technician_id": "T-04"},
    {"site_id": "S-04", "technician_id": "T-04"},
    {"site_id": "S-04", "technician_id": "T-03"},
    {"site_id": "S-05", "technician_id": "T-01"},
]
# fmt: on
