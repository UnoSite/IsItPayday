import logging
from datetime import date, datetime, time, timedelta
from functools import partial

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util
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
    EVENT_PAYDAY,
)
from .payday_calculator import (
    calculate_last_payday,
    calculate_upcoming_paydays,
    get_supported_countries,
)

_LOGGER = logging.getLogger(__name__)


def _normalize_pay_day(value):
    """Normalize pay_day from older config entries.

    Specific days may have been stored as strings (e.g. '31') by older
    versions; convert those to int. String options like 'last_bank_day'
    pass through unchanged.
    """
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return value


def _normalize_int(value, default: int) -> int:
    """Normalize an int setting that may have been stored as a string."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


_PLATFORMS = ["sensor", "binary_sensor", "calendar"]

# Tracks the scheduled "fire at midnight" callback per config entry.
_payday_event_unsubs: dict[str, object] = {}


@callback
def _fire_payday_event(hass, entry, instance_name: str, payday: date) -> None:
    """Fire the payday event on the HA event bus."""
    hass.bus.async_fire(
        EVENT_PAYDAY,
        {
            "entry_id": entry.entry_id,
            "name": instance_name,
            "date": payday.isoformat(),
        },
    )


async def _async_check_country_supported(hass, entry, country) -> None:
    """Create or clear a repair issue based on country support."""
    issue_id = f"unsupported_country_{entry.entry_id}"
    try:
        supported = await hass.async_add_executor_job(get_supported_countries)
    except Exception:  # pragma: no cover - defensive
        return

    if country and country not in supported:
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.ERROR,
            translation_key="unsupported_country",
            translation_placeholders={"country": str(country)},
        )
    else:
        ir.async_delete_issue(hass, DOMAIN, issue_id)


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
                    _normalize_pay_day(data.get(CONF_PAY_DAY)),
                    data.get(CONF_LAST_PAY_DATE),
                    data.get(CONF_WEEKDAY),
                    _normalize_int(data.get(CONF_BANK_OFFSET), 0),
                    data.get(CONF_SUBDIV),
                    12,
                )
            )

            last_payday = await hass.async_add_executor_job(
                partial(
                    calculate_last_payday,
                    data[CONF_COUNTRY],
                    data[CONF_PAY_FREQ],
                    _normalize_pay_day(data.get(CONF_PAY_DAY)),
                    data.get(CONF_LAST_PAY_DATE),
                    data.get(CONF_WEEKDAY),
                    _normalize_int(data.get(CONF_BANK_OFFSET), 0),
                    data.get(CONF_SUBDIV),
                )
            )

            result = {
                "payday_next": upcoming[0] if upcoming else None,
                "paydays_upcoming": upcoming,
                "payday_last": last_payday,
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

    # Raise a repair issue if the configured country is no longer supported
    # by the holidays package (e.g. removed in a later package version).
    await _async_check_country_supported(hass, entry, data.get(CONF_COUNTRY))

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "name": instance_name,
    }

    # Fire an event at midnight on each payday so automations can trigger
    # directly on the payday instead of watching the binary sensor.
    @callback
    def _schedule_payday_event(_now=None) -> None:
        unsub = _payday_event_unsubs.pop(entry.entry_id, None)
        if unsub:
            unsub()

        next_payday = coordinator.data.get("payday_next") if coordinator.data else None
        if not isinstance(next_payday, date):
            return

        fire_at = dt_util.as_utc(
            datetime.combine(next_payday, time(0, 0), tzinfo=dt_util.DEFAULT_TIME_ZONE)
        )
        if fire_at <= dt_util.utcnow():
            # Payday is today and midnight has passed; fire now.
            _fire_payday_event(hass, entry, instance_name, next_payday)
            return

        _payday_event_unsubs[entry.entry_id] = async_track_point_in_time(
            hass, _on_payday, fire_at
        )

    @callback
    def _on_payday(now) -> None:
        payday = coordinator.data.get("payday_next") if coordinator.data else None
        if isinstance(payday, date):
            _fire_payday_event(hass, entry, instance_name, payday)
        # Refresh so the coordinator advances to the following payday,
        # then reschedule for it.
        hass.async_create_task(coordinator.async_request_refresh())

    entry.async_on_unload(coordinator.async_add_listener(_schedule_payday_event))
    _schedule_payday_event()

    @callback
    def _cleanup_event() -> None:
        unsub = _payday_event_unsubs.pop(entry.entry_id, None)
        if unsub:
            unsub()

    entry.async_on_unload(_cleanup_event)

    # Reload automatically when the user saves new options.
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
