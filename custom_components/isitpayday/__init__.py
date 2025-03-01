"""Initialization file for the IsItPayday integration."""

import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import *
from .payday_calculator import async_calculate_next_payday

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = entry.data

    async def async_update_data():
        try:
            weekday = data.get(CONF_WEEKDAY)
            if data[CONF_PAY_FREQ] == PAY_FREQ_WEEKLY and weekday is None:
                raise ValueError("Weekly frequency requires weekday to be set.")

            next_payday = await async_calculate_next_payday(
                data[CONF_COUNTRY],
                data[CONF_PAY_FREQ],
                data.get(CONF_PAY_DAY),
                data.get(CONF_LAST_PAY_DATE),
                weekday,
                data.get(CONF_BANK_OFFSET, 0)
            )

            return {"payday_next": next_payday}
        except Exception as err:
            raise UpdateFailed(f"Error calculating next payday: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="IsItPayday Coordinator",
        update_method=async_update_data,
        update_interval=timedelta(minutes=5),
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"coordinator": coordinator}

    await coordinator.async_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])

    return True
