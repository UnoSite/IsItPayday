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
    """Opsætning af binary sensor-platformen."""
    _LOGGER.debug("Setting up IsItPayday binary sensor for entry: %s", entry.entry_id)

    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities([IsItPaydaySensor(coordinator)])

    _LOGGER.info("IsItPayday binary sensor added for entry: %s", entry.entry_id)


class IsItPaydaySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor der viser om det er lønningsdag."""

    _attr_name = "Is It Payday"
    _attr_device_class = None

    def __init__(self, coordinator: DataUpdateCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "payday"

    @property
    def is_on(self) -> bool:
        """Returnerer True hvis i dag er lønningsdag."""
        if not self.coordinator.data:
            _LOGGER.warning("Coordinator data is missing or None.")
            return False

        payday_next = self.coordinator.data.get("payday_next")

        if not payday_next:
            _LOGGER.debug("No payday_next data available in coordinator.")
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
        """Returnerer ikon afhængigt af om det er lønningsdag."""
        return ICON_TRUE if self.is_on else ICON_FALSE

    @property
    def extra_state_attributes(self) -> dict:
        """Returnerer eventuelle ekstra attributter for debugging."""
        return {
            "source": "IsItPayday DataUpdateCoordinator",
            "raw_data": str(self.coordinator.data),
        }

    @property
    def device_info(self) -> dict:
        """Returnerer enhedsinfo for visning i Home Assistant."""
        return {
            "identifiers": {(DOMAIN, "isitpayday_device")},
            "name": "IsItPayday",
            "manufacturer": CONF_MANUFACTURER,
            "model": CONF_MODEL,
        }
