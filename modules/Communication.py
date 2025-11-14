"""
Pacemaker Communication Manager
High-level interface for parameter communication with pacemaker devices
"""
from typing import Dict, Any
import struct
import time

try:
    from .Serial import SerialManager
except ImportError:
    from Serial import SerialManager

class PacemakerCommunication:
    """
    High-level communication interface for pacemaker parameter management
    Handles all parameter upload/download operations with proper protocol formatting
    """

    def __init__(self, port: str = "COM3", baudrate: int = 57600):
        """Initialize communication manager with serial connection parameters"""
        self.serial_mgr = SerialManager(port=port, baudrate=baudrate)
        self.is_connected = False

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

    def upload_parameters(self, mode: int, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload complete parameter set to pacemaker device
        
        Args:
            mode: Pacing mode (0-7)
            parameters: Dictionary containing all programmable parameters
            
        Returns:
            Dictionary with operation results and status information
        """
        result = {
            'success': False,
            'message': '',
            'sent_parameters': parameters.copy(),
            'errors': []
        }
        
        if not self.is_connected:
            result['message'] = "Device not connected"
            result['errors'].append("Device not connected")
            return result
        
        try:
            frame = self.serial_mgr.build_data_packet(mode=mode, params=parameters)
            
            if not frame:
                result['message'] = "Failed to build data packet"
                result['errors'].append("Packet build failed")
                return result
            
            success = self.serial_mgr.send_data(frame)
            
            if not success:
                result['message'] = "Parameter transmission failed"
                result['errors'].append("Data send failed")
                return result
            
            time.sleep(0.5)
            
            result['success'] = True
            result['message'] = f"Successfully uploaded {len(parameters)} parameters"
            
        except Exception as e:
            result['message'] = f"Upload error: {str(e)}"
            result['errors'].append(str(e))
        
        return result

    def download_parameters(self) -> Dict[str, Any]:
        """
        Download current parameters from pacemaker device
        
        Returns:
            Dictionary with operation results and downloaded parameters
        """
        result = {
            'success': False,
            'message': '',
            'parameters': {},
            'errors': []
        }
        
        if not self.is_connected:
            result['message'] = "Device not connected"
            result['errors'].append("Device not connected")
            return result
        
        try:
            result['message'] = "Download feature pending implementation"
            
        except Exception as e:
            result['message'] = f"Download error: {str(e)}"
            result['errors'].append(str(e))
        
        return result