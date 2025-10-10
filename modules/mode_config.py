# first, the class is constructed to store and verify parameters

class ParamEnum:
    MODES = {
        # D1
        "AOO": {
            "Lower_Rate_Limit",
            "Upper_Rate_Limit",
            "Atrial_Amplitude",
            "Atrial_Pulse_Width"
        },
        "VOO": {
            "Lower_Rate_Limit",
            "Upper_Rate_Limit",
            "Ventricular_Amplitude",
            "Ventricular_Pulse_Width"
        },
        "AAI": {
            "Lower_Rate_Limit",
            "Upper_Rate_Limit",
            "Atrial_Amplitude",
            "Atrial_Pulse_Width",
            "ARP"
        },
        "VVI": {
            "Lower_Rate_Limit",
            "Upper_Rate_Limit",
            "Ventricular_Amplitude",
            "Ventricular_Pulse_Width",
            "VRP"
        },

        # D2
        # "AOOR": {
        #     "Lower_Rate_Limit",
        #     "Upper_Rate_Limit",
        #     "Atrial_Amplitude",
        #     "Atrial_Pulse_Width",
        #     "Maximum_Sensor_Rate",
        #     "Activity_Threshold",
        #     "Response_Factor",
        #     "Reaction_Time",
        #     "Recovery_Time"
        # },
        # "VOOR": {
        #     "Lower_Rate_Limit",
        #     "Upper_Rate_Limit",
        #     "Ventricular_Amplitude",
        #     "Ventricular_Pulse_Width",
        #     "Maximum_Sensor_Rate",
        #     "Activity_Threshold",
        #     "Response_Factor",
        #     "Reaction_Time",
        #     "Recovery_Time"
        # },
        # "AAIR": {
        #     "Lower_Rate_Limit",
        #     "Upper_Rate_Limit",
        #     "Atrial_Amplitude",
        #     "Atrial_Pulse_Width",
        #     "ARP",
        #     "Maximum_Sensor_Rate",
        #     "Activity_Threshold",
        #     "Response_Factor",
        #     "Reaction_Time",
        #     "Recovery_Time"
        # },
        # "VVIR": {
        #     "Lower_Rate_Limit",
        #     "Upper_Rate_Limit",
        #     "Ventricular_Amplitude",
        #     "Ventricular_Pulse_Width",
        #     "VRP",
        #     "Maximum_Sensor_Rate",
        #     "Activity_Threshold",
        #     "Response_Factor",
        #     "Reaction_Time",
        #     "Recovery_Time"
        # }
    }
    

    def __init__(self):
        #default values
        # D1
        self.Lower_Rate_Limit = 60       
        self.Upper_Rate_Limit = 120
        self.Atrial_Amplitude = 3.5 
        self.Ventricular_Amplitude = 3.5  
        self.Atrial_Pulse_Width = 0.4 
        self.Ventricular_Pulse_Width = 0.4
        self.ARP                = 320
        self.VRP                = 320

        #D2
        # self.Maximum_Sensor_Rate = 120
        # self.Activity_Threshold  = 1.1        
        # self.Response_Factor     = 8
        # self.Reaction_Time       = 10         
        # self.Recovery_Time       = 30  

    # D1 parameters interface
    def get_Lower_Rate_Limit(self):
        return self.Lower_Rate_Limit
    
    def get_Upper_Rate_Limit(self):
        return self.Upper_Rate_Limit
    
    def get_Atrial_Amplitude(self):
        return self.Atrial_Amplitude if self.Atrial_Amplitude !=0 else 0
    
    def get_Ventricular_Amplitude(self):
        return self.Ventricular_Amplitude if self.Ventricular_Amplitude !=0 else 0
    
    def get_Atrial_Pulse_Width(self):
        return self.Atrial_Pulse_Width
    
    def get_Ventricular_Pulse_Width(self):
        return self.Ventricular_Pulse_Width
    
    def get_ARP(self):
        return self.ARP
    
    def get_VRP(self):
        return self.VRP

    