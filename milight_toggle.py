import json
import os
from pathlib import Path

import milight_ibox2


ZONE = 1
IBOX_IP = "10.10.100.254"
IBOX_PORT = 5987
APP_DIR = Path(os.getenv("APPDATA", str(Path.home()))) / "MiLightToggle"
STATE_FILE = APP_DIR / "state.json"
LAST_DEVICE_KEY = "_last_device"


def create_client():
    return milight_ibox2.MilightIBox(
        ibox_ip=IBOX_IP,
        ibox_port=IBOX_PORT,
        sock_timeout=2,
        tx_retries=5,
        verbose=False,
    )


def load_state():
    if not STATE_FILE.exists():
        return {}

    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(state):
    APP_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def device_state_key(device, zone=ZONE):
    return "{}:{}:zone{}".format(device["ip"], device["port"], zone)


def remembered_light_state():
    state = load_state()
    last_device = state.get(LAST_DEVICE_KEY)
    if not last_device:
        return None
    return state.get(last_device)


def scan_devices(client=None):
    if client is None:
        client = create_client()
    return client.scan()


def close_client(client):
    try:
        client.disconnect()
    finally:
        if getattr(client, "_sock_server", None):
            client._socket_close()


def toggle_device(client, device, zone=ZONE):
    client.connect(ibox_ip=device["ip"], ibox_port=device["port"])
    if not client.is_connected():
        close_client(client)
        raise RuntimeError("No response from iBox2 at {}:{}".format(device["ip"], device["port"]))

    try:
        client.lamp_type = client.RGBWW_TYPE
        client.zone = zone

        state = load_state()
        state_key = device_state_key(device, zone)
        is_on = state.get(state_key, False)

        if is_on:
            client.light_off(zone=zone)
            new_state = False
        else:
            client.light_on(zone=zone)
            new_state = True

        state[state_key] = new_state
        state[LAST_DEVICE_KEY] = state_key
        save_state(state)
        return new_state
    finally:
        close_client(client)
