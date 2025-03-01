"""Beregner naeste loenningsdag for IsItPayday."""

import logging
from datetime import date, timedelta
import aiohttp
from .const import *

_LOGGER = logging.getLogger(__name__)


async def async_get_bank_holidays(country: str, year: int) -> list:
    """Hent banklukkedage fra Nager.Date API."""
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
    """Beregner næste lønningsdag baseret på konfiguration."""
    _LOGGER.info("Beregner næste lønningsdag for %s med frekvens: %s", country, pay_frequency)

    today = date.today()
    year = today.year
    bank_holidays = await async_get_bank_holidays(country, year)

    if pay_frequency == PAY_FREQ_MONTHLY:
        payday = await async_calculate_monthly(pay_day, bank_holidays, today, bank_offset)

    elif pay_frequency in (PAY_FREQ_28_DAYS, PAY_FREQ_14_DAYS):
        payday = await async_calculate_recurring(last_pay_date, 28 if pay_frequency == PAY_FREQ_28_DAYS else 14)

    elif pay_frequency == PAY_FREQ_WEEKLY:
        if weekday is None:
            raise ValueError("Ugedag (weekday) mangler for weekly betaling.")
        payday = await async_calculate_weekly(today, weekday)

    else:
        _LOGGER.error("Ugyldig betalingsfrekvens: %s", pay_frequency)
        return None

    # Flyt tilbage hvis på weekend eller helligdag
    payday = await async_adjust_for_bank_holidays_and_weekends(payday, bank_holidays)

    _LOGGER.info("Næste lønningsdag efter justering: %s", payday)
    return payday


async def async_calculate_monthly(pay_day, bank_holidays, today, bank_offset):
    """Beregn næste månedlige lønningsdag baseret på pay_day type."""
    _LOGGER.info("Beregner månedlig lønningsdag: %s", pay_day)

    year, month = today.year, today.month

    if pay_day == "last_bank_day":
        payday = await async_find_last_bank_day(year, month, bank_holidays, bank_offset)
    elif pay_day == "first_bank_day":
        payday = await async_find_first_bank_day(year, month, bank_holidays)
    elif isinstance(pay_day, int):
        payday = await async_find_specific_day(year, month, pay_day, bank_holidays)
    else:
        _LOGGER.error("Ugyldig pay_day værdi for månedlig betaling: %s", pay_day)
        return None

    if payday <= today:
        month += 1
        if month > 12:
            month = 1
            year += 1
        return await async_calculate_monthly(pay_day, bank_holidays, date(year, month, 1), bank_offset)

    return payday


async def async_calculate_recurring(last_pay_date, interval):
    """Beregn næste lønningsdag for 14- eller 28-dages interval."""
    if not last_pay_date:
        _LOGGER.error("Mangler sidste lønningsdato for tilbagevendende betaling.")
        return None

    last_date = date.fromisoformat(last_pay_date)
    payday = last_date + timedelta(days=interval)

    # Hvis datoen er i fortiden, ryk frem til næste gyldige
    today = date.today()
    while payday <= today:
        payday += timedelta(days=interval)

    _LOGGER.info("Næste tilbagevendende lønningsdag beregnet til: %s", payday)
    return payday


async def async_calculate_weekly(today, weekday):
    """Beregn næste ugentlige lønningsdag."""
    days_ahead = (weekday - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7  # Hvis det er i dag, tag næste uge

    payday = today + timedelta(days=days_ahead)

    _LOGGER.info("Næste ugentlige lønningsdag beregnet til: %s", payday)
    return payday


async def async_find_last_bank_day(year, month, bank_holidays, bank_offset):
    """Find sidste bankdag i måneden."""
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
    """Find første bankdag i måneden."""
    day = 1
    while True:
        payday = date(year, month, day)
        if payday.weekday() < 5 and payday not in bank_holidays:
            _LOGGER.info("Første bankdag fundet: %s", payday)
            return payday
        day += 1


async def async_find_specific_day(year, month, day, bank_holidays):
    """Find specifik dag i måneden, ryk bagud hvis helligdag/weekend."""
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
    """Flyt dato bagud hvis weekend eller banklukket dag."""
    _LOGGER.debug("Tjekker og justerer for weekend/helligdag: %s", payday)

    while payday.weekday() >= 5 or payday in bank_holidays:
        _LOGGER.warning("Flytter lønningsdag bagud: %s", payday)
        payday -= timedelta(days=1)

    _LOGGER.debug("Endelig dato efter justering: %s", payday)
    return payday
