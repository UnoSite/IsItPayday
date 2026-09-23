"""Unit tests for the pure helper functions and flow structure in
`config_flow.py`.
"""

import pytest


# --------------------------------------------------------------------------- #
# _coerce_int                                                                 #
# --------------------------------------------------------------------------- #


def test_coerce_int_converts_string(config_flow_module):
    assert config_flow_module._coerce_int("31", 0) == 31


def test_coerce_int_passes_through_int(config_flow_module):
    assert config_flow_module._coerce_int(5, 0) == 5


@pytest.mark.parametrize("value", ["abc", None, ""])
def test_coerce_int_falls_back_to_default_for_invalid(config_flow_module, value):
    assert config_flow_module._coerce_int(value, 9) == 9


# --------------------------------------------------------------------------- #
# Config flow sets a unique_id from the instance name to prevent duplicates   #
# --------------------------------------------------------------------------- #


def test_config_flow_sets_unique_id_from_name(config_flow_module):
    import inspect

    source = inspect.getsource(config_flow_module.IsItPaydayConfigFlow.async_step_user)
    assert "async_set_unique_id" in source
    assert "_abort_if_unique_id_configured" in source
