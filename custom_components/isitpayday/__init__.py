import logging
from datetime import date, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_COUNTRY,
    CONF_PAY_FREQ,
    CONF_PAY_DAY,
    CONF_LAST_PAY_DATE,
    CONF_WEEKDAY,
    CONF_BANK_OFFSET,
)
from .payday_calculator import async_calculate_next_payday

_LOGGER = logging.getLogger(__name__)

_PLATFORMS = ["sensor", "binary_sensor", "calendar"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = entry.data
    instance_name = data.get(CONF_NAME, "IsItPayday")

    last_known_payday: date | None = None

    async def async_update_data() -> dict:
        nonlocal last_known_payday
        today = date.today()

        try:
            # Only use the cached value if payday is strictly in the future.
            # On payday itself we recalculate so the sensors immediately
            # start counting towards the next payday.
            if isinstance(last_known_payday, date) and last_known_payday > today:
                return {"payday_next": last_known_payday}

            new_payday = await async_calculate_next_payday(
                data[CONF_COUNTRY],
                data[CONF_PAY_FREQ],
                data.get(CONF_PAY_DAY),
                data.get(CONF_LAST_PAY_DATE),
                data.get(CONF_WEEKDAY),
                data.get(CONF_BANK_OFFSET, 0),
            )

            last_known_payday = new_payday
            return {"payday_next": new_payday}

        except Exception as err:
            raise UpdateFailed(f"Error calculating next payday: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{instance_name} Coordinator ({entry.entry_id})",
        update_method=async_update_data,
        update_interval=timedelta(minutes=5),
    )

    # FIX #7 from review: use async_config_entry_first_refresh() so that a
    # failed initial update raises ConfigEntryNotReady and HA retries setup
    # automatically, instead of loading dead sensors.
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "name": instance_name,
    }

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
