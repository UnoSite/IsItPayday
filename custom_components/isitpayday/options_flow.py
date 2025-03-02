"""Options flow for IsItPayday."""

import logging
from homeassistant import config_entries
import voluptuous as vol
from .const import *

_LOGGER = logging.getLogger(__name__)


class IsItPayday2OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.data.copy()

        schema = vol.Schema({
            vol.Required(CONF_NAME, default=options.get(CONF_NAME, "")): str,
            vol.Required(CONF_COUNTRY, default=options.get(CONF_COUNTRY)): vol.In(await self._fetch_countries()),
            vol.Required(CONF_PAY_FREQ, default=options.get(CONF_PAY_FREQ)): vol.In(PAY_FREQ_OPTIONS),
        })

        return self.async_show_form(step_id="init", data_schema=schema)

    async def _fetch_countries(self) -> dict:
        from aiohttp import ClientSession
        async with ClientSession() as session:
            async with session.get(API_COUNTRIES) as response:
                data = await response.json()
                return {country["countryCode"]: country["name"] for country in data}
