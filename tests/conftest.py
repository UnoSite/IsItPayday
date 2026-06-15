"""Shared fixtures and a lightweight mock of the `holidays` package.

The real `holidays` package is mocked so the calculation logic can be
tested in isolation without installing it. A small set of Danish and
German holidays is provided to exercise weekend/holiday adjustment,
the OPTIONAL category and regional (subdivision) holidays.
"""

import sys
import types
from datetime import date

import pytest

# Fixed "today" so date-based tests are deterministic.
FIXED_TODAY = date(2026, 6, 15)  # a Monday


def _build_holidays_mock():
    mock = types.ModuleType("holidays")
    constants = types.ModuleType("holidays.constants")
    constants.PUBLIC = "public"
    constants.BANK = "bank"
    constants.OPTIONAL = "optional"

    class FakeHolidays(dict):
        supported_categories = ("public", "optional")
        subdivisions_aliases = {"Bavaria": "BY", "Berlin": "BE"}

    def country_holidays(country, subdiv=None, years=None, categories=None):
        if country == "XX":
            raise NotImplementedError
        h = FakeHolidays()
        years = years or []
        for y in years:
            h[date(y, 1, 1)] = "New Year"
            h[date(y, 12, 25)] = "Christmas Day"
            if categories and "optional" in categories and country == "DK":
                h[date(y, 12, 24)] = "Christmas Eve"
                h[date(y, 12, 31)] = "New Year's Eve"
                h[date(y, 6, 5)] = "Constitution Day"
            if country == "DE" and subdiv == "BY":
                h[date(y, 8, 15)] = "Assumption Day"
        return h

    def list_supported_countries():
        return {"DK": [], "DE": ["BY", "BE"], "US": ["CA", "NY"]}

    mock.country_holidays = country_holidays
    mock.list_supported_countries = list_supported_countries
    mock.constants = constants

    registry = types.ModuleType("holidays.registry")
    registry.COUNTRIES = {
        "denmark": ("Denmark", "DK", "DNK"),
        "germany": ("Germany", "DE", "DEU"),
        "unitedstates": ("UnitedStates", "US", "USA"),
    }
    mock.registry = registry
    return mock, constants, registry


@pytest.fixture(autouse=True)
def mock_holidays(monkeypatch):
    """Install the holidays mock for every test."""
    mock, constants, registry = _build_holidays_mock()
    monkeypatch.setitem(sys.modules, "holidays", mock)
    monkeypatch.setitem(sys.modules, "holidays.constants", constants)
    monkeypatch.setitem(sys.modules, "holidays.registry", registry)
    yield


@pytest.fixture
def calc(mock_holidays, monkeypatch):
    """Import the calculator module fresh, with `date.today` pinned."""
    import importlib.util
    import os

    base = os.path.join(
        os.path.dirname(__file__),
        "..",
        "custom_components",
        "isitpayday",
    )

    pkg = types.ModuleType("custom_components")
    sys.modules.setdefault("custom_components", pkg)
    sub = types.ModuleType("custom_components.isitpayday")
    sub.__path__ = [base]
    sys.modules["custom_components.isitpayday"] = sub

    spec_const = importlib.util.spec_from_file_location(
        "custom_components.isitpayday.const", os.path.join(base, "const.py")
    )
    const = importlib.util.module_from_spec(spec_const)
    spec_const.loader.exec_module(const)
    sys.modules["custom_components.isitpayday.const"] = const

    spec = importlib.util.spec_from_file_location(
        "custom_components.isitpayday.payday_calculator",
        os.path.join(base, "payday_calculator.py"),
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Pin today for deterministic results.
    class _FixedDate(date):
        @classmethod
        def today(cls):
            return FIXED_TODAY

    monkeypatch.setattr(module, "date", _FixedDate)
    return module
