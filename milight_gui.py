import colorsys
import math
import threading
import tkinter as tk

from milight_toggle import (
    ZONE,
    close_client,
    create_client,
    remembered_device,
    remembered_light_state,
    scan_devices,
    set_brightness,
    set_color_raw,
    set_light,
    set_night,
    set_saturation,
    set_white,
)


APP_BG = "#edf1f7"
HEADER_BG = "#171717"
ZONE_BG = "#d9dde4"
ZONE_ACTIVE_BG = "#f4f6fb"
TEXT_DARK = "#20242a"
TEXT_MUTED = "#66707c"
GREEN = "#00c922"
RED = "#f20f18"
BLUE = "#3a8cff"
FOOTER_BG = "#181818"


class MilightColorsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MiLight 3.0")
        self.root.geometry("360x640")
        self.root.minsize(320, 560)
        self.root.configure(bg=APP_BG)

        self.active_zone = ZONE
        self.current_device = remembered_device()
        self.rgb_value = 166
        self.saturation = tk.IntVar(value=0)
        self.brightness = tk.IntVar(value=32)
        self.status_var = tk.StringVar(value="Ready")
        self.device_var = tk.StringVar(value=self._device_text())
        self.action_buttons = []
        self.zone_buttons = {}

        self._build_layout()
        self._sync_power_state()
        self._refresh_zone_buttons()

    def _build_layout(self):
        self._build_header()
        self._build_zone_bar()
        self._build_readout()
        self._build_color_wheel()
        self._build_sliders()
        self._build_presets()
        self._build_actions()
        self._build_status()
        self._build_footer()

    def _build_header(self):
        header = tk.Frame(self.root, bg=HEADER_BG, height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        back = tk.Label(header, text="<", bg=HEADER_BG, fg="#d6d6d6", font=("Segoe UI", 17))
        back.pack(side=tk.LEFT, padx=(12, 0))

        title = tk.Label(header, text="Colors", bg=HEADER_BG, fg="#f3f3f3", font=("Segoe UI", 11))
        title.pack(side=tk.LEFT, expand=True)

        scan = tk.Button(
            header,
            text="scan",
            bg=HEADER_BG,
            fg="#d6d6d6",
            activebackground=HEADER_BG,
            activeforeground="#ffffff",
            bd=0,
            command=self.scan_device,
            cursor="hand2",
            font=("Segoe UI", 9),
        )
        scan.pack(side=tk.RIGHT, padx=(0, 10))

    def _build_zone_bar(self):
        zone_bar = tk.Frame(self.root, bg=ZONE_BG, height=44)
        zone_bar.pack(fill=tk.X)
        zone_bar.pack_propagate(False)

        for zone in range(1, 5):
            button = tk.Button(
                zone_bar,
                text="*\nZone{}".format(zone),
                bd=0,
                bg=ZONE_BG,
                activebackground=ZONE_ACTIVE_BG,
                fg=TEXT_DARK,
                font=("Segoe UI", 8),
                command=lambda current_zone=zone: self.select_zone(current_zone),
                cursor="hand2",
            )
            button.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self.zone_buttons[zone] = button

    def _build_readout(self):
        readout = tk.Frame(self.root, bg=APP_BG)
        readout.pack(fill=tk.X, padx=8, pady=(4, 0))

        self.rgb_label = tk.Label(readout, text="RGB:{}".format(self.rgb_value), anchor="w", bg=APP_BG,
                                  fg=TEXT_DARK, font=("Segoe UI", 8))
        self.rgb_label.pack(fill=tk.X)

        self.saturation_label = tk.Label(readout, text="Saturation:{}".format(self.saturation.get()), anchor="w",
                                         bg=APP_BG, fg=TEXT_DARK, font=("Segoe UI", 8))
        self.saturation_label.pack(fill=tk.X)

        self.brightness_label = tk.Label(readout, text="Brightness:{}".format(self.brightness.get()), anchor="w",
                                         bg=APP_BG, fg=TEXT_DARK, font=("Segoe UI", 8))
        self.brightness_label.pack(fill=tk.X)

    def _build_color_wheel(self):
        wheel_frame = tk.Frame(self.root, bg=APP_BG)
        wheel_frame.pack(fill=tk.X, pady=(18, 12))

        self.wheel_size = 190
        self.wheel_outer_radius = 88
        self.wheel_inner_radius = 28
        self.wheel_canvas = tk.Canvas(
            wheel_frame,
            width=self.wheel_size,
            height=self.wheel_size,
            bg=APP_BG,
            highlightthickness=0,
        )
        self.wheel_canvas.pack(anchor=tk.CENTER)

        self.color_wheel_image = self._create_color_wheel_image(self.wheel_size)
        self.wheel_canvas.create_oval(4, 5, self.wheel_size - 4, self.wheel_size - 1, fill="#b9c0ca", outline="")
        self.wheel_canvas.create_image(0, 0, image=self.color_wheel_image, anchor=tk.NW)
        center = self.wheel_size // 2
        self.wheel_canvas.create_oval(center - 31, center - 31, center + 31, center + 31,
                                      fill="#f8f8f8", outline="#b5bbc5", width=2)
        self.wheel_canvas.create_text(center, center, text="W", fill="#2373c7", font=("Segoe UI", 18, "bold"))
        self.selection_dot = self.wheel_canvas.create_oval(center + 38, center - 50, center + 48, center - 40,
                                                           outline="#dce8ff", width=2)

        self.wheel_canvas.bind("<Button-1>", self._on_wheel_click)

    def _build_sliders(self):
        sliders = tk.Frame(self.root, bg=APP_BG)
        sliders.pack(fill=tk.X, padx=18)

        self._build_slider(sliders, "Saturation", self.saturation, BLUE, self._send_saturation)
        self._build_slider(sliders, "Brightness", self.brightness, "#111111", self._send_brightness)

    def _build_slider(self, parent, label, variable, color, release_handler):
        row = tk.Frame(parent, bg=APP_BG)
        row.pack(fill=tk.X, pady=(0, 8))

        text = tk.Label(row, text=label, bg=APP_BG, fg=TEXT_MUTED, font=("Segoe UI", 8), anchor="w")
        text.pack(fill=tk.X)

        scale = tk.Scale(
            row,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            showvalue=False,
            variable=variable,
            length=310,
            bg=APP_BG,
            fg=TEXT_DARK,
            highlightthickness=0,
            troughcolor="#ffffff",
            activebackground=color,
            sliderrelief=tk.FLAT,
            command=lambda _value: self._update_readouts(),
        )
        scale.pack(fill=tk.X)
        scale.bind("<ButtonRelease-1>", lambda _event: release_handler())

    def _build_presets(self):
        presets = tk.Frame(self.root, bg=APP_BG)
        presets.pack(fill=tk.X, padx=20, pady=(2, 10))

        swatches = [
            ("#ffffff", lambda: self._send_white(), ""),
            ("#fff7d8", lambda: self._send_color(28), ""),
            ("#ff1018", lambda: self._send_color(16), ""),
            ("#1bd04b", lambda: self._send_color(90), ""),
            ("#2394ff", lambda: self._send_color(170), ""),
            (RED, lambda: self._send_color(self.rgb_value), "+"),
        ]

        for color, command, label in swatches:
            self._make_swatch(presets, color, command, label)

    def _make_swatch(self, parent, color, command, label=""):
        canvas = tk.Canvas(parent, width=42, height=42, bg=APP_BG, highlightthickness=0, cursor="hand2")
        canvas.pack(side=tk.LEFT, expand=True)
        canvas.create_oval(8, 8, 34, 34, fill=color, outline="#c7ccd4", width=2)
        if label:
            canvas.create_text(21, 21, text=label, fill="#ffffff", font=("Segoe UI", 18, "bold"))
        canvas.bind("<Button-1>", lambda _event: command())

    def _build_actions(self):
        actions = tk.Frame(self.root, bg=APP_BG)
        actions.pack(fill=tk.X, padx=12, pady=(0, 8))

        self.all_button = self._make_action_button(actions, "All", "#ffffff", TEXT_DARK, lambda: self.select_zone(0))
        self._make_action_button(actions, "Night light", "#ffffff", TEXT_DARK, self._send_night)
        self.on_button = self._make_action_button(actions, "ON", GREEN, "#ffffff", lambda: self._send_power(True))
        self.off_button = self._make_action_button(actions, "OFF", RED, "#ffffff", lambda: self._send_power(False))

    def _make_action_button(self, parent, text, bg, fg, command):
        button = tk.Button(
            parent,
            text=text,
            bg=bg,
            fg=fg,
            activebackground=bg,
            activeforeground=fg,
            bd=1,
            relief=tk.RIDGE,
            width=9,
            height=1,
            font=("Segoe UI", 8),
            command=command,
            cursor="hand2",
        )
        button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        self.action_buttons.append(button)
        return button

    def _build_status(self):
        status = tk.Frame(self.root, bg=APP_BG)
        status.pack(fill=tk.X, padx=10, pady=(0, 8))

        self.status_label = tk.Label(status, textvariable=self.status_var, bg=APP_BG, fg=TEXT_DARK,
                                     font=("Segoe UI", 8), anchor="center")
        self.status_label.pack(fill=tk.X)

        self.device_label = tk.Label(status, textvariable=self.device_var, bg=APP_BG, fg=TEXT_MUTED,
                                     font=("Segoe UI", 8), anchor="center")
        self.device_label.pack(fill=tk.X)

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=FOOTER_BG, height=52)
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        footer.pack_propagate(False)

        items = [("WiFiBox", False), ("Colors", True), ("Kelvin", False), ("Modes", False), ("Timer", False)]
        for text, active in items:
            label = tk.Label(
                footer,
                text="o\n{}".format(text),
                bg=FOOTER_BG,
                fg="#ffffff" if active else "#6e6e6e",
                font=("Segoe UI", 8),
            )
            label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _create_color_wheel_image(self, size):
        image = tk.PhotoImage(width=size, height=size)
        center = size / 2

        for y in range(size):
            row = []
            for x in range(size):
                dx = x - center
                dy = y - center
                distance = math.sqrt(dx * dx + dy * dy)

                if self.wheel_inner_radius < distance <= self.wheel_outer_radius:
                    hue = self._point_to_hue(dx, dy)
                    red, green, blue = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                    row.append("#{:02x}{:02x}{:02x}".format(int(red * 255), int(green * 255), int(blue * 255)))
                else:
                    row.append(APP_BG)

            image.put("{" + " ".join(row) + "}", to=(0, y))

        return image

    def _point_to_hue(self, dx, dy):
        angle = math.atan2(-dy, dx)
        return ((angle + math.pi) / (2 * math.pi)) % 1.0

    def _on_wheel_click(self, event):
        center = self.wheel_size / 2
        dx = event.x - center
        dy = event.y - center
        distance = math.sqrt(dx * dx + dy * dy)

        if distance <= self.wheel_inner_radius:
            self._send_white()
            return

        if distance > self.wheel_outer_radius:
            return

        hue = self._point_to_hue(dx, dy)
        self.rgb_value = int(hue * 255) & 0xFF
        self._update_readouts()
        self._move_selection_dot(event.x, event.y)
        self._send_color(self.rgb_value)

    def _move_selection_dot(self, x, y):
        radius = 5
        self.wheel_canvas.coords(self.selection_dot, x - radius, y - radius, x + radius, y + radius)

    def _update_readouts(self):
        self.rgb_label.configure(text="RGB:{}".format(self.rgb_value))
        self.saturation_label.configure(text="Saturation:{}".format(self.saturation.get()))
        self.brightness_label.configure(text="Brightness:{}".format(self.brightness.get()))

    def _sync_power_state(self):
        is_on = remembered_light_state()
        if is_on is True:
            self.status_var.set("Light is ON")
        elif is_on is False:
            self.status_var.set("Light is OFF")

    def _device_text(self):
        zone_text = "All zones" if self.active_zone == 0 else "Zone {}".format(self.active_zone)
        if self.current_device:
            return "{}:{} | {}".format(self.current_device["ip"], self.current_device["port"], zone_text)
        return "No device selected | {}".format(zone_text)

    def _refresh_zone_buttons(self):
        for zone, button in self.zone_buttons.items():
            if zone == self.active_zone:
                button.configure(bg=ZONE_ACTIVE_BG)
            else:
                button.configure(bg=ZONE_BG)

        if hasattr(self, "all_button"):
            if self.active_zone == 0:
                self.all_button.configure(bg="#e9f1ff", activebackground="#e9f1ff")
            else:
                self.all_button.configure(bg="#ffffff", activebackground="#ffffff")

        self.device_var.set(self._device_text())

    def select_zone(self, zone):
        self.active_zone = zone
        self._refresh_zone_buttons()
        self.status_var.set("All zones selected" if zone == 0 else "Zone {} selected".format(zone))

    def scan_device(self):
        self._set_busy(True, "Searching iBox2...")

        def worker():
            client = create_client()
            try:
                devices = scan_devices(client)
                if not devices:
                    raise RuntimeError("iBox2 not found in local network")
                device = devices[0]
                self.root.after(0, lambda current=device: self._show_device(current))
            except Exception as exc:
                message = str(exc)
                self.root.after(0, lambda current=message: self._show_error(current))
            finally:
                close_client(client)

        threading.Thread(target=worker, daemon=True).start()

    def _run_action(self, status, action, success_message):
        self._set_busy(True, status)
        zone = self.active_zone
        device = self.current_device

        def worker():
            try:
                target, result = action(zone, device)
                self.root.after(0, lambda current=target, value=result: self._show_success(current, success_message, value))
            except Exception as exc:
                message = str(exc)
                self.root.after(0, lambda current=message: self._show_error(current))

        threading.Thread(target=worker, daemon=True).start()

    def _set_busy(self, busy, status=None):
        if status:
            self.status_var.set(status)
        state = tk.DISABLED if busy else tk.NORMAL
        for button in self.action_buttons:
            button.configure(state=state)

    def _show_device(self, device):
        self.current_device = device
        self.status_var.set("Device found")
        self.device_var.set(self._device_text())
        self._set_busy(False)

    def _show_success(self, device, message, _result=None):
        self.current_device = device
        self.status_var.set(message)
        self.device_var.set(self._device_text())
        self._set_busy(False)

    def _show_error(self, message):
        self.status_var.set(message)
        self.device_var.set(self._device_text())
        self._set_busy(False)

    def _send_power(self, on):
        message = "Sending ON..." if on else "Sending OFF..."
        done = "Light is ON" if on else "Light is OFF"
        self._run_action(message, lambda zone, device: set_light(on, zone=zone, device=device), done)

    def _send_white(self):
        self._run_action("Sending white...", lambda zone, device: set_white(zone=zone, device=device), "White mode")

    def _send_night(self):
        self._run_action("Sending night light...", lambda zone, device: set_night(zone=zone, device=device), "Night light")

    def _send_color(self, rgb):
        self.rgb_value = int(rgb) & 0xFF
        self._update_readouts()
        self._run_action(
            "Sending RGB:{}...".format(self.rgb_value),
            lambda zone, device: set_color_raw(self.rgb_value, zone=zone, device=device),
            "RGB:{} sent".format(self.rgb_value),
        )

    def _send_saturation(self):
        value = self.saturation.get()
        self._run_action(
            "Sending saturation:{}...".format(value),
            lambda zone, device: set_saturation(value, zone=zone, device=device),
            "Saturation:{} sent".format(value),
        )

    def _send_brightness(self):
        value = self.brightness.get()
        self._run_action(
            "Sending brightness:{}...".format(value),
            lambda zone, device: set_brightness(value, zone=zone, device=device),
            "Brightness:{} sent".format(value),
        )


def main():
    root = tk.Tk()
    MilightColorsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
