"""Diagnostics support for the IsItPayday integration."""

from datetime import date

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_NAME

# The instance name may contain personal information (e.g. a person's name).
TO_REDACT = {CONF_NAME}


def _serialize(value):
    """Recursively convert date objects to ISO strings for JSON output."""
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """Return diagnostics for a config entry."""
    info = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator = info.get("coordinator")

    return {
        "entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
        },
        "coordinator": {
            "data": _serialize(dict(coordinator.data))
            if coordinator and coordinator.data
            else None,
            "last_update_success": coordinator.last_update_success
            if coordinator
            else None,
        },
    }
