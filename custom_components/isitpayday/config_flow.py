"""Config flow and options flow for IsItPayday integration."""

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
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
    CONF_SUBDIV,
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
from .payday_calculator import get_country_subdivisions, get_supported_countries

_LOGGER = logging.getLogger(__name__)

# Sentinel for "no subdivision selected" in the subdivision dropdown.
SUBDIV_NONE = "none"


def _coerce_int(value, default: int) -> int:
    """Safely convert a stored config value to int.

    Older config entries may have stored numeric values as strings
    (e.g. '31'). This normalizes them.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class PaydayFlowMixin:
    """Shared steps for the config flow and the options flow.

    The two flows collect the same settings; only the entry point and the
    final save step differ. Subclasses must implement `_finish()`.
    """

    country: str | None = None
    subdiv: str | None = None
    pay_frequency: str | None = None
    pay_day = None
    last_pay_date: str | None = None
    bank_offset: int = 0
    weekday: int | None = None
    subdivision_list: dict[str, str]

    def _finish(self) -> FlowResult:
        raise NotImplementedError

    async def _async_continue_after_country(self) -> FlowResult:
        """Continue to subdivision selection if relevant, else frequency."""
        self.subdivision_list = await self.hass.async_add_executor_job(
            get_country_subdivisions, self.country
        )
        if self.subdivision_list:
            return await self.async_step_subdivision()

        self.subdiv = None
        return await self.async_step_frequency()

    async def async_step_subdivision(self, user_input=None) -> FlowResult:
        """Handle optional selection of a state/region within the country."""
        if user_input is None:
            options = {SUBDIV_NONE: "Entire country (no region)"}
            options.update(self.subdivision_list)
            default = self.subdiv if self.subdiv in options else SUBDIV_NONE
            return self.async_show_form(
                step_id="subdivision",
                data_schema=vol.Schema(
                    {vol.Required(CONF_SUBDIV, default=default): vol.In(options)}
                ),
            )

        selection = user_input[CONF_SUBDIV]
        self.subdiv = None if selection == SUBDIV_NONE else selection
        return await self.async_step_frequency()

    async def async_step_frequency(self, user_input=None) -> FlowResult:
        """Handle pay frequency selection."""
        if user_input is None:
            return self.async_show_form(
                step_id="frequency",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_PAY_FREQ,
                            default=self.pay_frequency or PAY_FREQ_MONTHLY,
                        ): vol.In(PAY_FREQ_OPTIONS)
                    }
                ),
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

        return self._finish()

    async def async_step_monthly_day(self, user_input=None) -> FlowResult:
        """Handle selection of which day of the month payday falls on."""
        if user_input is None:
            # If pay_day is an int (specific day) from a previous config,
            # the sensible default for this step is "specific_day".
            default = self.pay_day
            if isinstance(default, int) or default not in PAY_MONTHLY_OPTIONS:
                default = (
                    PAY_DAY_SPECIFIC_DAY
                    if isinstance(self.pay_day, int)
                    else PAY_DAY_LAST_BANK_DAY
                )
            return self.async_show_form(
                step_id="monthly_day",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_PAY_DAY, default=default): vol.In(
                            PAY_MONTHLY_OPTIONS
                        )
                    }
                ),
            )

        self.pay_day = user_input[CONF_PAY_DAY]

        if self.pay_day == PAY_DAY_LAST_BANK_DAY:
            return await self.async_step_bank_offset()
        elif self.pay_day == PAY_DAY_SPECIFIC_DAY:
            return await self.async_step_specific_day()

        return self._finish()

    async def async_step_bank_offset(self, user_input=None) -> FlowResult:
        """Handle selection of days before last bank day."""
        if user_input is None:
            default = _coerce_int(self.bank_offset, 0)
            if default not in range(0, 11):
                default = 0
            return self.async_show_form(
                step_id="bank_offset",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_BANK_OFFSET, default=default): vol.In(
                            range(0, 11)
                        )
                    }
                ),
            )

        self.bank_offset = _coerce_int(user_input[CONF_BANK_OFFSET], 0)
        return self._finish()

    async def async_step_specific_day(self, user_input=None) -> FlowResult:
        """Handle selection of a specific day of the month."""
        if user_input is None:
            default = _coerce_int(self.pay_day, 31)
            if default not in range(1, 32):
                default = 31
            return self.async_show_form(
                step_id="specific_day",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_PAY_DAY, default=default): vol.In(
                            range(1, 32)
                        )
                    }
                ),
            )

        self.pay_day = _coerce_int(user_input[CONF_PAY_DAY], 31)
        return self._finish()

    async def async_step_cycle_last_paydate(self, user_input=None) -> FlowResult:
        """Handle selection of the last payday date for interval-based frequencies."""
        if user_input is None:
            if self.last_pay_date:
                schema = vol.Schema(
                    {
                        vol.Required(
                            CONF_LAST_PAY_DATE, default=self.last_pay_date
                        ): DateSelector()
                    }
                )
            else:
                schema = vol.Schema(
                    {vol.Required(CONF_LAST_PAY_DATE): DateSelector()}
                )
            return self.async_show_form(
                step_id="cycle_last_paydate", data_schema=schema
            )

        self.last_pay_date = user_input[CONF_LAST_PAY_DATE]
        return self._finish()

    async def async_step_weekly(self, user_input=None) -> FlowResult:
        """Handle selection of weekday for weekly pay frequency."""
        if user_input is None:
            default = self.pay_day if self.pay_day in WEEKDAY_OPTIONS else "Monday"
            return self.async_show_form(
                step_id="weekly",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_PAY_DAY, default=default): vol.In(
                            WEEKDAY_OPTIONS
                        )
                    }
                ),
            )

        self.pay_day = user_input[CONF_PAY_DAY]
        self.weekday = WEEKDAY_MAP[self.pay_day]
        return self._finish()

    def _collect_settings(self) -> dict:
        """Return the collected settings as a dict."""
        return {
            CONF_COUNTRY: self.country,
            CONF_SUBDIV: self.subdiv,
            CONF_PAY_FREQ: self.pay_frequency,
            CONF_PAY_DAY: self.pay_day,
            CONF_LAST_PAY_DATE: self.last_pay_date,
            CONF_BANK_OFFSET: self.bank_offset,
            CONF_WEEKDAY: self.weekday,
        }


class IsItPaydayConfigFlow(PaydayFlowMixin, config_entries.ConfigFlow, domain=DOMAIN):
    """Initial setup flow (name + all payday settings)."""

    VERSION = 1

    def __init__(self) -> None:
        self.name: str | None = None
        self.country_list: dict[str, str] = {}
        self.subdivision_list: dict[str, str] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        """Return the options flow for an existing entry."""
        return IsItPaydayOptionsFlow()

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial user step (name + country)."""
        if user_input is None:
            if not self.country_list:
                self.country_list = await self.hass.async_add_executor_job(
                    get_supported_countries
                )

            ha_country = getattr(self.hass.config, "country", None)
            if ha_country and ha_country in self.country_list:
                default_country = ha_country
            elif DEFAULT_COUNTRY in self.country_list:
                default_country = DEFAULT_COUNTRY
            else:
                default_country = next(iter(self.country_list))

            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_NAME, default=""): vol.All(
                            str, vol.Length(min=1)
                        ),
                        vol.Required(
                            CONF_COUNTRY, default=default_country
                        ): vol.In(self.country_list),
                    }
                ),
            )

        self.name = user_input[CONF_NAME]
        self.country = user_input[CONF_COUNTRY]
        return await self._async_continue_after_country()

    def _finish(self) -> FlowResult:
        """Create the config entry."""
        data = {CONF_NAME: self.name, **self._collect_settings()}
        return self.async_create_entry(title=self.name, data=data)


class IsItPaydayOptionsFlow(PaydayFlowMixin, config_entries.OptionsFlow):
    """Options flow for changing settings on an existing entry.

    Saved options are stored in entry.options and take precedence over
    entry.data (see __init__.py). An update listener reloads the
    integration automatically when options change.
    """

    def __init__(self) -> None:
        self.country_list: dict[str, str] = {}
        self.subdivision_list: dict[str, str] = {}

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Entry point: select country, prefilled with current settings."""
        config = {**self.config_entry.data, **self.config_entry.options}

        if user_input is None:
            # Prefill all current settings so each step shows current values.
            self.country = config.get(CONF_COUNTRY)
            self.subdiv = config.get(CONF_SUBDIV)
            self.pay_frequency = config.get(CONF_PAY_FREQ)
            self.last_pay_date = config.get(CONF_LAST_PAY_DATE)
            self.bank_offset = _coerce_int(config.get(CONF_BANK_OFFSET), 0)
            self.weekday = config.get(CONF_WEEKDAY)

            pay_day = config.get(CONF_PAY_DAY)
            if isinstance(pay_day, str) and pay_day.isdigit():
                pay_day = int(pay_day)
            self.pay_day = pay_day

            if not self.country_list:
                self.country_list = await self.hass.async_add_executor_job(
                    get_supported_countries
                )

            default_country = (
                self.country
                if self.country in self.country_list
                else DEFAULT_COUNTRY
            )
            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_COUNTRY, default=default_country
                        ): vol.In(self.country_list)
                    }
                ),
            )

        self.country = user_input[CONF_COUNTRY]
        return await self._async_continue_after_country()

    def _finish(self) -> FlowResult:
        """Save the new settings to entry.options."""
        return self.async_create_entry(title="", data=self._collect_settings())
