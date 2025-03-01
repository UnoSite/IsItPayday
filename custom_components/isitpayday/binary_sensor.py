"""Binary sensor platform for IsItPayday."""

import logging
from datetime import date
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import *

_LOGGER = logging.getLogger(__name__)

ICON_FALSE = "mdi:cash-clock"
ICON_TRUE = "mdi:cash-fast"


async def async_setup_entry(hass, entry, async_add_entities):
    """Opsaetning af binary sensor-platformen."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities([IsItPaydaySensor(coordinator)])


class IsItPaydaySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor der viser om det er loenningsdag."""

    _attr_name = "Is It Payday"
    _attr_device_class = None

    def __init__(self, coordinator):
        """Initialisering."""
        super().__init__(coordinator)
        self._attr_unique_id = "payday"

    @property
    def is_on(self):
        """Returnerer True hvis i dag er loenningsdag."""
        payday_next = self.coordinator.data.get("payday_next")

        if not payday_next:
            return False

        if isinstance(payday_next, date):
            return payday_next == date.today()

        try:
            payday_next_date = date.fromisoformat(payday_next)
            return payday_next_date == date.today()
        except (ValueError, TypeError):
            _LOGGER.error("Ugyldig datoformat for payday_next: %s", payday_next)
            return False

    @property
    def icon(self):
        """Returnerer ikon afhaengigt af om det er loenningsdag."""
        return ICON_TRUE if self.is_on else ICON_FALSE

    @property
    def device_info(self):
        """Returnerer device info saa den vises som enhed i Home Assistant."""
        return {
            "identifiers": {(DOMAIN, "isitpayday_device")},
            "name": "IsItPayday",
            "manufacturer": CONF_MANUFACTURER,
            "model": CONF_MODEL,
        }
