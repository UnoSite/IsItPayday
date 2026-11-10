"""Base entity for the IsItPayday integration."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import CONF_CONFIG_URL, CONF_MANUFACTURER, CONF_MODEL, DOMAIN


class IsItPaydayEntity(CoordinatorEntity):
    """Common base for all IsItPayday entities.

    Holds the shared coordinator, instance name and the device info that
    groups all entities of one config entry under a single device.
    """

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry_id: str,
        instance_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._instance_name = instance_name
        self._entry_id = entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=instance_name,
            manufacturer=CONF_MANUFACTURER,
            model=CONF_MODEL,
            configuration_url=CONF_CONFIG_URL,
        )
