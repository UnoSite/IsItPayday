import logging
from datetime import date, timedelta
from functools import partial

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
    CONF_SUBDIV,
)
from .payday_calculator import calculate_upcoming_paydays

_LOGGER = logging.getLogger(__name__)

_PLATFORMS = ["sensor", "binary_sensor", "calendar"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration when options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Options (from the options flow) take precedence over the original
    # setup data, so changed settings apply without touching entry.data.
    data = {**entry.data, **entry.options}
    instance_name = data.get(CONF_NAME, "IsItPayday")

    last_data: dict | None = None

    async def async_update_data() -> dict:
        nonlocal last_data
        today = date.today()

        try:
            # Only use the cached result if the next payday is strictly in
            # the future. On payday itself we recalculate so the sensors
            # immediately start counting towards the next payday.
            if last_data:
                first = last_data.get("payday_next")
                if isinstance(first, date) and first > today:
                    return last_data

            # The holidays package is synchronous, so the calculation runs
            # in an executor to avoid blocking the event loop.
            upcoming = await hass.async_add_executor_job(
                partial(
                    calculate_upcoming_paydays,
                    data[CONF_COUNTRY],
                    data[CONF_PAY_FREQ],
                    data.get(CONF_PAY_DAY),
                    data.get(CONF_LAST_PAY_DATE),
                    data.get(CONF_WEEKDAY),
                    data.get(CONF_BANK_OFFSET, 0),
                    data.get(CONF_SUBDIV),
                    12,
                )
            )

            result = {
                "payday_next": upcoming[0] if upcoming else None,
                "paydays_upcoming": upcoming,
            }
            last_data = result if upcoming else None
            return result

        except Exception as err:
            raise UpdateFailed(f"Error calculating next payday: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{instance_name} Coordinator ({entry.entry_id})",
        update_method=async_update_data,
        update_interval=timedelta(minutes=5),
    )

    # A failed initial update raises ConfigEntryNotReady and HA retries
    # setup automatically, instead of loading dead sensors.
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "name": instance_name,
    }

    # Reload automatically when the user saves new options.
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
