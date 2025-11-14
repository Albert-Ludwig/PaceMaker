# This files contains the all windows operations, including the pop up/close and display.
import tkinter as tk
from tkinter import ttk, messagebox
from modules.mode_config import ParamEnum
from modules.ParamOps import ParameterManager, ParameterWindow
from modules.EGdiagram import EgramWindow
from modules.Help_Window import HelpWindow
from modules.Communication import PacemakerCommunication
from modules.Serial_Manager import SerialManager

# import the modes, parameters, and default values from mode_config.py
DEFAULT_PARAMS = ParamEnum().get_default_values()
MODES = list(ParamEnum.MODES.keys())

class DCMInterface:
    def __init__(self, root, username):
        self.root = root
        self.root.title("DCM Interface")
        self.root.geometry("900x700")
        self.username = username
        
        self.device_id = None # MODIFIED: Will hold the logical name (e.g., PACEMAKER-001)
        self.last_device_id = None # MODIFIED: Tracks the previous logical name
        self.is_connected = False
        self.comm_manager = None

        # initialize parameters
        self.param_window = None 
        self.egram_window = None
        self.help_window = None
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
        # Device ID display
        self.device_label = ttk.Label(self.root, text="", font=("Arial", 12))
        self.device_label.pack(pady=5)
        # New device warning
        self.new_device_warning_label = ttk.Label(self.root, text="", font=("Arial", 12))
        self.new_device_warning_label.pack(pady=5)

        # help button
        help_btn = ttk.Button(self.root, text="Help", command=self.open_help_window)
        help_btn.place(x=10, y=650)

        # port selection frame
        port_frame = ttk.Frame(self.root, padding=10)
        port_frame.place(relx=0.5, y=450, anchor="center")
        
        ttk.Label(port_frame, text="Select Port:").pack(side="left", padx=5)
    
        self.port_combobox = ttk.Combobox(
            port_frame,
            values=self.get_available_ports(),
            state="readonly",
            width=25
        )
        self.port_combobox.pack(side="left", padx=5)
        
        ttk.Button(port_frame, text="Refresh Ports", command=self.refresh_ports).pack(side="left", padx=5)
        ttk.Button(port_frame, text="Connect", command=self.toggle_connect).pack(side="left", padx=5)

        # This call will run check_device_identity before anything is connected
        self.update_status()
        self.check_device_identity()

    def apply_mode(self):
        """Apply selected mode"""
        mode = self.mode_var.get()
        self.status_label.config(text=f"Mode {mode} applied.")
        self.check_device_identity()

    def update_status(self):
        """Update connection status and device ID"""
        if self.is_connected:
            self.status_label.config(text="Status: Connected ✅", foreground="green")
        else:
            self.status_label.config(text="Status: Disconnected ❌", foreground="red")
        
        # MODIFIED: Show the logical device ID, or "--" if not connected
        device_display_name = self.device_id if self.device_id else "--"
        self.device_label.config(text=f"Device ID: {device_display_name}")

    def check_device_identity(self):
        """Check for new device connection"""
        # MODIFIED: This function now relies on comm_manager to get the logical name
        if self.comm_manager is None:
            # If no comm_manager, reset all device IDs
            self.device_id = None
            self.last_device_id = None
            self.device_label.config(text="Device ID: --")
            self.new_device_warning_label.config(text="")
            return

        # Get logical name info from the communication manager
        info = self.comm_manager.check_device_identity()
        current = info.get("device_id")
        last = info.get("last_device_id")
        is_same = info.get("is_same", False)

        # Store the names in the dashboard class
        self.last_device_id = last
        self.device_id = current if current is not None else "--"

        # Update the UI label
        self.device_label.config(text=f"Device ID: {self.device_id}")

        # Show a warning if the device name changed
        if current is not None and last is not None and not is_same:
            self.new_device_warning_label.config(text="🔔 New device detected!", foreground="red")
        else:
            self.new_device_warning_label.config(text="")


    def sign_out(self):
        """Sign out and return to welcome window"""
        self.root.destroy()
        import main
        main.main()

    def confirm_logout(self):
        """Confirm and log out account"""
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
        """Open parameter configuration window"""
        try:
            if (self.param_window is not None and 
                hasattr(self.param_window, 'param_win') and 
                self.param_window.param_win.winfo_exists()):
                self.param_window.param_win.lift()  
                return
        except (tk.TclError, AttributeError):
            self.param_window = None

        self.param_window = ParameterWindow(self.root, self.param_manager, self.comm_manager)
    
    def open_help_window(self):
        """Open help window"""
        try:
            if (self.help_window is not None and 
                hasattr(self.help_window, 'help_win') and 
                self.help_window.help_win.winfo_exists()):
                self.help_window.help_win.lift()
                return
        except (tk.TclError, AttributeError):
            self.help_window = None

        self.help_window = HelpWindow(self.root)
    
    def open_egram_window(self):
        """Open the EG diagram window"""
        try:
            if (self.egram_window and 
                hasattr(self.egram_window, 'window') and 
                self.egram_window.window.winfo_exists()):
                try:
                    self.egram_window.comm_manager = self.comm_manager
                except Exception:
                    pass
                self.egram_window.window.lift()  
                return
        except tk.TclError:
            self.egram_window = None

        self.egram_window = EgramWindow(self.root, self.comm_manager)
    
    def get_available_ports(self):
        """Get available serial ports"""
        ports = PacemakerCommunication().list_ports()
        return ports if ports else ["No ports available"]

    def refresh_ports(self):
        """Refresh available serial ports"""
        ports = self.get_available_ports()
        self.port_combobox.configure(values=ports)
        if ports and "No ports" not in ports[0]:
            self.port_combobox.set(ports[0])
        messagebox.showinfo("Refresh", f"Found {len(ports)} port(s)")

    def toggle_connect(self):
        """Connect or disconnect serial port"""
        # --- Handle disconnect ---
        if self.is_connected and self.comm_manager is not None:
            self.comm_manager.disconnect()
            self.is_connected = False
            self.check_device_identity() # MODIFIED: Check identity to clear the device name
            self.update_status()
            messagebox.showinfo("Disconnected", "Serial connection closed.")
            return

        # --- Handle connect ---
        selected_port = self.port_combobox.get()
        if not selected_port or "No ports" in selected_port:
            messagebox.showerror("Error", "No valid port selected")
            return
        
        # Create new communication manager with selected port
        self.comm_manager = PacemakerCommunication(port=selected_port)
        
        if self.comm_manager.connect():
            self.is_connected = True
            self.check_device_identity() # MODIFIED: Check identity to get/assign the logical name
            # Show the logical name in the success message
            assigned_name = self.device_id if self.device_id != "--" else selected_port
            messagebox.showinfo("Success", f"Connected to {assigned_name} (on {selected_port})")
        else:
            self.is_connected = False
            self.check_device_identity() # MODIFIED: Check identity to clear name on failure
            messagebox.showerror("Error", f"Failed to connect to {selected_port}")
        
        self.update_status()

    def save_parameters(self):
        """Save current parameters to JSON"""
        self.param_manager.save_params()

    def load_parameters(self):
        """Load parameters from JSON"""
        success = self.param_manager.load_params()
        if success:
            self.entries = {param: str(self.param_manager.defaults[param]) for param in self.param_manager.defaults}
        return success

    def apply_parameters(self):
        """Apply current parameters (update internal state)"""
        mode = self.mode_var.get()
        self.status_label.config(text=f"Parameters applied for mode {mode}")
        self.check_device_identity()

    def reset_parameters(self):
        """Reset parameters to defaults"""
        self.param_manager.reset_params()
        self.entries = {param: str(self.param_manager.defaults[param]) for param in self.param_manager.defaults}

class DashboardWindow(DCMInterface):
    pass