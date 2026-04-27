import json
from pathlib import Path

import milight_ibox2


STATE_FILE = Path(__file__).with_name(".milight_state.json")
ZONE = 1
DEFAULT_STATE = False


def load_state():
    if not STATE_FILE.exists():
        return {}

    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def toggle_light(ibox2, device):
    ibox2.connect(ibox_ip=device["ip"], ibox_port=device["port"])
    ibox2._lamp_type = ibox2.RGBWW_TYPE
    ibox2.zone = ZONE

    state = load_state()
    state_key = "{}:{}:zone{}".format(device["ip"], device["port"], ZONE)
    is_on = state.get(state_key, DEFAULT_STATE)

    if is_on:
        print("Zone {} is on, switching off...".format(ZONE))
        ibox2.light_off(zone=ZONE)
        state[state_key] = False
    else:
        print("Zone {} is off, switching on...".format(ZONE))
        ibox2.light_on(zone=ZONE)
        state[state_key] = True

    save_state(state)
    ibox2.disconnect()


def main():
    ibox2 = milight_ibox2.MilightIBox(
        ibox_ip="10.10.100.254",
        ibox_port=5987,
        sock_timeout=2,
        tx_retries=5,
        verbose=False,
    )

    found_devices = ibox2.scan()
    if not found_devices:
        print("No iBox2 devices found")
        return

    print("Found iBox2 devices:")
    for device in found_devices:
        print("  {}:{} ({})".format(device["ip"], device["port"], device["mac"]))
        toggle_light(ibox2, device)


if __name__ == "__main__":
    main()
