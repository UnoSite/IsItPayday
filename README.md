# Is It Payday? - Home Assistant Integration

[![Is It Payday?](https://img.shields.io/github/v/release/UnoSite/IsItPayday?label=version&style=for-the-badge)](https://github.com/UnoSite/IsItPayday/releases/latest)
[![GitHub last commit](https://img.shields.io/github/last-commit/UnoSite/IsItPayday?style=for-the-badge)](https://github.com/UnoSite/IsItPayday/commits/main/)
[![License](https://img.shields.io/github/license/UnoSite/IsItPayday?style=for-the-badge)](https://github.com/UnoSite/IsItPayday/blob/main/LICENSE.md)
[![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/UnoSite/IsItPayday?style=for-the-badge)](#)
[![GitHub Repo stars](https://img.shields.io/github/stars/UnoSite/IsItPayday?style=for-the-badge)](#)

[![LOGO](https://github.com/UnoSite/IsItPayday/blob/main/logo.png)](https://github.com/UnoSite/IsItPayday)

[![Sponsor Buy Me a Coffee](https://img.shields.io/badge/Sponsor-Buy_Me_a_Coffee-yellow?style=for-the-badge)](https://buymeacoffee.com/UnoSite)
[![Sponsor PayPal.Me](https://img.shields.io/badge/Sponsor-PayPal.me-blue?style=for-the-badge)](https://paypal.me/unosite)

---

## **Overview**
The **Is It Payday?** integration allows Home Assistant users to check whether today is a payday based on their country and payday preference. It retrieves payday information from the **IsItPayday API** and provides relevant sensors to monitor the next payday, country, timezone, and payday type.

## **Features**
- ✅ **Binary Sensor:** `binary_sensor.payday` - Indicates whether today is a payday (`on` or `off`).
- ✅ **Sensor:** `sensor.payday_next` - Displays the date of the next payday.
- ✅ **Sensor:** `sensor.payday_country` - Shows the selected country for payday calculations.
- ✅ **Sensor:** `sensor.payday_timezone` - Displays the timezone used for payday calculations.
- ✅ **Sensor:** `sensor.payday_type` - Shows the selected payday type (`Last day`, `First day`, or `Custom day: X`).
- ✅ **Custom Payday Selection:** Choose between:
  - 📅 **Last day of the month** → Uses the last day in API calculations.
  - 📅 **First day of the month** → Uses the first day in API calculations.
  - 📅 **Custom day of the month** → Select a specific day (dropdown menu: Day 1 - Day 31).
- ✅ **Automatic Updates:** The integration fetches new data periodically to ensure accuracy.
- ✅ **All Sensors Include API URL Attribute:** Every sensor includes the `API-link` attribute showing the exact API request used.

---

## **Installation**
### **1. Manual Installation**
1. Download the latest version from the [GitHub releases](https://github.com/UnoSite/IsItPayday/releases).
2. Copy the `isitpayday` folder into your Home Assistant `custom_components` directory.
3. Restart Home Assistant.

### **2. HACS Installation (Recommended)**
1. Add this repository as a **custom repository** in [HACS](https://hacs.xyz/).
2. Search for **Is It Payday?** in HACS and install the integration.
3. Restart Home Assistant.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=UnoSite&repository=IsItPayday&category=Integration)

---

## **Configuration**
### **1. Add the Integration**
1. Go to **Settings > Devices & Services > Integrations**.
2. Click **Add Integration** and search for **Is It Payday?**.
3. **Step 1:** 🌍 **Select your country** from the dropdown list.
4. **Step 2:** 📆 **Choose your payday type**:
   - **Last day of the month** → Uses the last day in API calculations.
   - **First day of the month** → Uses the first day in API calculations.
   - **Custom day of the month** → Allows you to specify an exact day.
5. **Step 3 (If Custom Day is selected):** 🔢 **Select a day** from the dropdown (Day 1 - Day 31).
6. Click **Submit** to complete the setup.

### **2. Sensors**
| Entity ID               | Name              | Description                          |
|-------------------------|------------------|--------------------------------------|
| `binary_sensor.payday`  | Is It Payday?    | Shows if today is a payday (`on`/`off`). |
| `sensor.payday_next`    | Next Payday      | Displays the next payday date.       |
| `sensor.payday_country` | Country          | Shows the selected country.          |
| `sensor.payday_timezone`| Timezone         | Displays the timezone in use.        |
| `sensor.payday_type`    | Payday Type      | Displays the selected payday type.   |

#### **API URL Attribute**
Each sensor now includes an attribute called `API-link`, which displays the exact API request used to fetch payday data.

---

## **Example Automation**
You can create an automation to send a notification on payday:

```yaml
alias: Payday Notification
trigger:
  - platform: state
    entity_id: binary_sensor.payday
    to: "on"
action:
  - service: notify.mobile_app
    data:
      title: "It's Payday!"
      message: "Today is payday! 🎉"
