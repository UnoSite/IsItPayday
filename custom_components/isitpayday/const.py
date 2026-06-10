"""Constants for IsItPayday integration."""

# Domain and general metadata
DOMAIN = "isitpayday"
CONF_TITLE = "Is It Payday"
CONF_MANUFACTURER = "UnoSite"
CONF_MODEL = "Payday Tracker"
CONF_CONFIG_URL = "https://github.com/UnoSite/IsItPayday"

# Configuration keys (stored in config entry)
CONF_COUNTRY = "country"
CONF_NAME = "name"
CONF_PAY_FREQ = "pay_frequency"
CONF_PAY_DAY = "pay_day"
CONF_LAST_PAY_DATE = "last_pay_date"
CONF_BANK_OFFSET = "bank_offset"
CONF_WEEKDAY = "weekday"

# Pay frequency options shown to user
PAY_FREQ_MONTHLY = "monthly"
PAY_FREQ_28_DAYS = "28_days"
PAY_FREQ_14_DAYS = "14_days"
PAY_FREQ_WEEKLY = "weekly"
PAY_FREQ_BIMONTHLY = "bimonthly"
PAY_FREQ_QUARTERLY = "quarterly"
PAY_FREQ_SEMIANNUAL = "semiannual"
PAY_FREQ_ANNUAL = "annual"

PAY_FREQ_OPTIONS = {
    PAY_FREQ_MONTHLY: "Monthly",
    PAY_FREQ_28_DAYS: "Every 28th day",
    PAY_FREQ_14_DAYS: "Every 14th day",
    PAY_FREQ_WEEKLY: "Weekly",
    PAY_FREQ_BIMONTHLY: "Every 2 months",
    PAY_FREQ_QUARTERLY: "Every 3 months",
    PAY_FREQ_SEMIANNUAL: "Every 6 months",
    PAY_FREQ_ANNUAL: "Every year",
}

# Monthly pay day options (only for monthly frequency)
PAY_DAY_LAST_BANK_DAY = "last_bank_day"
PAY_DAY_FIRST_BANK_DAY = "first_bank_day"
PAY_DAY_SPECIFIC_DAY = "specific_day"

PAY_MONTHLY_OPTIONS = {
    PAY_DAY_LAST_BANK_DAY: "Last bank day",
    PAY_DAY_FIRST_BANK_DAY: "First bank day",
    PAY_DAY_SPECIFIC_DAY: "Specific day",
}

# Weekday options (used for weekly pay frequency)
WEEKDAY_OPTIONS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# WEEKDAY_MAP is defined only here; config_flow.py imports it from here.
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


# Sensor icons
ICON_NEXT_PAYDAY = "mdi:calendar-clock"
ICON_IS_IT_PAYDAY_TRUE = "mdi:cash-fast"
ICON_IS_IT_PAYDAY_FALSE = "mdi:cash-clock"
ICON_DAYS_TO = "mdi:calendar-end"
