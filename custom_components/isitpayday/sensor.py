import logging
from datetime import date

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    CONF_CONFIG_URL,
    CONF_MANUFACTURER,
    CONF_MODEL,
    DOMAIN,
    ICON_DAYS_TO,
    ICON_LAST_PAYDAY,
    ICON_NEXT_PAYDAY,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DataUpdateCoordinator = data["coordinator"]
    instance_name = data.get("name", "IsItPayday")

    async_add_entities(
        [
            IsItPaydayNextSensor(coordinator, entry.entry_id, instance_name),
            IsItPaydayDaysToSensor(coordinator, entry.entry_id, instance_name),
            IsItPaydayLastSensor(coordinator, entry.entry_id, instance_name),
        ]
    )


class IsItPaydayNextSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing the date of the next payday."""

    _attr_device_class = None

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry_id: str,
        instance_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_payday_next"
        self._attr_name = f"{instance_name}: Next payday"
        self._attr_icon = ICON_NEXT_PAYDAY
        self._instance_name = instance_name
        self._entry_id = entry_id

    @property
    def state(self) -> str:
        payday = self.coordinator.data.get("payday_next")
        if not payday:
            return "Unknown"

        today = date.today()

        if not isinstance(payday, date):
            try:
                payday = date.fromisoformat(payday)
            except (ValueError, TypeError):
                return "Unknown"

        if payday >= today:
            return payday.strftime("%Y-%m-%d")
        return "Unknown"

    @property
    def extra_state_attributes(self) -> dict:
        """Expose upcoming paydays and remaining paydays this month.

        `paydays_this_month` contains the remaining paydays (today or
        later) in the current calendar month - useful for automations in
        months with e.g. three biweekly payouts.
        """
        upcoming = self.coordinator.data.get("paydays_upcoming") or []
        today = date.today()

        upcoming_dates = [d for d in upcoming if isinstance(d, date)]
        this_month = [
            d for d in upcoming_dates if d.year == today.year and d.month == today.month
        ]

        return {
            "upcoming_paydays": [d.isoformat() for d in upcoming_dates],
            "paydays_this_month": [d.isoformat() for d in this_month],
            "paydays_this_month_count": len(this_month),
        }

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._instance_name,
            "manufacturer": CONF_MANUFACTURER,
            "model": CONF_MODEL,
            "configuration_url": CONF_CONFIG_URL,
        }


class IsItPaydayDaysToSensor(CoordinatorEntity, SensorEntity):
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
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_days_to"
        self._attr_name = f"{instance_name}: Days until"
        self._attr_icon = ICON_DAYS_TO
        self._instance_name = instance_name
        self._entry_id = entry_id

    @property
    def native_value(self) -> int | None:
        payday = self.coordinator.data.get("payday_next")
        if not payday:
            return None

        try:
            if isinstance(payday, str):
                payday = date.fromisoformat(payday)

            today = date.today()
            if payday <= today:
                return 0

            return (payday - today).days
        except Exception as e:
            _LOGGER.exception("Error calculating days to payday: %s", e)
            return None

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._instance_name,
            "manufacturer": CONF_MANUFACTURER,
            "model": CONF_MODEL,
            "configuration_url": CONF_CONFIG_URL,
        }


class IsItPaydayLastSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing the most recent payday on or before today."""

    _attr_device_class = None

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry_id: str,
        instance_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_payday_last"
        self._attr_name = f"{instance_name}: Last payday"
        self._attr_icon = ICON_LAST_PAYDAY
        self._instance_name = instance_name
        self._entry_id = entry_id

    @property
    def state(self) -> str:
        payday = self.coordinator.data.get("payday_last")
        if not payday:
            return "Unknown"

        if not isinstance(payday, date):
            try:
                payday = date.fromisoformat(payday)
            except (ValueError, TypeError):
                return "Unknown"

        return payday.strftime("%Y-%m-%d")

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._instance_name,
            "manufacturer": CONF_MANUFACTURER,
            "model": CONF_MODEL,
            "configuration_url": CONF_CONFIG_URL,
        }
