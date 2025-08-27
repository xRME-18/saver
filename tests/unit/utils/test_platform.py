import pytest
import sys
from unittest.mock import patch, MagicMock

# Mock platform-specific modules before importing platform module
mock_quartz = MagicMock()
mock_appkit = MagicMock()
mock_win32gui = MagicMock()
mock_win32process = MagicMock()
mock_psutil = MagicMock()

sys.modules['Quartz'] = mock_quartz
sys.modules['AppKit'] = mock_appkit
sys.modules['win32gui'] = mock_win32gui
sys.modules['win32process'] = mock_win32process
sys.modules['psutil'] = mock_psutil

from src.saver.utils.platform import (
    get_system_type, is_macos, is_windows, is_linux,
    get_active_window_macos, get_active_window_windows, 
    get_active_window_linux, get_active_window
)


class TestPlatformDetection:
    """Test platform detection functions"""
    
    def test_get_system_type(self):
        """Test getting system type"""
        with patch('platform.system', return_value='Darwin'):
            assert get_system_type() == 'Darwin'
            
        with patch('platform.system', return_value='Windows'):
            assert get_system_type() == 'Windows'
            
        with patch('platform.system', return_value='Linux'):
            assert get_system_type() == 'Linux'
    
    def test_is_macos(self):
        """Test macOS detection"""
        with patch('platform.system', return_value='Darwin'):
            assert is_macos() is True
            
        with patch('platform.system', return_value='Windows'):
            assert is_macos() is False
    
    def test_is_windows(self):
        """Test Windows detection"""
        with patch('platform.system', return_value='Windows'):
            assert is_windows() is True
            
        with patch('platform.system', return_value='Darwin'):
            assert is_windows() is False
    
    def test_is_linux(self):
        """Test Linux detection"""
        with patch('platform.system', return_value='Linux'):
            assert is_linux() is True
            
        with patch('platform.system', return_value='Darwin'):
            assert is_linux() is False


class TestMacOSWindowDetection:
    """Test macOS window detection"""
    
    def setup_method(self):
        """Reset mocks before each test"""
        mock_quartz.reset_mock()
        mock_appkit.reset_mock()
        
    def test_get_active_window_macos_quartz_success(self):
        """Test successful Quartz window detection"""
        # Create complete mock modules before the function imports them
        mock_quartz_complete = MagicMock()
        mock_quartz_complete.kCGWindowListOptionOnScreenOnly = 0x1
        mock_quartz_complete.kCGNullWindowID = 0x0
        mock_quartz_complete.CGWindowListCopyWindowInfo.return_value = [
            {'kCGWindowLayer': 0, 'kCGWindowOwnerName': 'TestApp'}
        ]
        
        with patch.dict('sys.modules', {'Quartz': mock_quartz_complete}):
            result = get_active_window_macos()
            assert result == 'TestApp'
    
    def test_get_active_window_macos_quartz_no_windows(self):
        """Test Quartz when no windows found"""
        mock_quartz_complete = MagicMock()
        mock_quartz_complete.kCGWindowListOptionOnScreenOnly = 0x1
        mock_quartz_complete.kCGNullWindowID = 0x0
        mock_quartz_complete.CGWindowListCopyWindowInfo.return_value = []
        
        with patch.dict('sys.modules', {'Quartz': mock_quartz_complete}):
            result = get_active_window_macos()
            # When Quartz returns empty list, function returns None (doesn't fallback to NSWorkspace)
            assert result is None
    
    def test_get_active_window_macos_quartz_wrong_layer(self):
        """Test Quartz with windows on wrong layer"""
        mock_quartz_complete = MagicMock()
        mock_quartz_complete.kCGWindowListOptionOnScreenOnly = 0x1
        mock_quartz_complete.kCGNullWindowID = 0x0
        mock_quartz_complete.CGWindowListCopyWindowInfo.return_value = [
            {'kCGWindowLayer': 1, 'kCGWindowOwnerName': 'BackgroundApp'}
        ]
        
        with patch.dict('sys.modules', {'Quartz': mock_quartz_complete}):
            result = get_active_window_macos()
            # When Quartz finds no windows on layer 0, function returns None
            assert result is None
    
    def test_get_active_window_macos_quartz_exception(self):
        """Test Quartz fallback on exception"""
        # Mock Quartz to throw exception, then mock AppKit to work
        mock_quartz_fail = MagicMock()
        mock_quartz_fail.CGWindowListCopyWindowInfo.side_effect = Exception("Quartz failed")
        
        mock_appkit_complete = MagicMock()
        mock_app = MagicMock()
        mock_app.localizedName.return_value = 'NSWorkspaceApp'
        mock_appkit_complete.NSWorkspace.sharedWorkspace.return_value.frontmostApplication.return_value = mock_app
        
        with patch.dict('sys.modules', {'Quartz': mock_quartz_fail, 'AppKit': mock_appkit_complete}):
            result = get_active_window_macos()
            assert result == 'NSWorkspaceApp'
    
    def test_get_active_window_macos_both_fail(self):
        """Test when both Quartz and NSWorkspace fail"""
        mock_quartz_fail = MagicMock()
        mock_quartz_fail.CGWindowListCopyWindowInfo.side_effect = Exception("Quartz failed")
        
        mock_appkit_fail = MagicMock()
        mock_appkit_fail.NSWorkspace.sharedWorkspace.side_effect = Exception("NSWorkspace failed")
        
        with patch.dict('sys.modules', {'Quartz': mock_quartz_fail, 'AppKit': mock_appkit_fail}):
            result = get_active_window_macos()
            assert result is None
    
    def test_get_active_window_macos_nsworkspace_no_app(self):
        """Test NSWorkspace fallback when no app returned"""
        mock_quartz_fail = MagicMock()
        mock_quartz_fail.CGWindowListCopyWindowInfo.side_effect = Exception("Quartz failed")
        
        mock_appkit_complete = MagicMock()
        mock_appkit_complete.NSWorkspace.sharedWorkspace.return_value.frontmostApplication.return_value = None
        
        with patch.dict('sys.modules', {'Quartz': mock_quartz_fail, 'AppKit': mock_appkit_complete}):
            result = get_active_window_macos()
            assert result is None


class TestWindowsWindowDetection:
    """Test Windows window detection"""
    
    def setup_method(self):
        """Reset mocks before each test"""
        mock_win32gui.reset_mock()
        mock_win32process.reset_mock()
        mock_psutil.reset_mock()
        
    def test_get_active_window_windows_success(self):
        """Test successful Windows window detection"""
        mock_win32gui_complete = MagicMock()
        mock_win32gui_complete.GetForegroundWindow.return_value = 12345
        
        mock_win32process_complete = MagicMock()
        mock_win32process_complete.GetWindowThreadProcessId.return_value = (None, 6789)
        
        mock_psutil_complete = MagicMock()
        mock_process_instance = MagicMock()
        mock_process_instance.name.return_value = 'TestApp.exe'
        mock_psutil_complete.Process.return_value = mock_process_instance
        
        with patch.dict('sys.modules', {
            'win32gui': mock_win32gui_complete, 
            'win32process': mock_win32process_complete, 
            'psutil': mock_psutil_complete
        }):
            result = get_active_window_windows()
            assert result == 'TestApp.exe'
    
    def test_get_active_window_windows_no_window(self):
        """Test Windows detection when no window found"""
        mock_win32gui_complete = MagicMock()
        mock_win32gui_complete.GetForegroundWindow.return_value = 0  # No window
        
        with patch.dict('sys.modules', {'win32gui': mock_win32gui_complete}):
            result = get_active_window_windows()
            assert result is None
    
    def test_get_active_window_windows_exception(self):
        """Test Windows detection with exception"""
        mock_win32gui_fail = MagicMock()
        mock_win32gui_fail.GetForegroundWindow.side_effect = ImportError("win32gui not available")
        
        with patch.dict('sys.modules', {'win32gui': mock_win32gui_fail}):
            result = get_active_window_windows()
            assert result is None


class TestLinuxWindowDetection:
    """Test Linux window detection"""
    
    def test_get_active_window_linux_success(self):
        """Test successful Linux window detection"""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = 'TestApp Window Title'
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            result = get_active_window_linux()
            assert result == 'TestApp Window Title'
            
            # Check that correct command was called
            mock_run.assert_called_once_with(
                ["xdotool", "getwindowfocus", "getwindowname"],
                capture_output=True,
                text=True,
                timeout=1
            )
    
    def test_get_active_window_linux_command_failed(self):
        """Test Linux detection when command fails"""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_run.return_value = mock_result
            
            result = get_active_window_linux()
            assert result is None
    
    def test_get_active_window_linux_exception(self):
        """Test Linux detection with exception"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("xdotool not found")
            
            result = get_active_window_linux()
            assert result is None
    
    def test_get_active_window_linux_strips_whitespace(self):
        """Test that Linux detection strips whitespace"""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = '  TestApp  \n'
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            result = get_active_window_linux()
            assert result == 'TestApp'


class TestUnifiedWindowDetection:
    """Test unified get_active_window function"""
    
    def test_get_active_window_macos(self):
        """Test that get_active_window calls macOS function on Darwin"""
        with patch('src.saver.utils.platform.get_system_type', return_value='Darwin'):
            with patch('src.saver.utils.platform.get_active_window_macos', return_value='MacApp') as mock_mac:
                result = get_active_window()
                assert result == 'MacApp'
                mock_mac.assert_called_once()
    
    def test_get_active_window_windows(self):
        """Test that get_active_window calls Windows function on Windows"""
        with patch('src.saver.utils.platform.get_system_type', return_value='Windows'):
            with patch('src.saver.utils.platform.get_active_window_windows', return_value='WinApp.exe') as mock_win:
                result = get_active_window()
                assert result == 'WinApp.exe'
                mock_win.assert_called_once()
    
    def test_get_active_window_linux(self):
        """Test that get_active_window calls Linux function on Linux"""
        with patch('src.saver.utils.platform.get_system_type', return_value='Linux'):
            with patch('src.saver.utils.platform.get_active_window_linux', return_value='LinuxApp') as mock_linux:
                result = get_active_window()
                assert result == 'LinuxApp'
                mock_linux.assert_called_once()
    
    def test_get_active_window_unsupported(self):
        """Test that get_active_window returns None for unsupported systems"""
        with patch('src.saver.utils.platform.get_system_type', return_value='FreeBSD'):
            result = get_active_window()
            assert result is None
    
    def test_get_active_window_platform_functions_called_correctly(self):
        """Test that the right platform-specific function is called"""
        # Test all supported platforms
        platforms = {
            'Darwin': ('get_active_window_macos', 'MacApp'),
            'Windows': ('get_active_window_windows', 'WinApp'),
            'Linux': ('get_active_window_linux', 'LinuxApp')
        }
        
        for platform, (func_name, expected) in platforms.items():
            with patch('src.saver.utils.platform.get_system_type', return_value=platform):
                with patch(f'src.saver.utils.platform.{func_name}', return_value=expected) as mock_func:
                    result = get_active_window()
                    assert result == expected
                    mock_func.assert_called_once()


class TestPlatformSpecificImportErrors:
    """Test handling of platform-specific import errors"""
    
    def test_macos_import_errors_handled(self):
        """Test that macOS import errors are handled gracefully"""
        # When both Quartz and AppKit fail to import, should return None
        result = get_active_window_macos()
        # On non-macOS systems, this should return None without crashing
        # On macOS systems, this should either work or return None gracefully
        assert result is None or isinstance(result, str)
    
    def test_windows_import_errors_handled(self):
        """Test that Windows import errors are handled gracefully"""
        # When win32 modules fail to import, should return None
        result = get_active_window_windows()
        # On non-Windows systems, this should return None without crashing
        assert result is None or isinstance(result, str)
    
    def test_linux_import_errors_handled(self):
        """Test that Linux import errors are handled gracefully"""
        # When subprocess or xdotool fail, should return None
        result = get_active_window_linux()
        # Should not crash even if xdotool is not available
        assert result is None or isinstance(result, str)