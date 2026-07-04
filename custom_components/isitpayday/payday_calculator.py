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
    PAY_DAY_FIRST_BANK_DAY,
    PAY_DAY_LAST_BANK_DAY,
    PAY_FREQ_14_DAYS,
    PAY_FREQ_28_DAYS,
    PAY_FREQ_ANNUAL,
    PAY_FREQ_BIMONTHLY,
    PAY_FREQ_MONTHLY,
    PAY_FREQ_QUARTERLY,
    PAY_FREQ_SEMIANNUAL,
    PAY_FREQ_WEEKLY,
)

_LOGGER = logging.getLogger(__name__)


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


def get_country_subdivisions(country: str) -> dict[str, str]:
    """Return subdivisions (states/regions) for a country as {code: label}.

    Returns an empty dict if the country has no subdivisions. Friendly
    names are used where the holidays package provides aliases,
    e.g. "Bavaria (BY)" instead of just "BY".
    """
    try:
        supported = holidays_lib.list_supported_countries()
        subdivs = supported.get(country, [])
        if not subdivs:
            return {}

        code_to_alias: dict[str, str] = {}
        try:
            probe = holidays_lib.country_holidays(country)
            aliases = getattr(probe, "subdivisions_aliases", {}) or {}
            # aliases maps alias name -> subdivision code; invert it and
            # keep the first (usually most readable) alias per code.
            for alias, code in aliases.items():
                code_to_alias.setdefault(str(code), str(alias))
        except Exception:  # pragma: no cover - aliases are a nice-to-have
            code_to_alias = {}

        options: dict[str, str] = {}
        for code in subdivs:
            code = str(code)
            alias = code_to_alias.get(code)
            options[code] = f"{alias} ({code})" if alias else code
        return dict(sorted(options.items(), key=lambda item: item[1]))
    except Exception as e:
        _LOGGER.exception("Error listing subdivisions for %s: %s", country, e)
        return {}


# Some countries place their de facto bank closing days in categories other
# than BANK. For Denmark, Constitution Day, Christmas Eve and New Year's Eve
# are in the OPTIONAL category, but banks are closed on those days.
_EXTRA_CATEGORIES_PER_COUNTRY: dict[str, tuple] = {
    "DK": (OPTIONAL,),
}


def get_bank_holidays(country: str, years: list[int], subdiv: str | None = None):
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

        _LOGGER.debug("Using holiday categories %s for country %s", categories, country)
        return holidays_lib.country_holidays(
            country, subdiv=subdiv, years=years, categories=tuple(categories)
        )
    except NotImplementedError:
        _LOGGER.error("Country '%s' is not supported by the holidays package.", country)
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
    subdiv: str | None = None,
):
    """Calculate the next payday date (first of the upcoming paydays)."""
    paydays = calculate_upcoming_paydays(
        country,
        pay_frequency,
        pay_day,
        last_pay_date,
        weekday,
        bank_offset,
        subdiv,
        count=1,
    )
    return paydays[0] if paydays else None


def calculate_last_payday(
    country: str,
    pay_frequency: str,
    pay_day=None,
    last_pay_date=None,
    weekday=None,
    bank_offset: int = 0,
    subdiv: str | None = None,
) -> date | None:
    """Calculate the most recent payday on or before today.

    Returns None if no past payday can be determined (for example when an
    interval-based frequency has a last_pay_date in the future).
    """
    # Defensive normalization (mirrors calculate_upcoming_paydays).
    if isinstance(pay_day, str) and pay_day.isdigit():
        pay_day = int(pay_day)
    try:
        bank_offset = int(bank_offset)
    except (TypeError, ValueError):
        bank_offset = 0

    today = date.today()
    bank_holidays = get_bank_holidays(
        country, [today.year - 1, today.year, today.year + 1], subdiv
    )

    if pay_frequency == PAY_FREQ_MONTHLY:
        year, month = today.year, today.month
        for _ in range(24):
            payday = _payday_for_month(year, month, pay_day, bank_offset, bank_holidays)
            if payday is not None and payday <= today:
                return payday
            month -= 1
            if month == 0:
                month = 12
                year -= 1
        return None

    if pay_frequency == PAY_FREQ_BIMONTHLY:
        if not last_pay_date:
            return None
        anchor = date.fromisoformat(last_pay_date)
        prev = None
        cursor = anchor
        # Walk forward in 2-month steps, tracking the last value <= today.
        guard = 0
        while cursor <= today and guard < 600:
            prev = cursor
            cursor = _add_months(cursor, 2)
            guard += 1
        if prev is None:
            return None
        return _adjust_to_previous_bank_day(prev, bank_holidays)

    if pay_frequency in (
        PAY_FREQ_28_DAYS,
        PAY_FREQ_14_DAYS,
        PAY_FREQ_QUARTERLY,
        PAY_FREQ_SEMIANNUAL,
        PAY_FREQ_ANNUAL,
    ):
        interval = {
            PAY_FREQ_14_DAYS: 14,
            PAY_FREQ_28_DAYS: 28,
            PAY_FREQ_QUARTERLY: 91,
            PAY_FREQ_SEMIANNUAL: 182,
            PAY_FREQ_ANNUAL: 365,
        }[pay_frequency]
        if not last_pay_date:
            return None
        cursor = date.fromisoformat(last_pay_date)
        if cursor > today:
            return None
        prev = cursor
        while cursor <= today:
            prev = cursor
            cursor += timedelta(days=interval)
        return _adjust_to_previous_bank_day(prev, bank_holidays)

    if pay_frequency == PAY_FREQ_WEEKLY:
        if weekday is None:
            return None
        days_behind = (today.weekday() - weekday) % 7
        candidate = today - timedelta(days=days_behind)
        return _adjust_to_previous_bank_day(candidate, bank_holidays)

    _LOGGER.error("Invalid payday frequency: %s", pay_frequency)
    return None


def calculate_upcoming_paydays(
    country: str,
    pay_frequency: str,
    pay_day=None,
    last_pay_date=None,
    weekday=None,
    bank_offset: int = 0,
    subdiv: str | None = None,
    count: int = 12,
) -> list[date]:
    """Calculate the upcoming paydays, adjusted for weekends and holidays.

    Returns a sorted, de-duplicated list of at most `count` dates, all of
    which are today or later.
    """
    count = max(1, min(count, 24))

    # Defensive normalization: older config entries may provide numeric
    # settings as strings (e.g. pay_day='31', bank_offset='2').
    if isinstance(pay_day, str) and pay_day.isdigit():
        pay_day = int(pay_day)
    try:
        bank_offset = int(bank_offset)
    except (TypeError, ValueError):
        bank_offset = 0

    _LOGGER.debug(
        "Calculating %s upcoming paydays for %s with frequency: %s",
        count,
        country,
        pay_frequency,
    )

    today = date.today()
    bank_holidays = get_bank_holidays(
        country, [today.year, today.year + 1, today.year + 2], subdiv
    )

    raw: list[date] = []

    if pay_frequency == PAY_FREQ_MONTHLY:
        year, month = today.year, today.month
        for _ in range(count + 12):
            payday = _payday_for_month(year, month, pay_day, bank_offset, bank_holidays)
            if (
                payday is None
                and not isinstance(pay_day, int)
                and pay_day
                not in (
                    PAY_DAY_LAST_BANK_DAY,
                    PAY_DAY_FIRST_BANK_DAY,
                )
            ):
                _LOGGER.error("Invalid payday value: %s", pay_day)
                return []
            if payday is not None and payday >= today:
                raw.append(payday)
            if len(raw) >= count:
                break
            month += 1
            year += (month - 1) // 12
            month = (month - 1) % 12 + 1

    elif pay_frequency == PAY_FREQ_BIMONTHLY:
        if not last_pay_date:
            _LOGGER.error("Missing last payday date for month-interval payout.")
            return []
        nxt = _add_months(date.fromisoformat(last_pay_date), 2)
        while nxt < today:
            nxt = _add_months(nxt, 2)
        for _ in range(count):
            raw.append(_adjust_not_before_today(nxt, today, bank_holidays))
            nxt = _add_months(nxt, 2)

    elif pay_frequency in (
        PAY_FREQ_28_DAYS,
        PAY_FREQ_14_DAYS,
        PAY_FREQ_QUARTERLY,
        PAY_FREQ_SEMIANNUAL,
        PAY_FREQ_ANNUAL,
    ):
        interval = {
            PAY_FREQ_14_DAYS: 14,
            PAY_FREQ_28_DAYS: 28,
            PAY_FREQ_QUARTERLY: 91,
            PAY_FREQ_SEMIANNUAL: 182,
            PAY_FREQ_ANNUAL: 365,
        }[pay_frequency]
        if not last_pay_date:
            _LOGGER.error("Missing last payday date for recurring payout.")
            return []
        nxt = date.fromisoformat(last_pay_date) + timedelta(days=interval)
        while nxt < today:
            nxt += timedelta(days=interval)
        for _ in range(count):
            raw.append(_adjust_not_before_today(nxt, today, bank_holidays))
            nxt += timedelta(days=interval)

    elif pay_frequency == PAY_FREQ_WEEKLY:
        if weekday is None:
            raise ValueError("Weekday missing for weekly payday.")
        days_ahead = (weekday - today.weekday()) % 7
        nxt = today + timedelta(days=days_ahead)
        for _ in range(count):
            raw.append(_adjust_to_next_bank_day(nxt, bank_holidays))
            nxt += timedelta(days=7)

    else:
        _LOGGER.error("Invalid payday frequency: %s", pay_frequency)
        return []

    paydays = sorted(set(d for d in raw if d >= today))[:count]
    _LOGGER.debug("Upcoming paydays calculated: %s", paydays)
    return paydays


def _payday_for_month(
    year: int,
    month: int,
    pay_day,
    bank_offset: int,
    bank_holidays,
) -> date | None:
    """Return the payday for a specific month, fully adjusted, or None."""
    if pay_day == PAY_DAY_LAST_BANK_DAY:
        return _find_last_bank_day(year, month, bank_holidays, bank_offset)
    if pay_day == PAY_DAY_FIRST_BANK_DAY:
        return _find_first_bank_day(year, month, bank_holidays)
    if isinstance(pay_day, int):
        return _find_specific_day(year, month, pay_day, bank_holidays)
    return None


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


def _find_specific_day(year: int, month: int, day: int, bank_holidays) -> date | None:
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
