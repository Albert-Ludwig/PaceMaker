import tkinter as tk
from tkinter import ttk, messagebox
import json
from .mode_config import ParamEnum

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

        self.param = ParamEnum() #新增
        self.params = DEFAULT_PARAMS.copy()
        self.create_widgets()
    def save_params(self):
       
        try:
            data = {}
            for key in DEFAULT_PARAMS:
                getter = self._resolve_method(self.param, self._getter_candidates_for_key(key))
                if getter:
                    data[key] = getter()
            with open("data/parameters.json", "w") as f:
                json.dump(data, f, indent=2)
            messagebox.showinfo("Save", "Parameters saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_params(self):
        
        try:
            with open("data/parameters.json", "r") as f:
                data = json.load(f)
            for key, val in data.items():
                setter = self._resolve_method(self.param, self._setter_candidates_for_key(key))
                if setter:
                    setter(val)
            messagebox.showinfo("Load", "Parameters loaded successfully.")
        except FileNotFoundError:
            messagebox.showerror("Error", "No saved parameters found.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def reset_params(self):
        
        self.param = ParamEnum()
        messagebox.showinfo("Reset", "Parameters reset to defaults.")

    
    def _resolve_method(self, obj, candidates):
        for name in candidates:
            if hasattr(obj, name):
                return getattr(obj, name)
        return None

    def _getter_candidates_for_key(self, key):
        camel = "".join(p.title() for p in key.split("_"))
        snake = key.lower()
        return [
            f"get_{key}",         # get_Lower_Rate_Limit
            f"get{camel}",        # getLowerRateLimit
            f"get_{snake}",       # get_lower_rate_limit
            f"get{key}",          # getLower_Rate_Limit（备用）
        ]

    def _setter_candidates_for_key(self, key):
        camel = "".join(p.title() for p in key.split("_"))
        snake = key.lower()
        return [
            f"set_{key}",         # set_Lower_Rate_Limit
            f"set{camel}",        # setLowerRateLimit
            f"set_{snake}",       # set_lower_rate_limit
            f"set{key}",          # setLower_Rate_Limit（备用）
        ]


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
            data = {}
            for key in DEFAULT_PARAMS:
                getter = self._resolve_method(self.param, self._getter_candidates_for_key(key))
                data[key] = getter() if getter else param_entries[key].get()
            with open("data/parameters.json", "w") as f:
                json.dump(data, f, indent=2)
            messagebox.showinfo("Save", "Parameters saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def load_param_window(self, param_entries):
        try:
            with open("data/parameters.json", "r") as f:
                data = json.load(f)
            for key, val in data.items():
                setter = self._resolve_method(self.param, self._setter_candidates_for_key(key))
                if setter:
                    setter(val)
            
            for key, entry in param_entries.items():
                getter = self._resolve_method(self.param, self._getter_candidates_for_key(key))
                if getter:
                    entry.delete(0, tk.END)
                    entry.insert(0, str(getter()))
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
            frame = ttk.Frame(param_win); frame.pack(pady=3)
            ttk.Label(frame, text=f"{param}:").pack(side="left")

            getter = self._resolve_method(self.param, self._getter_candidates_for_key(param))
            value = getter() if getter else DEFAULT_PARAMS[param]

            entry = ttk.Entry(frame)
            entry.insert(0, str(value))
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
        errors = []

        # 1) 写入：调用 ParamEnum 的 setter（触发分段步进/校验）
        for key, entry in param_entries.items():
            setter = self._resolve_method(self.param, self._setter_candidates_for_key(key))
            if not setter:
                errors.append(f"{key}: setter not found")
                continue
            try:
                setter(entry.get())
            except Exception as e:
                errors.append(f"{key}: {e}")

        if errors:
            messagebox.showerror("Invalid Input", "\n".join(errors))
            return

        # 2) 读回：用 getter 把“修正后的值”（例如 0.66→0.7、3.26→3.5）刷新到界面
        for key, entry in param_entries.items():
            getter = self._resolve_method(self.param, self._getter_candidates_for_key(key))
            if getter:
                entry.delete(0, tk.END)
                entry.insert(0, str(getter()))

        messagebox.showinfo("Apply Mode", f"Mode {mode} applied.")
        # 你可以选择关窗或不关窗；若想保留界面供继续调整，就别关：
        # param_win.destroy()

class DashboardWindow(DCMInterface):
    pass
