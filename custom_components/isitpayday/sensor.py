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
    instance_name = data.get("name", "IsItPayday")

    async_add_entities([IsItPaydayNextSensor(coordinator, entry.entry_id, instance_name)])


class IsItPaydayNextSensor(CoordinatorEntity, SensorEntity):
    _attr_device_class = None

    def __init__(self, coordinator: DataUpdateCoordinator, entry_id: str, instance_name: str):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_payday_next"
        self._attr_name = f"{instance_name} Next Payday"
        self._attr_icon = ICON
        self._instance_name = instance_name
        self._entry_id = entry_id

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
    def extra_state_attributes(self) -> dict:
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
