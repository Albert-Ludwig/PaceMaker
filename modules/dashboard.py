# This files contains the all windows operations, including the pop up/close and display.
import tkinter as tk
from tkinter import ttk, messagebox
from modules.mode_config import ParamEnum
from modules.ParamOps import ParameterManager, ParameterWindow
from modules.EGdiagram import EgramWindow
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
            # 检查是否已存在且窗口有效
            if (self.egram_window and 
                hasattr(self.egram_window, 'window') and 
                self.egram_window.window.winfo_exists()):
                self.egram_window.window.lift()  # 提到前台
                return
        except tk.TclError:
            # 窗口已被销毁，重置引用
            self.egram_window = None
        
        # 创建新的EGdiagram窗口
        self.egram_window = EgramWindow(self.root)
    

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
            self._display_param_document(content)
        elif topic == "Mode description":
            self._display_mode_document(content)
        else:
            self._display_text_content(content)

    def _display_param_document(self, content):
        """Display parameter information in document format"""
        # Create frame for document
        doc_frame = ttk.Frame(self.content_area)
        doc_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create text widget
        text_widget = tk.Text(doc_frame, wrap=tk.WORD, font=("Arial", 14), padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(text_widget, orient="vertical", command=text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        text_widget.config(yscrollcommand=scrollbar.set)
        
        # Configure text tags for formatting
        text_widget.tag_configure("title", font=("Arial", 16, "bold"), foreground="navy")
        text_widget.tag_configure("heading", font=("Arial", 14, "bold"), foreground="darkblue")
        text_widget.tag_configure("label", font=("Arial", 12, "bold"))
        text_widget.tag_configure("value", font=("Arial", 12))
        
        # Add title
        text_widget.insert(tk.END, "Parameter Descriptions\n", "title")
        text_widget.insert(tk.END, "\n")
        
        # Display content
        if isinstance(content, dict) and "parameters" in content:
            parameters = content["parameters"]
            
            for i, param in enumerate(parameters):
                # Parameter name as heading
                param_name = param.get("name", "Unknown Parameter")
                text_widget.insert(tk.END, f"{param_name}\n", "heading")
                
                # Data type
                text_widget.insert(tk.END, "Data Type: ", "label")
                text_widget.insert(tk.END, f"{param.get('dataType', 'N/A')}\n", "value")
                
                # Unit
                text_widget.insert(tk.END, "Unit: ", "label")
                text_widget.insert(tk.END, f"{param.get('unit', 'N/A')}\n", "value")
                
                # Valid range
                text_widget.insert(tk.END, "Valid Range: ", "label")
                text_widget.insert(tk.END, f"{param.get('validRange', 'N/A')}\n", "value")
                
                # Description
                text_widget.insert(tk.END, "Description: ", "label")
                text_widget.insert(tk.END, f"{param.get('description', 'No description available')}\n", "value")
                
                # Applicable modes
                modes = ", ".join(param.get('applicableModes', [])) if param.get('applicableModes') else "All"
                text_widget.insert(tk.END, "Applicable Modes: ", "label")
                text_widget.insert(tk.END, f"{modes}\n", "value")
                
                # Add separator between parameters (except after the last one)
                if i < len(parameters) - 1:
                    text_widget.insert(tk.END, "\n" + "="*80 + "\n\n")
                else:
                    text_widget.insert(tk.END, "\n")
        
        elif isinstance(content, str):
            text_widget.insert(tk.END, content, "value")
        
        text_widget.config(state=tk.DISABLED)

    def _display_mode_document(self, content):
        """Display mode information in document format"""
        # Create frame for document
        doc_frame = ttk.Frame(self.content_area)
        doc_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create text widget
        text_widget = tk.Text(doc_frame, wrap=tk.WORD, font=("Arial", 14), padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(text_widget, orient="vertical", command=text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        text_widget.config(yscrollcommand=scrollbar.set)
        
        # Configure text tags for formatting
        text_widget.tag_configure("title", font=("Arial", 16, "bold"), foreground="navy")
        text_widget.tag_configure("heading", font=("Arial", 12, "bold"), foreground="darkblue")
        text_widget.tag_configure("label", font=("Arial", 12, "bold"))
        text_widget.tag_configure("value", font=("Arial", 12))
        
        # Add title
        text_widget.insert(tk.END, "Pacing Modes Description\n", "title")
        text_widget.insert(tk.END, "\n")
        
        # Display content
        if isinstance(content, dict):
            # Check for different possible JSON structures
            modes = []
            
            if "pacemaker_modes" in content:
                modes = content["pacemaker_modes"]
            elif "modes" in content:
                modes = content["modes"]
            else:
                # Try to find any list of modes in the dictionary
                for key, value in content.items():
                    if isinstance(value, list):
                        modes = value
                        break
            
            if modes:
                for i, mode in enumerate(modes):
                    # Mode name as heading
                    mode_name = mode.get("mode_name", mode.get("name", "Unknown Mode"))
                    text_widget.insert(tk.END, f"{mode_name}\n", "heading")
                    
                    # Pacing chamber
                    text_widget.insert(tk.END, "Pacing Chamber: ", "label")
                    text_widget.insert(tk.END, f"{mode.get('pacing_chamber', mode.get('pacingChamber', 'N/A'))}\n", "value")
                    
                    # Sensing chamber
                    text_widget.insert(tk.END, "Sensing Chamber: ", "label")
                    text_widget.insert(tk.END, f"{mode.get('sensing_chamber', mode.get('sensingChamber', 'N/A'))}\n", "value")
                    
                    # Response to sensing
                    text_widget.insert(tk.END, "Response to Sensing: ", "label")
                    text_widget.insert(tk.END, f"{mode.get('response_to_sensing', mode.get('response', 'N/A'))}\n", "value")
                    
                    # Purpose/description
                    text_widget.insert(tk.END, "Purpose/Description: ", "label")
                    text_widget.insert(tk.END, f"{mode.get('purpose', mode.get('description', 'No description available'))}\n", "value")
                    
                    # Required parameters
                    params = mode.get("required_parameters", mode.get("parameters", []))
                    if isinstance(params, list):
                        params_str = ", ".join(params)
                    else:
                        params_str = str(params)
                    
                    text_widget.insert(tk.END, "Required Parameters: ", "label")
                    text_widget.insert(tk.END, f"{params_str}\n", "value")
                    
                    # Add separator between modes (except after the last one)
                    if i < len(modes) - 1:
                        text_widget.insert(tk.END, "\n" + "="*80 + "\n\n")
                    else:
                        text_widget.insert(tk.END, "\n")
            else:
                text_widget.insert(tk.END, "No mode information found in the content.\n", "value")
                text_widget.insert(tk.END, f"Content structure: {json.dumps(content, indent=2)}", "value")
        
        elif isinstance(content, str):
            text_widget.insert(tk.END, content, "value")
        
        text_widget.config(state=tk.DISABLED)

    def _display_text_content(self, content):
        """Display generic text content"""
        text_widget = tk.Text(
            self.content_area, 
            wrap=tk.WORD, 
            font=("Arial", 14),
            padx=10, 
            pady=10
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(1.0, str(content))
        text_widget.config(state=tk.DISABLED)