from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN, VERSION

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Opsætning af integrationen."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Opsæt integrationen via config flow."""
    hass.data.setdefault(DOMAIN, {})

    # Opdater versionen korrekt
    if entry.version != VERSION:
        hass.config_entries.async_update_entry(entry, version=VERSION)

    # Brug den nye metode 'await async_forward_entry_setups'
    await hass.config_entries.async_forward_entry_setups(entry, ["binary_sensor", "sensor"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Fjern integrationen korrekt uden fejl."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "binary_sensor")
    unload_ok &= await hass.config_entries.async_forward_entry_unload(entry, "sensor")

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok

async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Håndter migrering af konfigurationsdata."""
    if entry.version != VERSION:
        hass.config_entries.async_update_entry(entry, version=VERSION)
    return True
