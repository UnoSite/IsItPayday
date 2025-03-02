"""Binary sensor platform for IsItPayday."""

import logging
from datetime import date
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from .const import *

_LOGGER = logging.getLogger(__name__)

ICON_FALSE = "mdi:cash-clock"
ICON_TRUE = "mdi:cash-fast"


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DataUpdateCoordinator = data["coordinator"]
    instance_name = data["name"]

    async_add_entities([IsItPaydaySensor(coordinator, instance_name)])


class IsItPaydaySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_device_class = None

    def __init__(self, coordinator: DataUpdateCoordinator, instance_name: str):
        super().__init__(coordinator)
        self._instance_name = instance_name
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_is_it_payday"
        self._attr_name = f"{self._instance_name} - Is It Payday"

    @property
    def is_on(self) -> bool:
        payday_next = self.coordinator.data.get("payday_next")

        if not payday_next:
            return False

        today = date.today()

        if isinstance(payday_next, date):
            return payday_next == today

        try:
            payday_next_date = date.fromisoformat(payday_next)
            return payday_next_date == today
        except (ValueError, TypeError):
            return False

    @property
    def icon(self) -> str:
        return ICON_TRUE if self.is_on else ICON_FALSE

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": self._instance_name,
            "manufacturer": CONF_MANUFACTURER,
            "model": CONF_MODEL,
        }
