# This file is used to store the modules for the parameter operations, including saving, loading, resetting, and applying parameters.
import tkinter as tk
from tkinter import ttk, messagebox
import json
from .mode_config import ParamEnum

DEFAULT_PARAMS = ParamEnum().get_default_values()
MODES = list(ParamEnum.MODES.keys())

class ParameterManager:
    def __init__(self):
        self.param = ParamEnum()
        self.defaults = DEFAULT_PARAMS.copy()

    def save_params(self):
        try:
            import os
            os.makedirs("data", exist_ok=True)  # Ensure directory exists
            
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
            
            loaded_mode = data.pop("Pacing_Mode", None)
            
            for key, val in data.items():
                setter = self._resolve_method(self.param, self._setter_candidates_for_key(key))
                if setter:
                    setter(val)
            messagebox.showinfo("Load", "Parameters loaded successfully.")
            return True, loaded_mode
        except FileNotFoundError:
            messagebox.showerror("Error", "No saved parameters found.")
            return False, None
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return False, None

    def reset_params(self):
        self.param = ParamEnum()
        messagebox.showinfo("Reset", "Parameters reset to defaults.")
        return True

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
        self._saved_ok = True
        self.param_win.title("Parameter Settings")
        self.param_win.geometry("500x700")
        self.param_manager = param_manager
        self.param_win.protocol("WM_DELETE_WINDOW", self._on_close)

        ttk.Label(self.param_win, text="Programmable Parameters", font=("Arial", 14)).pack(pady=10)

        # Mode selection in popup
        ttk.Label(self.param_win, text="Select Pacing Mode:").pack()
        self.mode_var = tk.StringVar(value=MODES[0])
        ttk.Combobox(self.param_win, textvariable=self.mode_var, values=MODES, state="readonly").pack()

        # Parameter inputs in popup
        self.param_entries = {}

        for param in DEFAULT_PARAMS:
            frame = ttk.Frame(self.param_win)
            frame.pack(pady=3)
            ttk.Label(frame, text=f"{param}:").pack(side="left")
            getter = self.param_manager._resolve_method(
                self.param_manager.param, 
                self.param_manager._getter_candidates_for_key(param)
            )
            value = getter() if getter else DEFAULT_PARAMS[param]
            
            # Special handling for Activity_Threshold - use Combobox
            if param == "Activity_Threshold":
                entry = ttk.Combobox(
                    frame,
                    values=["V-Low", "Low", "Med-Low", "Med", "Med-High", "High", "V-High"],
                    state="readonly",
                    width=18
                )
                entry.set(str(value) if value is not None else "Med")
                entry.bind("<<ComboboxSelected>>", self._mark_unsaved)
            else:
                # Regular entry for other parameters
                entry = ttk.Entry(frame)
                entry.insert(0, str(value))
                entry.bind("<KeyRelease>", self._mark_unsaved)
                entry.bind("<FocusOut>", self._mark_unsaved)
            
            entry.pack(side="left")
            self.param_entries[param] = entry

        # Update entry states based on mode
        def _update_entry_states(*_):
            mode = self.mode_var.get()
            required = set(ParamEnum.MODES.get(mode, set()))  
            for name, entry in self.param_entries.items():
                if name in required:
                    # For Activity_Threshold, use readonly instead of normal
                    if name == "Activity_Threshold":
                        entry.configure(state="readonly")
                    else:
                        entry.configure(state="normal")
                else:
                    entry.configure(state="disabled") 

        self.mode_var.trace_add("write", lambda *_: _update_entry_states())
        self.param_win.after(0, _update_entry_states)

        btn_frame = ttk.Frame(self.param_win)
        btn_frame.pack(pady=10)

        self.apply_btn = ttk.Button(btn_frame, text="Apply", command=self.apply, state="disabled")
        self.apply_btn.grid(row=0, column=0, padx=5)

        self.save_btn = ttk.Button(btn_frame, text="Save", command=self.save_and_round)
        self.save_btn.grid(row=0, column=1, padx=5)

        ttk.Button(btn_frame, text="Load", command=self._load_with_refresh).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Reset", command=self._reset_with_refresh).grid(row=0, column=3, padx=5)

    def _mark_unsaved(self, *args):
        self._saved_ok = False
        try:
            self.apply_btn.configure(state="disabled")
        except Exception:
            pass
    
    def _refresh_entries(self):
        """refresh all entries based on current parameter values"""
        for param_name, entry in self.param_entries.items():
            getter = self.param_manager._resolve_method(
                self.param_manager.param, 
                self.param_manager._getter_candidates_for_key(param_name)
            )
            if getter:
                current_value = getter()
                # Temporarily enable to update value
                if param_name == "Activity_Threshold":
                    entry.configure(state="readonly")
                else:
                    entry.configure(state="normal")
                
                if param_name == "Activity_Threshold":
                    entry.set(str(current_value))
                else:
                    entry.delete(0, "end")
                    entry.insert(0, str(current_value))

        # Update entry states based on current mode
        mode = self.mode_var.get()
        required = set(ParamEnum.MODES.get(mode, set()))
        for name, entry in self.param_entries.items():
            if name in required:
                if name == "Activity_Threshold":
                    entry.configure(state="readonly")
                else:
                    entry.configure(state="normal")
            else:
                entry.configure(state="disabled")
    
    def _load_with_refresh(self):
        """load parameters and refresh interface"""
        success, loaded_mode = self.param_manager.load_params()
        
        if success:
            if loaded_mode and loaded_mode in MODES:
                self.mode_var.set(loaded_mode)
                
            self._refresh_entries()
            self._saved_ok = True
            self.apply_btn.configure(state="normal")

    def _reset_with_refresh(self):
        """reset parameters and refresh interface"""
        success = self.param_manager.reset_params()
        if success:
            self._refresh_entries()
            self._saved_ok = True
            self.apply_btn.configure(state="normal")

    def save_and_round(self):
        import json, os
        mode = self.mode_var.get()
        required = set(ParamEnum.MODES.get(mode, set()))
        try:
            self.apply_btn.configure(state="disabled")
        except Exception:
            pass
        errors = []
        for name in required:
            if name not in self.param_entries:
                continue
            entry = self.param_entries[name]
            if str(entry.cget("state")) == "disabled":
                continue
            
            # Get value from Combobox or Entry
            if name == "Activity_Threshold":
                raw = entry.get()
            else:
                raw = entry.get()
            
            setter_name = f"set_{name}"
            if not hasattr(self.param_manager.param, setter_name):
                errors.append(f"{name}: setter not found")
                continue
            try:
                getattr(self.param_manager.param, setter_name)(raw)
            except Exception as e:
                errors.append(f"{name}: {e}")
        
        if errors:
            messagebox.showerror("Invalid Input", "\n".join(errors))
            self._saved_ok = False
            return
        
        # Refresh display with rounded values
        for name in required:
            if name not in self.param_entries:
                continue
            entry = self.param_entries[name]
            getter_name = f"get_{name}"
            if hasattr(self.param_manager.param, getter_name):
                try:
                    v = getattr(self.param_manager.param, getter_name)()
                    if name == "Activity_Threshold":
                        entry.configure(state="readonly")
                        entry.set(str(v))
                    else:
                        entry.configure(state="normal")
                        entry.delete(0, "end")
                        entry.insert(0, str(v))
                except Exception:
                    pass
        
        # Save all parameters to JSON
        all_keys = set()
        for s in ParamEnum.MODES.values():
            all_keys |= set(s)
        data = {}
        
        data["Pacing_Mode"] = mode
        
        for key in all_keys:
            g = f"get_{key}"
            if hasattr(self.param_manager.param, g):
                try:
                    data[key] = getattr(self.param_manager.param, g)()
                except Exception:
                    pass
        os.makedirs("data", exist_ok=True)
        with open(os.path.join("data", "parameters.json"), "w") as f:
            json.dump(data, f, indent=2)
        self._saved_ok = True
        try:
            self.apply_btn.configure(state="normal")
        except Exception:
            pass
        messagebox.showinfo("Saved", "The newest input values are rounded and saved.")

    def apply(self):
        if not getattr(self, "_saved_ok", False):
            try:
                self.apply_btn.configure(state="disabled")
            except Exception:
                pass
            
        mode = self.mode_var.get()
        required = set(ParamEnum.MODES.get(mode, set()))
        for name, entry in self.param_entries.items():
            if name in required:
                if name == "Activity_Threshold":
                    entry.configure(state="readonly")
                else:
                    entry.configure(state="normal")
            else:
                entry.configure(state="disabled")
        messagebox.showinfo("Apply", f"Mode {mode} applied.")

    def _on_close(self):
        if not getattr(self, "_saved_ok", False):
            if not messagebox.askokcancel(
                "Unsaved Changes",
                "The new changes on parameters have not saved. Close anyway?"
            ):
                return
        self.param_win.destroy()