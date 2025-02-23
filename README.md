# Is It Payday? - Home Assistant Integration

![HA Integration](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-blue?style=for-the-badge)
![License](https://img.shields.io/github/license/UnoSite/IsItPayday?style=for-the-badge)
![GitHub last commit](https://img.shields.io/github/last-commit/UnoSite/IsItPayday?style=for-the-badge)

![LOGO](https://github.com/UnoSite/IsItPayday/blob/main/logo.png)

## **Overview**
The **Is It Payday?** integration allows Home Assistant users to check whether today is a payday based on their country. It retrieves payday information from the **IsItPayday API** and provides relevant sensors to monitor the next payday, country, and timezone.

## **Features**
- ✅ **Binary Sensor:** `binary_sensor.payday` - Indicates whether today is payday (`on` or `off`).
- ✅ **Sensor:** `sensor.payday_next` - Displays the date of the next payday.
- ✅ **Sensor:** `sensor.payday_country` - Shows the selected country for payday calculations.
- ✅ **Sensor:** `sensor.payday_timezone` - Displays the timezone used for payday calculations.
- ✅ **Automatic Updates:** The integration fetches new data periodically to ensure accuracy.
- ✅ **Simple Setup:** Uses Home Assistant’s **Config Flow** for easy installation.

---

## **Installation**
### **HACS Installation**
1. Add this repository as a **custom repository** in [HACS](https://hacs.xyz/).
2. Search for **Is It Payday?** in HACS and install the integration.
3. Restart Home Assistant.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=UnoSite&repository=IsItPayday&category=Integration)

---

## **Configuration**
### **1. Add the Integration**
1. Go to **Settings > Devices & Services > Integrations**.
2. Click **Add Integration** and search for **Is It Payday?**.
3. Select your country from the dropdown list.
4. Click **Submit** to complete the setup.

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
