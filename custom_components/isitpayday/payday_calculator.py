import logging
from datetime import date, timedelta

import aiohttp

from .const import (
    API_HOLIDAYS,
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

# Safety limit for month-based search loops (FIX #4 from review).
_MAX_MONTH_ITERATIONS = 24


async def async_get_bank_holidays(country: str, year: int) -> list:
    """Fetch public holidays for a given country and year from Nager.Date API."""
    url = API_HOLIDAYS.format(year=year, country=country)
    _LOGGER.debug("Collecting bank holidays from: %s", url)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    _LOGGER.error(
                        "Error: Can't collect bank holidays: HTTP %s", response.status
                    )
                    return []
                holidays = await response.json()
                return [date.fromisoformat(h["date"]) for h in holidays]
    except Exception as e:
        _LOGGER.exception("Can't collect bank holidays: %s", e)
        return []


def _is_bank_day(d: date, bank_holidays: list) -> bool:
    """Return True if the date is a working bank day (not weekend, not holiday)."""
    return d.weekday() < 5 and d not in bank_holidays


def _adjust_to_previous_bank_day(d: date, bank_holidays: list) -> date:
    """Move date backwards until it lands on a valid bank day."""
    while not _is_bank_day(d, bank_holidays):
        d -= timedelta(days=1)
    return d


def _adjust_to_next_bank_day(d: date, bank_holidays: list) -> date:
    """Move date forwards until it lands on a valid bank day."""
    while not _is_bank_day(d, bank_holidays):
        d += timedelta(days=1)
    return d


def _add_months(d: date, months: int) -> date:
    """Add a number of months to a date, clamping the day to the month length."""
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    # Clamp day to last valid day of target month (handles e.g. Jan 31 -> Feb 28).
    day = d.day
    while day > 28:
        try:
            return date(year, month, day)
        except ValueError:
            day -= 1
    return date(year, month, day)


async def _get_holidays_for_years(country: str, years: set) -> list:
    """Fetch and combine bank holidays for multiple years."""
    all_holidays = []
    for year in years:
        holidays = await async_get_bank_holidays(country, year)
        all_holidays.extend(holidays)
    return all_holidays


async def async_calculate_next_payday(
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
    bank_holidays = await _get_holidays_for_years(
        country, {today.year, today.year + 1}
    )

    if pay_frequency == PAY_FREQ_MONTHLY:
        # async_calculate_month_based already returns an adjusted date.
        payday = await async_calculate_month_based(
            today, 1, pay_day, bank_offset, bank_holidays
        )

    elif pay_frequency == PAY_FREQ_BIMONTHLY:
        # FIX #1 from review: bimonthly is anchored to last_pay_date and uses
        # real month arithmetic (not pay_day-based logic, and not fixed 60 days).
        payday = await async_calculate_month_interval(
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
        payday = await async_calculate_recurring(
            last_pay_date, interval_days, bank_holidays
        )
        # FIX #3 from review: adjust, but never to a date before today.
        if payday is not None:
            payday = _adjust_not_before_today(payday, today, bank_holidays)

    elif pay_frequency == PAY_FREQ_WEEKLY:
        if weekday is None:
            raise ValueError("Weekday missing for weekly payday.")
        payday = await async_calculate_weekly(today, weekday, bank_holidays)
        if payday is not None:
            payday = _adjust_to_next_bank_day(payday, bank_holidays)

    else:
        _LOGGER.error("Invalid payday frequency: %s", pay_frequency)
        return None

    # FIX #6 from review: if the payday landed in a year we have no holiday
    # data for, fetch that year's holidays and re-validate the date.
    if payday is not None and payday.year > today.year + 1:
        extra_holidays = await async_get_bank_holidays(country, payday.year)
        if extra_holidays:
            combined = bank_holidays + extra_holidays
            payday = _adjust_not_before_today(payday, today, combined)

    _LOGGER.info("Next payday calculated: %s", payday)
    return payday


def _adjust_not_before_today(
    payday: date, today: date, bank_holidays: list
) -> date:
    """Adjust payday to the previous bank day, but never earlier than today.

    If adjusting backwards would land before today, adjust forwards instead.
    """
    adjusted = _adjust_to_previous_bank_day(payday, bank_holidays)
    if adjusted < today:
        adjusted = _adjust_to_next_bank_day(payday, bank_holidays)
    return adjusted


async def async_calculate_month_based(
    today: date,
    month_interval: int,
    pay_day,
    bank_offset: int,
    bank_holidays: list,
):
    """Calculate next payday for monthly frequency (pay_day based).

    Already returns a fully adjusted (bank day) date.
    """
    year, month = today.year, today.month

    # FIX #4 from review: bounded loop instead of `while True`.
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


async def async_calculate_month_interval(
    last_pay_date: str,
    month_interval: int,
    today: date,
    bank_holidays: list,
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

    # FIX #4 from review: bounded loop.
    for _ in range(_MAX_MONTH_ITERATIONS):
        if payday >= today:
            return _adjust_not_before_today(payday, today, bank_holidays)
        payday = _add_months(payday, month_interval)

    _LOGGER.error(
        "Could not find a valid payday within %s months.", _MAX_MONTH_ITERATIONS
    )
    return None


async def async_calculate_recurring(
    last_pay_date: str,
    interval: int,
    bank_holidays: list,
) -> date | None:
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


async def async_calculate_weekly(
    today: date,
    weekday: int,
    bank_holidays: list,
) -> date:
    """Return the next occurrence of the given weekday (unadjusted)."""
    days_ahead = (weekday - today.weekday()) % 7
    payday = today + timedelta(days=days_ahead)
    return payday


def _find_last_bank_day(
    year: int, month: int, bank_holidays: list, bank_offset: int
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


def _find_first_bank_day(
    year: int, month: int, bank_holidays: list
) -> date | None:
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
    year: int, month: int, day: int, bank_holidays: list
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
