import logging
from datetime import date

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import *

_LOGGER = logging.getLogger(__name__)

ICON_FALSE = "mdi:cash-clock"
ICON_TRUE = "mdi:cash-fast"


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DataUpdateCoordinator = data["coordinator"]
    instance_name = data.get("name", "IsItPayday")

    async_add_entities([IsItPaydaySensor(coordinator, entry.entry_id, instance_name)])


class IsItPaydaySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_device_class = None

    def __init__(
        self, coordinator: DataUpdateCoordinator, entry_id: str, instance_name: str
    ):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_is_it_payday"
        self._attr_name = f"{instance_name}: Is it payday"
        self._instance_name = instance_name
        self._entry_id = entry_id

    @property
    def is_on(self) -> bool:
        payday_next = self.coordinator.data.get("payday_next")
        if not payday_next:
            return False

        today = date.today()
        if isinstance(payday_next, date):
            return payday_next == today
        try:
            return date.fromisoformat(payday_next) == today
        except (ValueError, TypeError):
            return False

    @property
    def icon(self) -> str:
        return ICON_TRUE if self.is_on else ICON_FALSE

    @property
    def extra_state_attributes(self):
        return {
            "source": "IsItPayday DataUpdateCoordinator",
            "raw_data": str(self.coordinator.data),
        }

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._instance_name,
            "manufacturer": CONF_MANUFACTURER,
            "model": CONF_MODEL,
        }
