"""Options flow for IsItPayday."""

import logging
from homeassistant import config_entries
import voluptuous as vol
from .const import *
import aiohttp

_LOGGER = logging.getLogger(__name__)

WEEKDAY_MAP = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4
}


class IsItPayday2OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Start reconfiguration."""
        if user_input is not None:
            if user_input[CONF_PAY_FREQ] == PAY_FREQ_WEEKLY:
                user_input[CONF_WEEKDAY] = WEEKDAY_MAP[user_input[CONF_PAY_DAY]]
            else:
                user_input[CONF_WEEKDAY] = None

            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.data.copy()
        countries = await self._fetch_supported_countries()

        schema = vol.Schema({
            vol.Required(CONF_NAME, default=options.get(CONF_NAME, "")): str,
            vol.Required(CONF_COUNTRY, default=options.get(CONF_COUNTRY)): vol.In(countries),
            vol.Required(CONF_PAY_FREQ, default=options.get(CONF_PAY_FREQ)): vol.In(PAY_FREQ_OPTIONS),
            vol.Required(CONF_PAY_DAY, default=options.get(CONF_PAY_DAY)): vol.In(WEEKDAY_OPTIONS if options.get(CONF_PAY_FREQ) == PAY_FREQ_WEEKLY else PAY_MONTHLY_OPTIONS),
            vol.Optional(CONF_LAST_PAY_DATE, default=options.get(CONF_LAST_PAY_DATE)): str,
            vol.Optional(CONF_BANK_OFFSET, default=options.get(CONF_BANK_OFFSET, 0)): vol.In(range(0, 11)),
        })

        return self.async_show_form(step_id="init", data_schema=schema)

    async def _fetch_supported_countries(self) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(API_COUNTRIES) as response:
                data = await response.json()
                return {country["countryCode"]: country["name"] for country in data}
