import threading
import tkinter as tk
from tkinter import ttk

from milight_toggle import ZONE, close_client, create_client, remembered_light_state, scan_devices, toggle_device


class MilightToggleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MiLight Toggle")
        self.root.geometry("360x220")
        self.root.minsize(340, 210)
        self.root.configure(bg="#f4f6f8")

        self.status_var = tk.StringVar(value="Готово")
        self.device_var = tk.StringVar(value="Устройство не выбрано")

        self._build_style()
        self._build_layout()
        self._sync_button_label()

    def _build_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Frame.TFrame", background="#f4f6f8")
        style.configure("Title.TLabel", background="#f4f6f8", foreground="#16202a", font=("Segoe UI", 16, "bold"))
        style.configure("Status.TLabel", background="#f4f6f8", foreground="#52616f", font=("Segoe UI", 10))
        style.configure("Device.TLabel", background="#f4f6f8", foreground="#2d3a45", font=("Segoe UI", 9))
        style.configure("Toggle.TButton", font=("Segoe UI", 15, "bold"), padding=(18, 14))

    def _build_layout(self):
        frame = ttk.Frame(self.root, style="Frame.TFrame", padding=24)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(0, weight=1)

        title = ttk.Label(frame, text="MiLight iBox2", style="Title.TLabel", anchor="center")
        title.grid(row=0, column=0, sticky="ew")

        self.toggle_button = ttk.Button(
            frame,
            text="Включить / выключить",
            style="Toggle.TButton",
            command=self.toggle_light,
        )
        self.toggle_button.grid(row=1, column=0, sticky="ew", pady=(22, 18))

        status = ttk.Label(frame, textvariable=self.status_var, style="Status.TLabel", anchor="center")
        status.grid(row=2, column=0, sticky="ew")

        device = ttk.Label(frame, textvariable=self.device_var, style="Device.TLabel", anchor="center")
        device.grid(row=3, column=0, sticky="ew", pady=(10, 0))

    def _sync_button_label(self):
        is_on = remembered_light_state()
        if is_on is True:
            self.toggle_button.configure(text="Выключить")
        elif is_on is False:
            self.toggle_button.configure(text="Включить")
        else:
            self.toggle_button.configure(text="Включить / выключить")

    def toggle_light(self):
        self.toggle_button.configure(state=tk.DISABLED)
        self.status_var.set("Поиск iBox2 в сети...")
        self.device_var.set("Зона {}".format(ZONE))

        worker = threading.Thread(target=self._toggle_worker, daemon=True)
        worker.start()

    def _toggle_worker(self):
        client = None
        try:
            client = create_client()
            devices = scan_devices(client)
            if not devices:
                close_client(client)
                raise RuntimeError("iBox2 не найден в локальной сети")

            device = devices[0]
            is_on = toggle_device(client, device)
            self.root.after(0, lambda: self._show_success(device, is_on))
        except Exception as exc:
            if client is not None:
                close_client(client)
            message = str(exc)
            self.root.after(0, lambda: self._show_error(message))

    def _show_success(self, device, is_on):
        if is_on:
            self.status_var.set("Свет включен")
            self.toggle_button.configure(text="Выключить")
        else:
            self.status_var.set("Свет выключен")
            self.toggle_button.configure(text="Включить")

        self.device_var.set("{}:{}  |  зона {}".format(device["ip"], device["port"], ZONE))
        self.toggle_button.configure(state=tk.NORMAL)

    def _show_error(self, message):
        self.status_var.set(message)
        self._sync_button_label()
        self.toggle_button.configure(state=tk.NORMAL)


def main():
    root = tk.Tk()
    app = MilightToggleApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
