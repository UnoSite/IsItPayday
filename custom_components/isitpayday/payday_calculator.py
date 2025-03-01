"""Beregner naeste loenningsdag for IsItPayday."""

import logging
from datetime import date, timedelta
import aiohttp
from .const import *

_LOGGER = logging.getLogger(__name__)


async def async_get_bank_holidays(country: str, year: int) -> list:
    """Hent banklukkedage fra Nager.Date API for et givent land og aar."""
    url = API_HOLIDAYS.format(year=year, country=country)
    _LOGGER.debug("Henter banklukkedage fra: %s", url)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    _LOGGER.error("Fejl ved hentning af banklukkedage: HTTP %s", response.status)
                    return []
                holidays = await response.json()
                return [date.fromisoformat(h["date"]) for h in holidays]
    except Exception as e:
        _LOGGER.exception("Kunne ikke hente banklukkedage: %s", e)
        return []


async def async_calculate_next_payday(country: str, pay_frequency: str, pay_day=None, last_pay_date=None, weekday=None, bank_offset=0):
    """Udregn naeste loenningsdag baseret paa konfiguration."""
    _LOGGER.info("Starter beregning af naeste loenningsdag for %s med frekvens: %s", country, pay_frequency)

    today = date.today()
    year = today.year

    bank_holidays = await async_get_bank_holidays(country, year)
    _LOGGER.debug("Hentede %d banklukkedage for %s", len(bank_holidays), country)

    if pay_frequency == PAY_FREQ_MONTHLY:
        payday = await async_calculate_monthly(pay_day, bank_holidays, today, bank_offset)
    elif pay_frequency in (PAY_FREQ_28_DAYS, PAY_FREQ_14_DAYS):
        interval = 28 if pay_frequency == PAY_FREQ_28_DAYS else 14
        payday = await async_calculate_recurring(last_pay_date, interval)
    elif pay_frequency == PAY_FREQ_WEEKLY:
        payday = await async_calculate_weekly(today, weekday)
    else:
        _LOGGER.error("Ugyldig betalingsfrekvens: %s", pay_frequency)
        return None

    # Flyt automatisk tilbage hvis den falder på weekend eller helligdag
    payday = await async_adjust_for_bank_holidays_and_weekends(payday, bank_holidays)

    _LOGGER.info("Naeste loenningsdag efter justering: %s", payday)
    return payday


async def async_calculate_monthly(pay_day, bank_holidays, today, bank_offset):
    """Beregner naeste maanedlige loenningsdag baseret paa pay_day type."""
    _LOGGER.info("Beregner maanedlig loenningsdag: %s", pay_day)

    year, month = today.year, today.month

    if pay_day == "last_bank_day":
        payday = await async_find_last_bank_day(year, month, bank_holidays, bank_offset)
    elif pay_day == "first_bank_day":
        payday = await async_find_first_bank_day(year, month, bank_holidays)
    elif isinstance(pay_day, int):
        payday = await async_find_specific_day(year, month, pay_day, bank_holidays)
    else:
        _LOGGER.error("Ugyldig pay_day vaerdi for maanedlig betaling: %s", pay_day)
        return None

    if payday <= today:
        month += 1
        if month > 12:
            month = 1
            year += 1
        _LOGGER.info("Flytter til naeste maaned, da datoen er i dag eller tidligere.")
        return await async_calculate_monthly(pay_day, bank_holidays, date(year, month, 1), bank_offset)

    return payday


async def async_calculate_recurring(last_pay_date, interval):
    """Beregner naeste loenningsdag for 14- eller 28-dages interval."""
    if not last_pay_date:
        _LOGGER.error("Mangler sidste loenningsdato for tilbagevendende betaling.")
        return None

    last_date = date.fromisoformat(last_pay_date)
    next_payday = last_date + timedelta(days=interval)

    _LOGGER.info("Naeste tilbagevendende loenningsdag beregnet til: %s", next_payday)
    return next_payday


async def async_calculate_weekly(today, weekday):
    """Beregner naeste ugentlige loenningsdag."""
    days_ahead = (weekday - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7  # Hvis i dag er loenningsdag, vælg næste uge

    payday = today + timedelta(days=days_ahead)
    _LOGGER.info("Naeste ugentlige loenningsdag beregnet til: %s", payday)
    return payday


async def async_find_last_bank_day(year, month, bank_holidays, bank_offset):
    """Finder sidste bankdag i måneden."""
    day = 31
    while True:
        try:
            payday = date(year, month, day)
            if payday.weekday() < 5 and payday not in bank_holidays:
                payday -= timedelta(days=bank_offset)
                _LOGGER.info("Sidste bankdag fundet: %s", payday)
                return payday
            day -= 1
        except ValueError:
            day -= 1


async def async_find_first_bank_day(year, month, bank_holidays):
    """Finder første bankdag i måneden."""
    day = 1
    while True:
        payday = date(year, month, day)
        if payday.weekday() < 5 and payday not in bank_holidays:
            _LOGGER.info("Første bankdag fundet: %s", payday)
            return payday
        day += 1


async def async_find_specific_day(year, month, day, bank_holidays):
    """Finder specifik dag i måneden og flytter bagud ved helligdag/weekend."""
    while True:
        try:
            payday = date(year, month, day)
            if payday.weekday() < 5 and payday not in bank_holidays:
                _LOGGER.info("Specifik udbetalingsdag fundet: %s", payday)
                return payday
            day -= 1
        except ValueError:
            day -= 1


async def async_adjust_for_bank_holidays_and_weekends(payday, bank_holidays):
    """Flytter en dato tilbage hvis den falder på weekend eller banklukket dag."""
    _LOGGER.debug("Tjekker og justerer dato for weekend/helligdag: %s", payday)

    while payday.weekday() >= 5 or payday in bank_holidays:
        _LOGGER.warning("Loenningsdag falder på weekend eller helligdag: %s - Flytter bagud.", payday)
        payday -= timedelta(days=1)

    _LOGGER.debug("Justering færdig. Endelig dato: %s", payday)
    return payday
