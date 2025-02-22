"""Is It Payday? integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Is It Payday? from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry

    session = async_get_clientsession(hass)
    hass.data[DOMAIN][f"{entry.entry_id}_session"] = session

    hass.config_entries.async_setup_platforms(entry, ["sensor"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Is It Payday? config entry."""
    if f"{entry.entry_id}_session" in hass.data[DOMAIN]:
        del hass.data[DOMAIN][f"{entry.entry_id}_session"]

    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])
