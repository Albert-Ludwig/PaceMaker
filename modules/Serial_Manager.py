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
N_DATA    = 13    # Every packet must carry exactly 13 data bytes

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
        header_chksum = f_chk(header)
        return header, header_chksum

    def build_packet(self, fn_code: int, data: bytes = b'') -> bytes:
        """
        Build a full packet:
          [SYNC][SOH][FnCode][HeaderChk][Data(13)][DataChk]
        Rules enforced here:
          - Every command must carry exactly 13 data bytes.
          - For non-parameter commands (ECHO/EGRAM/ESTOP):
                Data must be all zeros and DataChk must be 0.
          - For parameter command (K_PPARAMS):
                DataChk is XOR of the 13 data bytes.
        """
        header, header_chksum = self._build_header(fn_code)

        # Ensure data is exactly 13 bytes according to the command type
        if fn_code == K_PPARAMS:
            data = (data + b'\x00' * N_DATA)[:N_DATA]
            data_chksum = f_chk(data)
        else:
            data = b'\x00' * N_DATA
            data_chksum = 0

        return header + bytes([header_chksum]) + data + bytes([data_chksum])

    def build_data_packet(self, *, mode: int, params: Dict[str, Any]) -> bytes:
        """
        Build K_PPARAMS packet with a 13-byte parameter payload (little-endian):

            B  p_pacingState
            B  p_pacingMode
            B  RESERVED (always 0)          <-- was hysteresis flag; not exposed here
            H  p_hysteresisInterval         <-- kept for compatibility; caller may ignore
            H  p_lowrateInterval
            H  p_vPaceAmp
            H  (10 * p_vPaceWidth)          <-- width encoded in 0.1 ms units (uint16)
            H  p_VRP

        The layout totals 13 data bytes (B B B H H H H H).
        """
        p = params or {}
        payload = struct.pack(
            "<BBBHHHHH",
            _u8(p.get("p_pacingState", 0)),
            _u8(p.get("p_pacingMode", mode)),
            0,  # RESERVED
            _u16(p.get("p_hysteresisInterval", 300)),
            _u16(p.get("p_lowrateInterval", 1000)),
            _u16(p.get("p_vPaceAmp", 3500)),
            _u16(int(round(float(p.get("p_vPaceWidth", 0.4)) * 10.0))),
            _u16(p.get("p_VRP", 320)),
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
        """Send K_ECHO (13 zero data bytes, DataChk=0)."""
        return self.send_data(self.build_packet(K_ECHO))

    def start_egram(self) -> bool:
        """Send K_EGRAM (13 zero data bytes, DataChk=0)."""
        return self.send_data(self.build_packet(K_EGRAM))

    def stop_egram(self) -> bool:
        """Send K_ESTOP (13 zero data bytes, DataChk=0)."""
        return self.send_data(self.build_packet(K_ESTOP))

    # ---------- Full-frame read & parse (Rx) ----------
    def read_packet(self, timeout: float = 2.0) -> bytes:
        """
        Read one full framed packet:
          4 bytes header + 13 bytes data + 1 byte data checksum = 18 bytes total.
        Returns b'' on failure or timeout.
        """
        try:
            sp = self._port()
            old_to = sp.timeout
            sp.timeout = timeout

            pkt = sp.read(18)
            sp.timeout = old_to
            if len(pkt) != 18:
                return b""
            return pkt
        except Exception:
            return b""

    def parse_packet(self, pkt: bytes) -> Optional[Dict[str, Any]]:
        """
        Verify header/data checksums and return a dict on success:
            {"fn": int, "data": bytes, "header_ok": True, "data_ok": True}
        Return None if anything is invalid.
        """
        if len(pkt) != 18:
            return None

        sync, soh, fn, hdr_chk = pkt[0], pkt[1], pkt[2], pkt[3]
        if sync != SYNC or soh != SOH:
            return None
        if f_chk(bytes([sync, soh, fn])) != hdr_chk:
            return None

        data = pkt[4:17]
        data_chk = pkt[17]

        if fn == K_PPARAMS:
            # For parameter packets, DataChk must be XOR of the 13 data bytes
            if f_chk(data) != data_chk:
                return None
        if fn == K_EGRAM:
            return {"fn": fn, "data": pkt[4:17], "header_ok": True, "data_ok": True}

        else:
            # For non-parameter commands, data must be all zeros and DataChk must be 0
            if any(data) or data_chk != 0:
                return None

        return {"fn": fn, "data": data, "header_ok": True, "data_ok": True}

    # ---------- Optional decoders ----------
    @staticmethod
    def decode_params(data: bytes) -> Dict[str, Any]:
        """
        Decode 13-byte parameter payload to a dictionary.
        The 3rd byte is reserved and ignored.
        """
        if len(data) != N_DATA:
            raise ValueError("params data length error")
        (pacing_state, pacing_mode, _reserved,
         hys_int, lowrate_int, v_amp, v_width_10x, vrp) = struct.unpack("<BBBHHHHH", data)
        return {
            "p_pacingState": pacing_state,
            "p_pacingMode": pacing_mode,
            "p_hysteresisInterval": hys_int,
            "p_lowrateInterval": lowrate_int,
            "p_vPaceAmp": v_amp,
            "p_vPaceWidth": (v_width_10x / 10.0),  # back to milliseconds
            "p_VRP": vrp,
        }

    @staticmethod
    def decode_egram(data: bytes) -> Dict[str, Any]:
        """
        Decode egram data area:
          Data[0:2] -> m_vraw (uint16, little-endian)
          Data[2:4] -> marker (2 chars)
          Remaining bytes are zeros.
        """
        if len(data) != N_DATA:
            raise ValueError("egram data length error")
        m_vraw = struct.unpack("<H", data[0:2])[0]
        marker = data[2:4].decode(errors="ignore")
        return {"m_vraw": m_vraw, "marker": marker}
