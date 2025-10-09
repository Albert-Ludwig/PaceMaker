import tkinter as tk
from tkinter import ttk, messagebox
import json
from .mode_config import ParamEnum

# import the modes, parameters, and default values from mode_config.py
MODES = list(ParamEnum.MODES.keys())
_defaults_obj = ParamEnum()
DEFAULT_PARAMS = {
    "Lower Rate Limit": _defaults_obj.get_default_lrl(),
    "Upper Rate Limit": _defaults_obj.get_default_url(),
    "Atrial Amplitude": _defaults_obj.get_default_amplitude(),
    "Atrial Pulse Width": _defaults_obj.get_default_pulse_width(),
    "Ventricular Amplitude": _defaults_obj.get_default_amplitude(),
    "Ventricular Pulse Width": _defaults_obj.get_default_pulse_width(),
    "VRP": _defaults_obj.get_default_vrp(),
    "ARP": _defaults_obj.get_default_arp(),
}

class DCMInterface:
    def __init__(self, root, username):
        self.root = root
        self.root.title("DCM Interface")
        self.root.geometry("900x700")
        self.username = username

        self.device_id = "PACEMAKER-001"
        self.last_device_id = "PACEMAKER-001"  # Simulate stored device ID
        self.is_connected = True  # Simulated connection status

        self.params = DEFAULT_PARAMS.copy()
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self.root, text=f"Welcome, {self.username}", font=("Arial", 18)).pack(pady=10)

        # Sign out button
        signout_btn = ttk.Button(self.root, text="Sign Out", command=self.sign_out)
        signout_btn.place(x=10, y=10)

        # View Parameters button
        view_params_btn = ttk.Button(self.root, text="View Parameters", command=self.open_param_window)
        view_params_btn.place(x=10, y=50)

        # Prepare entries dict for popup use only
        self.entries = {param: str(DEFAULT_PARAMS[param]) for param in DEFAULT_PARAMS}

        # Action buttons
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Save Parameters", command=self.save_params).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Load Parameters", command=self.load_params).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Reset to Defaults", command=self.reset_params).pack(side="left", padx=5)

        # Status indicators
        self.status_label = ttk.Label(self.root, text="", font=("Arial", 12))
        self.status_label.pack(pady=10)

        self.device_label = ttk.Label(self.root, text="", font=("Arial", 12))
        self.device_label.pack(pady=5)

        self.warning_label = ttk.Label(self.root, text="", font=("Arial", 12), foreground="orange")
        self.warning_label.pack(pady=5)

        self.update_status()

    def apply_mode(self):
        mode = self.mode_var.get()
        self.status_label.config(text=f"Mode {mode} applied.")
        self.check_device_identity()

    def save_param_window(self, param_entries):
        try:
            data = {param: float(entry.get()) for param, entry in param_entries.items()}
            with open("data/parameters.json", "w") as f:
                json.dump(data, f, indent=2)
            messagebox.showinfo("Save", "Parameters saved successfully.")
        except ValueError:
            messagebox.showerror("Error", "Invalid parameter value.")

    def load_param_window(self, param_entries):
        try:
            with open("data/parameters.json", "r") as f:
                data = json.load(f)
            for param, entry in param_entries.items():
                entry.delete(0, tk.END)
                entry.insert(0, str(data.get(param, DEFAULT_PARAMS[param])))
            messagebox.showinfo("Load", "Parameters loaded successfully.")
        except FileNotFoundError:
            messagebox.showerror("Error", "No saved parameters found.")

    def reset_param_window(self, param_entries):
        for param, entry in param_entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, str(DEFAULT_PARAMS[param]))
        messagebox.showinfo("Reset", "Parameters reset to defaults.")

    def update_status(self):
        if self.is_connected:
            self.status_label.config(text="Status: Connected ✅", foreground="green")
        else:
            self.status_label.config(text="Status: Disconnected ❌", foreground="red")
        self.device_label.config(text=f"Device ID: {self.device_id}")

    def check_device_identity(self):
        if self.device_id != self.last_device_id:
            self.warning_label.config(text="⚠️ New device detected!")
        else:
            self.warning_label.config(text="")

    def sign_out(self):
        self.root.destroy()
        import main
        main.main()


    def open_param_window(self):
        param_win = tk.Toplevel(self.root)
        param_win.title("Parameter Settings")
        param_win.geometry("500x700")

        ttk.Label(param_win, text="Programmable Parameters", font=("Arial", 14)).pack(pady=10)

        # Mode selection in popup
        ttk.Label(param_win, text="Select Pacing Mode:").pack()
        mode_var = tk.StringVar(value=MODES[0])
        ttk.Combobox(param_win, textvariable=mode_var, values=MODES, state="readonly").pack()

        # Parameter inputs in popup
        param_entries = {}
        for param in DEFAULT_PARAMS:
            frame = ttk.Frame(param_win)
            frame.pack(pady=3)
            ttk.Label(frame, text=f"{param}:").pack(side="left")
            entry = ttk.Entry(frame)
            entry.insert(0, str(DEFAULT_PARAMS[param]))
            entry.pack(side="left")
            param_entries[param] = entry

        btn_frame = ttk.Frame(param_win)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Apply", command=lambda: self.apply_popup(mode_var, param_entries, param_win)).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Save", command=lambda: self.save_param_window(param_entries)).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Load", command=lambda: self.load_param_window(param_entries)).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Reset", command=lambda: self.reset_param_window(param_entries)).pack(side="left", padx=5)

    def apply_popup(self, mode_var, param_entries, param_win):
        mode = mode_var.get()
        # Optionally update self.mode_var if you want to sync
        # self.mode_var = mode_var
        # Update self.entries with new values
        for param, entry in param_entries.items():
            self.entries[param] = entry.get()
        # Show confirmation (or call backend logic here)
        messagebox.showinfo("Apply Mode", f"Mode {mode} applied with parameters.")
        param_win.destroy()


class DashboardWindow(DCMInterface):
    pass
