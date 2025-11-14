"""
Pacemaker Communication Manager
High-level interface for parameter communication with pacemaker devices
"""
from typing import Dict, Any
import struct
import time

try:
    from .Serial_Manager import SerialManager
except ImportError:
    from modules.Serial_Manager import SerialManager

class PacemakerCommunication:
    """
    High-level communication interface for pacemaker parameter management
    Handles all parameter upload/download operations with proper protocol formatting
    """

    def __init__(self, port: str = "COM3", baudrate: int = 57600):
        """Initialize communication manager with serial connection parameters"""
        self.serial_mgr = SerialManager(port=port, baudrate=baudrate)
        self.is_connected = False

    def _prepare_firmware_params(self, mode, ui_params):
        p = {}
        lrl = float(ui_params.get("Lower_Rate_Limit", 60.0))
        lowrate_interval = int(round(60000.0 / lrl))
        p["p_pacingState"] = 1
        p["p_pacingMode"] = int(mode)
        p["p_hysteresisInterval"] = int(ui_params.get("ARP", lowrate_interval))
        v_amp = float(ui_params.get("Ventricular_Amplitude", ui_params.get("Atrial_Amplitude", 3.5)))
        p["p_vPaceAmp"] = int(round(v_amp * 100))
        v_pw = float(ui_params.get("Ventricular_Pulse_Width", ui_params.get("Atrial_Pulse_Width", 1.0)))
        p["p_vPaceWidth"] = v_pw
        p["p_VRP"] = int(ui_params.get("VRP", 320))
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
            firmware_params = self._prepare_firmware_params(mode, parameters or {})
            frame = self.serial_mgr.build_data_packet(mode=mode, params=firmware_params)
            if not frame:
                result["message"] = "Failed to build data packet"
                result["errors"].append("Packet build failed")
                return result
            success = self.serial_mgr.send_data(frame)
            if not success:
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
        Compare current connected device with the last one and return IDs.
        Returns:
            {
                "device_id": <current device id or None>,
                "last_device_id": <previous device id or None>,
                "is_same": True/False
            }
        """
        last_id = getattr(self, "_device_id", None)

        current_id = None
        try:
            if hasattr(self, "serial_mgr") and self.serial_mgr is not None:
                current_id = getattr(self.serial_mgr, "port", None)
        except Exception:
            current_id = None

        is_same = bool(last_id is not None and current_id is not None and current_id == last_id)

        self._device_id = current_id

        return {
            "device_id": current_id,
            "last_device_id": last_id,
            "is_same": is_same,
        }
