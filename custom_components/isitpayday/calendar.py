import logging
from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import CONF_CONFIG_URL, CONF_MANUFACTURER, CONF_MODEL, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DataUpdateCoordinator = data["coordinator"]
    instance_name = data.get("name", "IsItPayday")

    async_add_entities([IsItPaydayCalendar(coordinator, entry.entry_id, instance_name)])


class IsItPaydayCalendar(CoordinatorEntity, CalendarEntity):
    """Calendar entity exposing the next payday as an all-day event."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry_id: str,
        instance_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_payday_calendar"
        self._attr_name = f"{instance_name}: Payday"
        self._instance_name = instance_name
        self._entry_id = entry_id

    def _get_paydays(self) -> list[date]:
        """Return all upcoming paydays from the coordinator as dates."""
        data = self.coordinator.data or {}
        raw = data.get("paydays_upcoming")
        if not raw:
            # Fallback for older coordinator data with a single payday.
            single = data.get("payday_next")
            raw = [single] if single else []

        paydays: list[date] = []
        for value in raw:
            if isinstance(value, date):
                paydays.append(value)
                continue
            try:
                paydays.append(date.fromisoformat(value))
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid payday value in coordinator: %s", value)
        return sorted(paydays)

    def _build_event(self, payday: date) -> CalendarEvent:
        """Build an all-day CalendarEvent for the given payday.

        For all-day events, Home Assistant expects `start` and `end` as
        date objects, where `end` is exclusive (the day after).
        """
        return CalendarEvent(
            summary=f"{self._instance_name}: Payday",
            start=payday,
            end=payday + timedelta(days=1),
            description="Next payday calculated by the IsItPayday integration.",
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming payday event."""
        today = date.today()
        for payday in self._get_paydays():
            if payday >= today:
                return self._build_event(payday)
        return None

    async def async_get_events(
        self,
        hass,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return all payday events within the requested time window."""
        # Compare on dates since payday events are all-day.
        return [
            self._build_event(payday)
            for payday in self._get_paydays()
            if start_date.date() <= payday < end_date.date()
        ]

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._instance_name,
            "manufacturer": CONF_MANUFACTURER,
            "model": CONF_MODEL,
            "configuration_url": CONF_CONFIG_URL,
        }
