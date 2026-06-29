# IsItPayday - Home Assistant Integration <a href="https://translate.unosite.dk"><img align="right" src="https://img.shields.io/badge/Translate-This-000?style=for-the-badge&logo=crowdin&labelColor=333333&color=cad401"></a>

[![Version](https://img.shields.io/github/v/release/UnoSite/IsItPayday?label=version&style=for-the-badge&labelColor=333333&color=cad401)](https://github.com/UnoSite/IsItPayday/releases/latest)
[![Last Commit](https://img.shields.io/github/last-commit/UnoSite/IsItPayday?style=for-the-badge&labelColor=333333&color=cad401)](https://github.com/UnoSite/IsItPayday/commits/main/)
[![License](https://img.shields.io/github/license/UnoSite/IsItPayday?style=for-the-badge&labelColor=333333&color=cad401)](https://github.com/UnoSite/IsItPayday/blob/main/LICENSE.md)
[![Code Size](https://img.shields.io/github/languages/code-size/UnoSite/IsItPayday?style=for-the-badge&labelColor=333333&color=cad401)](#)
[![Stars](https://img.shields.io/github/stars/UnoSite/IsItPayday?style=for-the-badge&labelColor=333333&color=cad401)](#)
[![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/UnoSite/IsItPayday/total?style=for-the-badge&labelColor=333333&color=cad401)](#)



![Icon](https://raw.githubusercontent.com/UnoSite/IsItPayday/main/custom_components/isitpayday/brand/icon.png)



[![Sponsor Github](https://img.shields.io/badge/Sponsor-Github-000?style=for-the-badge&logo=githubsponsors&labelColor=333333&color=cad401&logoColor=EA4AAA)](https://github.com/sponsors/UnoSite)\
[![Sponsor Buy Me a Coffee](https://img.shields.io/badge/Sponsor-Buy%20me%20a%20coffee-000?style=for-the-badge&logo=buymeacoffee&labelColor=333333&color=cad401&logoColor=FFDD00)](https://buymeacoffee.com/UnoSite)\
[![Sponsor PayPal.Me](https://img.shields.io/badge/Sponsor-paypal.me-000?style=for-the-badge&logo=paypal&labelColor=333333&color=cad401&logoColor=002991)](https://paypal.me/UnoSite)

---

## 📌 Overview

**IsItPayday** is a custom integration for Home Assistant that calculates and displays your next payday based on your country's public and bank holidays and your chosen pay frequency.

All calculations are performed **locally** using the [holidays](https://pypi.org/project/holidays/) Python package - no cloud services, external API, or internet connection required.

---

## 🚀 Features

- **Device-based integration:** All entities are grouped under a single device for each configured instance.

- **Binary Sensor:** `binary_sensor.<instance_name>_is_it_payday`
  - Indicates whether today is a payday (`on` or `off`).
  - Icons:
    - `mdi:cash-fast` if it is payday. <sup><sup>([See icon](https://pictogrammers.com/library/mdi/icon/cash-fast/))</sup></sup>
    - `mdi:cash-clock` if it is not payday. <sup><sup>([See icon](https://pictogrammers.com/library/mdi/icon/cash-clock/))</sup></sup>

- **Sensor:** `sensor.<instance_name>_next_payday`
  - Displays the date of the next payday.
  - Exposes extra attributes: `upcoming_paydays` (the next several paydays), `paydays_this_month` (remaining paydays in the current month) and `paydays_this_month_count`.
  - Icon: `mdi:calendar-clock`. <sup><sup>([See icon](https://pictogrammers.com/library/mdi/icon/calendar-clock/))</sup></sup>

- **Sensor:** `sensor.<instance_name>_days_to`
  - Displays how many days until next payday.
  - Icon: `mdi:calendar-end`. <sup><sup>([See icon](https://pictogrammers.com/library/mdi/icon/calendar-end/))</sup></sup>

- **Sensor:** `sensor.<instance_name>_last_payday`
  - Displays the most recent payday on or before today.
  - Icon: `mdi:calendar-check`. <sup><sup>([See icon](https://pictogrammers.com/library/mdi/icon/calendar-check/))</sup></sup>

- **Calendar:** `calendar.<instance_name>_payday`
  - Shows your upcoming paydays as all-day calendar events.
  - Multiple future paydays are displayed, not just the next one.
  - Automatically updates when paydays change.

- **Custom Payday Calculation:**
  - Supports various pay frequencies:
    - **Weekly**
    - **Every 14 days**
    - **Every 28 days**
    - **Monthly**
    - **Every 2 months**
    - **Quarterly (every 3 months)**
    - **Semi-annually (every 6 months)**
    - **Annually**

- **Automatic Adjustment for Holidays and Weekends:**
  - Public holidays and bank holidays (where available) are calculated locally using the [holidays](https://pypi.org/project/holidays/) Python package.
  - Adjusts payday if it falls on a weekend or holiday.
  - Works fully offline - no internet connection or external API required.

- **Regional Holiday Support:**
  - For countries with regional holidays (e.g. German Bundesländer or US states), you can select your state/region during setup for the most accurate holiday calendar.

- **Payday Event:**
  - Fires an `isitpayday_payday` event on each payday, at a time of day you choose (default 06:00). Automations can trigger directly on this event.

- **Options Flow:**
  - After initial setup, you can adjust all settings via the **Configure** button in the **Devices & Services** section. The integration reloads automatically when settings are saved - no restart required.

- **Diagnostics:**
  - Downloadable diagnostics (configuration and latest calculation) are available from the device page to make troubleshooting and bug reports easier.

---

## 📥 Installation

### **1. HACS Installation (Recommended)**

1. Add this repository as a **custom repository** in [HACS](https://hacs.xyz/).
2. Search for **Is It Payday?** in HACS and install the integration.
3. Restart Home Assistant.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=UnoSite&repository=IsItPayday&category=Integration)

---

### **2. Manual Installation**

1. Download the [latest release](https://github.com/UnoSite/IsItPayday/releases/latest).
2. Copy the `custom_components/isitpayday` folder into your Home Assistant `custom_components` directory.
3. Restart Home Assistant.
4. Go to **Settings > Devices & Services > Add Integration** and search for **Is It Payday**.

---

## ⚙️ Configuration

### Step 1: Instance Name & Country

- Enter a name for this instance (e.g. `My Payday`).
- Choose your country from the dropdown list. The list contains all countries supported by the [holidays](https://pypi.org/project/holidays/) package. The integration automatically pre-selects your Home Assistant configured country, but you can change it if needed.

### Step 2: Region (only for some countries)

- If the selected country has regional holidays, you are asked to select your state/region. Choose **Entire country** to use only national holidays, or pick a region to include its regional holidays in the calculation.
- Countries without regional holidays skip this step automatically.

### Step 3: Select Payout Frequency

- **Options:**
  - `weekly`: Weekly
  - `14_days`: Every 14th day
  - `28_days`: Every 28th day
  - `monthly`: Monthly
  - `bimonthly`: Every 2 months
  - `quarterly`: Every 3 months
  - `semiannual`: Every 6 months
  - `annual`: Every year

### Step 4: Frequency-specific Settings

- **Monthly:**
  - **Options:**
    - `last_bank_day`: Last bank day
    - `first_bank_day`: First bank day
    - `specific_day`: Specific day

- **Every 14th or 28th day / Every 2 months / Quarterly / Semi-annually / Annually:**
  - **Select last payday:** Choose the date of your most recent payday. The integration uses this to calculate all future paydays.

- **Weekly:**
  - **Select weekday:** Choose the weekday you receive your payment.

### Additional Configuration for Monthly-Based Frequencies

- **If "Last bank day" is selected:**
  - **Days before last bank day** (0–10, default 0): Specify how many days before the last bank day you are paid. The resulting date is also validated to be a bank day.

- **If "Specific day" is selected:**
  - **Specific day** (1–31, default 31): Choose the exact day of the month. If that day falls on a weekend or holiday, the integration adjusts to the previous working day.

### Final Step: Payday Event Time

- Choose the time of day the `isitpayday_payday` event is fired on each payday. The default is **06:00**.

---

## 📡 Entities

| Entity ID                                     | Name          | Description                                       |
|-----------------------------------------------|---------------|---------------------------------------------------|
| `binary_sensor.<instance_name>_is_it_payday`  | Is It Payday? | `on` if today is payday, otherwise `off`.         |
| `sensor.<instance_name>_next_payday`          | Next Payday   | Date of the next payday (`YYYY-MM-DD`).           |
| `sensor.<instance_name>_days_to`              | Days until    | Number of days until the next payday.             |
| `sensor.<instance_name>_last_payday`          | Last Payday   | Most recent payday on or before today.            |
| `calendar.<instance_name>_payday`             | Payday        | All-day calendar events for upcoming paydays.     |

All entities are grouped under a single device, named after your chosen **Instance Name** during setup.

### Next Payday Attributes

The **Next Payday** sensor exposes additional attributes useful for automations:

| Attribute                  | Description                                                        |
|----------------------------|--------------------------------------------------------------------|
| `upcoming_paydays`         | List of the upcoming paydays (`YYYY-MM-DD`).                       |
| `paydays_this_month`       | Remaining paydays in the current calendar month.                   |
| `paydays_this_month_count` | Number of remaining paydays this month (handy for biweekly pay).   |

---

## 🔔 Payday Event

On each payday, at the configured time of day (default **06:00**), the integration fires an event on the Home Assistant event bus:

- **Event type:** `isitpayday_payday`
- **Event data:**
  - `entry_id` – the config entry id
  - `name` – the instance name
  - `date` – the payday date (`YYYY-MM-DD`)

You can change the event time at any time via **Configure**.

### Example automation

```yaml
automation:
  - alias: "Notify on payday"
    trigger:
      - platform: event
        event_type: isitpayday_payday
    action:
      - service: notify.notify
        data:
          message: "It's payday! 🎉"
```

---

## 🔧 Changing Settings

After the integration is set up, you can change any setting (country, region, pay frequency, day, event time, etc.) directly from:

**Settings > Devices & Services > Is It Payday > Configure**

The integration reloads automatically when you save - no restart required. To rename an instance, use the rename (pencil) option on the integration entry.

---

## 📋 Example Dashboard Card (Lovelace)

You can add a **Payday Info Card** to your Home Assistant dashboard using the following Lovelace YAML configuration:

```yaml
type: entities
title: Payday Information
entities:
  - entity: binary_sensor.my_payday_instance_is_it_payday
    name: Is It Payday Today?
  - entity: sensor.my_payday_instance_next_payday
    name: Next Payday Date
  - entity: sensor.my_payday_instance_days_to
    name: Days Until Payday
  - entity: sensor.my_payday_instance_last_payday
    name: Last Payday
  - entity: calendar.my_payday_instance_payday
    name: Payday Calendar
```

---

## 🛠️ Troubleshooting

**Sensors show "Unknown"**
- Check the Home Assistant logs for messages from `custom_components.isitpayday` - they will indicate if the configured country or pay settings are invalid.
- Verify that the selected country is supported by the [holidays package](https://github.com/vacanza/holidays#available-countries).

**Payday date seems wrong**
- Make sure the correct pay frequency and reference date (last payday) are configured.
- If you use "Last bank day with offset", verify that the offset does not push the date into a weekend or holiday — the integration adjusts automatically, but double-check in the logs.
- For regional holidays, make sure the correct state/region is selected via **Configure**.

**Payday event does not fire**
- The event fires once per payday at the configured time. If Home Assistant is not running at that time, the event fires once when it next starts up that day.
- Check **Developer Tools > Events** and listen for `isitpayday_payday` to verify.

**Integration fails to load**
- Check the Home Assistant logs under **Settings > System > Logs** and look for entries from `custom_components.isitpayday`.
- Download diagnostics from the device page and attach them to a bug report.
- Try removing and re-adding the integration.

---

## ⁉️ Issues & Support

If you encounter any issues or have feature requests, please open an issue on GitHub:

[![Badge](https://img.shields.io/badge/Report-issues-E00000?style=for-the-badge)](https://github.com/UnoSite/IsItPayday/issues)

---

## 📜 License

This integration is licensed under the [MIT License](https://github.com/UnoSite/IsItPayday/blob/main/LICENSE.md).
