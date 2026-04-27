import json
import os
from pathlib import Path

import milight_ibox2


ZONE = 0
IBOX_IP = "10.10.100.254"
IBOX_PORT = 5987
APP_DIR = Path(os.getenv("APPDATA", str(Path.home()))) / "MiLightToggle"
STATE_FILE = APP_DIR / "state.json"
LAST_DEVICE_KEY = "_last_device"
LAST_DEVICE_INFO_KEY = "_last_device_info"


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


def zone_state(state, state_key):
    value = state.get(state_key)
    if isinstance(value, dict):
        return value
    if isinstance(value, bool):
        return {"on": value}
    return {}


def remember_zone_state(device, zone=ZONE, **updates):
    state = load_state()
    state_key = device_state_key(device, zone)
    current = zone_state(state, state_key)
    current.update(updates)
    state[state_key] = current
    state[LAST_DEVICE_KEY] = state_key
    state[LAST_DEVICE_INFO_KEY] = device
    save_state(state)


def remembered_light_state():
    state = load_state()
    last_device = state.get(LAST_DEVICE_KEY)
    if not last_device:
        return None
    return zone_state(state, last_device).get("on")


def remembered_device():
    device = load_state().get(LAST_DEVICE_INFO_KEY)
    if isinstance(device, dict) and "ip" in device and "port" in device:
        return device
    return None


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


def connect_device(client, device, zone=ZONE):
    client.connect(ibox_ip=device["ip"], ibox_port=device["port"])
    if not client.is_connected():
        close_client(client)
        raise RuntimeError("No response from iBox2 at {}:{}".format(device["ip"], device["port"]))

    client.lamp_type = client.RGBWW_TYPE
    client.zone = zone


def find_target_device(client, device=None):
    if device:
        return device

    devices = scan_devices(client)
    if not devices:
        raise RuntimeError("iBox2 not found in local network")
    return devices[0]


def run_device_action(action, zone=ZONE, device=None):
    client = create_client()
    try:
        target = find_target_device(client, device)
        connect_device(client, target, zone)
        result = action(client, target, zone)
        return target, result
    finally:
        close_client(client)


def set_device_light(client, device, on, zone=ZONE):
    if on:
        client.light_on(zone=zone)
    else:
        client.light_off(zone=zone)
    remember_zone_state(device, zone, on=on)
    return on


def set_light(on, zone=ZONE, device=None):
    return run_device_action(lambda client, target, current_zone: set_device_light(client, target, on, current_zone),
                             zone=zone, device=device)


def toggle_device(client, device, zone=ZONE):
    connect_device(client, device, zone)

    try:
        state = load_state()
        state_key = device_state_key(device, zone)
        is_on = zone_state(state, state_key).get("on", False)

        if is_on:
            return set_device_light(client, device, False, zone)
        else:
            return set_device_light(client, device, True, zone)
    finally:
        close_client(client)


def set_white(zone=ZONE, device=None):
    def action(client, target, current_zone):
        client.white(zone=current_zone)
        remember_zone_state(target, current_zone, on=True, color="white")
        return True

    return run_device_action(action, zone=zone, device=device)


def set_night(zone=ZONE, device=None):
    def action(client, target, current_zone):
        client.night(zone=current_zone)
        remember_zone_state(target, current_zone, on=True, mode="night")
        return True

    return run_device_action(action, zone=zone, device=device)


def set_color_raw(rgb, zone=ZONE, device=None):
    rgb = max(0, min(255, int(rgb)))

    def action(client, target, current_zone):
        client.color_raw(rgb, zone=current_zone)
        remember_zone_state(target, current_zone, on=True, color=rgb)
        return rgb

    return run_device_action(action, zone=zone, device=device)


def set_saturation(saturation, zone=ZONE, device=None):
    saturation = max(0, min(100, int(saturation)))

    def action(client, target, current_zone):
        client.saturation(saturation, zone=current_zone)
        remember_zone_state(target, current_zone, saturation=saturation)
        return saturation

    return run_device_action(action, zone=zone, device=device)


def set_brightness(brightness, zone=ZONE, device=None):
    brightness = max(0, min(100, int(brightness)))

    def action(client, target, current_zone):
        client.brightness(brightness, zone=current_zone)
        remember_zone_state(target, current_zone, brightness=brightness)
        return brightness

    return run_device_action(action, zone=zone, device=device)


def set_mode(mode, zone=ZONE, device=None):
    mode = max(1, min(9, int(mode)))

    def action(client, target, current_zone):
        client.mode(mode, zone=current_zone)
        remember_zone_state(target, current_zone, on=True, mode=mode)
        return mode

    return run_device_action(action, zone=zone, device=device)
