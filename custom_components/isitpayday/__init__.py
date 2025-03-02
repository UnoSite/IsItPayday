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
    """Setup via configuration.yaml - not used for this integration."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup IsItPayday instance from a config entry."""
    data = entry.data
    instance_name = entry.title  # Use entry.title for naming across the integration

    async def async_update_data():
        """Fetch and calculate next payday."""
        try:
            next_payday = await async_calculate_next_payday(
                data[CONF_COUNTRY],
                data[CONF_PAY_FREQ],
                data.get(CONF_PAY_DAY),
                data.get(CONF_LAST_PAY_DATE),
                data.get(CONF_WEEKDAY),
                data.get(CONF_BANK_OFFSET, 0)
            )
            return {"payday_next": next_payday}
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
        "name": instance_name  # Save the name for entity naming
    }

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        _LOGGER.error("Initial data could not be fetched for entry: %s", entry.entry_id)

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload IsItPayday instance."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "binary_sensor"])

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
