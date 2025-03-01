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
    """Set up via configuration.yaml - unused."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up IsItPayday from a config entry."""

    data = entry.data

    async def async_update_data():
        """Fetch and calculate next payday data."""
        _LOGGER.debug("Updating payday data for entry: %s", entry.entry_id)
        try:
            next_payday = await async_calculate_next_payday(
                data[CONF_COUNTRY],
                data[CONF_PAY_FREQ],
                data.get(CONF_PAY_DAY),
                data.get(CONF_LAST_PAY_DATE),
                data.get(CONF_WEEKDAY),
                data.get(CONF_BANK_OFFSET, 0)
            )

            _LOGGER.info("Calculated next payday: %s", next_payday)

            return {
                "payday_next": next_payday
            }

        except Exception as err:
            _LOGGER.error("Error calculating next payday: %s", err)
            raise UpdateFailed(f"Error calculating next payday: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="IsItPayday Coordinator",
        update_method=async_update_data,
        update_interval=timedelta(minutes=5),
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        _LOGGER.error("Initial data could not be fetched for entry: %s", entry.entry_id)

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])

    _LOGGER.info("IsItPayday setup complete for entry: %s", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload IsItPayday config entry."""
    _LOGGER.debug("Unloading entry: %s", entry.entry_id)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "binary_sensor"])

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.info("Unloaded entry: %s", entry.entry_id)

    return unload_ok
