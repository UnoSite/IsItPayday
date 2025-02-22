import voluptuous as vol
import aiohttp
import logging
from homeassistant import config_entries
from .const import DOMAIN, CONF_COUNTRY, CONF_COUNTRY_ID

_LOGGER = logging.getLogger(__name__)
API_URL = "https://api.isitpayday.com/countries"

class IsItPaydayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for IsItPayday integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Prevent multiple installations."""
        if self._async_current_entries():
            return self.async_abort(reason="Only one installation is allowed.")

        return await self._show_setup_form(user_input)

    async def _show_setup_form(self, user_input):
        """Show form for selecting country."""
        errors = {}

        country_options = await self._fetch_supported_countries()
        if not country_options:
            errors["base"] = "API error. Please try again later."
            country_options = self._fetch_supported_countries_sync()

        if user_input is not None:
            selected_country_name = user_input[CONF_COUNTRY]
            selected_country_id = {v: k for k, v in country_options.items()}[selected_country_name]

            return self.async_create_entry(
                title="Is It Payday?",
                data={
                    CONF_COUNTRY: selected_country_name,
                    CONF_COUNTRY_ID: selected_country_id,
                }
            )

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_schema(country_options),
            errors=errors,
        )

    def _get_schema(self, country_options):
        """Return schema for selecting country."""
        return vol.Schema({
            vol.Required(CONF_COUNTRY, default="Denmark"): vol.In(country_options.values())
        })

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
