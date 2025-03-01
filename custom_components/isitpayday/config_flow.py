"""Config flow for IsItPayday integration."""

import logging
import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    DateSelector,
)

from .const import *

_LOGGER = logging.getLogger(__name__)


async def async_get_homeassistant_country(hass: HomeAssistant) -> str | None:
    """Henter Home Assistant country fra konfiguration og validerer mod understøttede lande."""
    _LOGGER.debug("Henter Home Assistant country fra konfiguration.")
    country = getattr(hass.config, "country", None)

    if not country:
        _LOGGER.warning("Home Assistant country er ikke sat.")
        return None

    supported_countries = await async_fetch_supported_countries()

    if country not in supported_countries:
        _LOGGER.warning("Landet '%s' er ikke blandt de understøttede lande.", country)
        return None

    _LOGGER.info("Home Assistant country '%s' er understøttet.", country)
    return country


async def async_fetch_supported_countries() -> dict[str, str]:
    """Henter liste over understøttede lande fra Nager.Date API."""
    _LOGGER.info("Henter liste over understøttede lande fra Nager.Date API.")
    async with aiohttp.ClientSession() as session:
        async with session.get(API_COUNTRIES) as response:
            data = await response.json()
            try:
                countries = {country["countryCode"]: country["name"] for country in data}
                _LOGGER.info("Hentede %d understøttede lande.", len(countries))
                return countries
            except KeyError as e:
                _LOGGER.error("Fejl ved behandling af lande-data: Manglende nøgle %s", e)
                raise


class IsItPayday2ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow til IsItPayday."""

    VERSION = 1

    def __init__(self) -> None:
        self.country = None
        self.pay_frequency = None
        self.pay_day = None
        self.last_pay_date = None
        self.bank_offset = 0
        self.country_list = {}

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Trin 1: Vælg land."""
        _LOGGER.info("Starter config flow - Trin 1 (Vælg land).")

        if user_input is None:
            self.country_list = await async_fetch_supported_countries()
            current_country = await async_get_homeassistant_country(self.hass)

            if not current_country:
                _LOGGER.warning("Ingen gyldig Home Assistant country fundet. Fallback til 'DK'.")
                current_country = "DK"

            _LOGGER.info("Standardland sat til: %s", current_country)

            return self.async_show_form(
                step_id="user",
                data_schema=self._create_country_schema(current_country),
            )

        self.country = user_input[CONF_COUNTRY]
        _LOGGER.info("Land valgt: %s", self.country)
        return await self.async_step_frequency()

    async def async_step_frequency(self, user_input: dict | None = None) -> FlowResult:
        """Trin 2: Vælg udbetalingsfrekvens."""
        _LOGGER.info("Starter config flow - Trin 2 (Vælg udbetalingsfrekvens).")

        if user_input is None:
            return self.async_show_form(
                step_id="frequency",
                data_schema=self._create_pay_frequency_schema(),
            )

        self.pay_frequency = user_input[CONF_PAY_FREQ]
        _LOGGER.info("Udbetalingsfrekvens valgt: %s", self.pay_frequency)

        if self.pay_frequency == "monthly":
            return await self.async_step_monthly_day()
        if self.pay_frequency in ["28_days", "14_days"]:
            return await self.async_step_cycle_last_paydate()
        if self.pay_frequency == "weekly":
            return await self.async_step_weekly()

        return self._create_entry()

    async def async_step_monthly_day(self, user_input: dict | None = None) -> FlowResult:
        """Trin 3: Vælg dag i måneden."""
        if user_input is None:
            return self.async_show_form(
                step_id="monthly_day",
                data_schema=self._create_monthly_day_schema(),
            )

        self.pay_day = user_input[CONF_PAY_DAY]
        _LOGGER.info("Månedlig udbetalingsdag valgt: %s", self.pay_day)

        if self.pay_day == "last_bank_day":
            return await self.async_step_bank_offset()
        if self.pay_day == "specific_day":
            return await self.async_step_specific_day()

        return self._create_entry()

    async def async_step_bank_offset(self, user_input: dict | None = None) -> FlowResult:
        """Trin 4: Vælg dage før sidste bankdag."""
        if user_input is None:
            return self.async_show_form(
                step_id="bank_offset",
                data_schema=self._create_bank_offset_schema(),
            )

        self.bank_offset = int(user_input[CONF_BANK_OFFSET])
        _LOGGER.info("Dage før sidste bankdag: %d", self.bank_offset)
        return self._create_entry()

    async def async_step_specific_day(self, user_input: dict | None = None) -> FlowResult:
        """Trin 4: Vælg specifik dag."""
        if user_input is None:
            return self.async_show_form(
                step_id="specific_day",
                data_schema=self._create_specific_day_schema(),
            )

        self.pay_day = int(user_input[CONF_PAY_DAY])
        _LOGGER.info("Specifik dag valgt: %d", self.pay_day)
        return self._create_entry()

    async def async_step_cycle_last_paydate(self, user_input: dict | None = None) -> FlowResult:
        """Trin 3: Vælg sidste udbetalingsdato."""
        if user_input is None:
            return self.async_show_form(
                step_id="cycle_last_paydate",
                data_schema=self._create_last_paydate_schema(),
            )

        self.last_pay_date = user_input[CONF_LAST_PAY_DATE]
        _LOGGER.info("Sidste udbetalingsdato valgt: %s", self.last_pay_date)
        return self._create_entry()

    async def async_step_weekly(self, user_input: dict | None = None) -> FlowResult:
        """Trin 3: Vælg ugedag for ugeløn."""
        if user_input is None:
            return self.async_show_form(
                step_id="weekly",
                data_schema=self._create_weekly_schema(),
            )

        self.pay_day = user_input[CONF_PAY_DAY]
        _LOGGER.info("Ugelønsdag valgt: %s", self.pay_day)
        return self._create_entry()

    def _create_entry(self) -> FlowResult:
        """Opret konfigurationsindgang."""
        _LOGGER.info("Opretter konfigurationsindgang.")
        return self.async_create_entry(
            title=CONF_TITLE,
            data={
                CONF_COUNTRY: self.country,
                CONF_PAY_FREQ: self.pay_frequency,
                CONF_PAY_DAY: self.pay_day,
                CONF_LAST_PAY_DATE: self.last_pay_date,
                CONF_BANK_OFFSET: self.bank_offset,
            },
        )

    def _create_country_schema(self, default_country: str) -> vol.Schema:
        return vol.Schema({vol.Required(CONF_COUNTRY, default=default_country): vol.In(self.country_list)})

    def _create_pay_frequency_schema(self) -> vol.Schema:
        return vol.Schema({vol.Required(CONF_PAY_FREQ): vol.In(PAY_FREQ_OPTIONS)})

    def _create_monthly_day_schema(self) -> vol.Schema:
        return vol.Schema({vol.Required(CONF_PAY_DAY): vol.In(PAY_MONTHLY_OPTIONS)})

    def _create_bank_offset_schema(self) -> vol.Schema:
        return vol.Schema({vol.Required(CONF_BANK_OFFSET, default=0): vol.In(DAYS_BEFORE_OPTIONS)})

    def _create_specific_day_schema(self) -> vol.Schema:
        return vol.Schema({vol.Required(CONF_PAY_DAY, default=1): vol.In(range(1, 32))})

    def _create_last_paydate_schema(self) -> vol.Schema:
        return vol.Schema({vol.Required(CONF_LAST_PAY_DATE): DateSelector()})

    def _create_weekly_schema(self) -> vol.Schema:
        return vol.Schema({vol.Required(CONF_PAY_DAY): vol.In(WEEKDAY_OPTIONS)})
