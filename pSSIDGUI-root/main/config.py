from pathlib import Path
import json, sys, jsonschema
from django.conf import settings

CONFIG_PATH = getattr(settings, "CONFIG_PATH", Path("/etc/pssid-gui/config.json"))

config = {}
try:
    with open(CONFIG_PATH) as config_file:
        config = json.load(config_file)
except FileNotFoundError as e:
    print("pssid-gui error: config file not found at " + str(CONFIG_PATH), file=sys.stderr)
    sys.exit(1)
except json.decoder.JSONDecodeError as e:
    print("pssid-gui error: config file " + str(CONFIG_PATH) + " appears to be invalid JSON:", file=sys.stderr)
    print(str(e), file=sys.stderr)
    sys.exit(1)

config_schema = {
    "type": "object",
    "properties": {
        "inventories-dir": { "type": "string" }
    },
    "required": [ "inventories-dir" ]
}

try:
    jsonschema.validate(config, config_schema)
except jsonschema.exceptions.ValidationError as e:
    print("pssid-gui error: config file " + str(CONFIG_PATH) + " is valid JSON but is not in required format:", file=sys.stderr)
    print(str(e), file=sys.stderr)
    sys.exit(1)

INVENTORIES_DIRECTORY = Path(config["inventories-dir"])

# FIXME: in principle this should be done through the jsonschema framework, but this works
if not INVENTORIES_DIRECTORY.is_absolute():
    print("pssid-gui error: in config file " + str(CONFIG_PATH) + ", inventories-dir must be an absolute path", file=sys.stderr)
    sys.exit(1)

if not INVENTORIES_DIRECTORY.exists():
    print("pssid-gui error: inventories-dir in config file " + str(CONFIG_PATH) + " does not exist", file=sys.stderr)
    sys.exit(1)