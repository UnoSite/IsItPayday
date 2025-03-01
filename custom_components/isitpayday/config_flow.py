"""Config flow for IsItPayday integration."""

import logging
import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode, DateSelector

from .const import *

_LOGGER = logging.getLogger(__name__)

WEEKDAY_MAP = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4
}


async def async_get_homeassistant_country(hass: HomeAssistant) -> str | None:
    _LOGGER.debug("Henter Home Assistant country fra konfiguration.")
    country = getattr(hass.config, "country", None)

    if not country:
        _LOGGER.warning("Home Assistant country er ikke sat.")
        return None

    supported_countries = await async_fetch_supported_countries()

    if country not in supported_countries:
        _LOGGER.warning("Landet '%s' er ikke blandt de understøttede lande.", country)
        return None

    return country


async def async_fetch_supported_countries() -> dict[str, str]:
    async with aiohttp.ClientSession() as session:
        async with session.get(API_COUNTRIES) as response:
            data = await response.json()
            return {country["countryCode"]: country["name"] for country in data}


class IsItPayday2ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self.country = None
        self.pay_frequency = None
        self.pay_day = None
        self.last_pay_date = None
        self.bank_offset = 0
        self.weekday = None
        self.country_list = {}

    async def async_step_user(self, user_input=None):
        if user_input is None:
            self.country_list = await async_fetch_supported_countries()
            current_country = await async_get_homeassistant_country(self.hass) or "DK"
            return self.async_show_form(step_id="user", data_schema=self._create_country_schema(current_country))

        self.country = user_input[CONF_COUNTRY]
        return await self.async_step_frequency()

    async def async_step_frequency(self, user_input=None):
        if user_input is None:
            return self.async_show_form(step_id="frequency", data_schema=self._create_pay_frequency_schema())

        self.pay_frequency = user_input[CONF_PAY_FREQ]

        if self.pay_frequency == PAY_FREQ_MONTHLY:
            return await self.async_step_monthly_day()
        elif self.pay_frequency in [PAY_FREQ_28_DAYS, PAY_FREQ_14_DAYS]:
            return await self.async_step_cycle_last_paydate()
        elif self.pay_frequency == PAY_FREQ_WEEKLY:
            return await self.async_step_weekly()

        return self._create_entry()

    async def async_step_monthly_day(self, user_input=None):
        if user_input is None:
            return self.async_show_form(step_id="monthly_day", data_schema=self._create_monthly_day_schema())

        self.pay_day = user_input[CONF_PAY_DAY]

        if self.pay_day == PAY_DAY_LAST_BANK_DAY:
            return await self.async_step_bank_offset()
        elif self.pay_day == PAY_DAY_SPECIFIC_DAY:
            return await self.async_step_specific_day()

        return self._create_entry()

    async def async_step_bank_offset(self, user_input=None):
        if user_input is None:
            return self.async_show_form(step_id="bank_offset", data_schema=self._create_bank_offset_schema())

        self.bank_offset = int(user_input[CONF_BANK_OFFSET])
        return self._create_entry()

    async def async_step_specific_day(self, user_input=None):
        if user_input is None:
            return self.async_show_form(step_id="specific_day", data_schema=self._create_specific_day_schema())

        self.pay_day = int(user_input[CONF_PAY_DAY])
        return self._create_entry()

    async def async_step_cycle_last_paydate(self, user_input=None):
        if user_input is None:
            return self.async_show_form(step_id="cycle_last_paydate", data_schema=self._create_last_paydate_schema())

        self.last_pay_date = user_input[CONF_LAST_PAY_DATE]
        return self._create_entry()

    async def async_step_weekly(self, user_input=None):
        if user_input is None:
            return self.async_show_form(step_id="weekly", data_schema=self._create_weekly_schema())

        self.pay_day = user_input[CONF_PAY_DAY]
        self.weekday = WEEKDAY_MAP[self.pay_day]
        return self._create_entry()

    def _create_entry(self) -> FlowResult:
        return self.async_create_entry(
            title=CONF_TITLE,
            data={
                CONF_COUNTRY: self.country,
                CONF_PAY_FREQ: self.pay_frequency,
                CONF_PAY_DAY: self.pay_day,
                CONF_LAST_PAY_DATE: self.last_pay_date,
                CONF_BANK_OFFSET: self.bank_offset,
                CONF_WEEKDAY: self.weekday,
            }
        )

    def _create_country_schema(self, default_country: str) -> vol.Schema:
        return vol.Schema({vol.Required(CONF_COUNTRY, default=default_country): vol.In(self.country_list)})

    def _create_pay_frequency_schema(self) -> vol.Schema:
        return vol.Schema({vol.Required(CONF_PAY_FREQ): vol.In(PAY_FREQ_OPTIONS)})

    def _create_monthly_day_schema(self) -> vol.Schema:
        return vol.Schema({vol.Required(CONF_PAY_DAY): vol.In(PAY_MONTHLY_OPTIONS)})

    def _create_bank_offset_schema(self) -> vol.Schema:
        return vol.Schema({vol.Required(CONF_BANK_OFFSET, default=0): vol.In(range(0, 11))})

    def _create_specific_day_schema(self) -> vol.Schema:
        return vol.Schema({vol.Required(CONF_PAY_DAY, default=31): vol.In(range(1, 32))})

    def _create_last_paydate_schema(self) -> vol.Schema:
        return vol.Schema({vol.Required(CONF_LAST_PAY_DATE): DateSelector()})

    def _create_weekly_schema(self) -> vol.Schema:
        return vol.Schema({vol.Required(CONF_PAY_DAY): vol.In(WEEKDAY_OPTIONS)})
