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
    """Setup IsItPayday binary sensor."""
    _LOGGER.debug("Setting up IsItPayday binary sensor for entry: %s", entry.entry_id)

    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    instance_name = data.get("name", entry.title)

    async_add_entities([IsItPaydaySensor(coordinator, instance_name)])

    _LOGGER.info("IsItPayday binary sensor added for entry: %s", entry.entry_id)

class IsItPaydaySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor that shows if it's payday."""

    _attr_device_class = None

    def __init__(self, coordinator: DataUpdateCoordinator, instance_name: str):
        super().__init__(coordinator)
        self._attr_unique_id = f"{instance_name.lower().replace(' ', '_')}_is_it_payday"
        self._attr_name = f"{instance_name} - Is It Payday"

    @property
    def is_on(self) -> bool:
        """Return true if today is payday."""
        if not self.coordinator.data:
            _LOGGER.warning("Coordinator data is missing or None.")
            return False

        payday_next = self.coordinator.data.get("payday_next")

        if not payday_next:
            _LOGGER.debug("No payday_next data available.")
            return False

        today = date.today()

        if isinstance(payday_next, date):
            is_payday = payday_next == today
        else:
            try:
                payday_next_date = date.fromisoformat(payday_next)
                is_payday = payday_next_date == today
            except (ValueError, TypeError) as err:
                _LOGGER.error("Invalid date format for payday_next: %s (error: %s)", payday_next, err)
                return False

        _LOGGER.debug("Payday check: today=%s, next_payday=%s, is_payday=%s", today, payday_next, is_payday)
        return is_payday

    @property
    def icon(self) -> str:
        """Return appropriate icon."""
        return ICON_TRUE if self.is_on else ICON_FALSE

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes for debugging."""
        return {
            "source": "IsItPayday DataUpdateCoordinator",
            "raw_data": str(self.coordinator.data),
        }

    @property
    def device_info(self) -> dict:
        """Link the entity to the device."""
        return {
            "identifiers": {(DOMAIN, f"isitpayday_{self.coordinator.config_entry.entry_id}")},
            "name": self.coordinator.config_entry.title,
            "manufacturer": CONF_MANUFACTURER,
            "model": CONF_MODEL,
        }
