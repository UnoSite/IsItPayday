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

# Hent Home Assistant country fra konfiguration og valider mod understoettede lande
async def async_get_homeassistant_country(hass: HomeAssistant) -> str | None:
    _LOGGER.debug("Henter Home Assistant country fra konfiguration.")
    country = getattr(hass.config, "country", None)

    if not country:
        _LOGGER.warning("Home Assistant country er ikke sat.")
        return None

    supported_countries = await async_fetch_supported_countries()

    if country not in supported_countries:
        _LOGGER.warning("Landet '%s' er ikke blandt de understoettede lande.", country)
        return None

    _LOGGER.info("Home Assistant country '%s' er understoettet.", country)
    return country

# Hent liste over understoettede lande fra Nager.Date API
async def async_fetch_supported_countries() -> dict[str, str]:
    _LOGGER.info("Henter liste over understoettede lande fra Nager.Date API.")
    async with aiohttp.ClientSession() as session:
        async with session.get(API_COUNTRIES) as response:
            data = await response.json()
            try:
                countries = {country["countryCode"]: country["name"] for country in data}
                _LOGGER.info("Hentede %d understoettede lande.", len(countries))
                return countries
            except KeyError as e:
                _LOGGER.error("Fejl ved behandling af lande-data: Manglende noegle %s", e)
                raise

# Hovedklasse for Config Flow
class IsItPayday2ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self.country = None
        self.pay_frequency = None
        self.pay_day = None
        self.last_pay_date = None
        self.bank_offset = 0
        self.country_list = {}

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        _LOGGER.info("Starter config flow - Trin 1 (Vaelg land).")

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
        _LOGGER.info("Starter config flow - Trin 2 (Vaelg udbetalingsfrekvens).")

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
        if user_input is None:
            return self.async_show_form(
                step_id="monthly_day",
                data_schema=self._create_monthly_day_schema(),
            )

        self.pay_day = user_input[CONF_PAY_DAY]
        _LOGGER.info("Maanedlig udbetalingsdag valgt: %s", self.pay_day)

        if self.pay_day == "last_bank_day":
            return await self.async_step_bank_offset()
        if self.pay_day == "specific_day":
            return await self.async_step_specific_day()

        return self._create_entry()

    async def async_step_bank_offset(self, user_input: dict | None = None) -> FlowResult:
        if user_input is None:
            return self.async_show_form(
                step_id="bank_offset",
                data_schema=self._create_bank_offset_schema(),
            )

        self.bank_offset = int(user_input[CONF_BANK_OFFSET])
        _LOGGER.info("Dage foer sidste bankdag: %d", self.bank_offset)
        return self._create_entry()

    async def async_step_specific_day(self, user_input: dict | None = None) -> FlowResult:
        if user_input is None:
            return self.async_show_form(
                step_id="specific_day",
                data_schema=self._create_specific_day_schema(),
            )

        self.pay_day = int(user_input[CONF_PAY_DAY])
        _LOGGER.info("Specifik dag valgt: %d", self.pay_day)
        return self._create_entry()

    async def async_step_cycle_last_paydate(self, user_input: dict | None = None) -> FlowResult:
        if user_input is None:
            return self.async_show_form(
                step_id="cycle_last_paydate",
                data_schema=self._create_last_paydate_schema(),
            )

        self.last_pay_date = user_input[CONF_LAST_PAY_DATE]
        _LOGGER.info("Sidste udbetalingsdato valgt: %s", self.last_pay_date)
        return self._create_entry()

    async def async_step_weekly(self, user_input: dict | None = None) -> FlowResult:
        if user_input is None:
            return self.async_show_form(
                step_id="weekly",
                data_schema=self._create_weekly_schema(),
            )

        self.pay_day = user_input[CONF_PAY_DAY]
        _LOGGER.info("Ugeloensdag valgt: %s", self.pay_day)
        return self._create_entry()

    def _create_entry(self) -> FlowResult:
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
        return vol.Schema({
            vol.Required(CONF_COUNTRY, default=default_country): SelectSelector(
                SelectSelectorConfig(
                    options=[{"value": k, "label": v} for k, v in self.country_list.items()],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        })

    def _create_pay_frequency_schema(self) -> vol.Schema:
        return vol.Schema({
            vol.Required(CONF_PAY_FREQ): SelectSelector(
                SelectSelectorConfig(
                    options=[{"value": k, "label": v} for k, v in PAY_FREQ_OPTIONS.items()],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        })

    def _create_monthly_day_schema(self) -> vol.Schema:
        return vol.Schema({
            vol.Required(CONF_PAY_DAY): SelectSelector(
                SelectSelectorConfig(
                    options=[{"value": k, "label": v} for k, v in PAY_MONTHLY_OPTIONS.items()],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        })

    def _create_bank_offset_schema(self) -> vol.Schema:
    	"""Opret schema for valg af dage foer sidste bankdag. Default sættes til 0."""
    	_LOGGER.debug("Opretter schema for dage foer sidste bankdag med default 0.")
    	return vol.Schema({
	        vol.Required(CONF_BANK_OFFSET, default=0): SelectSelector(
	            SelectSelectorConfig(
	                options=[{"value": v, "label": str(v)} for v in DAYS_BEFORE_OPTIONS],
	                mode=SelectSelectorMode.DROPDOWN,
	            )
	        )
        })

    def _create_specific_day_schema(self) -> vol.Schema:
        return vol.Schema({
            vol.Required(CONF_PAY_DAY, default=1): SelectSelector(
                SelectSelectorConfig(
                    options=[{"value": v, "label": str(v)} for v in SPECIFIC_DAY_OPTIONS],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        })

    def _create_last_paydate_schema(self) -> vol.Schema:
        return vol.Schema({vol.Required(CONF_LAST_PAY_DATE): DateSelector()})
