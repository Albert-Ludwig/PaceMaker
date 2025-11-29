# This file implements the help window for the pacemaker application.
import tkinter as tk
from tkinter import ttk
import json
import os

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
        text_widget = tk.Text(doc_frame, wrap=tk.WORD, font=("Arial", 16), padx=10, pady=10)
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