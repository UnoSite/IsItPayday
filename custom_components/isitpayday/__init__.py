"""Initialization file for the IsItPayday integration."""

import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.typing import ConfigType

from .const import *
from .payday_calculator import async_calculate_next_payday

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """
    Setup via configuration.yaml - unused for this integration.
    Required for Home Assistant to load the integration.
    """
    _LOGGER.debug("async_setup called - no YAML configuration used.")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Setup IsItPayday integration from a config entry.

    Initializes the DataUpdateCoordinator which handles periodic data fetching and updates.
    """
    _LOGGER.info("Setting up IsItPayday entry: %s", entry.entry_id)

    data = entry.data

    async def async_update_data():
        """
        Fetch and calculate next payday data.

        This method will be called periodically by the DataUpdateCoordinator.
        """
        _LOGGER.debug("Updating payday data for entry: %s", entry.entry_id)

        try:
            # Log the configuration used for calculation (for debugging purposes)
            _LOGGER.debug(
                "Calculating next payday with country=%s, frequency=%s, pay_day=%s, "
                "last_pay_date=%s, weekday=%s, bank_offset=%d",
                data.get(CONF_COUNTRY),
                data.get(CONF_PAY_FREQ),
                data.get(CONF_PAY_DAY),
                data.get(CONF_LAST_PAY_DATE),
                data.get(CONF_WEEKDAY),
                data.get(CONF_BANK_OFFSET, 0),
            )

            # Beregn næste lønningsdag baseret på konfigurationsdata
            next_payday = await async_calculate_next_payday(
                data[CONF_COUNTRY],
                data[CONF_PAY_FREQ],
                data.get(CONF_PAY_DAY),
                data.get(CONF_LAST_PAY_DATE),
                data.get(CONF_WEEKDAY),
                data.get(CONF_BANK_OFFSET, 0)
            )

            _LOGGER.info("Calculated next payday for entry %s: %s", entry.entry_id, next_payday)

            # Returnerer data i et format som sensorer og binary sensorer kan bruge
            return {"payday_next": next_payday}

        except Exception as err:
            _LOGGER.exception("Error calculating next payday for entry %s: %s", entry.entry_id, err)
            raise UpdateFailed(f"Error calculating next payday: {err}") from err

    # Opretter DataUpdateCoordinator til at håndtere periodiske opdateringer
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"IsItPayday Coordinator ({entry.entry_id})",
        update_method=async_update_data,
        update_interval=timedelta(minutes=5),  # Opdaterer hver 5. minut
    )

    # Gemmer coordinatoren i Home Assistants data-lager
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    _LOGGER.debug("Initial data fetch starting for entry: %s", entry.entry_id)

    # Henter initial data
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        _LOGGER.error("Initial data could not be fetched for entry: %s", entry.entry_id)

    # Videregiver entry til sensor og binary_sensor platformene
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])

    _LOGGER.info("IsItPayday setup complete for entry: %s", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Unload IsItPayday config entry.

    Cleans up all data related to the entry and removes sensors/binary_sensors.
    """
    _LOGGER.debug("Unloading IsItPayday entry: %s", entry.entry_id)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "binary_sensor"])

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        _LOGGER.info("Successfully unloaded entry: %s", entry.entry_id)

    return unload_ok
