import aiohttp
import logging
import calendar
from datetime import datetime
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, CONF_COUNTRY_ID, VERSION

_LOGGER = logging.getLogger(__name__)

API_URL_TEMPLATE = "https://api.isitpayday.com/monthly?payday={days}&country={country}&timezone={tz}"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up binary sensor based on configuration."""
    country_id = entry.data.get(CONF_COUNTRY_ID, "DK")
    timezone = hass.config.time_zone

    async_add_entities([IsItPaydayBinarySensor(entry.entry_id, country_id, timezone)], True)

class IsItPaydayBinarySensor(BinarySensorEntity):
    """Represents an Is It Payday? sensor."""

    def __init__(self, entry_id, country_id, timezone):
        self._entry_id = entry_id
        self._state = False
        self._country_id = country_id
        self._timezone = timezone
        self._api_url = None
        self._attr_unique_id = "payday"
        self.entity_id = "binary_sensor.payday"

    @property
    def name(self):
        return "Is It Payday?"

    @property
    def is_on(self):
        return self._state

    @property
    def device_class(self):
        return None

    @property
    def icon(self):
        return "mdi:cash" if self._state else "mdi:cash-remove"

    @property
    def extra_state_attributes(self):
        return {"API-link": self._api_url} if self._api_url else {}

    @property
    def device_info(self) -> DeviceInfo:
        """Ensure all entities belong to the same device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name="Is It Payday?",
            manufacturer="IsItPayday API",
            model="Payday Checker",
            sw_version=VERSION,
            entry_type="service"
        )

    async def async_update(self):
        """Fetch data from the API on each polling cycle."""
        days_in_month = calendar.monthrange(datetime.now().year, datetime.now().month)[1]
        self._api_url = API_URL_TEMPLATE.format(days=days_in_month, country=self._country_id, tz=self._timezone)

        _LOGGER.debug(f"IsItPayday: Fetching data from {self._api_url}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self._api_url, timeout=10) as response:
                    if response.status != 200:
                        _LOGGER.error(f"IsItPayday: API error {response.status}")
                        return

                    data = await response.json()
                    _LOGGER.debug(f"IsItPayday: API response: {data}")
                    self._state = data.get("isPayDay", False)
        except aiohttp.ClientError as err:
            _LOGGER.error(f"IsItPayday: API request failed - {err}")
            self._state = False
