"""Payday calculation logic for the IsItPayday integration.

All functions in this module are synchronous. Holiday data is generated
locally by the `holidays` package, so no network access is required.
Callers inside Home Assistant must run these functions in an executor,
e.g. via `hass.async_add_executor_job`.
"""

import logging
import re
from datetime import date, timedelta

import holidays as holidays_lib
from holidays.constants import BANK, OPTIONAL, PUBLIC

from .const import (
    PAY_FREQ_MONTHLY,
    PAY_FREQ_28_DAYS,
    PAY_FREQ_14_DAYS,
    PAY_FREQ_BIMONTHLY,
    PAY_FREQ_QUARTERLY,
    PAY_FREQ_SEMIANNUAL,
    PAY_FREQ_ANNUAL,
    PAY_FREQ_WEEKLY,
    PAY_DAY_LAST_BANK_DAY,
    PAY_DAY_FIRST_BANK_DAY,
)

_LOGGER = logging.getLogger(__name__)

# Safety limit for month-based search loops.
_MAX_MONTH_ITERATIONS = 24


def get_supported_countries() -> dict[str, str]:
    """Return supported countries as {ISO code: display name}, sorted by name."""
    countries: dict[str, str] = {}
    try:
        from holidays.registry import COUNTRIES

        for entry in COUNTRIES.values():
            class_name, alpha2 = entry[0], entry[1]
            # Convert CamelCase class names to readable names,
            # e.g. "UnitedStates" -> "United States".
            display_name = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", class_name)
            countries[alpha2] = display_name
    except Exception:  # pragma: no cover - fallback for registry changes
        _LOGGER.warning(
            "Could not read country names from holidays registry; "
            "falling back to country codes."
        )
        for code in holidays_lib.list_supported_countries():
            countries[code] = code

    return dict(sorted(countries.items(), key=lambda item: item[1]))


# Some countries place their de facto bank closing days in categories other
# than BANK. For Denmark, Constitution Day, Christmas Eve and New Year's Eve
# are in the OPTIONAL category, but banks are closed on those days.
_EXTRA_CATEGORIES_PER_COUNTRY: dict[str, tuple] = {
    "DK": (OPTIONAL,),
}


def get_bank_holidays(country: str, years: list[int]):
    """Return a holidays object covering all bank closing days for a country.

    Includes the PUBLIC category, the BANK category where the country
    supports it, and any country-specific extra categories that represent
    de facto bank closing days. Only categories actually supported by the
    country are requested, so no errors are raised for unsupported ones.

    The returned object supports `date in obj` membership checks and lazily
    populates additional years on demand, so lookups outside the given
    years also work correctly.
    """
    try:
        probe = holidays_lib.country_holidays(country)
        supported = getattr(probe, "supported_categories", (PUBLIC,))

        categories = [PUBLIC]
        if BANK in supported:
            categories.append(BANK)
        for extra in _EXTRA_CATEGORIES_PER_COUNTRY.get(country, ()):
            if extra in supported and extra not in categories:
                categories.append(extra)

        _LOGGER.debug(
            "Using holiday categories %s for country %s", categories, country
        )
        return holidays_lib.country_holidays(
            country, years=years, categories=tuple(categories)
        )
    except NotImplementedError:
        _LOGGER.error(
            "Country '%s' is not supported by the holidays package.", country
        )
        return {}
    except Exception as e:
        _LOGGER.exception("Error generating holidays for %s: %s", country, e)
        return {}


def _is_bank_day(d: date, bank_holidays) -> bool:
    """Return True if the date is a working bank day (not weekend, not holiday)."""
    return d.weekday() < 5 and d not in bank_holidays


def _adjust_to_previous_bank_day(d: date, bank_holidays) -> date:
    """Move date backwards until it lands on a valid bank day."""
    while not _is_bank_day(d, bank_holidays):
        d -= timedelta(days=1)
    return d


def _adjust_to_next_bank_day(d: date, bank_holidays) -> date:
    """Move date forwards until it lands on a valid bank day."""
    while not _is_bank_day(d, bank_holidays):
        d += timedelta(days=1)
    return d


def _adjust_not_before_today(payday: date, today: date, bank_holidays) -> date:
    """Adjust payday to the previous bank day, but never earlier than today.

    If adjusting backwards would land before today, adjust forwards instead.
    """
    adjusted = _adjust_to_previous_bank_day(payday, bank_holidays)
    if adjusted < today:
        adjusted = _adjust_to_next_bank_day(payday, bank_holidays)
    return adjusted


def _add_months(d: date, months: int) -> date:
    """Add a number of months to a date, clamping the day to the month length."""
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = d.day
    while day > 28:
        try:
            return date(year, month, day)
        except ValueError:
            day -= 1
    return date(year, month, day)


def calculate_next_payday(
    country: str,
    pay_frequency: str,
    pay_day=None,
    last_pay_date=None,
    weekday=None,
    bank_offset: int = 0,
):
    """Calculate the next payday date, adjusted for weekends and public holidays."""
    _LOGGER.info(
        "Starting calculation of the next payday for %s with frequency: %s",
        country,
        pay_frequency,
    )

    today = date.today()
    bank_holidays = get_bank_holidays(country, [today.year, today.year + 1])

    if pay_frequency == PAY_FREQ_MONTHLY:
        payday = calculate_month_based(
            today, 1, pay_day, bank_offset, bank_holidays
        )

    elif pay_frequency == PAY_FREQ_BIMONTHLY:
        payday = calculate_month_interval(
            last_pay_date, 2, today, bank_holidays
        )

    elif pay_frequency in (
        PAY_FREQ_28_DAYS,
        PAY_FREQ_14_DAYS,
        PAY_FREQ_QUARTERLY,
        PAY_FREQ_SEMIANNUAL,
        PAY_FREQ_ANNUAL,
    ):
        interval_days = {
            PAY_FREQ_14_DAYS: 14,
            PAY_FREQ_28_DAYS: 28,
            PAY_FREQ_QUARTERLY: 91,
            PAY_FREQ_SEMIANNUAL: 182,
            PAY_FREQ_ANNUAL: 365,
        }[pay_frequency]
        payday = calculate_recurring(last_pay_date, interval_days)
        if payday is not None:
            payday = _adjust_not_before_today(payday, today, bank_holidays)

    elif pay_frequency == PAY_FREQ_WEEKLY:
        if weekday is None:
            raise ValueError("Weekday missing for weekly payday.")
        payday = calculate_weekly(today, weekday)
        if payday is not None:
            payday = _adjust_to_next_bank_day(payday, bank_holidays)

    else:
        _LOGGER.error("Invalid payday frequency: %s", pay_frequency)
        return None

    _LOGGER.info("Next payday calculated: %s", payday)
    return payday


def calculate_month_based(
    today: date,
    month_interval: int,
    pay_day,
    bank_offset: int,
    bank_holidays,
):
    """Calculate next payday for monthly frequency (pay_day based).

    Already returns a fully adjusted (bank day) date.
    """
    year, month = today.year, today.month

    for _ in range(_MAX_MONTH_ITERATIONS):
        if pay_day == PAY_DAY_LAST_BANK_DAY:
            payday = _find_last_bank_day(year, month, bank_holidays, bank_offset)
        elif pay_day == PAY_DAY_FIRST_BANK_DAY:
            payday = _find_first_bank_day(year, month, bank_holidays)
        elif isinstance(pay_day, int):
            payday = _find_specific_day(year, month, pay_day, bank_holidays)
        else:
            _LOGGER.error("Invalid payday value: %s", pay_day)
            return None

        if payday is not None and payday >= today:
            return payday

        month += month_interval
        year += (month - 1) // 12
        month = (month - 1) % 12 + 1

    _LOGGER.error(
        "Could not find a valid payday within %s months.", _MAX_MONTH_ITERATIONS
    )
    return None


def calculate_month_interval(
    last_pay_date: str,
    month_interval: int,
    today: date,
    bank_holidays,
) -> date | None:
    """Calculate next payday for month-interval frequencies anchored to a date.

    Used for bimonthly (every 2 months). Adds whole months to the last
    payday date until the result is today or later, then adjusts to a
    valid bank day (never before today).
    """
    if not last_pay_date:
        _LOGGER.error("Missing last payday date for month-interval payout.")
        return None

    anchor = date.fromisoformat(last_pay_date)
    payday = _add_months(anchor, month_interval)

    for _ in range(_MAX_MONTH_ITERATIONS):
        if payday >= today:
            return _adjust_not_before_today(payday, today, bank_holidays)
        payday = _add_months(payday, month_interval)

    _LOGGER.error(
        "Could not find a valid payday within %s months.", _MAX_MONTH_ITERATIONS
    )
    return None


def calculate_recurring(last_pay_date: str, interval: int) -> date | None:
    """Calculate next payday for fixed-interval frequencies.

    Returns an unadjusted date. The caller is responsible for adjusting.
    """
    if not last_pay_date:
        _LOGGER.error("Missing last payday date for recurring payout.")
        return None

    last_date = date.fromisoformat(last_pay_date)
    payday = last_date + timedelta(days=interval)

    today = date.today()
    while payday < today:
        payday += timedelta(days=interval)

    _LOGGER.info("Next recurring payday (before adjustment): %s", payday)
    return payday


def calculate_weekly(today: date, weekday: int) -> date:
    """Return the next occurrence of the given weekday (unadjusted)."""
    days_ahead = (weekday - today.weekday()) % 7
    return today + timedelta(days=days_ahead)


def _find_last_bank_day(
    year: int, month: int, bank_holidays, bank_offset: int
) -> date | None:
    """Find the last bank day of the month, then apply bank_offset.

    After applying bank_offset, the result is re-validated as a bank day.
    """
    day = 31
    while day > 0:
        try:
            candidate = date(year, month, day)
            if _is_bank_day(candidate, bank_holidays):
                result = candidate - timedelta(days=bank_offset)
                return _adjust_to_previous_bank_day(result, bank_holidays)
            day -= 1
        except ValueError:
            day -= 1
    return None


def _find_first_bank_day(year: int, month: int, bank_holidays) -> date | None:
    """Find the first bank day of the month."""
    day = 1
    while day <= 31:
        try:
            candidate = date(year, month, day)
            if _is_bank_day(candidate, bank_holidays):
                return candidate
            day += 1
        except ValueError:
            break
    return None


def _find_specific_day(
    year: int, month: int, day: int, bank_holidays
) -> date | None:
    """Find a specific day of the month, adjusting backwards if not a bank day."""
    while day > 0:
        try:
            candidate = date(year, month, day)
            if _is_bank_day(candidate, bank_holidays):
                return candidate
            day -= 1
        except ValueError:
            day -= 1
    return None
