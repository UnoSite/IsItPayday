import logging
from datetime import date, datetime, time, timedelta
from functools import partial

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_BANK_OFFSET,
    CONF_COUNTRY,
    CONF_EVENT_TIME,
    CONF_LAST_PAY_DATE,
    CONF_NAME,
    CONF_PAY_DAY,
    CONF_PAY_FREQ,
    CONF_SUBDIV,
    CONF_WEEKDAY,
    DEFAULT_EVENT_TIME,
    DOMAIN,
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


def _parse_event_time(value) -> time:
    """Parse a stored 'HH:MM:SS' (or 'HH:MM') string into a time object.

    Falls back to the default event time if the value is missing or invalid.
    """
    if not value:
        value = DEFAULT_EVENT_TIME
    try:
        parts = [int(p) for p in str(value).split(":")]
        while len(parts) < 3:
            parts.append(0)
        return time(parts[0], parts[1], parts[2])
    except (ValueError, IndexError):
        _LOGGER.warning(
            "Invalid event_time %r, falling back to %s", value, DEFAULT_EVENT_TIME
        )
        h, m, s = (int(p) for p in DEFAULT_EVENT_TIME.split(":"))
        return time(h, m, s)


_PLATFORMS = ["sensor", "binary_sensor", "calendar"]


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
    except Exception:
        _LOGGER.exception(
            "Could not determine supported countries; skipping the "
            "unsupported-country repair check for this refresh"
        )
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
    event_time = _parse_event_time(data.get(CONF_EVENT_TIME))

    last_data: dict | None = None

    async def async_update_data() -> dict:
        nonlocal last_data
        # Use HA's configured time zone rather than the host system clock,
        # which may run in a different zone (e.g. UTC in a container).
        today = dt_util.now().date()

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
                    today,
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
                    today,
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
        # Paydays only change once per day and the exact payday moment is
        # already handled precisely by the scheduled timer below; this
        # periodic refresh is just a fallback (e.g. after a restart that
        # missed the timer), so it does not need to run every few minutes.
        update_interval=timedelta(hours=1),
    )

    # A failed initial update raises ConfigEntryNotReady and HA retries
    # setup automatically, instead of loading dead sensors.
    await coordinator.async_config_entry_first_refresh()

    # Raise a repair issue if the configured country is no longer supported
    # by the holidays package (e.g. removed in a later package version).
    await _async_check_country_supported(hass, entry, data.get(CONF_COUNTRY))

    # Per-entry runtime state (not persisted): the scheduled "fire at
    # event_time" callback unsub, and the last payday date we already fired
    # the event for (so coordinator refreshes during the day do not fire it
    # repeatedly).
    entry.runtime_data = {
        "coordinator": coordinator,
        "name": instance_name,
        "event_unsub": None,
        "last_fired": None,
    }

    # Fire an event at the configured local time on each payday so
    # automations can trigger directly on the payday instead of watching
    # the binary sensor.
    #
    # The event must fire exactly once per payday. The coordinator refreshes
    # periodically, so we guard with the last date we already fired for
    # and (re)schedule a single timer for the next payday's event time.
    def _payday_fire_time(payday: date) -> datetime:
        """Return the UTC datetime at which to fire for a given payday."""
        local = datetime.combine(
            payday,
            event_time,
            tzinfo=dt_util.DEFAULT_TIME_ZONE,
        )
        return dt_util.as_utc(local)

    @callback
    def _schedule_payday_event(_now=None) -> None:
        next_payday = coordinator.data.get("payday_next") if coordinator.data else None
        if not isinstance(next_payday, date):
            return

        already_fired = entry.runtime_data["last_fired"]
        now = dt_util.utcnow()
        fire_at = _payday_fire_time(next_payday)

        # Payday is today (or earlier) and the event time has already passed.
        if fire_at <= now:
            # Only fire if we have not already fired for this exact date.
            if already_fired != next_payday:
                entry.runtime_data["last_fired"] = next_payday
                _fire_payday_event(hass, entry, instance_name, next_payday)
                # Advance the coordinator to the following payday.
                hass.async_create_task(coordinator.async_request_refresh())
            return

        # Otherwise schedule a single timer for the event time on the payday.
        # Cancel any existing timer first so we never stack multiple timers.
        unsub = entry.runtime_data["event_unsub"]
        if unsub:
            unsub()
        entry.runtime_data["event_unsub"] = async_track_point_in_time(
            hass, _on_payday, fire_at
        )

    @callback
    def _on_payday(now) -> None:
        entry.runtime_data["event_unsub"] = None
        payday = coordinator.data.get("payday_next") if coordinator.data else None
        if (
            isinstance(payday, date)
            and entry.runtime_data["last_fired"] != payday
        ):
            entry.runtime_data["last_fired"] = payday
            _fire_payday_event(hass, entry, instance_name, payday)
        # Refresh so the coordinator advances to the following payday,
        # then reschedule for it.
        hass.async_create_task(coordinator.async_request_refresh())

    entry.async_on_unload(coordinator.async_add_listener(_schedule_payday_event))
    _schedule_payday_event()

    @callback
    def _cleanup_event() -> None:
        unsub = entry.runtime_data["event_unsub"]
        if unsub:
            unsub()
        entry.runtime_data["event_unsub"] = None
        entry.runtime_data["last_fired"] = None

    entry.async_on_unload(_cleanup_event)

    # Reload automatically when the user saves new options.
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
