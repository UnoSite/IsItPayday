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


def _build_homeassistant_mock():
    """Build a minimal fake `homeassistant` package tree.

    Only provides the names imported by `__init__.py` and `config_flow.py`
    at module scope, so those files can be imported (and their small pure
    helper functions tested) without depending on the real, heavy
    `homeassistant` package.
    """
    ha = types.ModuleType("homeassistant")

    core = types.ModuleType("homeassistant.core")

    class HomeAssistant:
        pass

    def callback(func):
        return func

    core.HomeAssistant = HomeAssistant
    core.callback = callback

    config_entries = types.ModuleType("homeassistant.config_entries")

    class ConfigEntry:
        pass

    class ConfigFlow:
        def __init_subclass__(cls, domain=None, **kwargs):
            super().__init_subclass__(**kwargs)

    class OptionsFlow:
        pass

    config_entries.ConfigEntry = ConfigEntry
    config_entries.ConfigFlow = ConfigFlow
    config_entries.OptionsFlow = OptionsFlow

    data_entry_flow = types.ModuleType("homeassistant.data_entry_flow")

    class FlowResult(dict):
        pass

    data_entry_flow.FlowResult = FlowResult

    helpers = types.ModuleType("homeassistant.helpers")

    issue_registry = types.ModuleType("homeassistant.helpers.issue_registry")

    class IssueSeverity:
        ERROR = "error"
        WARNING = "warning"

    def async_create_issue(*args, **kwargs):
        pass

    def async_delete_issue(*args, **kwargs):
        pass

    issue_registry.IssueSeverity = IssueSeverity
    issue_registry.async_create_issue = async_create_issue
    issue_registry.async_delete_issue = async_delete_issue

    event = types.ModuleType("homeassistant.helpers.event")

    def async_track_point_in_time(*args, **kwargs):
        return lambda: None

    event.async_track_point_in_time = async_track_point_in_time

    typing_mod = types.ModuleType("homeassistant.helpers.typing")
    typing_mod.ConfigType = dict

    update_coordinator = types.ModuleType("homeassistant.helpers.update_coordinator")

    class DataUpdateCoordinator:
        def __init__(self, *args, **kwargs):
            self.data = None

    class UpdateFailed(Exception):
        pass

    class CoordinatorEntity:
        def __init__(self, coordinator):
            self.coordinator = coordinator

    update_coordinator.DataUpdateCoordinator = DataUpdateCoordinator
    update_coordinator.UpdateFailed = UpdateFailed
    update_coordinator.CoordinatorEntity = CoordinatorEntity

    selector = types.ModuleType("homeassistant.helpers.selector")

    class DateSelector:
        def __init__(self, *args, **kwargs):
            pass

    class TimeSelector:
        def __init__(self, *args, **kwargs):
            pass

    selector.DateSelector = DateSelector
    selector.TimeSelector = TimeSelector

    util = types.ModuleType("homeassistant.util")

    def slugify(value):
        return "_".join(str(value).strip().lower().split())

    util.slugify = slugify

    dt_util = types.ModuleType("homeassistant.util.dt")
    dt_util.DEFAULT_TIME_ZONE = None
    dt_util.now = lambda: None
    dt_util.utcnow = lambda: None
    dt_util.as_utc = lambda value: value

    # Wire up parent -> child attributes too, so `from homeassistant import
    # config_entries` style imports work even without going through the
    # real import machinery.
    ha.core = core
    ha.config_entries = config_entries
    ha.data_entry_flow = data_entry_flow
    ha.helpers = helpers
    ha.util = util
    helpers.issue_registry = issue_registry
    helpers.event = event
    helpers.typing = typing_mod
    helpers.update_coordinator = update_coordinator
    helpers.selector = selector
    util.dt = dt_util

    return {
        "homeassistant": ha,
        "homeassistant.core": core,
        "homeassistant.config_entries": config_entries,
        "homeassistant.data_entry_flow": data_entry_flow,
        "homeassistant.helpers": helpers,
        "homeassistant.helpers.issue_registry": issue_registry,
        "homeassistant.helpers.event": event,
        "homeassistant.helpers.typing": typing_mod,
        "homeassistant.helpers.update_coordinator": update_coordinator,
        "homeassistant.helpers.selector": selector,
        "homeassistant.util": util,
        "homeassistant.util.dt": dt_util,
    }


@pytest.fixture
def mock_homeassistant(monkeypatch):
    """Install the fake `homeassistant` package tree for a single test."""
    for name, module in _build_homeassistant_mock().items():
        monkeypatch.setitem(sys.modules, name, module)


def _base_dir():
    import os

    return os.path.join(
        os.path.dirname(__file__), "..", "custom_components", "isitpayday"
    )


def _load_isitpayday_prereqs(monkeypatch):
    """Register the const and payday_calculator submodules in sys.modules.

    Shared setup needed before `__init__.py` or `config_flow.py` can be
    imported standalone, since both use relative imports (`.const`,
    `.payday_calculator`) that are resolved via sys.modules.
    """
    import importlib.util
    import os

    base = _base_dir()

    pkg = types.ModuleType("custom_components")
    monkeypatch.setitem(sys.modules, "custom_components", pkg)
    placeholder = types.ModuleType("custom_components.isitpayday")
    placeholder.__path__ = [base]
    monkeypatch.setitem(sys.modules, "custom_components.isitpayday", placeholder)

    spec_const = importlib.util.spec_from_file_location(
        "custom_components.isitpayday.const", os.path.join(base, "const.py")
    )
    const = importlib.util.module_from_spec(spec_const)
    spec_const.loader.exec_module(const)
    monkeypatch.setitem(sys.modules, "custom_components.isitpayday.const", const)

    spec_calc = importlib.util.spec_from_file_location(
        "custom_components.isitpayday.payday_calculator",
        os.path.join(base, "payday_calculator.py"),
    )
    calc_module = importlib.util.module_from_spec(spec_calc)
    spec_calc.loader.exec_module(calc_module)
    monkeypatch.setitem(
        sys.modules, "custom_components.isitpayday.payday_calculator", calc_module
    )

    return base


@pytest.fixture
def init_module(mock_holidays, mock_homeassistant, monkeypatch):
    """Import `custom_components/isitpayday/__init__.py` fresh and isolated."""
    import importlib.util
    import os

    base = _load_isitpayday_prereqs(monkeypatch)

    spec_init = importlib.util.spec_from_file_location(
        "custom_components.isitpayday",
        os.path.join(base, "__init__.py"),
        submodule_search_locations=[base],
    )
    module = importlib.util.module_from_spec(spec_init)
    monkeypatch.setitem(sys.modules, "custom_components.isitpayday", module)
    spec_init.loader.exec_module(module)
    return module


@pytest.fixture
def config_flow_module(mock_holidays, mock_homeassistant, monkeypatch):
    """Import `custom_components/isitpayday/config_flow.py` fresh and isolated."""
    import importlib.util
    import os

    base = _load_isitpayday_prereqs(monkeypatch)

    spec = importlib.util.spec_from_file_location(
        "custom_components.isitpayday.config_flow",
        os.path.join(base, "config_flow.py"),
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
