import logging
from datetime import date
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.config_entries import ConfigEntry
from .const import *

_LOGGER = logging.getLogger(__name__)

ICON_FALSE = "mdi:cash-clock"
ICON_TRUE = "mdi:cash-fast"


async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities):
    _LOGGER.debug("Setting up IsItPayday binary sensor for entry: %s", entry.entry_id)

    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    instance_name = entry.data.get(CONF_NAME, "IsItPayday")

    async_add_entities([IsItPaydaySensor(coordinator, entry, instance_name)])

    _LOGGER.info("IsItPayday binary sensor added for entry: %s", entry.entry_id)


class IsItPaydaySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry, instance_name: str):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_is_it_payday"
        self._attr_name = f"{instance_name} - Is It Payday"

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
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, f"isitpayday_{self._entry.entry_id}")},
            "name": self._entry.data.get(CONF_NAME, "IsItPayday"),
            "manufacturer": CONF_MANUFACTURER,
            "model": CONF_MODEL,
        }
