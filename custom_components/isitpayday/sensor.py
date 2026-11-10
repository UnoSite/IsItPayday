import logging
from datetime import date

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import ICON_DAYS_TO, ICON_LAST_PAYDAY, ICON_NEXT_PAYDAY
from .entity import IsItPaydayEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    data = entry.runtime_data
    coordinator: DataUpdateCoordinator = data["coordinator"]
    instance_name = data.get("name", "IsItPayday")

    async_add_entities(
        [
            IsItPaydayNextSensor(coordinator, entry.entry_id, instance_name),
            IsItPaydayDaysToSensor(coordinator, entry.entry_id, instance_name),
            IsItPaydayLastSensor(coordinator, entry.entry_id, instance_name),
        ]
    )


class IsItPaydayNextSensor(IsItPaydayEntity, SensorEntity):
    """Sensor showing the date of the next payday."""

    _attr_device_class = SensorDeviceClass.DATE

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry_id: str,
        instance_name: str,
    ) -> None:
        super().__init__(coordinator, entry_id, instance_name)
        self._attr_unique_id = f"{entry_id}_payday_next"
        self._attr_name = f"{instance_name}: Next payday"
        self._attr_icon = ICON_NEXT_PAYDAY

    @property
    def native_value(self) -> date | None:
        payday = self.coordinator.data.get("payday_next")
        if not payday:
            return None

        if not isinstance(payday, date):
            try:
                payday = date.fromisoformat(payday)
            except (ValueError, TypeError):
                return None

        today = dt_util.now().date()
        return payday if payday >= today else None

    @property
    def extra_state_attributes(self) -> dict:
        """Expose upcoming paydays and remaining paydays this month.

        `paydays_this_month` contains the remaining paydays (today or
        later) in the current calendar month - useful for automations in
        months with e.g. three biweekly payouts.
        """
        upcoming = self.coordinator.data.get("paydays_upcoming") or []
        today = dt_util.now().date()

        upcoming_dates = [d for d in upcoming if isinstance(d, date)]
        this_month = [
            d for d in upcoming_dates if d.year == today.year and d.month == today.month
        ]

        return {
            "upcoming_paydays": [d.isoformat() for d in upcoming_dates],
            "paydays_this_month": [d.isoformat() for d in this_month],
            "paydays_this_month_count": len(this_month),
        }


class IsItPaydayDaysToSensor(IsItPaydayEntity, SensorEntity):
    """Sensor showing the number of days until the next payday."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "d"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry_id: str,
        instance_name: str,
    ) -> None:
        super().__init__(coordinator, entry_id, instance_name)
        self._attr_unique_id = f"{entry_id}_days_to"
        self._attr_name = f"{instance_name}: Days until"
        self._attr_icon = ICON_DAYS_TO

    @property
    def native_value(self) -> int | None:
        payday = self.coordinator.data.get("payday_next")
        if not payday:
            return None

        try:
            if isinstance(payday, str):
                payday = date.fromisoformat(payday)

            today = dt_util.now().date()
            if payday <= today:
                return 0

            return (payday - today).days
        except Exception as e:
            _LOGGER.exception("Error calculating days to payday: %s", e)
            return None


class IsItPaydayLastSensor(IsItPaydayEntity, SensorEntity):
    """Sensor showing the most recent payday on or before today."""

    _attr_device_class = SensorDeviceClass.DATE

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry_id: str,
        instance_name: str,
    ) -> None:
        super().__init__(coordinator, entry_id, instance_name)
        self._attr_unique_id = f"{entry_id}_payday_last"
        self._attr_name = f"{instance_name}: Last payday"
        self._attr_icon = ICON_LAST_PAYDAY

    @property
    def native_value(self) -> date | None:
        payday = self.coordinator.data.get("payday_last")
        if not payday:
            return None

        if not isinstance(payday, date):
            try:
                payday = date.fromisoformat(payday)
            except (ValueError, TypeError):
                return None

        return payday
