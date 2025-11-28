# This file is used to implement serial communication for hiding the details
from __future__ import annotations
from typing import Optional, Dict, Any, Tuple
import serial
import struct
from serial.tools import list_ports

# ---------- Protocol constants ----------
SYNC = 0x16   # Synchronization byte
SOH  = 0x01   # Start of Header
K_ECHO    = 0x49  # Request parameters
K_PPARAMS = 0x55  # Send parameters
K_EGRAM   = 0x47  # Start egram stream
K_ESTOP   = 0x62  # Stop egram stream
N_DATA    = 30    # Every packet must carry exactly 30 data bytes

# Activity threshold mapping (kept here for completeness; not used in packing)
ACTIVITY_MAP: Dict[str, int] = {
    "V-Low": 0, "Low": 1, "Med-Low": 2, "Med": 3,
    "Med-High": 4, "High": 5, "V-High": 6,
}

def f_chk(data: bytes) -> int:
    """Compute XOR checksum over given bytes (returns uint8)."""
    checksum = 0
    for byte in data:
        checksum ^= byte
    return checksum & 0xFF

def _u8(x: Any) -> int:
    """Clamp to uint8, raising on overflow."""
    v = int(x)
    if not (0 <= v <= 0xFF):
        raise ValueError(f"uint8 out of range: {v}")
    return v

def _u16(x: Any) -> int:
    """Clamp to uint16, raising on overflow."""
    v = int(x)
    if not (0 <= v <= 0xFFFF):
        raise ValueError(f"uint16 out of range: {v}")
    return v

class SerialManager:
    """Minimal, transport-only serial layer: connect / send / read / parse."""

    def __init__(self, port: str = "COM3", baudrate: int = 115200,
                 timeout: float = 1.0, write_timeout: float = 1.0) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.write_timeout = write_timeout
        self.serial_port: Optional[serial.Serial] = None

    # ---------- Internal helper ----------
    def _port(self) -> serial.Serial:
        """
        Return the active serial port or raise an error.
        This keeps the public methods tidy and avoids repetitive checks.
        """
        if self.serial_port is None or not getattr(self.serial_port, "is_open", False):
            raise RuntimeError("Serial port not connected")
        return self.serial_port

    # ---------- Connection management ----------
    @staticmethod
    def list_available_ports() -> list[str]:
        """List available serial ports (device names)."""
        return [p.device for p in list_ports.comports()]

    def config(self, *, port=None, baudrate=None, timeout=None, write_timeout=None):
        """Configure connection parameters; takes effect on next connect()."""
        if port is not None:
            self.port = port
        if baudrate is not None:
            self.baudrate = baudrate
        if timeout is not None:
            self.timeout = timeout
        if write_timeout is not None:
            self.write_timeout = write_timeout

    def connect(self) -> bool:
        """Open serial port; returns True on success."""
        try:
            if self.serial_port and getattr(self.serial_port, "is_open", False):
                self.serial_port.close()
            self.serial_port = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,      # 57,600 baud as required
                timeout=self.timeout,
                write_timeout=self.write_timeout,
            )
            return self.serial_port.is_open

        except Exception as e:
            print(f"[SerialManager] Error opening port {self.port}: {e}")
            self.serial_port = None
            return False

    def disconnect(self) -> None:
        """Close serial port safely; idempotent."""
        try:
            if self.serial_port and getattr(self.serial_port, "is_open", False):
                self.serial_port.close()
        except Exception:
            pass
        finally:
            self.serial_port = None

    def is_connected(self) -> bool:
        """Check if the port is open."""
        return bool(self.serial_port and getattr(self.serial_port, "is_open", False))

    # ---------- Low-level send / receive ----------
    def send_data(self, data: bytes) -> bool:
        """
        Send raw bytes; returns True only if all bytes were written.
        High-level callers should prefer the packet helpers below.
        """
        if not isinstance(data, (bytes, bytearray)):
            return False
        try:
            sp = self._port()
            n = sp.write(data)
            sp.flush()
            return n == len(data)
        except Exception:
            return False

    def read_data(self, num_bytes: int = 1) -> bytes:
        """Read a specific number of bytes (may return fewer on timeout)."""
        try:
            sp = self._port()
            return sp.read(num_bytes)
        except Exception:
            return b""

    def flush_buffers(self) -> bool:
        """Clear input/output buffers."""
        try:
            sp = self._port()
            sp.reset_input_buffer()
            sp.reset_output_buffer()
            return True
        except Exception:
            return False

    def wait_for_response(self, expected_bytes: int = 1, timeout: float = 2.0) -> bytes:
        """
        Temporarily override port timeout and read up to expected_bytes.
        Use read_packet() when you expect a full framed packet.
        """
        try:
            sp = self._port()
            old_timeout = sp.timeout
            sp.timeout = timeout
            try:
                return sp.read(expected_bytes)
            finally:
                sp.timeout = old_timeout
        except Exception:
            return b""

    # ---------- Packet building (Tx) ----------
    def _build_header(self, fn_code: int) -> Tuple[bytes, int]:
        """
        Build the 3-byte header [SYNC, SOH, FnCode] and compute the header checksum.
        The header checksum is XOR over these three bytes.
        """
        header = bytes([SYNC, SOH, _u8(fn_code)])
        header_chksum = 0
        return header, header_chksum

    def build_packet(self, fn_code: int, data: bytes = b'') -> bytes:
        header, header_chksum = self._build_header(fn_code)

        if data is None:
            data = b''

        if len(data) > N_DATA:
            raise ValueError(f"data length {len(data)} exceeds N_DATA={N_DATA}")

        if len(data) < N_DATA:
            data = data + bytes(N_DATA - len(data))

        data_chksum = 0

        return header + bytes([header_chksum]) + data + bytes([data_chksum])

    def build_data_packet(self, mode, params):
        p = params or {}

        pacing_mode = int(p.get("p_pacingMode", mode))
        lrl = int(p.get("p_LRL", 60))
        url = int(p.get("p_URL", 120))
        max_sensor_rate = int(p.get("p_MaxSensorRate", url))

        arp = int(p.get("p_ARP", 320))
        vrp = int(p.get("p_VRP", 320))
        pvarp = int(p.get("p_PVARP", 250))

        a_pw_ms = float(p.get("p_aPaceWidth", 1.0))
        v_pw_ms = float(p.get("p_vPaceWidth", 1.0))

        a_amp_raw = int(p.get("p_aPaceAmp", 500))
        v_amp_raw = int(p.get("p_vPaceAmp", 500))

        a_sens_raw = int(p.get("p_aSens", 500))
        v_sens_raw = int(p.get("p_vSens", 500))

        activity_th = int(p.get("p_ActivityThreshold", 0))
        reaction_time = int(p.get("p_ReactionTime", 30))
        response_factor = int(p.get("p_ResponseFactor", 8))
        recovery_time = int(p.get("p_RecoveryTime", 5))

        hyst_flag = int(p.get("p_hysteresisFlag", 0))
        rate_smoothing = int(p.get("p_RateSmoothing", 0))

        payload = struct.pack(
            "<BBBBHHHBBHHHHBBBBBB4x",
            pacing_mode,
            lrl,
            url,
            max_sensor_rate,
            arp,
            vrp,
            pvarp,
            int(round(a_pw_ms)),
            int(round(v_pw_ms)),
            a_amp_raw,
            v_amp_raw,
            a_sens_raw,
            v_sens_raw,
            activity_th,
            reaction_time,
            response_factor,
            recovery_time,
            hyst_flag,
            rate_smoothing,
        )

        return self.build_packet(K_PPARAMS, payload)

    def send_parameters(self, params: Dict[str, Any], mode: int = 0) -> bool:
        """High-level helper to send programmable parameters."""
        try:
            packet = self.build_data_packet(mode=mode, params=params)
        except Exception:
            return False
        return self.send_data(packet)

    def request_parameters(self) -> bool:
        """Send K_ECHO (30 zero data bytes, DataChk=0)."""
        return self.send_data(self.build_packet(K_ECHO))

    def start_egram(self) -> bool:
        """Send K_EGRAM (30 zero data bytes, DataChk=0)."""
        return self.send_data(self.build_packet(K_EGRAM))

    def stop_egram(self) -> bool:
        """Send K_ESTOP (30 zero data bytes, DataChk=0)."""
        return self.send_data(self.build_packet(K_ESTOP))


    def read_packet(self, timeout: float = 2.0) -> bytes:
        try:
            sp = self._port()
            old_to = sp.timeout
            sp.timeout = timeout

            total_len = 4 + N_DATA + 1
            pkt = sp.read(total_len)
            sp.timeout = old_to

            if len(pkt) != total_len:
                return b""
            return pkt
        except Exception:
            return b""

    def parse_packet(self, pkt: bytes) -> Optional[Dict[str, Any]]:
        expected_len = 4 + N_DATA + 1

        if len(pkt) != expected_len:
            return None

        sync, soh, fn, hdr_chk = pkt[0], pkt[1], pkt[2], pkt[3] # hdr_chk is not used since don't have the time to implement
        if sync != SYNC or soh != SOH:
            return None

        data_start = 4
        data_end = 4 + N_DATA
        data = pkt[data_start:data_end]

        return {"fn": fn, "data": data, "header_ok": True, "data_ok": True}

    @staticmethod
    def decode_params(data: bytes) -> Dict[str, Any]:
        if len(data) != N_DATA:
            raise ValueError("params data length error")

        (pacing_mode,
        lrl,
        url,
        max_sensor_rate,
        arp,
        vrp,
        pvarp,
        a_pw,
        v_pw,
        a_amp_raw,
        v_amp_raw,
        a_sens_raw,
        v_sens_raw,
        activity_th,
        reaction_time,
        response_factor,
        recovery_time,
        hyst_flag,
        rate_smoothing) = struct.unpack("<BBBBHHHBBHHHHBBBBBB4x", data)

        rate_smoothing_map = {
            0: "Off", 1: "3%", 2: "6%", 3: "9%", 4: "12%",
            5: "15%", 6: "18%", 7: "21%", 8: "25%"
        }

        activity_threshold_map = {
            0: "V-Low", 1: "Low", 2: "Med-Low", 3: "Med",
            4: "Med-High", 5: "High", 6: "V-High"
        }

        return {
            "Pacing_Mode": pacing_mode,  # Changed from pacing_mode to Pacing_Mode
            "Lower_Rate_Limit": lrl,
            "Upper_Rate_Limit": url, 
            "Maximum_Sensor_Rate": max_sensor_rate,
            "ARP": arp,
            "VRP": vrp,
            "PVARP": pvarp,
            "Atrial_Pulse_Width": float(a_pw),
            "Ventricular_Pulse_Width": float(v_pw),
            "Atrial_Amplitude": round(a_amp_raw / 100.0, 1),
            "Ventricular_Amplitude": round(v_amp_raw / 100.0, 1),
            "Atrial_Sensitivity": round(a_sens_raw / 100.0, 1),
            "Ventricular_Sensitivity": round(v_sens_raw / 100.0, 1),
            "Activity_Threshold": activity_threshold_map.get(activity_th, "Med"),
            "Reaction_Time": reaction_time,
            "Response_Factor": response_factor,
            "Recovery_Time": recovery_time,
            "Hysteresis": "On" if hyst_flag else "Off",
            "Rate_Smoothing": rate_smoothing_map.get(rate_smoothing, "Off"),
        }
    
    # def decode_egram(self, data: bytes) -> Dict[str, Any]:
    #     if len(data) != N_DATA:
    #         raise ValueError(f"EGRAM data length must be {N_DATA}, got {len(data)}")
    #     atr_raw_100 = struct.unpack_from('<H', data, 12)[0]
    #     ven_raw_100 = struct.unpack_from('<H', data, 14)[0]
    #     atr_amp = atr_raw_100 / 100.0
    #     ven_amp = ven_raw_100 / 100.0
    #     return {
    #         "m_araw": atr_amp,
    #         "m_vraw": ven_amp,
    #     }
    def decode_egram(self, data: bytes) -> Dict[str, Any]:
        atr_raw_100 = struct.unpack_from('<H', data, 12)[0]
        ven_raw_100 = struct.unpack_from('<H', data, 14)[0]

        atr_norm = atr_raw_100 / 100.0
        ven_norm = ven_raw_100 / 100.0

        atr_amp = 0.5 - atr_norm
        ven_amp = 0.5 - ven_norm

        return {
            "m_araw": atr_amp,
            "m_vraw": ven_amp,
        }
