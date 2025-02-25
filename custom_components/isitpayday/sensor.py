import aiohttp
import logging
import calendar
from datetime import datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, CONF_COUNTRY, CONF_COUNTRY_ID, CONF_PAYDAY_TYPE, CONF_CUSTOM_DAY, VERSION

_LOGGER = logging.getLogger(__name__)

API_URL_TEMPLATE = "https://api.isitpayday.com/monthly?payday={day}&country={country}&timezone={tz}"

PAYDAY_TYPE_MAPPING = {
    "last_day": "Last day of the month",
    "first_day": "First day of the month",
    "custom_day": "Custom day of the month"
}

class BaseIsItPaydaySensor(SensorEntity):
    """Base class for all sensors, ensuring they share device_info and API attribute."""

    def __init__(self, entry_id, unique_id, entity_id):
        self._entry_id = entry_id
        self._attr_unique_id = unique_id
        self.entity_id = entity_id
        self._api_url = None  # API-link attribute

    @property
    def extra_state_attributes(self):
        """Return API-link as an attribute for all sensors."""
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

class CountrySensor(BaseIsItPaydaySensor):
    """Sensor to display the selected country."""

    def __init__(self, entry_id, country_name, api_url):
        super().__init__(entry_id, "payday_country", "sensor.payday_country")
        self._state = country_name
        self._api_url = api_url

    @property
    def name(self):
        return "Country"

    @property
    def state(self):
        return self._state

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC

    @property
    def icon(self):
        return "mdi:flag"

class PaydayTypeSensor(BaseIsItPaydaySensor):
    """Sensor to display the selected payday type in a user-friendly format."""

    def __init__(self, entry_id, payday_type, custom_day, api_url):
        super().__init__(entry_id, "payday_type", "sensor.payday_type")
        self._payday_type = payday_type
        self._custom_day = custom_day
        self._api_url = api_url

    @property
    def name(self):
        return "Payday Type"

    @property
    def state(self):
        """Return a human-readable payday type."""
        if self._payday_type == "custom_day" and self._custom_day:
            return f"Custom day: {self._custom_day}"
        return PAYDAY_TYPE_MAPPING.get(self._payday_type, "Unknown")

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC

    @property
    def icon(self):
        return "mdi:calendar"

class TimezoneSensor(BaseIsItPaydaySensor):
    """Sensor to display the timezone being used."""

    def __init__(self, entry_id, timezone, api_url):
        super().__init__(entry_id, "payday_timezone", "sensor.payday_timezone")
        self._state = timezone
        self._api_url = api_url

    @property
    def name(self):
        return "Timezone"

    @property
    def state(self):
        return self._state

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC

    @property
    def icon(self):
        return "mdi:earth"

class NextPaydaySensor(BaseIsItPaydaySensor):
    """Represents a Next Payday sensor."""

    def __init__(self, entry_id, country_id, payday_type, custom_day, timezone, hass):
        super().__init__(entry_id, "payday_next", "sensor.payday_next")
        self._state = "Unknown"
        self._country_id = country_id
        self._payday_type = payday_type
        self._custom_day = custom_day
        self._timezone = timezone
        self._hass = hass
        self._api_url = None

    @property
    def name(self):
        return "Next Payday"

    @property
    def state(self):
        """Return the next payday as a date from the API."""
        return self._state

    @property
    def icon(self):
        return "mdi:cash-clock"

    async def async_update(self):
        """Fetch data from the API on each polling cycle."""
        today = datetime.now()

        if self._payday_type == "last_day":
            payday_day = calendar.monthrange(today.year, today.month)[1]
        elif self._payday_type == "first_day":
            payday_day = 1
        elif self._payday_type == "custom_day" and self._custom_day:
            payday_day = min(self._custom_day, calendar.monthrange(today.year, today.month)[1])
        else:
            payday_day = calendar.monthrange(today.year, today.month)[1]  # Default to last day

        self._api_url = API_URL_TEMPLATE.format(day=payday_day, country=self._country_id, tz=self._timezone)

        _LOGGER.debug(f"NextPayday: Fetching data from {self._api_url}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self._api_url, timeout=10) as response:
                    if response.status != 200:
                        _LOGGER.error(f"NextPayday: API error {response.status}")
                        return

                    data = await response.json()
                    _LOGGER.debug(f"NextPayday: API response: {data}")

                    next_payday_str = data.get("nextPayDay", None)
                    if next_payday_str:
                        self._state = next_payday_str.split("T")[0]  # Remove time part
                        _LOGGER.info(f"NextPayday: Updated to {self._state}")
                    else:
                        self._state = "Unknown"
                        _LOGGER.warning("NextPayday: API returned no nextPayDay")
        except aiohttp.ClientError as err:
            _LOGGER.error(f"NextPayday: API request failed - {err}")
            self._state = "Unknown"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up sensors based on configuration."""
    country_name = entry.data.get(CONF_COUNTRY, "Unknown")
    country_id = entry.data.get(CONF_COUNTRY_ID, "DK")
    payday_type = entry.data.get(CONF_PAYDAY_TYPE, "last_day")
    custom_day = entry.data.get(CONF_CUSTOM_DAY, None)
    timezone = hass.config.time_zone

    # Generate API URL
    today = datetime.now()
    payday_day = (
        custom_day if payday_type == "custom_day" else
        (1 if payday_type == "first_day" else calendar.monthrange(today.year, today.month)[1])
    )
    api_url = API_URL_TEMPLATE.format(day=payday_day, country=country_id, tz=timezone)

    next_payday_sensor = NextPaydaySensor(entry.entry_id, country_id, payday_type, custom_day, timezone, hass)

    async_add_entities([
        next_payday_sensor,
        CountrySensor(entry.entry_id, country_name, api_url),
        TimezoneSensor(entry.entry_id, timezone, api_url),
        PaydayTypeSensor(entry.entry_id, payday_type, custom_day, api_url)
    ], True)

    await next_payday_sensor.async_update()
