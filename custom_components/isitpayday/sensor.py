"""Sensor platform for IsItPayday."""

import logging
from datetime import date
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from .const import *

_LOGGER = logging.getLogger(__name__)

ICON = "mdi:calendar-clock"


async def async_setup_entry(hass, entry, async_add_entities):
    """Opsætning af sensor-platformen."""
    _LOGGER.debug("Setting up IsItPayday sensor for entry: %s", entry.entry_id)

    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DataUpdateCoordinator = data["coordinator"]
    instance_name = data.get("name", "IsItPayday")

    async_add_entities([IsItPaydayNextSensor(coordinator, instance_name)])

    _LOGGER.info("IsItPayday sensor added for entry: %s", entry.entry_id)


class IsItPaydayNextSensor(CoordinatorEntity, SensorEntity):
    """Sensor der viser datoen for næste lønningsdag."""

    _attr_device_class = None

    def __init__(self, coordinator: DataUpdateCoordinator, instance_name: str):
        super().__init__(coordinator)
        self._attr_unique_id = f"{instance_name}_payday_next"
        self._attr_name = f"{instance_name} - Next Payday"
        self._attr_icon = ICON

    @property
    def state(self) -> str:
        """Returnerer datoen for næste lønningsdag i format YYYY-MM-DD."""
        payday = self.coordinator.data.get("payday_next")

        if not payday:
            _LOGGER.warning("Ingen payday_next data tilgængelig.")
            return "Unknown"

        if isinstance(payday, date):
            return payday.strftime("%Y-%m-%d")

        try:
            payday_date = date.fromisoformat(payday)
            return payday_date.strftime("%Y-%m-%d")
        except (ValueError, TypeError) as err:
            _LOGGER.error("Payday data har ugyldigt format: %s (error: %s)", payday, err)
            return "Unknown"

    @property
    def extra_state_attributes(self) -> dict:
        """Returnerer ekstra attributter for debugging."""
        return {
            "source": "IsItPayday DataUpdateCoordinator",
            "raw_data": str(self.coordinator.data),
        }

    @property
    def device_info(self) -> dict:
    	"""Return device information so both entities are grouped under the same device."""
    	return {
        	"identifiers": {(DOMAIN, f"isitpayday_{self.coordinator.config_entry.entry_id}")},
        	"name": self.coordinator.config_entry.data.get(CONF_NAME, "IsItPayday"),
        	"manufacturer": CONF_MANUFACTURER,
        	"model": CONF_MODEL,
    	}
