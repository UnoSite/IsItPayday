# IsItPayday - Home Assistant Integration <a href="https://translate.unosite.dk"><img align="right" src="https://img.shields.io/badge/Translate-This-000?style=for-the-badge&logo=crowdin&labelColor=333333&color=cad401"></a>

[![Version](https://img.shields.io/github/v/release/UnoSite/IsItPayday?label=version&style=for-the-badge&labelColor=333333&color=cad401)](https://github.com/UnoSite/IsItPayday/releases/latest)
[![Last Commit](https://img.shields.io/github/last-commit/UnoSite/IsItPayday?style=for-the-badge&labelColor=333333&color=cad401)](https://github.com/UnoSite/IsItPayday/commits/main/)
[![License](https://img.shields.io/github/license/UnoSite/IsItPayday?style=for-the-badge&labelColor=333333&color=cad401)](https://github.com/UnoSite/IsItPayday/blob/main/LICENSE.md)
[![Code Size](https://img.shields.io/github/languages/code-size/UnoSite/IsItPayday?style=for-the-badge&labelColor=333333&color=cad401)](#)
[![Stars](https://img.shields.io/github/stars/UnoSite/IsItPayday?style=for-the-badge&labelColor=333333&color=cad401)](#)
[![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/UnoSite/IsItPayday/total?style=for-the-badge&labelColor=333333&color=cad401)](#)

<!-- FIX #1: Changed to raw.githubusercontent.com so the image renders correctly -->


![Logo](https://raw.githubusercontent.com/UnoSite/IsItPayday/main/logo.png)



[![Sponsor Github](https://img.shields.io/badge/Sponsor-Github-000?style=for-the-badge&logo=githubsponsors&labelColor=333333&color=cad401&logoColor=EA4AAA)](https://github.com/sponsors/UnoSite)\
[![Sponsor Buy Me a Coffee](https://img.shields.io/badge/Sponsor-Buy%20me%20a%20coffee-000?style=for-the-badge&logo=buymeacoffee&labelColor=333333&color=cad401&logoColor=FFDD00)](https://buymeacoffee.com/UnoSite)\
[![Sponsor PayPal.Me](https://img.shields.io/badge/Sponsor-paypal.me-000?style=for-the-badge&logo=paypal&labelColor=333333&color=cad401&logoColor=002991)](https://paypal.me/UnoSite)

---

## 📌 Overview

**IsItPayday** is a custom integration for Home Assistant that calculates and displays your next payday based on your country's public holidays and your specified pay frequency. All calculations are performed locally - no cloud services or internet connection required.

---

## 🚀 Features

- **Device-based integration:** All sensors are grouped under a single device for each configured instance.

- **Binary Sensor:** `binary_sensor.<instance_name>_is_it_payday`
  - Indicates whether today is a payday (`on` or `off`).
  - Icons:
    - `mdi:cash-fast` if it is payday. <sup><sup>([See icon](https://pictogrammers.com/library/mdi/icon/cash-fast/))</sup></sup>
    - `mdi:cash-clock` if it is not payday. <sup><sup>([See icon](https://pictogrammers.com/library/mdi/icon/cash-clock/))</sup></sup>

- **Sensor:** `sensor.<instance_name>_next_payday`
  - Displays the date of the next payday.
  - Icon: `mdi:calendar-clock`. <sup><sup>([See icon](https://pictogrammers.com/library/mdi/icon/calendar-clock/))</sup></sup>

- **Sensor:** `sensor.<instance_name>_days_to`
  - Displays how many days until next payday.
  - Icon: `mdi:calendar-end`. <sup><sup>([See icon](https://pictogrammers.com/library/mdi/icon/calendar-end/))</sup></sup>

- **Calendar:** `calendar.<instance_name>_payday`
  - Adds your next payday as a calendar event.
  - All-day event.
  - Automatically updates when payday changes.

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
  - Public holidays are calculated locally using the [holidays](https://pypi.org/project/holidays/) Python package.
  - Adjusts payday if it falls on a weekend or public holiday.
  - Works fully offline - no internet connection or external API required.

- **Reconfiguration Support:**
  - After initial setup, you can adjust all settings via the **Configure** button in the **Devices & Services** section.

- **Persistent Notification After Reconfiguration:**
  - When settings are updated, you will see a persistent notification confirming the change.

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
- Choose your country from the dropdown list. The list contains all countries supported by the [holidays](https://pypi.org/project/holidays/) package. The integration will automatically pre-select the country based on your Home Assistant configuration, but you can change it if needed.

### Step 2: Select Payout Frequency

- **Options:**
  - `weekly`: Weekly
  - `14_days`: Every 14th day
  - `28_days`: Every 28th day
  - `monthly`: Monthly
  - `bimonthly`: Every 2 months
  - `quarterly`: Every 3 months
  - `semiannual`: Every 6 months
  - `annual`: Every year

### Step 3: Frequency-specific Settings

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
  - **Specific day** (1–31, default 31): Choose the exact day of the month. If that day falls on a weekend or public holiday, the integration adjusts to the previous working day.

---

## 📡 Entities

<!-- FIX #3: Added the calendar entity to the table -->
| Entity ID                                     | Name          | Description                                       |
|-----------------------------------------------|---------------|---------------------------------------------------|
| `binary_sensor.<instance_name>_is_it_payday`  | Is It Payday? | `on` if today is payday, otherwise `off`.         |
| `sensor.<instance_name>_next_payday`          | Next Payday   | Date of the next payday (`YYYY-MM-DD`).           |
| `sensor.<instance_name>_days_to`              | Days until    | Number of days until the next payday.             |
| `calendar.<instance_name>_payday`             | Payday        | All-day calendar event for the next payday.       |

All entities are grouped under a single device, named after your chosen **Instance Name** during setup.

---

## 🔧 Reconfiguration

After the integration is set up, you can change any setting (country, pay frequency, day, etc.) directly from:

**Settings > Devices & Services > Is It Payday > Configure**

Once saved, a **persistent notification** will appear confirming the update.

---

## 📋 Example Dashboard Card (Lovelace)

You can add a **Payday Info Card** to your Home Assistant dashboard using the following Lovelace YAML configuration:

<!-- FIX #5: Added the calendar entity to the dashboard example -->
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

**Integration fails to load**
- Check the Home Assistant logs under **Settings > System > Logs** and look for entries from `custom_components.isitpayday`.
- Try removing and re-adding the integration.

---

## ⁉️ Issues & Support

If you encounter any issues or have feature requests, please open an issue on GitHub:

[![Badge](https://img.shields.io/badge/Report-issues-E00000?style=for-the-badge)](https://github.com/UnoSite/IsItPayday/issues)

---

## 📜 License

This integration is licensed under the [MIT License](https://github.com/UnoSite/IsItPayday/blob/main/LICENSE.md).
