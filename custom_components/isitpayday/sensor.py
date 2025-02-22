import aiohttp
import logging
import calendar
from datetime import datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, CONF_COUNTRY, CONF_COUNTRY_ID, VERSION

_LOGGER = logging.getLogger(__name__)

API_URL_TEMPLATE = "https://api.isitpayday.com/monthly?payday={days}&country={country}&timezone={tz}"

class BaseIsItPaydaySensor(SensorEntity):
    """Baseklasse for alle sensorer, så de deler device_info."""

    def __init__(self, entry_id, unique_id, entity_id):
        self._entry_id = entry_id
        self._attr_unique_id = unique_id
        self.entity_id = entity_id

    @property
    def device_info(self) -> DeviceInfo:
        """Gør alle enheder til en del af samme device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name="Is It Payday?",
            manufacturer="IsItPayday API",
            model="Payday Checker",
            sw_version=VERSION,
            entry_type="service"
        )

class CountrySensor(BaseIsItPaydaySensor):
    """Sensor til at vise hvilket land der er valgt."""

    def __init__(self, entry_id, country_name):
        super().__init__(entry_id, "payday_country", "sensor.payday_country")
        self._state = country_name

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

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Opsæt sensorer baseret på konfiguration."""
    country_name = entry.data.get(CONF_COUNTRY, "Unknown")
    country_id = entry.data.get(CONF_COUNTRY_ID, "DK")
    timezone = hass.config.time_zone

    next_payday_sensor = NextPaydaySensor(entry.entry_id, country_id, timezone, hass)

    async_add_entities([
        next_payday_sensor,
        CountrySensor(entry.entry_id, country_name),
        TimezoneSensor(entry.entry_id, timezone)
    ], True)

    await next_payday_sensor.async_update()

class NextPaydaySensor(BaseIsItPaydaySensor):
    """Repræsenterer en Next Payday-sensor."""

    def __init__(self, entry_id, country_id, timezone, hass):
        super().__init__(entry_id, "payday_next", "sensor.payday_next")
        self._state = "Unknown"
        self._country_id = country_id
        self._timezone = timezone
        self._hass = hass

    @property
    def name(self):
        return "Next Payday"

    @property
    def state(self):
        """Returnerer næste payday som dato fra API'et."""
        return self._state

    @property
    def icon(self):
        return "mdi:cash-clock"

    async def async_update(self):
        """Henter data fra API ved hver polling."""
        days_in_month = calendar.monthrange(datetime.now().year, datetime.now().month)[1]
        url = API_URL_TEMPLATE.format(days=days_in_month, country=self._country_id, tz=self._timezone)

        _LOGGER.debug(f"NextPayday: Henter data fra {url}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        _LOGGER.error(f"NextPayday: API-fejl {response.status}")
                        return

                    data = await response.json()
                    _LOGGER.debug(f"NextPayday: API response: {data}")

                    next_payday_str = data.get("nextPayDay", None)
                    if next_payday_str:
                        self._state = next_payday_str.split("T")[0]  # Fjerner klokkeslæt
                        _LOGGER.info(f"NextPayday: Opdateret til {self._state}")
                    else:
                        self._state = "Unknown"
                        _LOGGER.warning("NextPayday: API returnerede ingen nextPayDay")
        except aiohttp.ClientError as err:
            _LOGGER.error(f"NextPayday: API-kald fejlede - {err}")
            self._state = "Unknown"

class TimezoneSensor(BaseIsItPaydaySensor):
    """Sensor til at vise hvilken tidszone der bliver brugt."""

    def __init__(self, entry_id, timezone):
        super().__init__(entry_id, "payday_timezone", "sensor.payday_timezone")
        self._state = timezone

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
