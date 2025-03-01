"""Sensor platform for IsItPayday."""

import logging
from datetime import date
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import *

_LOGGER = logging.getLogger(__name__)

ICON = "mdi:calendar-clock"


async def async_setup_entry(hass, entry, async_add_entities):
    """Opsaetning af sensor-platformen."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities([IsItPaydayNextSensor(coordinator)])


class IsItPaydayNextSensor(CoordinatorEntity, SensorEntity):
    """Sensor der viser naeste loenningsdag."""

    _attr_name = "Next Payday"
    _attr_icon = ICON
    _attr_device_class = None

    def __init__(self, coordinator):
        """Initialisering."""
        super().__init__(coordinator)
        self._attr_unique_id = "payday_next"

    @property
    def state(self):
        """Returnerer dato for naeste loenningsdag."""
        payday = self.coordinator.data.get("payday_next")

        if payday:
            if isinstance(payday, date):
                return payday.strftime("%Y-%m-%d")

            try:
                payday_date = date.fromisoformat(payday)
                return payday_date.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                _LOGGER.error("Payday data har ugyldigt format: %s", payday)
                return "Unknown"

        return "Unknown"

    @property
    def device_info(self):
        """Returnerer device info saa den vises som enhed i Home Assistant."""
        return {
            "identifiers": {(DOMAIN, "isitpayday_device")},
            "name": "IsItPayday",
            "manufacturer": CONF_MANUFACTURER,
            "model": CONF_MODEL,
        }
