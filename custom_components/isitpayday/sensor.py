"""Sensor platform for IsItPayday."""

import logging
from datetime import date
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from .const import *

_LOGGER = logging.getLogger(__name__)

ICON = "mdi:calendar-clock"


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DataUpdateCoordinator = data["coordinator"]
    instance_name = data["name"]

    async_add_entities([IsItPaydayNextSensor(coordinator, instance_name)])


class IsItPaydayNextSensor(CoordinatorEntity, SensorEntity):
    _attr_device_class = None

    def __init__(self, coordinator: DataUpdateCoordinator, instance_name: str):
        super().__init__(coordinator)
        self._instance_name = instance_name
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_payday_next"
        self._attr_name = f"{self._instance_name} - Next Payday"
        self._attr_icon = ICON

    @property
    def state(self) -> str:
        payday = self.coordinator.data.get("payday_next")

        if not payday:
            return "Unknown"

        if isinstance(payday, date):
            return payday.strftime("%Y-%m-%d")

        try:
            payday_date = date.fromisoformat(payday)
            return payday_date.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return "Unknown"

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": self._instance_name,
            "manufacturer": CONF_MANUFACTURER,
            "model": CONF_MODEL,
        }
