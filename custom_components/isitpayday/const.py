"""Constants for IsItPayday integration."""

# Domain and general metadata
DOMAIN = "isitpayday"
CONF_TITLE = "Is It Payday"
CONF_MANUFACTURER = "UnoSite"
CONF_MODEL = "Payday Tracker"

# Configuration keys (stored in config entry)
CONF_COUNTRY = "country"
CONF_PAY_FREQ = "pay_frequency"
CONF_PAY_DAY = "pay_day"
CONF_LAST_PAY_DATE = "last_pay_date"
CONF_BANK_OFFSET = "bank_offset"
CONF_WEEKDAY = "weekday"  # Bruges kun til ugentlig betaling

# Labels used in config flow (visible to user)
LABEL_SELECT_COUNTRY = "Select country"
LABEL_SELECT_PAYOUT_FREQUENCY = "Select the payout frequency"
LABEL_SELECT_DAY_OF_MONTH = "Select day of month"
LABEL_DAYS_BEFORE_LAST_BANK_DAY = "Days before last bank day"
LABEL_SELECT_SPECIFIC_DAY = "Select specific day"
LABEL_SELECT_WEEKDAY = "Select weekday"
LABEL_SELECT_LAST_PAYDAY = "Select last payday"

# Pay frequency options shown to user
PAY_FREQ_MONTHLY = "monthly"
PAY_FREQ_28_DAYS = "28_days"
PAY_FREQ_14_DAYS = "14_days"
PAY_FREQ_WEEKLY = "weekly"

PAY_FREQ_OPTIONS = {
    PAY_FREQ_MONTHLY: "Monthly",
    PAY_FREQ_28_DAYS: "Every 28th day",
    PAY_FREQ_14_DAYS: "Every 14th day",
    PAY_FREQ_WEEKLY: "Weekly",
}

# Monthly pay day options (only for monthly frequency)
PAY_DAY_LAST_BANK_DAY = "last_bank_day"
PAY_DAY_FIRST_BANK_DAY = "first_bank_day"
PAY_DAY_SPECIFIC_DAY = "specific_day"

PAY_MONTHLY_OPTIONS = {
    PAY_DAY_LAST_BANK_DAY: "Last bank day",
    PAY_DAY_FIRST_BANK_DAY: "First bank day",
    PAY_DAY_SPECIFIC_DAY: "Specific day"
}

DAYS_BEFORE_OPTIONS = [str(i) for i in range(0, 11)]  # 0 til 10 som tekst
SPECIFIC_DAY_OPTIONS = [str(i) for i in range(1, 32)]  # 1 til 31 som tekst

# Weekday options (used for weekly pay frequency)
WEEKDAY_OPTIONS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# Mapping weekday strings to integer (Python weekday format: Monday = 0, ..., Sunday = 6)
WEEKDAY_MAP = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
}

# Default values
DEFAULT_COUNTRY = "DK"
DEFAULT_PAY_FREQ = PAY_FREQ_MONTHLY
DEFAULT_MONTHLY_DAY = PAY_DAY_LAST_BANK_DAY
DEFAULT_BANK_OFFSET = 0
DEFAULT_SPECIFIC_DAY = 31

# Device class, model and manufacturer
DEVICE_NAME = CONF_TITLE
DEVICE_MANUFACTURER = CONF_MANUFACTURER
DEVICE_MODEL = CONF_MODEL

# API endpoints (dynamic year handling is done in payday_calculator.py)
API_COUNTRIES = "https://date.nager.at/api/v3/AvailableCountries"
API_HOLIDAYS = "https://date.nager.at/api/v3/PublicHolidays/{year}/{country}"

# Logger prefix
LOGGER_NAME = DOMAIN

# Sensor and binary sensor entity names (fixed to required format)
SENSOR_NEXT_PAYDAY = "sensor.payday_next"
BINARY_SENSOR_IS_IT_PAYDAY = "binary_sensor.payday"

# Sensor icons
ICON_NEXT_PAYDAY = "mdi:calendar-clock"
ICON_IS_IT_PAYDAY_TRUE = "mdi:cash-fast"
ICON_IS_IT_PAYDAY_FALSE = "mdi:cash-clock"

# Log messages (standardized to use across all files)
LOG_INIT = "Initializing IsItPayday integration."
LOG_SETUP = "Setting up IsItPayday integration."
LOG_FETCH_COUNTRIES = "Fetching supported countries from API."
LOG_FETCH_HOLIDAYS = "Fetching public holidays for {year} in {country}."
LOG_CALCULATE_PAYDAY = "Calculating next payday using frequency {frequency}."
LOG_PAYDAY_CALCULATED = "Next payday calculated: {payday}"
LOG_API_ERROR = "Error fetching data from API: {error}"
LOG_UNEXPECTED_ERROR = "Unexpected error: {error}"
LOG_FALLBACK_NO_HOLIDAYS = "No holidays could be fetched. Using empty list."

# Error messages (for logging and debugging)
ERROR_INVALID_COUNTRY = "Invalid country selected ({country}). Cannot calculate payday."
ERROR_INVALID_PAYDAY = "Unable to calculate valid payday. Returning 'Unknown'."

# Validation errors
ERROR_WEEKDAY_REQUIRED_FOR_WEEKLY = "Weekly frequency requires weekday to be set."
ERROR_LAST_PAYDATE_REQUIRED = "Last payday date is required for 14-day or 28-day pay frequencies."
