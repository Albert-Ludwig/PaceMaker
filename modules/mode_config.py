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

    # for atrial amplitude, step 0.1 between [0.5,3.2], step 0.5 between [3.5,7.0], range [0.5,7.0]
    def set_Atrial_Amplitude(self, val):
        if not self._is_number(val):
            raise TypeError("Atrial_Amplitude must be numeric")
        x = float(val)
        if 0.5 <= x <= 3.2:
            y = self._round_to_step(x, 0.1)                    
        elif 3.5 <= x <= 7.0:
            y = self._round_to_step(x, 0.5)             
        else:
            raise ValueError("Atrial_Amplitude out of range: [0.5–3.2] or [3.5–7.0] V")
        self.Atrial_Amplitude = y

    # for ventricular amplitude, step 0.1 between [0.5,3.2], step 0.5 between [3.5,7.0], range [0.5,7.0]
    def set_Atrial_Pulse_Width(self, val):
        if not self._is_number(val):
            raise TypeError("Atrial_Pulse_Width must be numeric")
        x = float(val)
        if abs(x - 0.05) < 1e-6:
            y = 0.05
        elif 0.10 <= x <= 1.90:
            y = round((x - 0.10) / 0.10) * 0.10 + 0.10   # 0.10 步进
            y = round(y, 2)
        else:
            raise ValueError("Atrial_Pulse_Width out of range: 0.05 or 0.10–1.90 ms")
        self.Atrial_Pulse_Width = y

    # for ventricular amplitude, step 0.1 between [0.5,3.2], step 0.5 between [3.5,7.0], range [0.5,7.0]
    def set_Ventricular_Pulse_Width(self, val):
        if not self._is_number(val):
            raise TypeError("Ventricular_Pulse_Width must be numeric")
        x = float(val)
        if abs(x - 0.05) < 1e-6:
            y = 0.05
        elif 0.10 <= x <= 1.90:
            y = round((x - 0.10) / 0.10) * 0.10 + 0.10
            y = round(y, 2)
        else:
            raise ValueError("Ventricular_Pulse_Width out of range: 0.05 or 0.10–1.90 ms")
        self.Ventricular_Pulse_Width = y

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