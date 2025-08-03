# IsItPayday - Home Assistant Integration

[![Version](https://img.shields.io/github/v/release/UnoSite/IsItPayday?label=version&style=for-the-badge&labelColor=333333&color=cad401)](https://github.com/UnoSite/IsItPayday/releases/latest)
[![Last Commit](https://img.shields.io/github/last-commit/UnoSite/IsItPayday?style=for-the-badge&labelColor=333333&color=cad401)](https://github.com/UnoSite/IsItPayday/commits/main/)
[![License](https://img.shields.io/github/license/UnoSite/IsItPayday?style=for-the-badge&labelColor=333333&color=cad401)](https://github.com/UnoSite/IsItPayday/blob/main/LICENSE.md)
[![Code Size](https://img.shields.io/github/languages/code-size/UnoSite/IsItPayday?style=for-the-badge&labelColor=333333&color=cad401)](#)
[![Stars](https://img.shields.io/github/stars/UnoSite/IsItPayday?style=for-the-badge&labelColor=333333&color=cad401)](#)
[![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/UnoSite/IsItPayday/total?style=for-the-badge&labelColor=333333&color=cad401)](#)

![Logo](https://github.com/UnoSite/IsItPayday/blob/main/logo.png)

[![Sponsor Github](https://img.shields.io/badge/Sponsor-Github-000?style=for-the-badge&logo=githubsponsors&labelColor=333333&color=cad401&logoColor=EA4AAA)](https://github.com/sponsors/UnoSite)\
[![Sponsor Buy Me a Coffee](https://img.shields.io/badge/Sponsor-Buy%20me%20a%20coffee-000?style=for-the-badge&logo=buymeacoffee&labelColor=333333&color=cad401&logoColor=FFDD00)](https://buymeacoffee.com/UnoSite)\
[![Sponsor PayPal.Me](https://img.shields.io/badge/Sponsor-paypal.me-000?style=for-the-badge&logo=paypal&labelColor=333333&color=cad401&logoColor=002991)](https://paypal.me/UnoSite)

---

## 📌 Overview

**IsItPayday** is a custom integration for Home Assistant that calculates and displays your next payday based on your country's holidays and your specified pay frequency.

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

- **Sensor:** `senspr.<instance_name>_days_to`
  - Displays how many days until next payday.
  - Icon: `mdi:calendar-end`. <sup><sup>([See icon](https://pictogrammers.com/library/mdi/icon/calendar-end/))</sup></sup>

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
  - Fetches public holidays from the [Nager.Date API](https://date.nager.at).
  - Adjusts payday if it falls on a weekend or public holiday.

- **Reconfiguration Support:**
  - After initial setup, you can adjust all settings via the **Configure** button in the **Devices & Services** section.

- **Persistent Notification After Reconfiguration:**
  - When settings are updated, you will see a persistent notification confirming the change.

---

## 📥 Installation

### **1. Manual Installation**
1. **Download the latest release** from the [GitHub releases](https://github.com/UnoSite/IsItPayday/releases).
2. **Copy the `isitpayday` folder** into your Home Assistant `custom_components` directory.
3. **Restart Home Assistant.**
4. **Add the integration:**
   - Navigate to **Settings > Devices & Services > Integrations**.
   - Click **Add Integration** and search for **IsItPayday**.
  
### **2. HACS Installation (Recommended)**
1. Add this repository as a **custom repository** in [HACS](https://hacs.xyz/).
2. Search for **Is It Payday?** in HACS and install the integration.
3. Restart Home Assistant.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=UnoSite&repository=IsItPayday&category=Integration)

---

## ⚙️ Configuration

### Step 1: Select Country

- **Label:** Select country
- **Description:** Choose your country from the dropdown list. The integration will automatically select the country based on your Home Assistant configuration, but you can change it if needed.

### Step 2: Select Payout Frequency

- **Label:** Select the payout frequency
- **Options:**
  - `weekly`: Weekly
  - `14_days`: Every 14th day
  - `28_days`: Every 28th day
  - `monthly`: Monthly
  - `bimonthly`: Every 2 months
  - `quarterly`: Every 3 months
  - `semiannual`: Every 6 months
  - `annual`: Every year

### Step 3: Depending on the Selected Frequency

- **Monthly:**
  - **Label:** Select day of month
  - **Options:**
    - `last_bank_day`: Last bank day
    - `first_bank_day`: First bank day
    - `specific_day`: Specific day

- **Every 14th or 28th day / Bimonthly / Quarterly / Semiannual / Annual:**
  - **Label:** Select last payday
  - **Description:** Choose the date of your last payday. The integration will calculate future paydays based on this date.

- **Weekly:**
  - **Label:** Select weekday
  - **Description:** Choose the weekday you receive your payment.

### Additional Configuration for Monthly-Based Frequencies

- **If "Last bank day" is selected:**
  - **Label:** Days before last bank day
  - **Options:** 0 to 10 (default is 0)
  - **Description:** Specify how many days before the last bank day you receive your payment.

- **If "Specific day" is selected:**
  - **Label:** Select specific day
  - **Options:** 1 to 31 (default is 31)
  - **Description:** Choose the specific day of the month for your payday. If this day falls on a weekend or public holiday, the integration will adjust to the previous working day.

---

## 📡 Sensors

| Entity ID                                    | Name                 | Description                                  |
|----------------------------------------------|----------------------|----------------------------------------------|
| `binary_sensor.<instance_name>_is_it_payday` | Is It Payday?        | Indicates if today is a payday (`on`/`off`). |
| `sensor.<instance_name>_next_payday`         | Next Payday          | Displays the date of the next payday.        |
| `sensor.<instance_name>_days_to`             | Days until           | Displays how many days until next payday.    |

- All entities are grouped under a single device, named after your chosen **Instance Name** during setup.

---

## 🔧 Reconfiguration

- After the integration is set up, you can change the settings (country, pay frequency, day, etc.) directly from **Settings > Devices & Services > Is It Payday > Configure**.
- Once saved, a **persistent notification** will appear confirming the update.

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
```

---

## ⁉️ **Issues & Support**
If you encounter any issues or have feature requests, please open an issue on GitHub:

[![ Badge](https://img.shields.io/badge/Report-issues-E00000?style=for-the-badge)](https://github.com/UnoSite/IsItPayday/issues)

---

## 📜 **License**
This integration is licensed under the [MIT License](https://github.com/UnoSite/IsItPayday/blob/main/LICENSE.md).
