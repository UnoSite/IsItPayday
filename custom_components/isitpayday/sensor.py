import logging
from datetime import date, datetime, timedelta
from math import ceil
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from .const import *

_LOGGER = logging.getLogger(__name__)

ICON = "mdi:calendar-clock"
ICON_DAYS_TO = "mdi:calendar-end"

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DataUpdateCoordinator = data["coordinator"]
    instance_name = data.get("name", "IsItPayday")

    async_add_entities([
        IsItPaydayNextSensor(coordinator, entry.entry_id, instance_name),
        IsItPaydayDaysToSensor(coordinator, entry.entry_id, instance_name)
    ])


class IsItPaydayNextSensor(CoordinatorEntity, SensorEntity):
    _attr_device_class = None

    def __init__(self, coordinator: DataUpdateCoordinator, entry_id: str, instance_name: str):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_payday_next"
        self._attr_name = f"{instance_name}: Next payday"
        self._attr_icon = ICON
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
        return {
            "source": "IsItPayday DataUpdateCoordinator",
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


class IsItPaydayDaysToSensor(CoordinatorEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "d"
    _attr_state_class = "measurement"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: DataUpdateCoordinator, entry_id: str, instance_name: str):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_days_to"
        self._attr_name = f"{instance_name}: Days to"
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

            now = datetime.now().date()
            if payday <= now:
                return 0

            delta = payday - now
            return delta.days
        except Exception as e:
            _LOGGER.exception("Error calculating days to payday: %s", e)
            return None

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "source": "IsItPayday DataUpdateCoordinator",
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
