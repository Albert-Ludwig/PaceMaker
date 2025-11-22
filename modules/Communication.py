"""
Pacemaker Communication Manager
High-level interface for parameter communication with pacemaker devices
"""
from typing import Dict, Any
import struct
import time

try:
    from .Serial_Manager import SerialManager
    from .auth import get_or_assign_device_name, set_last_connected_device
except ImportError:
    from modules.Serial_Manager import SerialManager
    from modules.auth import get_or_assign_device_name, set_last_connected_device

class PacemakerCommunication:
    """
    High-level communication interface for pacemaker parameter management
    Handles all parameter upload/download operations with proper protocol formatting
    """

    def __init__(self, port: str = "COM3", baudrate: int = 115200):
        """Initialize communication manager with serial connection parameters"""
        self.serial_mgr = SerialManager(port=port, baudrate=baudrate)
        self.is_connected = False

    def _prepare_firmware_params(self, mode, ui_params):
        ui_params = ui_params or {}
        p = {}

        lrl_source = None
        for k in ("Lower_Rate_Limit", "LRL", "LRL_bpm"):
            if k in ui_params:
                lrl_source = ui_params.get(k)
                break
        try:
            lrl_bpm = float(lrl_source) if lrl_source is not None else 60.0
        except Exception:
            lrl_bpm = 60.0
        p["p_LRL"] = int(round(lrl_bpm))

        url_src = ui_params.get("Upper_Rate_Limit")
        try:
            url_bpm = float(url_src) if url_src is not None else 120.0
        except Exception:
            url_bpm = 120.0
        p["p_URL"] = int(round(url_bpm))

        msr_src = ui_params.get("Maximum_Sensor_Rate")
        try:
            msr_bpm = float(msr_src) if msr_src is not None else p["p_URL"]
        except Exception:
            msr_bpm = p["p_URL"]
        p["p_MaxSensorRate"] = int(round(msr_bpm))

        arp_src = ui_params.get("ARP")
        try:
            p["p_ARP"] = int(arp_src) if arp_src is not None else 320
        except Exception:
            p["p_ARP"] = 320

        vrp_src = ui_params.get("VRP", ui_params.get("VRP_ms"))
        try:
            p["p_VRP"] = int(vrp_src) if vrp_src is not None else 320
        except Exception:
            p["p_VRP"] = 320

        pvarp_src = ui_params.get("PVARP")
        try:
            p["p_PVARP"] = int(pvarp_src) if pvarp_src is not None else 250
        except Exception:
            p["p_PVARP"] = 250

        a_pw_src = ui_params.get("Atrial_Pulse_Width", ui_params.get("A_PW_ms"))
        try:
            a_pw_ms = float(a_pw_src) if a_pw_src is not None else 1.0
        except Exception:
            a_pw_ms = 1.0
        p["p_aPaceWidth"] = a_pw_ms

        v_pw_src = ui_params.get("Ventricular_Pulse_Width", ui_params.get("V_PW_ms"))
        try:
            v_pw_ms = float(v_pw_src) if v_pw_src is not None else 1.0
        except Exception:
            v_pw_ms = 1.0
        p["p_vPaceWidth"] = v_pw_ms

        a_amp_src = ui_params.get("Atrial_Amplitude", ui_params.get("A_Amp_V"))
        try:
            a_amp_v = float(a_amp_src) if a_amp_src is not None else 5.0
        except Exception:
            a_amp_v = 5.0
        p["p_aPaceAmp"] = int(round(a_amp_v * 100.0))

        v_amp_src = ui_params.get("Ventricular_Amplitude", ui_params.get("V_Amp_V"))
        try:
            v_amp_v = float(v_amp_src) if v_amp_src is not None else 5.0
        except Exception:
            v_amp_v = 5.0
        p["p_vPaceAmp"] = int(round(v_amp_v * 100.0))

        a_sens_src = ui_params.get("Atrial_Sensitivity")
        try:
            a_sens_v = float(a_sens_src) if a_sens_src is not None else 5.0
        except Exception:
            a_sens_v = 5.0
        p["p_aSens"] = int(round(a_sens_v * 100.0))

        v_sens_src = ui_params.get("Ventricular_Sensitivity")
        try:
            v_sens_v = float(v_sens_src) if v_sens_src is not None else 5.0
        except Exception:
            v_sens_v = 5.0
        p["p_vSens"] = int(round(v_sens_v * 100.0))

        act_src = ui_params.get("Activity_Threshold")
        try:
            p["p_ActivityThreshold"] = int(act_src) if act_src is not None else 0
        except Exception:
            p["p_ActivityThreshold"] = 0

        react_src = ui_params.get("Reaction_Time")
        try:
            p["p_ReactionTime"] = int(react_src) if react_src is not None else 30
        except Exception:
            p["p_ReactionTime"] = 30

        resp_src = ui_params.get("Response_Factor")
        try:
            p["p_ResponseFactor"] = int(resp_src) if resp_src is not None else 8
        except Exception:
            p["p_ResponseFactor"] = 8

        rec_src = ui_params.get("Recovery_Time")
        try:
            p["p_RecoveryTime"] = int(rec_src) if rec_src is not None else 5
        except Exception:
            p["p_RecoveryTime"] = 5

        hyst_src = ui_params.get("Hysteresis")
        hyst_flag = 0
        if isinstance(hyst_src, str):
            s = hyst_src.strip().lower()
            if s in ("1", "on", "true", "yes"):
                hyst_flag = 1
        elif isinstance(hyst_src, (int, float, bool)):
            hyst_flag = 1 if int(hyst_src) != 0 else 0
        p["p_hysteresisFlag"] = hyst_flag

        rs_src = ui_params.get("Rate_Smoothing")
        try:
            p["p_RateSmoothing"] = int(rs_src) if rs_src is not None else 0
        except Exception:
            p["p_RateSmoothing"] = 0

        p["p_pacingState"] = 1
        try:
            p["p_pacingMode"] = int(mode)
        except Exception:
            p["p_pacingMode"] = 0

        return p

    def connect(self) -> bool:
        """Establish connection to pacemaker device"""
        self.is_connected = self.serial_mgr.connect()
        if self.is_connected:
            self.serial_mgr.flush_buffers()
        return self.is_connected

    def disconnect(self):
        """Close connection to pacemaker device"""
        if self.is_connected:
            self.serial_mgr.disconnect()
            self.is_connected = False

    def get_connection_status(self) -> bool:
        """Return current connection status"""
        return self.is_connected and self.serial_mgr.is_connected()

    def list_ports(self) -> list:
        """List all available serial ports"""
        return SerialManager.list_available_ports()

    def read_data(self, num_bytes: int = 1) -> bytes:
        """Read data from serial port"""
        if not self.is_connected:
            return b""
        return self.serial_mgr.read_data(num_bytes)

    def upload_parameters(self, mode, parameters):
        result = {
            "success": False,
            "message": "",
            "sent_parameters": dict(parameters or {}),
            "errors": []
        }

        if not self.is_connected:
            result["message"] = "Device not connected"
            result["errors"].append("Device not connected")
            return result

        try:
            fw_params = self._prepare_firmware_params(mode, parameters or {})

            frame = self.serial_mgr.build_data_packet(mode=mode, params=fw_params)
            if not frame:
                result["message"] = "Failed to build data packet"
                result["errors"].append("Packet build failed")
                return result

            ok = self.serial_mgr.send_data(frame)
            if not ok:
                result["message"] = "Parameter transmission failed"
                result["errors"].append("Data send failed")
                return result

            time.sleep(0.5)

            result["success"] = True
            result["message"] = "Successfully uploaded {} parameters".format(len(parameters or {}))

        except Exception as e:
            result["message"] = "Upload error: {}".format(str(e))
            result["errors"].append(str(e))

        return result


    def download_parameters(self):
        result = {
            "success": False,
            "message": "",
            "parameters": {},
            "errors": []
        }
        if not self.is_connected:
            result["message"] = "Device not connected"
            result["errors"].append("Device not connected")
            return result
        try:
            ok = self.serial_mgr.request_parameters()
            if not ok:
                result["message"] = "Failed to send K_ECHO request"
                result["errors"].append("Echo send failed")
                return result
            pkt = self.serial_mgr.read_packet(timeout=2.0)
            if not pkt:
                result["message"] = "No response from pacemaker"
                result["errors"].append("Timeout waiting for echo")
                return result
            parsed = self.serial_mgr.parse_packet(pkt)
            if not parsed:
                result["message"] = "Invalid packet received"
                result["errors"].append("Packet parse failed")
                return result
            params = self.serial_mgr.decode_params(parsed["data"])
            result["success"] = True
            result["parameters"] = params
            result["message"] = "Successfully downloaded parameters from pacemaker"
        except Exception as e:
            result["message"] = "Download error: {}".format(str(e))
            result["errors"].append(str(e))
        return result

    def check_device_identity(self) -> Dict[str, Any]:
        """
        Check and return the identity of the connected pacemaker device.
        Updates the "last_connected_device_name" in the JSON file.
        """
        current_logical_name = None 

        if self.is_connected and hasattr(self, "serial_mgr") and self.serial_mgr is not None:
            try:
                port_name = getattr(self.serial_mgr, "port", None)
                if port_name:
                    current_logical_name = get_or_assign_device_name(port_name)
                    
                    if current_logical_name:
                        set_last_connected_device(current_logical_name)
                        
            except Exception as e:
                print(f"Error getting device name: {e}")
                current_logical_name = None
                
        return {
            "device_id": current_logical_name,
        }