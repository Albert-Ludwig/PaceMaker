import tkinter as tk
from tkinter import ttk, messagebox
import json

MODES = ["AOO", "VOO", "AAI", "VVI"]
DEFAULT_PARAMS = {
    "Lower Rate Limit": 60,
    "Upper Rate Limit": 120,
    "Atrial Amplitude": 3.5,
    "Atrial Pulse Width": 0.4,
    "Ventricular Amplitude": 3.5,
    "Ventricular Pulse Width": 0.4,
    "VRP": 250,
    "ARP": 250
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

        signout_btn = ttk.Button(self.root, text="Sign Out", command=self.sign_out)
        signout_btn.place(x=10, y=10)

        # Mode selection
        ttk.Label(self.root, text="Select Pacing Mode:").pack()
        self.mode_var = tk.StringVar(value=MODES[0])
        ttk.Combobox(self.root, textvariable=self.mode_var, values=MODES, state="readonly").pack()

        # Parameter inputs
        self.entries = {}
        for param in DEFAULT_PARAMS:
            frame = ttk.Frame(self.root)
            frame.pack(pady=3)
            ttk.Label(frame, text=param + ":").pack(side="left")
            entry = ttk.Entry(frame)
            entry.insert(0, str(DEFAULT_PARAMS[param]))
            entry.pack(side="left")
            self.entries[param] = entry

        # Buttons
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Apply Mode", command=self.apply_mode).pack(side="left", padx=5)
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

    def save_params(self):
        try:
            data = {param: float(self.entries[param].get()) for param in self.entries}
            with open("data/parameters.json", "w") as f:
                json.dump(data, f)
            messagebox.showinfo("Save", "Parameters saved successfully.")
        except ValueError:
            messagebox.showerror("Error", "Invalid parameter value.")

    def load_params(self):
        try:
            with open("saved_params.json", "r") as f:
                data = json.load(f)
            for param in self.entries:
                self.entries[param].delete(0, tk.END)
                self.entries[param].insert(0, str(data.get(param, DEFAULT_PARAMS[param])))
            messagebox.showinfo("Load", "Parameters loaded successfully.")
        except FileNotFoundError:
            messagebox.showerror("Error", "No saved parameters found.")

    def reset_params(self):
        for param in self.entries:
            self.entries[param].delete(0, tk.END)
            self.entries[param].insert(0, str(DEFAULT_PARAMS[param]))
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

class DashboardWindow(DCMInterface):
    pass
   