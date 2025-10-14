# This files contains the 
import tkinter as tk
from tkinter import ttk, messagebox
from modules.mode_config import ParamEnum
from modules.ParamOps import ParameterManager, ParameterWindow
import json
import os

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

        # help button
        help_btn = ttk.Button(self.root, text="Help", command=self.open_help_window)
        help_btn.place(x=10, y=650)

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
    
    def open_help_window(self):
        # Check if help window already exists
        if hasattr(self, 'help_window') and self.help_window and self.help_window.help_win.winfo_exists():
            self.help_window.help_win.lift()  # Bring to front if exists
            return
        
        # Create new help window
        self.help_window = HelpWindow(self.root)

class DashboardWindow(DCMInterface):
    pass

class HelpWindow:
    def __init__(self, parent):
        self.help_win = tk.Toplevel(parent)
        self.help_win.title("Help Documentation")
        self.help_win.geometry("800x600")
        
        # Create main frame
        main_frame = ttk.Frame(self.help_win)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create left sidebar for navigation
        self.sidebar = ttk.Frame(main_frame, width=150)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        self.sidebar.pack_propagate(False)
        
        # Create right content area
        self.content_area = ttk.Frame(main_frame)
        self.content_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Add navigation options
        ttk.Label(self.sidebar, text="Help Topics", font=("Arial", 14, "bold")).pack(pady=10)
        
        self.topics = self.load_help_content()
        
        self.current_topic = tk.StringVar()
        
        for topic in self.topics.keys():
            ttk.Radiobutton(
                self.sidebar, 
                text=topic, 
                variable=self.current_topic,
                value=topic,
                command=self.update_content
            ).pack(anchor="w", pady=5)
        
        # Set default topic
        if self.topics:
            self.current_topic.set(list(self.topics.keys())[0])
        
        self.update_content()
    
    def load_help_content(self):
        """Load help content from JSON files"""
        content = {}
        
        # Load parameter descriptions
        param_file = os.path.join("data", "Param_Help.json")
        if os.path.exists(param_file):
            try:
                with open(param_file, "r", encoding="utf-8") as f:
                    content["Param description"] = json.load(f)  # Parse JSON directly
            except Exception as e:
                content["Param description"] = f"Error loading parameter help: {e}"
        else:
            content["Param description"] = "Parameter help file not found."
        
        # Load mode descriptions
        mode_file = os.path.join("data", "Mode_Help.json")
        if os.path.exists(mode_file):
            try:
                with open(mode_file, "r", encoding="utf-8") as f:
                    content["Mode description"] = json.load(f)  # Parse JSON directly
            except Exception as e:
                content["Mode description"] = f"Error loading mode help: {e}"
        else:
            content["Mode description"] = "Mode help file not found."
        
        return content
    
    def update_content(self):
        """Update the content area based on selected topic"""
        topic = self.current_topic.get()
        content = self.topics.get(topic, "Content not available.")
        
        # Clear existing content
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        if topic == "Param description":
            self._display_param_table(content)
        elif topic == "Mode description":
            self._display_mode_table(content)
        else:
            self._display_text_content(content)

    def _display_param_table(self, content):
        """Display parameter information in a table format"""
        table_frame = ttk.Frame(self.content_area)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(table_frame, text="Parameter Descriptions",
                font=("Arial", 16, "bold")).pack(pady=(0, 15))

        tree = ttk.Treeview(
            table_frame,
            columns=("Name", "DataType", "Unit", "Range", "Description", "Modes"),
            show="headings", height=20
        )

        tree.heading("Name", text="Name")
        tree.heading("DataType", text="Data Type")
        tree.heading("Unit", text="Unit")
        tree.heading("Range", text="Valid Range")
        tree.heading("Description", text="Description")
        tree.heading("Modes", text="Applicable Modes")

        tree.column("Name", width=160)
        tree.column("DataType", width=100)
        tree.column("Unit", width=80)
        tree.column("Range", width=120)
        tree.column("Description", width=300)
        tree.column("Modes", width=150)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if isinstance(content, dict) and "parameters" in content:
            for param in content["parameters"]:
                param_name = param.get("name") or param.get("Name") or "Unknown"
                data_type = param.get("dataType", "N/A")
                unit = param.get("unit", "N/A")
                valid_range = param.get("validRange", "N/A")
                description = param.get("description", "No description available")
                modes = ", ".join(param.get("applicableModes", [])) if param.get("applicableModes") else "All"
                tree.insert("", "end",
                            values=(param_name, data_type, unit, valid_range, description, modes))
        elif isinstance(content, str):
            ttk.Label(table_frame, text=content, foreground="red").pack(pady=20)
    
    def _display_mode_table(self, content):
        """Display mode information in a table format"""
        # Create frame for table
        table_frame = ttk.Frame(self.content_area)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create title
        title_label = ttk.Label(table_frame, text="Pacing Modes Description", 
                            font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 15))
        
        # Create treeview for table
        tree = ttk.Treeview(table_frame, columns=("Mode", "Pacing Chamber", "Sensing Chamber", 
                                                "Response", "Purpose", "Parameters"), 
                        show="headings", height=20)
        
        # Define headings
        tree.heading("Mode", text="Mode")
        tree.heading("Pacing Chamber", text="Pacing Chamber")
        tree.heading("Sensing Chamber", text="Sensing Chamber")
        tree.heading("Response", text="Response to Sensing")
        tree.heading("Purpose", text="Purpose / Meaning")
        tree.heading("Parameters", text="Required Parameters")
        
        # Define column widths
        tree.column("Mode", width=80)
        tree.column("Pacing Chamber", width=120)
        tree.column("Sensing Chamber", width=120)
        tree.column("Response", width=150)
        tree.column("Purpose", width=300)
        tree.column("Parameters", width=200)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Populate table with data
        if isinstance(content, dict):
            # Check for different possible JSON structures
            if "pacemaker_modes" in content:
                # Structure: {"pacemaker_modes": [{...}, {...}]}
                modes = content["pacemaker_modes"]
                for mode in modes:
                    mode_name = mode.get("mode_name", mode.get("name", "Unknown"))
                    pacing_chamber = mode.get("pacing_chamber", mode.get("pacingChamber", "N/A"))
                    sensing_chamber = mode.get("sensing_chamber", mode.get("sensingChamber", "N/A"))
                    response = mode.get("response_to_sensing", mode.get("response", "N/A"))
                    purpose = mode.get("purpose", mode.get("description", "No description available"))
                    
                    # Format parameters as comma-separated string
                    params = mode.get("required_parameters", [])
                    if isinstance(params, list):
                        params_str = ", ".join(params)
                    else:
                        params_str = str(params)
                    
                    tree.insert("", "end", values=(mode_name, pacing_chamber, sensing_chamber, 
                                                response, purpose, params_str))
            
            elif "modes" in content:
                # Structure: {"modes": [{...}, {...}]}
                modes = content["modes"]
                for mode in modes:
                    mode_name = mode.get("name", "Unknown")
                    pacing_chamber = mode.get("pacing_chamber", "N/A")
                    sensing_chamber = mode.get("sensing_chamber", "N/A")
                    response = mode.get("response", "N/A")
                    purpose = mode.get("description", "No description available")
                    
                    # Format parameters as comma-separated string
                    params = mode.get("parameters", [])
                    if isinstance(params, list):
                        params_str = ", ".join(params)
                    else:
                        params_str = str(params)
                    
                    tree.insert("", "end", values=(mode_name, pacing_chamber, sensing_chamber, 
                                                response, purpose, params_str))
            
            else:
                # Try to find any list of modes in the dictionary
                modes_found = False
                for key, value in content.items():
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict) and ("name" in item or "mode_name" in item):
                                modes_found = True
                                mode_name = item.get("name", item.get("mode_name", "Unknown"))
                                pacing_chamber = item.get("pacing_chamber", "N/A")
                                sensing_chamber = item.get("sensing_chamber", "N/A")
                                response = item.get("response", "N/A")
                                purpose = item.get("description", "No description available")
                                
                                # Format parameters as comma-separated string
                                params = item.get("parameters", [])
                                if isinstance(params, list):
                                    params_str = ", ".join(params)
                                else:
                                    params_str = str(params)
                                
                                tree.insert("", "end", values=(mode_name, pacing_chamber, sensing_chamber, 
                                                            response, purpose, params_str))
                
                if not modes_found:
                    # Fallback: display as text
                    text_widget = tk.Text(table_frame, wrap=tk.WORD, font=("Arial", 11))
                    text_widget.pack(fill=tk.BOTH, expand=True)
                    text_widget.insert(1.0, f"Unexpected content structure:\n\n{json.dumps(content, indent=2)}")
                    text_widget.config(state=tk.DISABLED)
                    return
        
        elif isinstance(content, str):
            # Display error message if content is a string (error occurred)
            error_label = ttk.Label(table_frame, text=content, foreground="red")
            error_label.pack(pady=20)
        else:
            # Fallback: display as text
            text_widget = tk.Text(table_frame, wrap=tk.WORD, font=("Arial", 11))
            text_widget.pack(fill=tk.BOTH, expand=True)
            text_widget.insert(1.0, f"Content structure: {type(content)}\n\n{content}")
            text_widget.config(state=tk.DISABLED)

    def _display_text_content(self, content):
        """Display generic text content"""
        text_widget = tk.Text(
            self.content_area, 
            wrap=tk.WORD, 
            font=("Arial", 11),
            padx=10, 
            pady=10
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(1.0, str(content))
        text_widget.config(state=tk.DISABLED)