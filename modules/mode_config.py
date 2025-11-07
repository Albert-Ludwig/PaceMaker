# This class is used to store the mode and essential parameters (the enum); and, the getter and setter interfece also be finished in this file.

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
            "ARP",
            "PVARP",
            "Atrial_Sensitivity"
        },
        "VVI": {
            "Lower_Rate_Limit",
            "Upper_Rate_Limit",
            "Ventricular_Amplitude",
            "Ventricular_Pulse_Width",
            "VRP",
            "Ventricular_Sensitivity"
        },

        #D2
        "AOOR": {
            "Lower_Rate_Limit",
            "Upper_Rate_Limit",
            "Atrial_Amplitude",
            "Atrial_Pulse_Width",
            "Maximum_Sensor_Rate",
            "Activity_Threshold",
            "Response_Factor",
            "Reaction_Time",
            "Recovery_Time"
        },
        "VOOR": {
            "Lower_Rate_Limit",
            "Upper_Rate_Limit",
            "Ventricular_Amplitude",
            "Ventricular_Pulse_Width",
            "Maximum_Sensor_Rate",
            "Activity_Threshold",
            "Response_Factor",
            "Reaction_Time",
            "Recovery_Time"
        },
        "AAIR": {
            "Lower_Rate_Limit",
            "Upper_Rate_Limit",
            "Atrial_Amplitude",
            "Atrial_Pulse_Width",
            "ARP",
            "Maximum_Sensor_Rate",
            "Activity_Threshold",
            "Response_Factor",
            "Reaction_Time",
            "Recovery_Time",
            "Atrial_Sensitivity",
            "PVARP"
        },
        "VVIR": {
            "Lower_Rate_Limit",
            "Upper_Rate_Limit",
            "Ventricular_Amplitude",
            "Ventricular_Pulse_Width",
            "VRP",
            "Maximum_Sensor_Rate",
            "Activity_Threshold",
            "Response_Factor",
            "Reaction_Time",
            "Recovery_Time",
            "Ventricular_Sensitivity"
        }
    }
    

    def __init__(self):
        #default values
        # D1
        self.Lower_Rate_Limit = 60       
        self.Upper_Rate_Limit = 120
        self.Atrial_Amplitude = 5.0
        self.Ventricular_Amplitude = 5.0
        self.Atrial_Pulse_Width = 1
        self.Ventricular_Pulse_Width = 1
        self.ARP                = 320
        self.VRP                = 320

        #D2
        self.Maximum_Sensor_Rate = 120
        self.Activity_Threshold  = "Med"       
        self.Response_Factor     = 8
        self.Reaction_Time       = 10         
        self.Recovery_Time       = 30
        self.Atrial_Sensitivity   = None
        self.Ventricular_Sensitivity = None 
        self.PVARP               = 250

    # D1 parameters getter interface 
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
    
    # D2 parameters getter interface
    def get_Atrial_Sensitivity(self):
        return self.Atrial_Sensitivity 

    def get_Ventricular_Sensitivity(self):
        return self.Ventricular_Sensitivity 
    
    def get_Maximum_Sensor_Rate(self):
        return self.Maximum_Sensor_Rate

    def get_Activity_Threshold(self):
        return self.Activity_Threshold
    
    def get_Response_Factor(self):
        return self.Response_Factor
    
    def get_PVARP(self):
        return self.PVARP
    
    def get_Recovery_Time(self):
        return self.Recovery_Time
    
    def get_Reaction_Time(self):
        return self.Reaction_Time


    # D1 parameters setter interface

    # function helpers
    @staticmethod
    def _is_number(v):
        try:
            float(v)
            return True
        except (TypeError, ValueError):
            return False
        
    @staticmethod
    def _round_to_step(v, step):
            return step * round(v / step)

    # setter functions
    # for lower rate limit, step 1 when between 50 and 90, else step 5 , range [30,175]
    def set_Lower_Rate_Limit(self, val):
            if not self._is_number(val):
                raise TypeError("Lower_Rate_Limit must be numeric")
            x = float(val)

            if 30 <= x < 50:
                y = self._round_to_step(x, 5)
            elif 50 <= x <= 90:
                y = round(x)
            elif 90 < x <= 175:
                y = self._round_to_step(x, 5)
            else:
                raise ValueError("Lower_Rate_Limit out of range [30,175] bpm")

            y = max(30, min(175, y))
            if hasattr(self, "Upper_Rate_Limit") and y > float(self.Upper_Rate_Limit):
                raise ValueError("Lower_Rate_Limit must be less than or equal to Upper_Rate_Limit")
            self.Lower_Rate_Limit = int(y)

    # for upper rate limit, stepping in 5 ppm and range [50,175]
    def set_Upper_Rate_Limit(self, val):
        if not self._is_number(val):
            raise TypeError("Upper_Rate_Limit must be numeric")
        x = float(val)

        if not (50 <= x <= 175):
            raise ValueError("Upper_Rate_Limit out of range [50,175] bpm")

        y = self._round_to_step(x, 5)
        y = max(50, min(175, y))
        # note: Upper_Rate_Limit must > Lower_Rate_Limit
        if y <= int(self.Lower_Rate_Limit):
            raise ValueError("Upper_Rate_Limit must be greater than Lower_Rate_Limit")
        self.Upper_Rate_Limit = int(y)

    # for atrial amplitude, step 0.1, range [0.1,5.0]
    def set_Atrial_Amplitude(self, val):
        if not self._is_number(val):
            raise TypeError("Atrial_Amplitude must be numeric")
        x = float(val)
        if 0.1 <= x <= 5.0:
            y = self._round_to_step(x, 0.1)                                 
        else:
            raise ValueError("Atrial_Amplitude out of range: [0.1–5.0] V")
        self.Atrial_Amplitude = y

    # for ventricular amplitude, step 0.1, range [0.1,5.0]
    def set_Ventricular_Amplitude(self, val):
        if not self._is_number(val):
            raise TypeError("Ventricular_Amplitude must be numeric")
        x = float(val)
        if not (0.1 <= x <= 5.0):
            raise ValueError("Ventricular_Amplitude out of range: [0.1–5.0] V")
        y = self._round_to_step(x, 0.1)
        self.Ventricular_Amplitude = round(y, 1)
    
    # for atrial pulse width, range [1, 30] ms, step 1 ms
    def set_Atrial_Pulse_Width(self, val):
        if not self._is_number(val):
            raise TypeError("Atrial_Pulse_Width must be numeric")
        x = float(val)
        if not (1 <= x <= 30):
            raise ValueError("Atrial_Pulse_Width out of range: [1–30] ms")
        y = round(x)  
        self.Atrial_Pulse_Width = int(y)

    # for ventricular pulse width, range [1, 30] ms, step 1 ms
    def set_Ventricular_Pulse_Width(self, val):
        if not self._is_number(val):
            raise TypeError("Ventricular_Pulse_Width must be numeric")
        x = float(val)
        if not (1 <= x <= 30):
            raise ValueError("Ventricular_Pulse_Width out of range: [1–30] ms")
        y = round(x) 
        self.Ventricular_Pulse_Width = int(y)

    # for atrial pulse width, step 0.1 between [0.5,3.2], step 0.5 between [3.5,7.0], range [0.5,7.0]
    def set_ARP(self, val):
        if not self._is_number(val):
            raise TypeError("ARP must be numeric")
        x = float(val)
        if not (150 <= x <= 500):
            raise ValueError("ARP out of range [150,500] ms")
        y = self._round_to_step(x, 10)
        self.ARP = int(y)

    # for ventricular pulse width, step 0.1 between [0.5,3.2], step 0.5 between [3.5,7.0], range [0.5,7.0]
    def set_VRP(self, val):
        if not self._is_number(val):
            raise TypeError("VRP must be numeric")
        x = float(val)
        if not (150 <= x <= 500):
            raise ValueError("VRP out of range [150,500] ms")
        y = self._round_to_step(x, 10)
        self.VRP = int(y)
    
    # D2 parameters setter interface
    # for atrial sensitivity, step 0.1, range [0–5.0]
    def set_Atrial_Sensitivity(self, val):
        if not self._is_number(val):
            raise TypeError("Atrial_Sensitivity must be numeric")
        x = float(val)
        if not (0 <= x <= 5.0):
            raise ValueError("Atrial_Sensitivity out of range: [0–5.0] V")
        y = self._round_to_step(x, 0.1)
        self.Atrial_Sensitivity = round(y, 1)
    
    # for ventricular sensitivity, range [0, 5.0] V, step 0.1 V
    def set_Ventricular_Sensitivity(self, val):
        if not self._is_number(val):
            raise TypeError("Ventricular_Sensitivity must be numeric")
        x = float(val)
        if not (0 <= x <= 5.0):
            raise ValueError("Ventricular_Sensitivity out of range: [0–5.0] V")
        y = self._round_to_step(x, 0.1)
        self.Ventricular_Sensitivity = round(y, 1) 

    # for maximum sensor rate, range [50, 175] ppm, step 5 ppm
    def set_Maximum_Sensor_Rate(self, val):
        if not self._is_number(val):
            raise TypeError("Maximum_Sensor_Rate must be numeric")
        x = float(val)
        if not (50 <= x <= 175):
            raise ValueError("Maximum_Sensor_Rate out of range: [50–175] ppm")
        y = self._round_to_step(x, 5)
        y = max(50, min(175, y))
        self.Maximum_Sensor_Rate = int(y)   

    # for activity threshold, discrete values: V-Low, Low, Med-Low, Med, Med-High, High, V-High
    def set_Activity_Threshold(self, val):
        valid_values = {"V-Low", "Low", "Med-Low", "Med", "Med-High", "High", "V-High"}
        if val not in valid_values:
            raise ValueError(f"Activity_Threshold must be one of {valid_values}")
        self.Activity_Threshold = val

    # for response factor, range [1, 16], step 1
    def set_Response_Factor(self, val):
        if not self._is_number(val):
            raise TypeError("Response_Factor must be numeric")
        x = float(val)
        if not (1 <= x <= 16):
            raise ValueError("Response_Factor out of range: [1–16]")
        y = round(x)
        self.Response_Factor = int(y)

    # for PVARP, range [150, 500] ms, step 10 ms
    def set_PVARP(self, val):
        if not self._is_number(val):
            raise TypeError("PVARP must be numeric")
        x = float(val)
        if not (150 <= x <= 500):
            raise ValueError("PVARP out of range [150,500] ms")
        y = self._round_to_step(x, 10)
        self.PVARP = int(y)
    
    # for recovery time, range [2, 16] min, step 1 min
    def set_Recovery_Time(self, val):
        if not self._is_number(val):
            raise TypeError("Recovery_Time must be numeric")
        x = float(val)
        if not (2 <= x <= 16):
            raise ValueError("Recovery_Time out of range: [2–16] min")
        y = round(x)
        self.Recovery_Time = int(y)
    
    # for reaction time, range [10, 50] sec, step 10 sec
    def set_Reaction_Time(self, val):
        if not self._is_number(val):
            raise TypeError("Reaction_Time must be numeric")
        x = float(val)
        if not (10 <= x <= 50):
            raise ValueError("Reaction_Time out of range: [10–50] sec")
        y = self._round_to_step(x, 10)
        self.Reaction_Time = int(y)

    def get_default_values(self):
        return {
            # D1 parameters
            "Lower_Rate_Limit":        self.get_Lower_Rate_Limit(),
            "Upper_Rate_Limit":        self.get_Upper_Rate_Limit(),
            "Atrial_Amplitude":        self.get_Atrial_Amplitude(),
            "Ventricular_Amplitude":   self.get_Ventricular_Amplitude(),
            "Atrial_Pulse_Width":      self.get_Atrial_Pulse_Width(),
            "Ventricular_Pulse_Width": self.get_Ventricular_Pulse_Width(),
            "ARP":                     self.get_ARP(),
            "VRP":                     self.get_VRP(),
            # D2 parameters
            "Atrial_Sensitivity":      self.get_Atrial_Sensitivity(),
            "Ventricular_Sensitivity": self.get_Ventricular_Sensitivity(),
            "Maximum_Sensor_Rate":     self.get_Maximum_Sensor_Rate(),
            "Activity_Threshold":      self.get_Activity_Threshold(),
            "Response_Factor":         self.get_Response_Factor(),
            "Reaction_Time":           self.get_Reaction_Time(),
            "Recovery_Time":           self.get_Recovery_Time(),
            "PVARP":                   self.get_PVARP(),
        }