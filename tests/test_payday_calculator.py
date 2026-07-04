"""Unit tests for the payday calculation logic."""

from datetime import date

import pytest

TODAY = date(2026, 6, 15)  # Monday, matches conftest FIXED_TODAY


# --------------------------------------------------------------------------- #
# Supported countries / subdivisions                                          #
# --------------------------------------------------------------------------- #


def test_supported_countries_readable_names(calc):
    countries = calc.get_supported_countries()
    assert countries["DK"] == "Denmark"
    assert countries["US"] == "United States"


def test_supported_countries_sorted_by_name(calc):
    names = list(calc.get_supported_countries().values())
    assert names == sorted(names)


def test_subdivisions_with_alias(calc):
    subs = calc.get_country_subdivisions("DE")
    assert subs["BY"] == "Bavaria (BY)"
    assert subs["BE"] == "Berlin (BE)"


def test_subdivisions_empty_for_country_without_regions(calc):
    assert calc.get_country_subdivisions("DK") == {}


# --------------------------------------------------------------------------- #
# Bank holidays / categories                                                  #
# --------------------------------------------------------------------------- #


def test_denmark_includes_optional_bank_closing_days(calc):
    holidays = calc.get_bank_holidays("DK", [2026])
    assert date(2026, 12, 24) in holidays  # Christmas Eve
    assert date(2026, 6, 5) in holidays  # Constitution Day


def test_unknown_country_returns_empty(calc):
    assert calc.get_bank_holidays("XX", [2026]) == {}


def test_regional_holiday_only_with_subdivision(calc):
    with_region = calc.get_bank_holidays("DE", [2026], "BY")
    without_region = calc.get_bank_holidays("DE", [2026], None)
    assert date(2026, 8, 15) in with_region
    assert date(2026, 8, 15) not in without_region


# --------------------------------------------------------------------------- #
# Upcoming paydays - monthly                                                   #
# --------------------------------------------------------------------------- #


def test_monthly_last_bank_day_returns_requested_count(calc):
    paydays = calc.calculate_upcoming_paydays(
        "DK", "monthly", "last_bank_day", count=12
    )
    assert len(paydays) == 12


def test_upcoming_paydays_sorted_unique_and_future(calc):
    paydays = calc.calculate_upcoming_paydays(
        "DK", "monthly", "last_bank_day", count=12
    )
    assert paydays == sorted(set(paydays))
    assert all(p >= TODAY for p in paydays)


def test_monthly_specific_day_adjusts_off_holiday(calc):
    # 25 Dec is a holiday and 24 Dec is an OPTIONAL bank closing day in DK,
    # so a "25th" payday in December lands on the 23rd.
    holidays = calc.get_bank_holidays("DK", [2026])
    assert calc._payday_for_month(2026, 12, 25, 0, holidays) == date(2026, 12, 23)


def test_monthly_string_pay_day_is_normalized(calc):
    paydays = calc.calculate_upcoming_paydays("DK", "monthly", "31", count=3)
    assert len(paydays) == 3


def test_monthly_string_bank_offset_is_normalized(calc):
    paydays = calc.calculate_upcoming_paydays(
        "DK", "monthly", "last_bank_day", bank_offset="2", count=3
    )
    assert len(paydays) == 3


def test_invalid_bank_offset_falls_back_to_zero(calc):
    paydays = calc.calculate_upcoming_paydays(
        "DK", "monthly", "last_bank_day", bank_offset="abc", count=2
    )
    assert len(paydays) == 2


def test_monthly_invalid_pay_day_returns_empty(calc):
    assert calc.calculate_upcoming_paydays("DK", "monthly", None, count=3) == []


# --------------------------------------------------------------------------- #
# Upcoming paydays - interval & bimonthly                                      #
# --------------------------------------------------------------------------- #


def test_14_day_interval_is_stable(calc):
    paydays = calc.calculate_upcoming_paydays(
        "DK", "14_days", None, "2026-06-12", count=6
    )
    diffs = [(paydays[i + 1] - paydays[i]).days for i in range(5)]
    assert all(10 <= d <= 18 for d in diffs)


def test_bimonthly_with_very_old_anchor(calc):
    # Anchor 10 years ago must still yield future paydays (no guard limit bug).
    paydays = calc.calculate_upcoming_paydays(
        "DK", "bimonthly", None, "2016-06-15", count=6
    )
    assert len(paydays) == 6
    assert all(p >= TODAY for p in paydays)


def test_bimonthly_requires_last_pay_date(calc):
    assert calc.calculate_upcoming_paydays("DK", "bimonthly", None, None, count=3) == []


def test_interval_requires_last_pay_date(calc):
    assert calc.calculate_upcoming_paydays("DK", "14_days", None, None, count=3) == []


@pytest.mark.parametrize("freq", ["28_days", "quarterly", "semiannual", "annual"])
def test_other_intervals_return_requested_count(calc, freq):
    paydays = calc.calculate_upcoming_paydays("DK", freq, None, "2026-06-12", count=4)
    assert len(paydays) == 4


# --------------------------------------------------------------------------- #
# Upcoming paydays - weekly                                                    #
# --------------------------------------------------------------------------- #


def test_weekly_returns_requested_count(calc):
    paydays = calc.calculate_upcoming_paydays("DK", "weekly", weekday=4, count=12)
    assert len(paydays) == 12


def test_weekly_without_weekday_raises(calc):
    with pytest.raises(ValueError):
        calc.calculate_upcoming_paydays("DK", "weekly", count=3)


# --------------------------------------------------------------------------- #
# Count bounds & invalid frequency                                            #
# --------------------------------------------------------------------------- #


def test_count_capped_at_24(calc):
    assert (
        len(calc.calculate_upcoming_paydays("DK", "weekly", weekday=0, count=99)) == 24
    )


def test_count_minimum_one(calc):
    assert len(calc.calculate_upcoming_paydays("DK", "weekly", weekday=0, count=0)) == 1


def test_invalid_frequency_returns_empty(calc):
    assert calc.calculate_upcoming_paydays("DK", "fortnightly", count=3) == []


# --------------------------------------------------------------------------- #
# next == first upcoming                                                       #
# --------------------------------------------------------------------------- #


def test_next_payday_equals_first_upcoming(calc):
    nxt = calc.calculate_next_payday("DK", "monthly", "last_bank_day")
    first = calc.calculate_upcoming_paydays("DK", "monthly", "last_bank_day", count=1)[
        0
    ]
    assert nxt == first


# --------------------------------------------------------------------------- #
# Last payday                                                                  #
# --------------------------------------------------------------------------- #


def test_last_payday_monthly_is_on_or_before_today(calc):
    last = calc.calculate_last_payday("DK", "monthly", "last_bank_day")
    assert last is not None and last <= TODAY


def test_last_payday_weekly(calc):
    # Today is Monday (weekday 0); last Friday payday should be 12 June 2026.
    last = calc.calculate_last_payday("DK", "weekly", weekday=4)
    assert last == date(2026, 6, 12)


def test_last_payday_interval_future_anchor_returns_none(calc):
    assert calc.calculate_last_payday("DK", "14_days", None, "2026-12-01") is None


def test_last_payday_bimonthly(calc):
    last = calc.calculate_last_payday("DK", "bimonthly", None, "2026-04-15")
    assert last is not None and last <= TODAY
