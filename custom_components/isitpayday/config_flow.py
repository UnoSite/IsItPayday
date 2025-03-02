"""Config flow for IsItPayday integration."""

import logging
import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import DateSelector

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
    """Get Home Assistant configured country."""
    country = getattr(hass.config, "country", None)

    if not country:
        _LOGGER.warning("Home Assistant country is not set.")
        return None

    supported_countries = await async_fetch_supported_countries()

    if country not in supported_countries:
        _LOGGER.warning("Country '%s' is not supported.", country)
        return None

    return country


async def async_fetch_supported_countries() -> dict[str, str]:
    """Fetch supported countries from Nager.Date API."""
    async with aiohttp.ClientSession() as session:
        async with session.get(API_COUNTRIES) as response:
            data = await response.json()
            return {country["countryCode"]: country["name"] for country in data}


class IsItPayday2ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self.name = None
        self.country = None
        self.pay_frequency = None
        self.pay_day = None
        self.last_pay_date = None
        self.bank_offset = 0
        self.weekday = None
        self.country_list = {}
        self.reconfig_entry = None

    async def async_step_reconfigure(self, user_input=None):
        """Start reconfiguration flow."""
        _LOGGER.info("Starting reconfiguration flow")

        entry_id = self.context.get("entry_id")
        if not entry_id:
            _LOGGER.error("Reconfiguration started without valid entry_id in context.")
            return self.async_abort(reason="missing_entry")

        entry = self.hass.config_entries.async_get_entry(entry_id)
        if not entry:
            _LOGGER.error("Could not find entry with id %s", entry_id)
            return self.async_abort(reason="entry_not_found")

        self.reconfig_entry = entry
        data = entry.data

        self.name = data.get(CONF_NAME, "")
        self.country = data.get(CONF_COUNTRY)
        self.pay_frequency = data.get(CONF_PAY_FREQ)
        self.pay_day = data.get(CONF_PAY_DAY)
        self.last_pay_date = data.get(CONF_LAST_PAY_DATE)
        self.bank_offset = data.get(CONF_BANK_OFFSET, 0)
        self.weekday = data.get(CONF_WEEKDAY)

        self.country_list = await async_fetch_supported_countries()

        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        if user_input is None:
            self.country_list = await async_fetch_supported_countries()
            current_country = self.country or await async_get_homeassistant_country(self.hass) or "DK"

            return self.async_show_form(
                step_id="user",
                data_schema=self._create_user_schema(current_country)
            )

        self.name = user_input[CONF_NAME]
        self.country = user_input[CONF_COUNTRY]
        return await self.async_step_frequency()

    async def async_step_frequency(self, user_input=None):
        if user_input is None:
            return self.async_show_form(
                step_id="frequency",
                data_schema=self._create_pay_frequency_schema()
            )

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
            return self.async_show_form(
                step_id="monthly_day",
                data_schema=self._create_monthly_day_schema()
            )

        self.pay_day = user_input[CONF_PAY_DAY]

        if self.pay_day == PAY_DAY_LAST_BANK_DAY:
            return await self.async_step_bank_offset()
        elif self.pay_day == PAY_DAY_SPECIFIC_DAY:
            return await self.async_step_specific_day()

        return self._create_entry()

    async def async_step_bank_offset(self, user_input=None):
        if user_input is None:
            return self.async_show_form(
                step_id="bank_offset",
                data_schema=self._create_bank_offset_schema()
            )

        self.bank_offset = int(user_input[CONF_BANK_OFFSET])
        return self._create_entry()

    async def async_step_specific_day(self, user_input=None):
        if user_input is None:
            return self.async_show_form(
                step_id="specific_day",
                data_schema=self._create_specific_day_schema()
            )

        self.pay_day = int(user_input[CONF_PAY_DAY])
        return self._create_entry()

    async def async_step_cycle_last_paydate(self, user_input=None):
        if user_input is None:
            return self.async_show_form(
                step_id="cycle_last_paydate",
                data_schema=self._create_last_paydate_schema()
            )

        self.last_pay_date = user_input[CONF_LAST_PAY_DATE]
        return self._create_entry()

    async def async_step_weekly(self, user_input=None):
        if user_input is None:
            return self.async_show_form(
                step_id="weekly",
                data_schema=self._create_weekly_schema()
            )

        self.pay_day = user_input[CONF_PAY_DAY]
        self.weekday = WEEKDAY_MAP[self.pay_day]
        return self._create_entry()

    def _create_entry(self) -> FlowResult:
        data = {
            CONF_NAME: self.name,
            CONF_COUNTRY: self.country,
            CONF_PAY_FREQ: self.pay_frequency,
            CONF_PAY_DAY: self.pay_day,
            CONF_LAST_PAY_DATE: self.last_pay_date,
            CONF_BANK_OFFSET: self.bank_offset,
            CONF_WEEKDAY: self.weekday,
        }

        if self.reconfig_entry:
            _LOGGER.info("Updating existing entry: %s", self.reconfig_entry.entry_id)
            self.hass.config_entries.async_update_entry(self.reconfig_entry, data=data)
            self.hass.async_create_task(self.hass.config_entries.async_reload(self.reconfig_entry.entry_id))

            # Use service call instead of direct import
            self.hass.async_create_task(self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "IsItPayday",
                    "message": f"The configuration for '{self.name}' has been successfully updated."
                }
            ))

            return self.async_abort(reason="reconfigured")

        return self.async_create_entry(title=self.name, data=data)

    def _create_user_schema(self, default_country: str) -> vol.Schema:
        return vol.Schema({
            vol.Required(CONF_NAME, default=self.name or ""): str,
            vol.Required(CONF_COUNTRY, default=default_country): vol.In(self.country_list)
        })

    def _create_pay_frequency_schema(self) -> vol.Schema:
        return vol.Schema({
            vol.Required(CONF_PAY_FREQ, default=self.pay_frequency or PAY_FREQ_MONTHLY): vol.In(PAY_FREQ_OPTIONS)
        })

    def _create_monthly_day_schema(self) -> vol.Schema:
        return vol.Schema({
            vol.Required(CONF_PAY_DAY, default=self.pay_day or PAY_DAY_LAST_BANK_DAY): vol.In(PAY_MONTHLY_OPTIONS)
        })

    def _create_bank_offset_schema(self) -> vol.Schema:
        return vol.Schema({
            vol.Required(CONF_BANK_OFFSET, default=self.bank_offset or 0): vol.In(range(0, 11))
        })

    def _create_specific_day_schema(self) -> vol.Schema:
        return vol.Schema({
            vol.Required(CONF_PAY_DAY, default=self.pay_day or 31): vol.In(range(1, 32))
        })

    def _create_last_paydate_schema(self) -> vol.Schema:
        return vol.Schema({
            vol.Required(CONF_LAST_PAY_DATE, default=self.last_pay_date): DateSelector()
        })

    def _create_weekly_schema(self) -> vol.Schema:
        return vol.Schema({
            vol.Required(CONF_PAY_DAY, default=self.pay_day or "Monday"): vol.In(WEEKDAY_OPTIONS)
        })
