import logging
from datetime import date
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.config_entries import ConfigEntry
from .const import *

_LOGGER = logging.getLogger(__name__)

ICON = "mdi:calendar-clock"


async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities):
    _LOGGER.debug("Setting up IsItPayday sensor for entry: %s", entry.entry_id)

    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    instance_name = entry.data.get(CONF_NAME, "IsItPayday")

    async_add_entities([IsItPaydayNextSensor(coordinator, entry, instance_name)])

    _LOGGER.info("IsItPayday sensor added for entry: %s", entry.entry_id)


class IsItPaydayNextSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry, instance_name: str):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_payday_next"
        self._attr_name = f"{instance_name} - Next Payday"
        self._attr_icon = ICON

    @property
    def state(self) -> str:
        payday = self.coordinator.data.get("payday_next")

        if not payday:
            return "Unknown"

        if isinstance(payday, date):
            return payday.strftime("%Y-%m-%d")

        try:
            return date.fromisoformat(payday).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return "Unknown"

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, f"isitpayday_{self._entry.entry_id}")},
            "name": self._entry.data.get(CONF_NAME, "IsItPayday"),
            "manufacturer": CONF_MANUFACTURER,
            "model": CONF_MODEL,
        }
