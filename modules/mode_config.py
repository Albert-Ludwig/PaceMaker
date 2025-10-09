# first, the class is constructed to store and verify parameters

class ParamEnum:
    MODES = {
        "AOO": {"lrl", "url", "a_amp", "a_pw"},
        "VOO": {"lrl", "url", "v_amp", "v_pw"},
        "AAI": {"lrl", "url", "a_amp", "a_pw", "a_sens", "arp", "pvarp"},
        "VVI": {"lrl", "url", "v_amp", "v_pw", "v_sens", "vrp"},
        "DDD": {"lrl","url","a_amp","v_amp","a_pw","v_pw","a_sens","v_sens",
                "fixed_av","dyn_av","sensed_av_off","vrp","arp","pvarp","pvarp_ext",
                "hysteresis","rate_smoothing"},
        "AAIR": {"lrl","url","a_amp","a_pw","a_sens","arp","pvarp",
                "msr","activity_threshold","reaction_time","response_factor","recovery_time"},
        "VVIR": {"lrl","url","v_amp","v_pw","v_sens","vrp",
                "msr","activity_threshold","reaction_time","response_factor","recovery_time"},
    }
    def __init__(self):
        #default val
        self.__amplitude = 100
        self.__lrl = 60
        self.__pulse_width = 0.4
        self.__threshold = 66
        self.__arp = 320
        self.__vrp = 320
        self.__url = 120        
        self.__msr = 120
        self.__activity_threshold = 1.1 # Med
        self.__response_factor = 8
        self.__reaction_time = 10
        self.__recovery_time = 30 
    
    def get_default_amplitude(self):
        return self.__amplitude
    def get_default_lrl(self):
        return self.__lrl
    def get_default_pulse_width(self):  
        return self.__pulse_width
    def get_default_threshold(self):
        return self.__threshold
    def get_default_arp(self):
        return self.__arp
    def get_default_vrp(self):
        return self.__vrp
    def get_default_url(self):
        return self.__url
    def get_default_msr(self):
        return self.__msr
    def get_default_activity_threshold(self):
        return self.__activity_threshold
    def get_default_response_factor(self):
        return self.__response_factor
    def get_default_reaction_time(self):
        return self.__reaction_time
    def get_default_recovery_time(self):
        return self.__recovery_time
    