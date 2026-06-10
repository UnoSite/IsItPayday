import logging
from datetime import date

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    CONF_CONFIG_URL,
    DOMAIN,
    CONF_MANUFACTURER,
    CONF_MODEL,
    ICON_IS_IT_PAYDAY_TRUE,
    ICON_IS_IT_PAYDAY_FALSE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DataUpdateCoordinator = data["coordinator"]
    instance_name = data.get("name", "IsItPayday")

    async_add_entities(
        [IsItPaydaySensor(coordinator, entry.entry_id, instance_name)]
    )


class IsItPaydaySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor that is 'on' when today is payday."""

    _attr_device_class = None

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry_id: str,
        instance_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_is_it_payday"
        self._attr_name = f"{instance_name}: Is it payday"
        self._instance_name = instance_name
        self._entry_id = entry_id

    @property
    def is_on(self) -> bool:
        payday_next = self.coordinator.data.get("payday_next")
        if not payday_next:
            return False

        today = date.today()
        if isinstance(payday_next, date):
            return payday_next == today
        try:
            return date.fromisoformat(payday_next) == today
        except (ValueError, TypeError):
            return False

    @property
    def icon(self) -> str:
        return ICON_IS_IT_PAYDAY_TRUE if self.is_on else ICON_IS_IT_PAYDAY_FALSE

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._instance_name,
            "manufacturer": CONF_MANUFACTURER,
            "model": CONF_MODEL,
            "configuration_url": CONF_CONFIG_URL,
        }
