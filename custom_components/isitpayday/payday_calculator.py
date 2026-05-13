import logging
from datetime import date, timedelta

import aiohttp

from .const import *

_LOGGER = logging.getLogger(__name__)


async def async_get_bank_holidays(country: str, year: int) -> list:
    url = API_HOLIDAYS.format(year=year, country=country)
    _LOGGER.debug("Collecting bank holidays from: %s", url)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
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


async def async_calculate_next_payday(
    country: str,
    pay_frequency: str,
    pay_day=None,
    last_pay_date=None,
    weekday=None,
    bank_offset=0,
):
    _LOGGER.info(
        "Starting calculation of the next payday for %s with frequency: %s",
        country,
        pay_frequency,
    )

    today = date.today()
    year = today.year
    bank_holidays = await async_get_bank_holidays(country, year)

    if pay_frequency == PAY_FREQ_MONTHLY:
        payday = await async_calculate_month_based(
            today, 1, pay_day, bank_offset, bank_holidays
        )

    elif pay_frequency in (
        PAY_FREQ_28_DAYS,
        PAY_FREQ_14_DAYS,
        PAY_FREQ_BIMONTHLY,
        PAY_FREQ_QUARTERLY,
        PAY_FREQ_SEMIANNUAL,
        PAY_FREQ_ANNUAL,
    ):
        interval_days = {
            PAY_FREQ_14_DAYS: 14,
            PAY_FREQ_28_DAYS: 28,
            PAY_FREQ_BIMONTHLY: 60,
            PAY_FREQ_QUARTERLY: 91,
            PAY_FREQ_SEMIANNUAL: 182,
            PAY_FREQ_ANNUAL: 365,
        }[pay_frequency]
        payday = await async_calculate_recurring(
            last_pay_date, interval_days, bank_holidays
        )

    elif pay_frequency == PAY_FREQ_WEEKLY:
        if weekday is None:
            raise ValueError("Weekday missing for weekly payday.")
        payday = await async_calculate_weekly(today, weekday, bank_holidays)

    else:
        _LOGGER.error("Invalid payday frequency: %s", pay_frequency)
        return None

    payday = await async_adjust_for_bank_holidays_and_weekends(payday, bank_holidays)
    _LOGGER.info("Next payday after adjustment: %s", payday)
    return payday


async def async_calculate_month_based(
    today, month_interval, pay_day, bank_offset, bank_holidays
):
    year, month = today.year, today.month

    while True:
        if pay_day == PAY_DAY_LAST_BANK_DAY:
            payday = await async_find_last_bank_day(
                year, month, bank_holidays, bank_offset
            )
        elif pay_day == PAY_DAY_FIRST_BANK_DAY:
            payday = await async_find_first_bank_day(year, month, bank_holidays)
        elif isinstance(pay_day, int):
            payday = await async_find_specific_day(year, month, pay_day, bank_holidays)
        else:
            _LOGGER.error("Invalid payday value: %s", pay_day)
            return None

        if payday >= today:
            return payday

        month += month_interval
        year += (month - 1) // 12
        month = (month - 1) % 12 + 1


async def async_calculate_recurring(last_pay_date, interval, bank_holidays):
    if not last_pay_date:
        _LOGGER.error("Missing last payday date for recurring payout.")
        return None

    last_date = date.fromisoformat(last_pay_date)
    payday = last_date + timedelta(days=interval)

    today = date.today()
    while payday < today:
        payday += timedelta(days=interval)

    _LOGGER.info("Next recurring payday is calculated to: %s", payday)
    return payday


async def async_calculate_weekly(today, weekday, bank_holidays):
    days_ahead = (weekday - today.weekday()) % 7
    payday = today + timedelta(days=days_ahead)
    return payday


async def async_find_last_bank_day(year, month, bank_holidays, bank_offset):
    day = 31
    while day > 0:
        try:
            payday = date(year, month, day)
            if payday.weekday() < 5 and payday not in bank_holidays:
                return payday - timedelta(days=bank_offset)
            day -= 1
        except ValueError:
            day -= 1


async def async_find_first_bank_day(year, month, bank_holidays):
    day = 1
    while day <= 31:
        try:
            payday = date(year, month, day)
            if payday.weekday() < 5 and payday not in bank_holidays:
                return payday
            day += 1
        except ValueError:
            day += 1


async def async_find_specific_day(year, month, day, bank_holidays):
    while day > 0:
        try:
            payday = date(year, month, day)
            if payday.weekday() < 5 and payday not in bank_holidays:
                return payday
            day -= 1
        except ValueError:
            day -= 1


async def async_adjust_for_bank_holidays_and_weekends(payday, bank_holidays):
    while payday.weekday() >= 5 or payday in bank_holidays:
        payday -= timedelta(days=1)
    return payday
