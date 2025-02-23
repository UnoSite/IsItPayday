import voluptuous as vol
import aiohttp
import logging
from homeassistant import config_entries
from .const import DOMAIN, CONF_COUNTRY, CONF_COUNTRY_ID, CONF_PAYDAY_TYPE, CONF_CUSTOM_DAY

_LOGGER = logging.getLogger(__name__)
API_URL = "https://api.isitpayday.com/countries"

PAYDAY_OPTIONS = {
    "last_day": "Last day of the month",
    "first_day": "First day of the month",
    "custom_day": "Custom day of the month"
}

class IsItPaydayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for IsItPayday integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Prevent multiple installations."""
        if self._async_current_entries():
            return self.async_abort(reason="Only one installation is allowed.")

        return await self._show_country_form(user_input)

    async def _show_country_form(self, user_input):
        """Step 1: Select country."""
        errors = {}

        country_options = await self._fetch_supported_countries()
        if not country_options:
            errors["base"] = "API error. Please try again later."

        if user_input is not None:
            self.selected_country_name = user_input[CONF_COUNTRY]
            self.selected_country_id = {v: k for k, v in country_options.items()}[self.selected_country_name]
            return await self.async_step_payday_type()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_COUNTRY, default="Denmark"): vol.In(country_options.values())
            }),
            errors=errors,
        )

    async def async_step_payday_type(self, user_input=None):
        """Step 2: Select payday type."""
        errors = {}

        if user_input is not None:
            self.payday_type = user_input[CONF_PAYDAY_TYPE]

            if self.payday_type == "custom_day":
                return await self.async_step_custom_day()

            return self.async_create_entry(
                title="Is It Payday?",
                data={
                    CONF_COUNTRY: self.selected_country_name,
                    CONF_COUNTRY_ID: self.selected_country_id,
                    CONF_PAYDAY_TYPE: self.payday_type,
                    CONF_CUSTOM_DAY: None  # No custom day selected
                }
            )

        return self.async_show_form(
            step_id="payday_type",
            data_schema=vol.Schema({
                vol.Required(CONF_PAYDAY_TYPE, default="last_day"): vol.In(PAYDAY_OPTIONS)
            }),
            errors=errors,
        )

    async def async_step_custom_day(self, user_input=None):
        """Step 3: Select a custom day of the month."""
        errors = {}

        if user_input is not None:
            custom_day = user_input[CONF_CUSTOM_DAY]

            if not (1 <= custom_day <= 31):
                errors["base"] = "Invalid day. Choose between 1 and 31."
            else:
                return self.async_create_entry(
                    title="Is It Payday?",
                    data={
                        CONF_COUNTRY: self.selected_country_name,
                        CONF_COUNTRY_ID: self.selected_country_id,
                        CONF_PAYDAY_TYPE: self.payday_type,
                        CONF_CUSTOM_DAY: custom_day
                    }
                )

        return self.async_show_form(
            step_id="custom_day",
            data_schema=vol.Schema({
                vol.Required(CONF_CUSTOM_DAY, default=15): vol.All(vol.Coerce(int), vol.Range(min=1, max=31))
            }),
            errors=errors,
        )

    async def _fetch_supported_countries(self):
        """Fetch supported countries from the API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL, timeout=10) as response:
                    if response.status != 200:
                        return None

                    data = await response.json()
                    return {country["id"]: country["name"] for country in data}

        except aiohttp.ClientError:
            return None
