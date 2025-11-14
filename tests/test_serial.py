# tests/test_serial.py
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
# 文件名: test_serial.py
import pytest
import struct
from modules.Serial import (
    SerialManager, f_chk,
    SYNC, SOH, K_ECHO, K_PPARAMS, K_EGRAM, K_ESTOP, N_DATA
)

def test_constants_match_spec():
    """
    验证 Serial.py 中的常量是否与 PDF 规范中的值匹配。
    """
    # 来自 PDF 第 4 页, 3.2. Internal Constants
    assert SYNC == 0x16       # k_sync
    assert SOH == 0x01        # k_soh
    assert K_EGRAM == 0x47    # k_egram
    assert K_ECHO == 0x49     # k_echo
    assert K_ESTOP == 0x62    # k_estop
    assert K_PPARAMS == 0x55  # k_pparams
    
    # 来自 PDF 第 13 页, 5.1.1 Structure of Receive Packet
    assert N_DATA == 13       # n=13

def test_f_chk_matches_spec():
    """
    验证 f_chk (XOR 校验和) 是否符合 PDF 第 20 页 的定义。
    """
    data = b'\x12\x34\x56'
    # 13.5 f_Chk(a0, a1, ..., an) = a0 XOR a1 XOR ... XOR an
    expected_checksum = 0x12 ^ 0x34 ^ 0x56
    assert f_chk(data) == expected_checksum
    
    data_empty = b''
    assert f_chk(data_empty) == 0

def test_non_parameter_packet_build():
    """
    验证非参数命令 (如 K_ECHO) 的数据包构建。
    根据 PDF，数据应为全零，数据校验和为 0。
    """
    mgr = SerialManager()
    packet = mgr.build_packet(K_ECHO)
    
    assert len(packet) == 18  # 4 字节头部 + 13 字节数据 + 1 字节数据校验和
    
    header = packet[0:4]
    data = packet[4:17]
    data_chk = packet[17]
    
    # 验证头部
    assert header[0] == SYNC
    assert header[1] == SOH
    assert header[2] == K_ECHO
    assert header[3] == f_chk(header[0:3]) # 头部校验和
    
    # 验证数据和数据校验和
    assert data == b'\x00' * 13
    assert data_chk == 0

def test_parameter_packet_build_parse_roundtrip():
    """
    验证 K_PPARAMS 数据包的构建、解析和解码的完整往返过程。
    使用 PDF 第 3 页 中的值作为测试数据。
    """
    mgr = SerialManager()
    
    # 使用 PDF 中的默认值/范围
    test_params = {
        "p_pacingState": 0, # PERMANENT
        "p_pacingMode": 7,  # 假设 VVI 映射到 7 (PDF 未指定数字)
        "p_hysteresisInterval": 300, #
        "p_lowrateInterval": 1000,   #
        "p_vPaceAmp": 3500,          #
        "p_vPaceWidth": 0.4,         #
        "p_VRP": 320                 #
    }
    test_mode = 7 # VVI

    # 1. 构建 (Build)
    packet = mgr.build_data_packet(mode=test_mode, params=test_params)
    
    assert len(packet) == 18
    payload = packet[4:17]
    data_chk = packet[17]
    
    # 验证数据包头部
    assert packet[0] == SYNC
    assert packet[1] == SOH
    assert packet[2] == K_PPARAMS
    assert packet[3] == f_chk(packet[0:3]) # 头部校验和
    
    # 验证数据包载荷和校验和
    assert len(payload) == 13
    assert data_chk == f_chk(payload) # 数据校验和
    
    # 2. 解析 (Parse)
    parsed = mgr.parse_packet(packet)
    assert parsed is not None
    assert parsed['fn'] == K_PPARAMS
    assert parsed['data_ok'] is True
    assert parsed['header_ok'] is True
    assert parsed['data'] == payload
    
    # 3. 解码 (Decode)
    decoded = mgr.decode_params(parsed['data'])
    
    # 验证解码后的值是否与输入一致
    assert decoded['p_pacingState'] == test_params['p_pacingState']
    assert decoded['p_pacingMode'] == test_mode
    assert decoded['p_lowrateInterval'] == test_params['p_lowrateInterval']
    assert decoded['p_vPaceAmp'] == test_params['p_vPaceAmp']
    assert decoded['p_VRP'] == test_params['p_VRP']
    # 特别注意 p_vPaceWidth 的 10 倍转换
    assert decoded['p_vPaceWidth'] == test_params['p_vPaceWidth']