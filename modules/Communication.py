# this file uses the serial.py to achieve the reading, writing and load the parameters. Then, other files will use this file to update the status.
"""
Pacemaker Communication Manager
High-level interface for parameter communication with pacemaker devices
"""
from typing import Dict, Any, Optional
import struct
import time

# Import SerialManager with fallback for different execution contexts
try:
    # Try relative import (when imported as module)
    from .Serial import SerialManager
except ImportError:
    # Try absolute import (when run directly)
    from Serial import SerialManager

class PacemakerCommunication:
    """
    High-level communication interface for pacemaker parameter management
    Handles all parameter upload/download operations with proper protocol formatting
    """

    def __init__(self, port: str = "COM3", baudrate: int = 115200):
        """Initialize communication manager with serial connection parameters"""
        self.serial_mgr = SerialManager(port=port, baudrate=baudrate)
        self.is_connected = False

    def connect(self) -> bool:
        """Establish connection to pacemaker device"""
        self.is_connected = self.serial_mgr.connect()
        if self.is_connected:
            self.serial_mgr.flush_buffers()
            print("[OK] Connected to pacemaker device")
        return self.is_connected

    def disconnect(self):
        """Close connection to pacemaker device"""
        if self.is_connected:
            self.serial_mgr.disconnect()
            self.is_connected = False
            print("[OK] Disconnected from pacemaker device")

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
        
        # Validate connection
        if not self.is_connected:
            result['message'] = "Device not connected"
            result['errors'].append("Device not connected")
            return result
        
        try:
            # Build data packet using SerialManager
            frame = self.serial_mgr.build_data_packet(mode=mode, params=parameters)
            
            if not frame:
                result['message'] = "Failed to build data packet"
                result['errors'].append("Packet build failed")
                return result
            
            # Send data packet
            success = self.serial_mgr.send_data(frame)
            
            if not success:
                result['message'] = "Parameter transmission failed"
                result['errors'].append("Data send failed")
                return result
            
            # Allow device processing time
            time.sleep(0.5)
            
            result['success'] = True
            result['message'] = f"Successfully uploaded {len(parameters)} parameters"
            print(f"[OK] Parameters uploaded: mode={mode}, count={len(parameters)}")
            
        except Exception as e:
            result['message'] = f"Upload error: {str(e)}"
            result['errors'].append(str(e))
            print(f"[ERR] Upload exception: {e}")
        
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
        
        # Validate connection
        if not self.is_connected:
            result['message'] = "Device not connected"
            result['errors'].append("Device not connected")
            return result
        
        try:
            # Send read request (implement based on your protocol)
            # This is a placeholder - adjust based on actual protocol
            print("[INFO] Parameter download not yet implemented")
            result['message'] = "Download feature pending implementation"
            
        except Exception as e:
            result['message'] = f"Download error: {str(e)}"
            result['errors'].append(str(e))
            print(f"[ERR] Download exception: {e}")
        
        return result

    def get_connection_status(self) -> bool:
        """Return current connection status"""
        return self.is_connected and self.serial_mgr.is_connected()

    def list_ports(self):
        """List all available serial ports"""
        return self.serial_mgr.list_available_ports()

# Example usage and test function
def main():
    """Example usage of PacemakerCommunication class"""
    
    # Sample parameter set for testing
    test_params = {
        "Lower_Rate_Limit": 60,
        "Upper_Rate_Limit": 120,
        "Maximum_Sensor_Rate": 120,
        "ARP": 320,
        "VRP": 320,
        "PVARP": 250,
        "Atrial_Amplitude": 5.0,
        "Ventricular_Amplitude": 5.0,
        "Atrial_Pulse_Width": 1,
        "Ventricular_Pulse_Width": 1,
        "Atrial_Sensitivity": 0.5,
        "Ventricular_Sensitivity": 2.5,
        "Response_Factor": 8,
        "Reaction_Time": 10,
        "Recovery_Time": 5,
        "Activity_Threshold": "Med"
    }
    
    # Initialize communication manager
    comm = PacemakerCommunication(port="/dev/tty.usbserial-XXX")  # macOS
    # For Windows use: comm = PacemakerCommunication(port="COM3")
    
    # List available ports
    print("Available ports:", comm.list_ports())
    
    try:
        # Connect to device
        if comm.connect():
            print("[OK] Starting parameter operations...")
            
            # Upload parameters to device (AAIR mode = 6)
            upload_result = comm.upload_parameters(mode=6, parameters=test_params)
            print(f"Upload result: {upload_result['message']}")
            
            if upload_result['success']:
                print("[OK] Upload successful")
            else:
                print(f"[ERR] Upload failed: {upload_result['errors']}")
            
            # Download parameters from device
            download_result = comm.download_parameters()
            print(f"Download result: {download_result['message']}")
            
            if download_result['success']:
                print("Downloaded parameters:")
                for param, value in download_result['parameters'].items():
                    print(f"  {param}: {value}")
        else:
            print("[ERR] Failed to connect to device")
    
    except KeyboardInterrupt:
        print("\n[INFO] Operation interrupted by user")
    except Exception as e:
        print(f"[ERR] Unexpected error: {e}")
    finally:
        # Ensure proper cleanup
        comm.disconnect()
        print("[OK] Communication test completed")

if __name__ == "__main__":
    main()