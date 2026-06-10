import logging
from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    CONF_CONFIG_URL,
    DOMAIN,
    CONF_MANUFACTURER,
    CONF_MODEL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DataUpdateCoordinator = data["coordinator"]
    instance_name = data.get("name", "IsItPayday")

    async_add_entities(
        [IsItPaydayCalendar(coordinator, entry.entry_id, instance_name)]
    )


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

    def _get_payday(self) -> date | None:
        """Return the next payday from the coordinator as a date, or None."""
        payday = self.coordinator.data.get("payday_next")
        if not payday:
            return None
        if isinstance(payday, date):
            return payday
        try:
            return date.fromisoformat(payday)
        except (ValueError, TypeError):
            _LOGGER.warning("Invalid payday value in coordinator: %s", payday)
            return None

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
        payday = self._get_payday()
        if payday is None or payday < date.today():
            return None
        return self._build_event(payday)

    async def async_get_events(
        self,
        hass,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return payday events within the requested time window."""
        payday = self._get_payday()
        if payday is None:
            return []

        # Compare on dates since the payday event is all-day.
        if start_date.date() <= payday < end_date.date():
            return [self._build_event(payday)]

        return []

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._instance_name,
            "manufacturer": CONF_MANUFACTURER,
            "model": CONF_MODEL,
            "configuration_url": CONF_CONFIG_URL,
        }
