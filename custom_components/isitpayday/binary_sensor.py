"""Binary sensor platform for IsItPayday."""

import logging
from datetime import date
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import *

_LOGGER = logging.getLogger(__name__)

# Ikoner til visning af om det er lønningsdag eller ej
ICON_FALSE = "mdi:cash-clock"
ICON_TRUE = "mdi:cash-fast"


async def async_setup_entry(hass, entry, async_add_entities):
    """
    Opsætning af binary sensor-platformen.
    Henter coordinator fra hass.data og opretter sensoren.
    """
    _LOGGER.debug("Setting up IsItPayday binary sensor for entry: %s", entry.entry_id)

    # Henter coordinator (DataUpdateCoordinator) fra hass data
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    # Tilføjer binary sensor til Home Assistant
    async_add_entities([IsItPaydaySensor(coordinator)])

    _LOGGER.info("IsItPayday binary sensor added for entry: %s", entry.entry_id)


class IsItPaydaySensor(CoordinatorEntity, BinarySensorEntity):
    """
    Binary sensor der viser om det er lønningsdag.
    """

    _attr_name = "Is It Payday"
    _attr_device_class = None  # Ingen specifik device class

    def __init__(self, coordinator):
        """
        Initialisering af sensoren.
        """
        super().__init__(coordinator)
        self._attr_unique_id = "payday"

    @property
    def is_on(self):
        """
        Returnerer True hvis i dag er lønningsdag.
        """
        payday_next = self.coordinator.data.get("payday_next")

        if not payday_next:
            _LOGGER.debug("No payday_next data available in coordinator.")
            return False

        if isinstance(payday_next, date):
            return payday_next == date.today()

        try:
            # Håndterer dato som string (ISO-format)
            payday_next_date = date.fromisoformat(payday_next)
            return payday_next_date == date.today()
        except (ValueError, TypeError) as err:
            _LOGGER.error("Invalid date format for payday_next: %s (error: %s)", payday_next, err)
            return False

    @property
    def icon(self):
        """
        Returnerer ikon afhængigt af om det er lønningsdag.
        """
        return ICON_TRUE if self.is_on else ICON_FALSE

    @property
    def device_info(self):
        """
        Returnerer device info, så sensoren vises som en del af enheden i Home Assistant.
        """
        return {
            "identifiers": {(DOMAIN, "isitpayday_device")},
            "name": "IsItPayday",
            "manufacturer": CONF_MANUFACTURER,
            "model": CONF_MODEL,
        }
