"""Unit tests for the pure helper functions in `__init__.py`."""

from datetime import time

import pytest


# --------------------------------------------------------------------------- #
# _normalize_pay_day                                                          #
# --------------------------------------------------------------------------- #


def test_normalize_pay_day_converts_digit_string(init_module):
    assert init_module._normalize_pay_day("31") == 31


def test_normalize_pay_day_passes_through_string_option(init_module):
    assert init_module._normalize_pay_day("last_bank_day") == "last_bank_day"


def test_normalize_pay_day_passes_through_int(init_module):
    assert init_module._normalize_pay_day(15) == 15


def test_normalize_pay_day_passes_through_none(init_module):
    assert init_module._normalize_pay_day(None) is None


# --------------------------------------------------------------------------- #
# _normalize_int                                                              #
# --------------------------------------------------------------------------- #


def test_normalize_int_converts_string(init_module):
    assert init_module._normalize_int("2", 0) == 2


def test_normalize_int_passes_through_int(init_module):
    assert init_module._normalize_int(5, 0) == 5


@pytest.mark.parametrize("value", ["abc", None, ""])
def test_normalize_int_falls_back_to_default_for_invalid(init_module, value):
    assert init_module._normalize_int(value, 7) == 7


# --------------------------------------------------------------------------- #
# _parse_event_time                                                           #
# --------------------------------------------------------------------------- #


def test_parse_event_time_full_hh_mm_ss(init_module):
    assert init_module._parse_event_time("14:30:15") == time(14, 30, 15)


def test_parse_event_time_hh_mm_defaults_seconds_to_zero(init_module):
    assert init_module._parse_event_time("08:05") == time(8, 5, 0)


def test_parse_event_time_missing_falls_back_to_default(init_module):
    assert init_module._parse_event_time(None) == time(6, 0, 0)
    assert init_module._parse_event_time("") == time(6, 0, 0)


def test_parse_event_time_invalid_falls_back_to_default(init_module):
    assert init_module._parse_event_time("not-a-time") == time(6, 0, 0)
