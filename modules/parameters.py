import tkinter as tk
from tkinter import ttk, messagebox
import json
from .mode_config import ParamEnum

MODES = list(ParamEnum.MODES.keys())
_defaults_obj = ParamEnum()
DEFAULT_PARAMS = {
    "Lower_Rate_Limit":        _defaults_obj.get_Lower_Rate_Limit(),
    "Upper_Rate_Limit":        _defaults_obj.get_Upper_Rate_Limit(),
    "Atrial_Amplitude":        _defaults_obj.get_Atrial_Amplitude(),
    "Ventricular_Amplitude":   _defaults_obj.get_Ventricular_Amplitude(),
    "Atrial_Pulse_Width":      _defaults_obj.get_Atrial_Pulse_Width(),
    "Ventricular_Pulse_Width": _defaults_obj.get_Ventricular_Pulse_Width(),
    "ARP":                     _defaults_obj.get_ARP(),
    "VRP":                     _defaults_obj.get_VRP(),
}

class ParameterManager:
    def __init__(self):
        self.param = ParamEnum()
        self.defaults = DEFAULT_PARAMS.copy()

    def save_params(self):
        try:
            data = {}
            for key in self.defaults:
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
            f"get_{key}",
            f"get{camel}",
            f"get_{snake}",
            f"get{key}",
        ]

    def _setter_candidates_for_key(self, key):
        camel = "".join(p.title() for p in key.split("_"))
        snake = key.lower()
        return [
            f"set_{key}",
            f"set{camel}",
            f"set_{snake}",
            f"set{key}",
        ]

class ParameterWindow:
    def __init__(self, parent, param_manager):
        self.param_win = tk.Toplevel(parent)
        self.param_win.title("Parameter Settings")
        self.param_win.geometry("500x700")
        self.param_manager = param_manager

        ttk.Label(self.param_win, text="Programmable Parameters", font=("Arial", 14)).pack(pady=10)

        # Mode selection in popup
        ttk.Label(self.param_win, text="Select Pacing Mode:").pack()
        self.mode_var = tk.StringVar(value=MODES[0])
        ttk.Combobox(self.param_win, textvariable=self.mode_var, values=MODES, state="readonly").pack()

        # Parameter inputs in popup
        self.param_entries = {}
        for param in DEFAULT_PARAMS:
            frame = ttk.Frame(self.param_win); frame.pack(pady=3)
            ttk.Label(frame, text=f"{param}:").pack(side="left")
            getter = self.param_manager._resolve_method(self.param_manager.param, self.param_manager._getter_candidates_for_key(param))
            value = getter() if getter else DEFAULT_PARAMS[param]
            entry = ttk.Entry(frame)
            entry.insert(0, str(value))
            entry.pack(side="left")
            self.param_entries[param] = entry

        btn_frame = ttk.Frame(self.param_win)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Apply", command=self.apply).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Load", command=self.load).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Reset", command=self.reset).pack(side="left", padx=5)

    def apply(self):
        mode = self.mode_var.get()
        errors = []
        for key, entry in self.param_entries.items():
            setter = self.param_manager._resolve_method(self.param_manager.param, self.param_manager._setter_candidates_for_key(key))
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
        for key, entry in self.param_entries.items():
            getter = self.param_manager._resolve_method(self.param_manager.param, self.param_manager._getter_candidates_for_key(key))
            if getter:
                entry.delete(0, tk.END)
                entry.insert(0, str(getter()))
        messagebox.showinfo("Apply Mode", f"Mode {mode} applied.")
        # self.param_win.destroy() # Uncomment to close window after apply
