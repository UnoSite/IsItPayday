"""Home Assistant runtime tests for the IsItPayday integration."""

from datetime import timedelta
from unittest.mock import patch

import pytest

pytest.importorskip("homeassistant")

from homeassistant.config_entries import ConfigEntryState
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.isitpayday.const import (
    CONF_BANK_OFFSET,
    CONF_COUNTRY,
    CONF_EVENT_TIME,
    CONF_LAST_PAY_DATE,
    CONF_NAME,
    CONF_PAY_DAY,
    CONF_PAY_FREQ,
    CONF_SUBDIV,
    CONF_WEEKDAY,
    DOMAIN,
)


@pytest.mark.real_holidays
async def test_entry_setup_uses_home_assistant_local_date(hass):
    """Set up all platforms and pass HA's local date to the calculator."""
    local_today = dt_util.now().date()
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test payday",
        data={
            CONF_NAME: "Test payday",
            CONF_COUNTRY: "DK",
            CONF_PAY_FREQ: "weekly",
            CONF_PAY_DAY: "Monday",
            CONF_LAST_PAY_DATE: None,
            CONF_BANK_OFFSET: 0,
            CONF_WEEKDAY: 0,
            CONF_SUBDIV: None,
            CONF_EVENT_TIME: "06:00:00",
        },
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.isitpayday.calculate_upcoming_paydays",
            return_value=[local_today + timedelta(days=7)],
        ) as calculate_upcoming,
        patch(
            "custom_components.isitpayday.calculate_last_payday",
            return_value=local_today,
        ) as calculate_last,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert calculate_upcoming.call_args.args[-1] == local_today
    assert calculate_last.call_args.args[-1] == local_today
    assert len(hass.states.async_entity_ids("sensor")) == 3
    assert len(hass.states.async_entity_ids("binary_sensor")) == 1
    assert len(hass.states.async_entity_ids("calendar")) == 1

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
