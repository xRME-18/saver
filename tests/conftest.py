import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import threading
from datetime import datetime

from src.saver.storage.models import CaptureSession


@pytest.fixture
def temp_config_file():
    """Create temporary config file for testing"""
    config_content = """capture:
  save_interval_seconds: 5
  min_chars_threshold: 2
  enabled: true
apps:
  mode: "exclude"
  include_list: []
  exclude_list: ["TestExcludedApp"]
storage:
  database_path: "test.db"
  auto_cleanup_days: 30
security:
  exclude_password_fields: true
  pause_on_secure_input: true"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        f.flush()  # Ensure content is written
        yield Path(f.name)
    Path(f.name).unlink()


@pytest.fixture
def temp_db_path(tmp_path):
    """Create temporary database path"""
    return str(tmp_path / "test.db")


@pytest.fixture
def sample_capture_session():
    """Create sample CaptureSession for testing"""
    return CaptureSession(
        app_name="TestApp",
        content="Hello world test content",
        start_time=datetime(2024, 1, 1, 12, 0, 0),
        end_time=datetime(2024, 1, 1, 12, 5, 0),
        char_count=25,
        word_count=4
    )


@pytest.fixture
def mock_keyboard_listener():
    """Mock pynput keyboard listener"""
    with patch('src.saver.monitors.key_listener.keyboard.Listener') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_keyboard_key():
    """Mock keyboard key objects"""
    with patch('src.saver.monitors.key_listener.keyboard.Key') as mock_key:
        # Set up common key attributes
        mock_key.space = 'space'
        mock_key.enter = 'enter' 
        mock_key.tab = 'tab'
        mock_key.cmd = 'cmd'
        mock_key.cmd_l = 'cmd_l'
        mock_key.cmd_r = 'cmd_r'
        mock_key.alt = 'alt'
        mock_key.alt_l = 'alt_l'
        mock_key.alt_r = 'alt_r'
        mock_key.ctrl = 'ctrl'
        mock_key.ctrl_l = 'ctrl_l'
        mock_key.ctrl_r = 'ctrl_r'
        mock_key.shift = 'shift'
        mock_key.shift_l = 'shift_l'
        mock_key.shift_r = 'shift_r'
        yield mock_key


@pytest.fixture
def mock_platform_detection():
    """Mock platform detection functions"""
    with patch('src.saver.utils.platform.get_active_window') as mock:
        mock.return_value = "TestApp"
        yield mock


@pytest.fixture
def mock_threading_timer():
    """Mock threading.Timer for testing"""
    with patch('threading.Timer') as mock_timer:
        mock_instance = MagicMock()
        mock_timer.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_signal():
    """Mock signal registration"""
    with patch('signal.signal') as mock_signal:
        yield mock_signal


@pytest.fixture
def sample_buffer_data():
    """Sample buffer data for testing"""
    return {
        "app_name": "TestApp",
        "content": "Sample text content",
        "start_time": datetime(2024, 1, 1, 12, 0, 0),
        "end_time": datetime(2024, 1, 1, 12, 5, 0),
        "char_count": 18,
        "word_count": 3
    }


@pytest.fixture
def mock_app_apis():
    """Mock all platform-specific app detection APIs"""
    mocks = {}
    
    # macOS mocks
    with patch('src.saver.utils.platform.CGWindowListCopyWindowInfo') as mock_quartz:
        mock_quartz.return_value = [
            {'kCGWindowLayer': 0, 'kCGWindowOwnerName': 'TestApp'}
        ]
        mocks['quartz'] = mock_quartz
        
        with patch('src.saver.utils.platform.NSWorkspace') as mock_workspace:
            mock_app = MagicMock()
            mock_app.localizedName.return_value = 'TestApp'
            mock_workspace.sharedWorkspace.return_value.frontmostApplication.return_value = mock_app
            mocks['workspace'] = mock_workspace
            
            # Windows mocks
            with patch('src.saver.utils.platform.win32gui.GetForegroundWindow') as mock_win32:
                mock_win32.return_value = 12345
                mocks['win32'] = mock_win32
                
                # Linux mocks
                with patch('src.saver.utils.platform.subprocess.run') as mock_subprocess:
                    mock_subprocess.return_value.stdout = 'TestApp'
                    mock_subprocess.return_value.returncode = 0
                    mocks['subprocess'] = mock_subprocess
                    
                    yield mocks


@pytest.fixture
def mock_datetime():
    """Mock datetime.now() for consistent testing"""
    fixed_time = datetime(2024, 1, 1, 12, 0, 0)
    with patch('src.saver.core.buffer_manager.datetime') as mock_dt:
        mock_dt.now.return_value = fixed_time
        yield mock_dt