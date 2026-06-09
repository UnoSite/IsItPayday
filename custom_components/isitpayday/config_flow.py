"""Config flow for IsItPayday integration."""

import logging

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
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
    API_COUNTRIES,
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

_LOGGER = logging.getLogger(__name__)


def _coerce_int(value, default: int) -> int:
    """Safely convert a stored config value to int.

    FIX #5 from review: older config entries may have stored numeric
    values as strings (e.g. '31'). This normalizes them.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


async def async_get_homeassistant_country(hass: HomeAssistant) -> str | None:
    """Return HA's configured country if it is supported by Nager.Date API."""
    country = getattr(hass.config, "country", None)
    if not country:
        _LOGGER.warning("Home Assistant country is not set.")
        return None
    supported_countries = await async_fetch_supported_countries()
    if supported_countries is None or country not in supported_countries:
        _LOGGER.warning("Country '%s' is not supported.", country)
        return None
    return country


async def async_fetch_supported_countries() -> dict[str, str] | None:
    """Fetch available countries from Nager.Date API.

    Returns None on failure instead of raising an unhandled exception.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                API_COUNTRIES, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    _LOGGER.error(
                        "Failed to fetch supported countries: HTTP %s", response.status
                    )
                    return None
                data = await response.json()
                return {country["countryCode"]: country["name"] for country in data}
    except aiohttp.ClientError as e:
        _LOGGER.error("Network error fetching supported countries: %s", e)
        return None
    except Exception as e:
        _LOGGER.exception("Unexpected error fetching supported countries: %s", e)
        return None


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
        # FIX #5 from review: normalize possibly string-typed stored values.
        self.bank_offset = _coerce_int(data.get(CONF_BANK_OFFSET), 0)
        self.weekday = data.get(CONF_WEEKDAY)

        # pay_day can be a string option (last_bank_day, weekday name) OR an
        # int (specific day). Old entries may have ints stored as strings.
        pay_day = data.get(CONF_PAY_DAY)
        if isinstance(pay_day, str) and pay_day.isdigit():
            pay_day = int(pay_day)
        self.pay_day = pay_day

        # Fetch country list once here; async_step_user reuses it.
        self.country_list = await async_fetch_supported_countries() or {}

        return await self.async_step_user()

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial user step (name + country)."""
        if user_input is None:
            if not self.country_list:
                self.country_list = await async_fetch_supported_countries() or {}

            # FIX #2 from review: abort cleanly when the API is unreachable
            # instead of showing an empty form that would crash on submit.
            if not self.country_list:
                return self.async_abort(reason="cannot_connect")

            current_country = (
                self.country
                or await async_get_homeassistant_country(self.hass)
                or "DK"
            )
            return self.async_show_form(
                step_id="user",
                data_schema=self._create_user_schema(current_country),
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
        # FIX #5 from review: normalize to int so the default always matches
        # the option list, even for entries stored with string values.
        default = _coerce_int(self.bank_offset, 0)
        if default not in range(0, 11):
            default = 0
        return vol.Schema(
            {
                vol.Required(CONF_BANK_OFFSET, default=default): vol.In(range(0, 11))
            }
        )

    def _create_specific_day_schema(self) -> vol.Schema:
        # FIX #5 from review: same normalization for specific day.
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
