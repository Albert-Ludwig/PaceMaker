# tests/test_serial.py
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
# 文件名: test_communication.py
import pytest
from pytest_mock import MockerFixture
from modules.Communication import PacemakerCommunication
from modules.Serial import SerialManager # 仅用于类型提示和模拟

def test_baudrate_compliance():
    """
    验证通信管理器是否遵守 PDF 规范中的波特率要求。
    PDF 第 18 页, 7. Performance Requirements 
    "2. Serial communication baud rate shall be 57600."
    
    注意：根据所提供的 Communication.py 文件，该测试预期会失败，
    因为它硬编码了 115200，而不是规范的 57600。
    """
    spec_baudrate = 57600 # 
    comm = PacemakerCommunication(port="COM_TEST")
    
    # 断言初始化时设置的波特率是否符合规范
    assert comm.serial_mgr.baudrate == spec_baudrate, \
        f"Baudrate is {comm.serial_mgr.baudrate}, but spec requires {spec_baudrate}"

def test_upload_parameters_uses_serial_manager(mocker: MockerFixture):
    """
    使用模拟 (mocking) 来验证 upload_parameters 是否正确调用了 SerialManager。
    """
    # 1. 准备模拟
    # 模拟 SerialManager 实例
    mock_serial_mgr = mocker.MagicMock(spec=SerialManager)
    
    # 模拟 build_data_packet 的返回值
    test_packet = b'\x16\x01\x55\x42' + (b'\x00' * 13) + b'\x00' # 模拟一个 18 字节的数据包
    mock_serial_mgr.build_data_packet.return_value = test_packet
    
    # 模拟 send_data 的返回值
    mock_serial_mgr.send_data.return_value = True
    
    # 2. 注入模拟
    # Patcher (修补) 'Communication.SerialManager' 构造函数，使其返回我们的模拟实例
    mocker.patch('modules.Communication.SerialManager', return_value=mock_serial_mgr)

    # 3. 设置测试
    # 现在创建 PacemakerCommunication 时，它将使用我们的 mock_serial_mgr
    comm = PacemakerCommunication(port="COM_TEST")
    comm.is_connected = True # 手动设置连接状态
    
    # 来自 PDF 第 3 页 [cite: 42] 的测试参数
    test_params = {"p_lowrateInterval": 1000, "p_vPaceAmp": 3500}
    test_mode = 7 # VVI [cite: 42]
    
    # 4. 执行
    result = comm.upload_parameters(mode=test_mode, parameters=test_params)

    # 5. 断言
    assert result['success'] is True
    assert result['message'] == "Successfully uploaded 2 parameters"
    
    # 验证 SerialManager 的方法是否被正确调用
    mock_serial_mgr.build_data_packet.assert_called_once_with(
        mode=test_mode, 
        params=test_params
    )
    
    mock_serial_mgr.send_data.assert_called_once_with(test_packet)

def test_upload_parameters_fails_if_not_connected(mocker: MockerFixture):
    """
    验证如果未连接，upload_parameters 是否会快速失败。
    """
    # 模拟 SerialManager
    mock_serial_mgr = mocker.MagicMock(spec=SerialManager)
    mocker.patch('modules.Communication.SerialManager', return_value=mock_serial_mgr)

    comm = PacemakerCommunication(port="COM_TEST")
    comm.is_connected = False # 确保处于未连接状态
    
    test_params = {"p_lowrateInterval": 1000}
    
    # 执行
    result = comm.upload_parameters(mode=7, parameters=test_params)
    
    # 断言
    assert result['success'] is False
    assert result['message'] == "Device not connected"
    
    # 验证没有尝试发送任何数据
    mock_serial_mgr.build_data_packet.assert_not_called()
    mock_serial_mgr.send_data.assert_not_called()