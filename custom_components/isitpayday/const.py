import json
from pathlib import Path

DOMAIN = "isitpayday"
CONF_COUNTRY = "country"
CONF_COUNTRY_ID = "country_id"

# Hent version automatisk fra manifest.json
with open(Path(__file__).parent / "manifest.json", encoding="utf-8") as manifest_file:
    VERSION = json.load(manifest_file)["version"]
