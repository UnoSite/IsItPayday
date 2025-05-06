import logging
from datetime import date, timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.typing import ConfigType

from .const import *
from .payday_calculator import async_calculate_next_payday

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = entry.data
    instance_name = data.get(CONF_NAME, "IsItPayday")

    last_known_payday = None

    async def async_update_data():
        nonlocal last_known_payday
        today = date.today()

        try:
            if last_known_payday and isinstance(last_known_payday, date):
                if last_known_payday >= today:
                    return {"payday_next": last_known_payday}

            new_payday = await async_calculate_next_payday(
                data[CONF_COUNTRY],
                data[CONF_PAY_FREQ],
                data.get(CONF_PAY_DAY),
                data.get(CONF_LAST_PAY_DATE),
                data.get(CONF_WEEKDAY),
                data.get(CONF_BANK_OFFSET, 0)
            )

            last_known_payday = new_payday
            return {"payday_next": new_payday}

        except Exception as err:
            raise UpdateFailed(f"Error calculating next payday: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{instance_name} Coordinator ({entry.entry_id})",
        update_method=async_update_data,
        update_interval=timedelta(minutes=5),
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "name": instance_name
    }

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        _LOGGER.error("Initial data could not be fetched for entry: %s", entry.entry_id)

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "binary_sensor"])

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
