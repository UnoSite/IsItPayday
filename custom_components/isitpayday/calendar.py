import logging
from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import *

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DataUpdateCoordinator = data["coordinator"]
    instance_name = data.get("name", "IsItPayday")

    async_add_entities([
        IsItPaydayCalendar(coordinator, entry.entry_id, instance_name)
    ])


class IsItPaydayCalendar(CoordinatorEntity, CalendarEntity):
    def __init__(self, coordinator: DataUpdateCoordinator, entry_id: str, instance_name: str):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_calendar"
        self._attr_name = f"{instance_name}: Payday"
        self._instance_name = instance_name
        self._entry_id = entry_id

    @property
    def event(self) -> CalendarEvent | None:
        payday = self.coordinator.data.get("payday_next")
        if not payday:
            return None

        try:
            if isinstance(payday, str):
                payday = datetime.fromisoformat(payday).date()

            start = datetime.combine(payday, datetime.min.time())
            end = start + timedelta(days=1)

            return CalendarEvent(
                summary="Payday",
                start=start,
                end=end,
                all_day=True,
            )
        except Exception as e:
            _LOGGER.exception("Error creating calendar event: %s", e)
            return None

    async def async_get_events(self, hass, start_date, end_date):
        event = self.event
        if not event:
            return []

        if event.start.date() >= start_date.date() and event.start.date() <= end_date.date():
            return [event]

        return []

    @property
    def extra_state_attributes(self):
        return {
            "source": "IsItPayday Calendar",
            "raw_data": str(self.coordinator.data),
        }

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._instance_name,
            "manufacturer": CONF_MANUFACTURER,
            "model": CONF_MODEL,
                               }
