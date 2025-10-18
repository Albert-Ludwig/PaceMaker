# This files contains the all windows operations, including the pop up/close and display.
import tkinter as tk
from tkinter import ttk
from modules.mode_config import ParamEnum
from modules.ParamOps import ParameterManager, ParameterWindow
from modules.EGdiagram import EgramWindow
from modules.Help_Window import HelpWindow

# import the modes, parameters, and default values from mode_config.py
DEFAULT_PARAMS = ParamEnum().get_default_values()
MODES = list(ParamEnum.MODES.keys())

class DCMInterface:
    def __init__(self, root, username):
        self.root = root
        self.root.title("DCM Interface")
        self.root.geometry("900x700")
        self.username = username
        
        #@@@ D1: Only keep the boolean rather than read the serial communication.
        self.device_id = "PACEMAKER-001"
        self.last_device_id = "PACEMAKER-001" 
        self.is_connected = True 
        self.out_of_range = False
        self.noise_unstable = False
        #@@@ end

        self.egram_window = None
        self.param_manager = ParameterManager()
        self.entries = {param: str(self.param_manager.defaults[param]) for param in self.param_manager.defaults}
        self.mode_var = tk.StringVar()
        self.mode_var.set(MODES[0] if MODES else "AOO")
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self.root, text=f"Welcome, {self.username}", font=("Arial", 18)).pack(pady=30)

        # Sign out button
        signout_btn = ttk.Button(self.root, text="Sign Out", command=self.sign_out)
        signout_btn.place(x=10, y=10)

        # log out button
        logout_btn = ttk.Button(self.root, text="Log Out", command=self.confirm_logout)
        logout_btn.place(x=10, y=50)

        # View Parameters button
        view_params_btn = ttk.Button(self.root, text="View Parameters", command=self.open_param_window)
        view_params_btn.place(relx=0.5, y=320, anchor="center")

        # EG diagram button
        eg_diagram_btn = ttk.Button(self.root, text="EG Diagram", command=self.open_egram_window)
        eg_diagram_btn.place(relx=0.5, y=360, anchor="center")

        # Status indicators
        self.status_label = ttk.Label(self.root, text="", font=("Arial", 12))
        self.status_label.pack(pady=(2, 5)) 

        self.device_label = ttk.Label(self.root, text="", font=("Arial", 12))
        self.device_label.pack(pady=5)

        self.new_device_warning_label = ttk.Label(self.root, text="", font=("Arial", 12))
        self.new_device_warning_label.pack(pady=5)

        self.noise_warning_label = ttk.Label(self.root, text="", font=("Arial", 12))
        self.noise_warning_label.pack(pady=5)

        self.out_of_range_warning_label = ttk.Label(self.root, text="", font=("Arial", 12))
        self.out_of_range_warning_label.pack(pady=5)

        # help button
        help_btn = ttk.Button(self.root, text="Help", command=self.open_help_window)
        help_btn.place(x=10, y=650)

        self.update_status()
        self.check_device_identity()
        self.out_of_range_detection()
        self.noise_unstable_detection()

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
    
    def noise_unstable_detection(self):
        if self.noise_unstable:
            self.noise_warning_label.config(text="⚠️ Noise/Unstable serial connection!", foreground="orange")
        else:
            self.noise_warning_label.config(text="")

    def out_of_range_detection(self):
        if self.out_of_range:
            self.out_of_range_warning_label.config(text="⚠️ Communication out of range!", foreground="orange")
        else:
            self.out_of_range_warning_label.config(text="")

    def check_device_identity(self):
        if self.device_id != self.last_device_id:
            self.new_device_warning_label.config(text="🔔 New device detected!", foreground="red")
        else:
            self.new_device_warning_label.config(text="")

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
    
    def open_help_window(self):
        # Check if help window already exists
        if hasattr(self, 'help_window') and self.help_window and self.help_window.help_win.winfo_exists():
            self.help_window.help_win.lift()  # Bring to front if exists
            return
        
        # Create new help window
        self.help_window = HelpWindow(self.root)
    
    def open_egram_window(self):
        """Open the EG diagram window"""
        try:
            if (self.egram_window and 
                hasattr(self.egram_window, 'window') and 
                self.egram_window.window.winfo_exists()):
                self.egram_window.window.lift()  
                return
        except tk.TclError:
            self.egram_window = None

        self.egram_window = EgramWindow(self.root)
    

class DashboardWindow(DCMInterface):
    pass