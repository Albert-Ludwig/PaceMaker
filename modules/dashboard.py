# This files contains the 
import tkinter as tk
from tkinter import ttk, messagebox
from .mode_config import ParamEnum
from modules.ParamOps import ParameterManager, ParameterWindow

# import the modes, parameters, and default values from mode_config.py
MODES = list(ParamEnum.MODES.keys())
_defaults_obj = ParamEnum()
DEFAULT_PARAMS = {
    # D1
    "Lower_Rate_Limit":        _defaults_obj.get_Lower_Rate_Limit(),
    "Upper_Rate_Limit":        _defaults_obj.get_Upper_Rate_Limit(),
    "Atrial_Amplitude":        _defaults_obj.get_Atrial_Amplitude(),
    "Ventricular_Amplitude":   _defaults_obj.get_Ventricular_Amplitude(),
    "Atrial_Pulse_Width":      _defaults_obj.get_Atrial_Pulse_Width(),
    "Ventricular_Pulse_Width": _defaults_obj.get_Ventricular_Pulse_Width(),
    "ARP":                     _defaults_obj.get_ARP(),
    "VRP":                     _defaults_obj.get_VRP(),

    # D2
    # "Maximum_Sensor_Rate":     _defaults_obj.Maximum_Sensor_Rate,
    # "Activity_Threshold":      _defaults_obj.Activity_Threshold,
    # "Response_Factor":         _defaults_obj.Response_Factor,
    # "Reaction_Time":           _defaults_obj.Reaction_Time,
    # "Recovery_Time":           _defaults_obj.Recovery_Time
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

        self.param_manager = ParameterManager()
        self.entries = {param: str(self.param_manager.defaults[param]) for param in self.param_manager.defaults}
        self.mode_var = tk.StringVar()
        self.mode_var.set(MODES[0] if MODES else "AOO")
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self.root, text=f"Welcome, {self.username}", font=("Arial", 18)).pack(pady=10)

        # Sign out button
        signout_btn = ttk.Button(self.root, text="Sign Out", command=self.sign_out)
        signout_btn.place(x=10, y=10)

        # log out button
        logout_btn = ttk.Button(self.root, text="Log Out", command=self.confirm_logout)
        logout_btn.place(x=10, y=50)

        # View Parameters button
        view_params_btn = ttk.Button(self.root, text="View Parameters", command=self.open_param_window)
        view_params_btn.place(relx=0.5, y=200, anchor="center")

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

    def confirm_logout(self):
        from tkinter import messagebox
        response = messagebox.askokcancel("Confirm Logout", "This account will be logged out")
        if response:
            from modules.auth import logout_account
            success = logout_account(self.username, "data/users.json")  
            if success:
                messagebox.showinfo("Success", "Account has been logged out.")
                self.sign_out()  
            else:
                messagebox.showerror("Error", "Failed to log out. Account not found.")


    def open_param_window(self):
        ParameterWindow(self.root, self.param_manager)

class DashboardWindow(DCMInterface):
    pass
