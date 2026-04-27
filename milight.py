from milight_toggle import ZONE, close_client, create_client, scan_devices, toggle_device


def main():
    client = create_client()
    found_devices = scan_devices(client)
    if not found_devices:
        close_client(client)
        print("No iBox2 devices found")
        return

    print("Found iBox2 devices:")
    for device in found_devices:
        print("  {}:{} ({})".format(device["ip"], device["port"], device["mac"]))

    device = found_devices[0]
    is_on = toggle_device(client, device)
    if is_on:
        print("Zone {} switched on".format(ZONE))
    else:
        print("Zone {} switched off".format(ZONE))


if __name__ == "__main__":
    main()
