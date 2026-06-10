"""Config flow for IsItPayday integration."""

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import DateSelector

from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_COUNTRY,
    CONF_PAY_FREQ,
    CONF_PAY_DAY,
    CONF_LAST_PAY_DATE,
    CONF_BANK_OFFSET,
    CONF_WEEKDAY,
    DEFAULT_COUNTRY,
    PAY_FREQ_MONTHLY,
    PAY_FREQ_BIMONTHLY,
    PAY_FREQ_QUARTERLY,
    PAY_FREQ_SEMIANNUAL,
    PAY_FREQ_ANNUAL,
    PAY_FREQ_28_DAYS,
    PAY_FREQ_14_DAYS,
    PAY_FREQ_WEEKLY,
    PAY_FREQ_OPTIONS,
    PAY_MONTHLY_OPTIONS,
    PAY_DAY_LAST_BANK_DAY,
    PAY_DAY_SPECIFIC_DAY,
    WEEKDAY_MAP,
    WEEKDAY_OPTIONS,
)
from .payday_calculator import get_supported_countries

_LOGGER = logging.getLogger(__name__)


def _coerce_int(value, default: int) -> int:
    """Safely convert a stored config value to int.

    Older config entries may have stored numeric values as strings
    (e.g. '31'). This normalizes them.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class IsItPayday2ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self.name: str | None = None
        self.country: str | None = None
        self.pay_frequency: str | None = None
        self.pay_day = None
        self.last_pay_date: str | None = None
        self.bank_offset: int = 0
        self.weekday: int | None = None
        self.country_list: dict[str, str] = {}
        self.reconfig_entry = None

    async def _async_load_country_list(self) -> None:
        """Load the supported country list from the holidays package.

        The holidays package is synchronous, so this runs in an executor.
        """
        if not self.country_list:
            self.country_list = await self.hass.async_add_executor_job(
                get_supported_countries
            )

    def _default_country(self) -> str:
        """Return the best default country for the form."""
        if self.country and self.country in self.country_list:
            return self.country
        ha_country = getattr(self.hass.config, "country", None)
        if ha_country and ha_country in self.country_list:
            return ha_country
        if DEFAULT_COUNTRY in self.country_list:
            return DEFAULT_COUNTRY
        return next(iter(self.country_list))

    async def async_step_reconfigure(self, user_input=None) -> FlowResult:
        """Handle reconfiguration of an existing entry."""
        _LOGGER.info("Starting reconfiguration flow")
        entry_id = self.context.get("entry_id")
        if not entry_id:
            _LOGGER.error("Reconfiguration started without valid entry_id in context.")
            return self.async_abort(reason="missing_entry")

        entry = self.hass.config_entries.async_get_entry(entry_id)
        if not entry:
            _LOGGER.error("Could not find entry with id %s", entry_id)
            return self.async_abort(reason="entry_not_found")

        self.reconfig_entry = entry
        data = entry.data

        self.name = data.get(CONF_NAME, "")
        self.country = data.get(CONF_COUNTRY)
        self.pay_frequency = data.get(CONF_PAY_FREQ)
        self.last_pay_date = data.get(CONF_LAST_PAY_DATE)
        self.bank_offset = _coerce_int(data.get(CONF_BANK_OFFSET), 0)
        self.weekday = data.get(CONF_WEEKDAY)

        # pay_day can be a string option (last_bank_day, weekday name) OR an
        # int (specific day). Old entries may have ints stored as strings.
        pay_day = data.get(CONF_PAY_DAY)
        if isinstance(pay_day, str) and pay_day.isdigit():
            pay_day = int(pay_day)
        self.pay_day = pay_day

        return await self.async_step_user()

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial user step (name + country)."""
        if user_input is None:
            await self._async_load_country_list()
            return self.async_show_form(
                step_id="user",
                data_schema=self._create_user_schema(self._default_country()),
            )

        self.name = user_input[CONF_NAME]
        self.country = user_input[CONF_COUNTRY]
        return await self.async_step_frequency()

    async def async_step_frequency(self, user_input=None) -> FlowResult:
        """Handle pay frequency selection."""
        if user_input is None:
            return self.async_show_form(
                step_id="frequency", data_schema=self._create_pay_frequency_schema()
            )

        self.pay_frequency = user_input[CONF_PAY_FREQ]

        if self.pay_frequency == PAY_FREQ_MONTHLY:
            return await self.async_step_monthly_day()
        elif self.pay_frequency in [
            PAY_FREQ_BIMONTHLY,
            PAY_FREQ_QUARTERLY,
            PAY_FREQ_SEMIANNUAL,
            PAY_FREQ_ANNUAL,
            PAY_FREQ_28_DAYS,
            PAY_FREQ_14_DAYS,
        ]:
            return await self.async_step_cycle_last_paydate()
        elif self.pay_frequency == PAY_FREQ_WEEKLY:
            return await self.async_step_weekly()

        return self._create_entry()

    async def async_step_monthly_day(self, user_input=None) -> FlowResult:
        """Handle selection of which day of the month payday falls on."""
        if user_input is None:
            return self.async_show_form(
                step_id="monthly_day", data_schema=self._create_monthly_day_schema()
            )

        self.pay_day = user_input[CONF_PAY_DAY]

        if self.pay_day == PAY_DAY_LAST_BANK_DAY:
            return await self.async_step_bank_offset()
        elif self.pay_day == PAY_DAY_SPECIFIC_DAY:
            return await self.async_step_specific_day()

        return self._create_entry()

    async def async_step_bank_offset(self, user_input=None) -> FlowResult:
        """Handle selection of days before last bank day."""
        if user_input is None:
            return self.async_show_form(
                step_id="bank_offset", data_schema=self._create_bank_offset_schema()
            )

        self.bank_offset = _coerce_int(user_input[CONF_BANK_OFFSET], 0)
        return self._create_entry()

    async def async_step_specific_day(self, user_input=None) -> FlowResult:
        """Handle selection of a specific day of the month."""
        if user_input is None:
            return self.async_show_form(
                step_id="specific_day", data_schema=self._create_specific_day_schema()
            )

        self.pay_day = _coerce_int(user_input[CONF_PAY_DAY], 31)
        return self._create_entry()

    async def async_step_cycle_last_paydate(self, user_input=None) -> FlowResult:
        """Handle selection of the last payday date for interval-based frequencies."""
        if user_input is None:
            return self.async_show_form(
                step_id="cycle_last_paydate",
                data_schema=self._create_last_paydate_schema(),
            )

        self.last_pay_date = user_input[CONF_LAST_PAY_DATE]
        return self._create_entry()

    async def async_step_weekly(self, user_input=None) -> FlowResult:
        """Handle selection of weekday for weekly pay frequency."""
        if user_input is None:
            return self.async_show_form(
                step_id="weekly", data_schema=self._create_weekly_schema()
            )

        self.pay_day = user_input[CONF_PAY_DAY]
        self.weekday = WEEKDAY_MAP[self.pay_day]
        return self._create_entry()

    def _create_entry(self) -> FlowResult:
        """Persist the config entry or update the existing one on reconfigure."""
        data = {
            CONF_NAME: self.name,
            CONF_COUNTRY: self.country,
            CONF_PAY_FREQ: self.pay_frequency,
            CONF_PAY_DAY: self.pay_day,
            CONF_LAST_PAY_DATE: self.last_pay_date,
            CONF_BANK_OFFSET: self.bank_offset,
            CONF_WEEKDAY: self.weekday,
        }

        if self.reconfig_entry:
            _LOGGER.info(
                "Updating existing entry: %s", self.reconfig_entry.entry_id
            )
            self.hass.config_entries.async_update_entry(
                self.reconfig_entry, data=data
            )
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(self.reconfig_entry.entry_id)
            )
            self.hass.async_create_task(
                self.hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "IsItPayday",
                        "message": (
                            f"The configuration for '{self.name}' "
                            "has been successfully updated."
                        ),
                    },
                )
            )
            return self.async_abort(reason="reconfigured")

        return self.async_create_entry(title=self.name, data=data)

    # ------------------------------------------------------------------ #
    # Schema helpers                                                       #
    # ------------------------------------------------------------------ #

    def _create_user_schema(self, default_country: str) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(CONF_NAME, default=self.name or ""): str,
                vol.Required(CONF_COUNTRY, default=default_country): vol.In(
                    self.country_list
                ),
            }
        )

    def _create_pay_frequency_schema(self) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(
                    CONF_PAY_FREQ, default=self.pay_frequency or PAY_FREQ_MONTHLY
                ): vol.In(PAY_FREQ_OPTIONS)
            }
        )

    def _create_monthly_day_schema(self) -> vol.Schema:
        # If pay_day is an int (specific day) from a previous config, the
        # sensible default for this step is "specific_day".
        default = self.pay_day
        if isinstance(default, int) or default not in PAY_MONTHLY_OPTIONS:
            default = (
                PAY_DAY_SPECIFIC_DAY
                if isinstance(self.pay_day, int)
                else PAY_DAY_LAST_BANK_DAY
            )
        return vol.Schema(
            {
                vol.Required(CONF_PAY_DAY, default=default): vol.In(
                    PAY_MONTHLY_OPTIONS
                )
            }
        )

    def _create_bank_offset_schema(self) -> vol.Schema:
        default = _coerce_int(self.bank_offset, 0)
        if default not in range(0, 11):
            default = 0
        return vol.Schema(
            {
                vol.Required(CONF_BANK_OFFSET, default=default): vol.In(range(0, 11))
            }
        )

    def _create_specific_day_schema(self) -> vol.Schema:
        default = _coerce_int(self.pay_day, 31)
        if default not in range(1, 32):
            default = 31
        return vol.Schema(
            {
                vol.Required(CONF_PAY_DAY, default=default): vol.In(range(1, 32))
            }
        )

    def _create_last_paydate_schema(self) -> vol.Schema:
        if self.last_pay_date:
            return vol.Schema(
                {
                    vol.Required(
                        CONF_LAST_PAY_DATE, default=self.last_pay_date
                    ): DateSelector()
                }
            )
        return vol.Schema(
            {
                vol.Required(CONF_LAST_PAY_DATE): DateSelector()
            }
        )

    def _create_weekly_schema(self) -> vol.Schema:
        default = self.pay_day if self.pay_day in WEEKDAY_OPTIONS else "Monday"
        return vol.Schema(
            {
                vol.Required(CONF_PAY_DAY, default=default): vol.In(WEEKDAY_OPTIONS)
            }
            )
