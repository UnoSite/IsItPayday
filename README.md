# Is It Payday? - Home Assistant Integration

[![Is It Payday?](https://img.shields.io/github/v/release/UnoSite/IsItPayday?label=version&style=for-the-badge)](https://github.com/UnoSite/IsItPayday/releases/latest)
[![HA Integration](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-blue?style=for-the-badge)](#)
[![License](https://img.shields.io/github/license/UnoSite/IsItPayday?style=for-the-badge)](https://github.com/UnoSite/IsItPayday/blob/main/LICENSE.md)
[![GitHub last commit](https://img.shields.io/github/last-commit/UnoSite/IsItPayday?style=for-the-badge)](https://github.com/UnoSite/IsItPayday/commits/main/)

[![LOGO](https://github.com/UnoSite/IsItPayday/blob/main/logo.png)](https://github.com/UnoSite/IsItPayday)

## **Overview**
The **Is It Payday?** integration allows Home Assistant users to check whether today is a payday based on their country and payday preference. It retrieves payday information from the **IsItPayday API** and provides relevant sensors to monitor the next payday, country, and timezone.

## **Features**
- ✅ **Binary Sensor:** `binary_sensor.payday` - Indicates whether today is a payday (`on` or `off`).
- ✅ **Sensor:** `sensor.payday_next` - Displays the date of the next payday.
- ✅ **Sensor:** `sensor.payday_country` - Shows the selected country for payday calculations.
- ✅ **Sensor:** `sensor.payday_timezone` - Displays the timezone used for payday calculations.
- ✅ **Custom Payday Selection:** Choose between:
  - **Last day of the month**
  - **First day of the month**
  - **A custom day (1-31)**
- ✅ **Automatic Updates:** The integration fetches new data periodically to ensure accuracy.
- ✅ **Simple Setup:** Uses Home Assistant’s **Config Flow** for easy installation.

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
3. **Step 1:** Select your country from the dropdown list.
4. **Step 2:** Choose your payday type:
   - **Last day of the month**
   - **First day of the month**
   - **Custom day of the month**
5. **Step 3 (If Custom Day is selected):** Enter a number between **1-31**.
6. Click **Submit** to complete the setup.

### **2. Sensors**
| Entity ID               | Name              | Description                          |
|-------------------------|------------------|--------------------------------------|
| `binary_sensor.payday`  | Is It Payday?    | Shows if today is a payday (`on`/`off`). |
| `sensor.payday_next`    | Next Payday      | Displays the next payday date.       |
| `sensor.payday_country` | Country          | Shows the selected country.          |
| `sensor.payday_timezone`| Timezone         | Displays the timezone in use.        |

### **3. API Usage**
The integration uses the following API endpoints:
- **Supported Countries:** `https://api.isitpayday.com/countries`
- **Payday Data:** `https://api.isitpayday.com/monthly?payday={days}&country={country_id}&timezone={tz}`

The API link is also available as an **attribute** in `binary_sensor.payday`.

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
