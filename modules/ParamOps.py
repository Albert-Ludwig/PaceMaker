# This module manages parameter saving, loading, resetting, and the GUI for parameter settings.
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from .mode_config import ParamEnum
from typing import Optional

try:
    from .Communication import PacemakerCommunication
except ImportError:
    from modules.Communication import PacemakerCommunication


DEFAULT_PARAMS = ParamEnum().get_default_values()
MODES = list(ParamEnum.MODES.keys())

class ParameterManager:
    def __init__(self):
        self.param = ParamEnum()
        self.defaults = DEFAULT_PARAMS.copy()
        self.pacing_mode = "AOO"

    def save_params(self):
        try:
            os.makedirs("data", exist_ok=True)
            
            all_keys = set(self.defaults.keys())
            for s in ParamEnum.MODES.values():
                all_keys |= set(s)
            
            data = {}
            data["Pacing_Mode"] = self.pacing_mode
            
            for key in all_keys:
                getter = self._resolve_method(self.param, self._getter_candidates_for_key(key))
                if getter:
                    try:
                        data[key] = getter()
                    except Exception:
                        pass
            
            with open("data/parameters.json", "w") as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_params(self):
        try:
            with open("data/parameters.json", "r") as f:
                data = json.load(f)
            
            loaded_mode = data.get("Pacing_Mode")
            if loaded_mode and loaded_mode in MODES:
                self.pacing_mode = loaded_mode
            
            for key, val in data.items():
                if key == "Pacing_Mode":
                    continue
                setter = self._resolve_method(self.param, self._setter_candidates_for_key(key))
                if setter:
                    try:
                        setter(val)
                    except Exception:
                        pass
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"Error loading JSON: {e}")
            return False

    def reset_params(self):
        self.param = ParamEnum()
        self.pacing_mode = "AOO"
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
    def __init__(self, parent, param_manager, comm_manager: Optional[PacemakerCommunication]):
        self.param_win = tk.Toplevel(parent)
        self._saved_ok = True
        self._device_synced = False 
        self._applied_after_save = True 
        self.param_win.title("Parameter Settings")
        self.param_win.geometry("900x500")
        self.param_manager = param_manager
        self.comm_manager = comm_manager
        self.param_win.protocol("WM_DELETE_WINDOW", self._on_close)

        ttk.Label(self.param_win, text="Programmable Parameters", font=("Arial", 14)).pack(pady=10)

        self.param_manager.load_params()
        initial_mode = self.param_manager.pacing_mode

        ttk.Label(self.param_win, text="Select Pacing Mode:").pack()
        self.mode_var = tk.StringVar(value=initial_mode)
        ttk.Combobox(self.param_win, textvariable=self.mode_var, values=MODES, state="readonly").pack()

        main_param_frame = ttk.Frame(self.param_win)
        main_param_frame.pack(fill="x", expand=True, padx=10, pady=5)

        frame_left = ttk.Frame(main_param_frame)
        frame_left.pack(side="left", fill="x", expand=True, padx=10, anchor="n")

        frame_right = ttk.Frame(main_param_frame)
        frame_right.pack(side="right", fill="x", expand=True, padx=10, anchor="n")

        params_list = list(DEFAULT_PARAMS.keys())
        midpoint = (len(params_list) + 1) // 2

        self.param_entries = {}

        for i, param in enumerate(params_list):
            parent_frame = frame_left if i < midpoint else frame_right

            frame = ttk.Frame(parent_frame)
            frame.pack(pady=3, fill='x')
            
            ttk.Label(frame, text=f"{param}:", width=22, anchor="w").pack(side="left")
            
            getter = self.param_manager._resolve_method(
                self.param_manager.param, 
                self.param_manager._getter_candidates_for_key(param)
            )
            value = getter() if getter else DEFAULT_PARAMS[param]
            
            if param == "Activity_Threshold":
                entry = ttk.Combobox(
                    frame,
                    values=["V-Low", "Low", "Med-Low", "Med", "Med-High", "High", "V-High"],
                    state="readonly",
                    width=15
                )
                entry.set(str(value) if value is not None else "Med")
                entry.bind("<<ComboboxSelected>>", self._mark_unsaved)
            elif param == "Hysteresis":
                entry = ttk.Combobox(
                    frame,
                    values=["Off", "On"],
                    state="readonly",
                    width=15
                )
                entry.set(str(value) if value is not None else "Off")
                entry.bind("<<ComboboxSelected>>", self._mark_unsaved)
            elif param == "Rate_Smoothing":
                entry = ttk.Combobox(
                    frame,
                    values=["Off", "3%", "6%", "9%", "12%", "15%", "18%", "21%", "25%"],
                    state="readonly",
                    width=15
                )
                entry.set(str(value) if value is not None else "Off")
                entry.bind("<<ComboboxSelected>>", self._mark_unsaved)
            else:
                entry = ttk.Entry(frame, width=18)
                entry.insert(0, str(value))
                entry.bind("<KeyRelease>", self._mark_unsaved)
                entry.bind("<FocusOut>", self._mark_unsaved)
            
            entry.pack(side="left", fill='x', expand=True, padx=5)
            self.param_entries[param] = entry

        def _update_entry_states(*_):
            mode = self.mode_var.get()
            required = set(ParamEnum.MODES.get(mode, set()))  
            for name, entry in self.param_entries.items():
                if name in required:
                    if name in {"Activity_Threshold", "Hysteresis", "Rate_Smoothing"}:
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

        self.load_btn = ttk.Button(btn_frame, text="Load to Pacemaker", command=self._upload_from_json, state="disabled")
        self.load_btn.grid(row=0, column=2, padx=5)
        
        ttk.Button(btn_frame, text="Reset", command=self._reset_with_refresh).grid(row=0, column=3, padx=5)

    def _mark_unsaved(self, *args):
        self._saved_ok = False
        self._device_synced = False
        try:
            self.apply_btn.configure(state="disabled")
            self.load_btn.configure(state="disabled")
        except Exception:
            pass
    
    def _refresh_entries(self):
        for param_name, entry in self.param_entries.items():
            getter = self.param_manager._resolve_method(
                self.param_manager.param, 
                self.param_manager._getter_candidates_for_key(param_name)
            )
            if getter:
                current_value = getter()
                
                is_readonly = (str(entry.cget("state")) == "readonly")
                if is_readonly:
                    entry.configure(state="normal")
                
                if isinstance(entry, ttk.Combobox):
                    entry.set(str(current_value))
                elif isinstance(entry, ttk.Entry):
                    entry.delete(0, "end")
                    entry.insert(0, str(current_value))
                
                if param_name in {"Activity_Threshold", "Hysteresis", "Rate_Smoothing"}:
                    entry.configure(state="readonly")

        mode = self.mode_var.get()
        required = set(ParamEnum.MODES.get(mode, set()))
        for name, entry in self.param_entries.items():
            if name in required:
                if name in {"Activity_Threshold", "Hysteresis", "Rate_Smoothing"}:
                    entry.configure(state="readonly")
                else:
                    entry.configure(state="normal")
            else:
                entry.configure(state="disabled")
    
    def _upload_from_json(self):
        if self.comm_manager is None or not self.comm_manager.get_connection_status():
            messagebox.showerror("Connection Error", "Pacemaker is NOT connected. Cannot upload.")
            return

        success = self.param_manager.load_params()
        if not success:
            messagebox.showerror("File Error", "Failed to load parameters.json")
            return

        if self.param_manager.pacing_mode in MODES:
            self.mode_var.set(self.param_manager.pacing_mode)
        self._refresh_entries()
        
        mode_str = self.mode_var.get()
        mode_int = MODES.index(mode_str)

        params_to_send = {}
        for key in DEFAULT_PARAMS.keys():
            getter = self.param_manager._resolve_method(
                self.param_manager.param, 
                self.param_manager._getter_candidates_for_key(key)
            )
            if getter:
                params_to_send[key] = getter()
        
        result = self.comm_manager.upload_parameters(
            mode=mode_int, 
            parameters=params_to_send
        )
        
        if result['success']:
            self._device_synced = True
            messagebox.showinfo("Success", "JSON parameters loaded and uploaded to Pacemaker successfully!")
        else:
            self._device_synced = False
            messagebox.showerror("Upload Failed", f"Device communication error: {result['message']}")

    def _reset_with_refresh(self):
        success = self.param_manager.reset_params()
        if success:
            self.mode_var.set(self.param_manager.pacing_mode)
            self._refresh_entries()
            self._saved_ok = False
            self._device_synced = False
            self.apply_btn.configure(state="disabled")
            self.load_btn.configure(state="disabled")

    def save_and_round(self):
        mode = self.mode_var.get()
        required = set(ParamEnum.MODES.get(mode, set()))
        self._device_synced = False
        self._applied_after_save = False
        try:
            self.apply_btn.configure(state="disabled")
            self.load_btn.configure(state="disabled")
        except Exception:
            pass
        errors = []
        for name in required:
            if name not in self.param_entries:
                continue
            entry = self.param_entries[name]
            if str(entry.cget("state")) == "disabled":
                continue
            
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
        
        for name in required:
            if name not in self.param_entries:
                continue
            entry = self.param_entries[name]
            getter_name = f"get_{name}"
            if hasattr(self.param_manager.param, getter_name):
                try:
                    v = getattr(self.param_manager.param, getter_name)()
                    if str(entry.cget("state")) == "readonly":
                        if hasattr(entry, "set"):
                             entry.set(str(v))
                    else:
                        entry.delete(0, "end")
                        entry.insert(0, str(v))
                except Exception:
                    pass
        
        self.param_manager.pacing_mode = mode
        self.param_manager.save_params()

        self._saved_ok = True
        try:
            self.apply_btn.configure(state="normal")
            self.load_btn.configure(state="disabled")
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
                if name in {"Activity_Threshold", "Hysteresis", "Rate_Smoothing"}:
                    entry.configure(state="readonly")
                else:
                    entry.configure(state="normal")
            else:
                entry.configure(state="disabled")
        
        self._applied_after_save = True  
        self.param_manager.pacing_mode = mode

        try:
            self.load_btn.configure(state="normal")
        except Exception:
            pass

        messagebox.showinfo("Apply", f"Mode {mode} applied locally.")

    def _on_close(self):
        if not getattr(self, "_saved_ok", False):
            if not messagebox.askokcancel(
                "Unsaved Changes",
                "The new changes on parameters have not saved. Close anyway?"
            ):
                return
        self.param_win.destroy()