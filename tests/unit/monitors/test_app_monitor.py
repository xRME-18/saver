import pytest
import time
import threading
from unittest.mock import MagicMock, patch, call

from src.saver.monitors.app_monitor import AppMonitor


class TestAppMonitor:
    """Test AppMonitor class"""
    
    def setup_method(self):
        """Setup for each test"""
        self.callback_mock = MagicMock()
        self.monitor = AppMonitor(self.callback_mock)
    
    def test_init_sets_callback_and_initial_state(self):
        """Test that initialization sets up callback and initial state"""
        callback = MagicMock()
        monitor = AppMonitor(callback)
        
        assert monitor.on_app_change_callback == callback
        assert monitor.current_app == ""
        assert monitor.running is False
        assert monitor.thread is None
        assert monitor.poll_interval == 1.0
    
    def test_start_creates_and_starts_thread(self):
        """Test that start creates and starts monitoring thread"""
        with patch('threading.Thread') as mock_thread_class:
            mock_thread = MagicMock()
            mock_thread_class.return_value = mock_thread
            
            self.monitor.start()
            
            assert self.monitor.running is True
            mock_thread_class.assert_called_once_with(
                target=self.monitor._monitor_loop,
                daemon=True
            )
            mock_thread.start.assert_called_once()
            assert self.monitor.thread == mock_thread
    
    def test_start_when_already_running(self):
        """Test that start does nothing when already running"""
        self.monitor.running = True
        
        with patch('threading.Thread') as mock_thread_class:
            self.monitor.start()
            
            mock_thread_class.assert_not_called()
    
    def test_stop_when_running(self):
        """Test stop functionality when monitor is running"""
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        self.monitor.thread = mock_thread
        self.monitor.running = True
        
        self.monitor.stop()
        
        assert self.monitor.running is False
        mock_thread.join.assert_called_once_with(timeout=2.0)
    
    def test_stop_when_not_running(self):
        """Test that stop works when monitor is not running"""
        self.monitor.running = False
        self.monitor.thread = None
        
        self.monitor.stop()
        
        assert self.monitor.running is False
    
    def test_stop_with_dead_thread(self):
        """Test stop when thread exists but is not alive"""
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = False
        self.monitor.thread = mock_thread
        self.monitor.running = True
        
        self.monitor.stop()
        
        assert self.monitor.running is False
        mock_thread.join.assert_not_called()
    
    def test_stop_with_no_thread(self):
        """Test stop when no thread exists"""
        self.monitor.thread = None
        self.monitor.running = True
        
        self.monitor.stop()
        
        assert self.monitor.running is False
    
    def test_get_active_app_calls_platform_function(self):
        """Test that _get_active_app calls get_active_window"""
        with patch('src.saver.monitors.app_monitor.get_active_window') as mock_get_active_window:
            mock_get_active_window.return_value = "TestApp"
            
            result = self.monitor._get_active_app()
            
            assert result == "TestApp"
            mock_get_active_window.assert_called_once()
    
    def test_get_current_app_returns_current_app(self):
        """Test get_current_app returns the current app name"""
        self.monitor.current_app = "MyApp"
        
        result = self.monitor.get_current_app()
        
        assert result == "MyApp"
    
    def test_monitor_loop_detects_app_change(self):
        """Test that monitor loop detects and handles app changes"""
        with patch('src.saver.monitors.app_monitor.get_active_window') as mock_get_active_window:
            # Set up sequence of app detections
            mock_get_active_window.side_effect = [
                "App1",  # First detection
                "App1",  # Same app (should not trigger callback)
                "App2",  # App change (should trigger callback)
                "App2",  # Same app again (should not trigger callback)
            ]
            
            self.monitor.running = True
            
            with patch('time.sleep') as mock_sleep:
                mock_sleep.side_effect = [None, None, None, Exception("Stop loop")]
                
                try:
                    self.monitor._monitor_loop()
                except Exception:
                    pass  # Expected to stop the loop
            
            # Should be called twice: once for App1, once for App2
            expected_calls = [call("App1"), call("App2")]
            assert self.callback_mock.call_args_list == expected_calls
            assert self.monitor.current_app == "App2"
    
    def test_monitor_loop_ignores_none_app_name(self):
        """Test that monitor loop ignores None app names"""
        with patch('src.saver.monitors.app_monitor.get_active_window') as mock_get_active_window:
            mock_get_active_window.side_effect = [
                None,     # No app detected
                "App1",   # Valid app
                None,     # No app again
            ]
            
            self.monitor.running = True
            
            with patch('time.sleep') as mock_sleep:
                mock_sleep.side_effect = [None, None, Exception("Stop loop")]
                
                try:
                    self.monitor._monitor_loop()
                except Exception:
                    pass
            
            # Should only be called once for App1
            self.callback_mock.assert_called_once_with("App1")
            assert self.monitor.current_app == "App1"
    
    def test_monitor_loop_ignores_empty_app_name(self):
        """Test that monitor loop ignores empty app names"""
        with patch('src.saver.monitors.app_monitor.get_active_window') as mock_get_active_window:
            mock_get_active_window.side_effect = [
                "",       # Empty app name
                "App1",   # Valid app
                "",       # Empty again
            ]
            
            self.monitor.running = True
            
            with patch('time.sleep') as mock_sleep:
                mock_sleep.side_effect = [None, None, Exception("Stop loop")]
                
                try:
                    self.monitor._monitor_loop()
                except Exception:
                    pass
            
            # Should only be called once for App1
            self.callback_mock.assert_called_once_with("App1")
            assert self.monitor.current_app == "App1"
    
    def test_monitor_loop_handles_get_active_app_exception(self):
        """Test that monitor loop handles exceptions from get_active_app"""
        with patch('src.saver.monitors.app_monitor.get_active_window') as mock_get_active_window:
            mock_get_active_window.side_effect = [
                Exception("Platform error"),
                "App1",   # Should continue after exception
            ]
            
            self.monitor.running = True
            
            with patch('time.sleep') as mock_sleep:
                mock_sleep.side_effect = [None, Exception("Stop loop")]
                
                try:
                    self.monitor._monitor_loop()
                except Exception:
                    pass
            
            # Should still be called for App1 after the exception
            self.callback_mock.assert_called_once_with("App1")
    
    def test_monitor_loop_sleeps_with_poll_interval(self):
        """Test that monitor loop sleeps with correct poll interval"""
        with patch('src.saver.monitors.app_monitor.get_active_window') as mock_get_active_window:
            self.monitor.poll_interval = 2.5
            mock_get_active_window.return_value = "App1"
            self.monitor.running = True
            
            with patch('time.sleep') as mock_sleep:
                mock_sleep.side_effect = [Exception("Stop loop")]
                
                try:
                    self.monitor._monitor_loop()
                except Exception:
                    pass
            
            mock_sleep.assert_called_once_with(2.5)
    
    def test_monitor_loop_stops_when_running_false(self):
        """Test that monitor loop stops when running is set to False"""
        with patch('src.saver.monitors.app_monitor.get_active_window') as mock_get_active_window:
            mock_get_active_window.return_value = "App1"
            
            # Start with running=True, then set to False after first iteration
            self.monitor.running = True
            
            call_count = 0
            def side_effect(*args):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    # After first sleep, stop the monitor
                    self.monitor.running = False
                # Second call should not happen due to while condition
            
            with patch('time.sleep', side_effect=side_effect):
                self.monitor._monitor_loop()
            
            # Should only be called once before stopping
            self.callback_mock.assert_called_once_with("App1")
    
    def test_monitor_loop_from_initial_empty_state(self):
        """Test monitor loop starting from empty current_app state"""
        with patch('src.saver.monitors.app_monitor.get_active_window') as mock_get_active_window:
            mock_get_active_window.return_value = "FirstApp"
            self.monitor.running = True
            
            with patch('time.sleep') as mock_sleep:
                mock_sleep.side_effect = [Exception("Stop loop")]
                
                try:
                    self.monitor._monitor_loop()
                except Exception:
                    pass
            
            self.callback_mock.assert_called_once_with("FirstApp")
            assert self.monitor.current_app == "FirstApp"
    
    def test_app_change_sequence(self):
        """Test a realistic sequence of app changes"""
        with patch('src.saver.monitors.app_monitor.get_active_window') as mock_get_active_window:
            app_sequence = [
                "Chrome",
                "Chrome",      # Same app, no callback
                "VSCode", 
                "Terminal",
                "Terminal",    # Same app, no callback
                "Chrome",      # Back to Chrome
            ]
            
            mock_get_active_window.side_effect = app_sequence
            self.monitor.running = True
            
            with patch('time.sleep') as mock_sleep:
                mock_sleep.side_effect = [None] * (len(app_sequence) - 1) + [Exception("Stop")]
                
                try:
                    self.monitor._monitor_loop()
                except Exception:
                    pass
            
            expected_calls = [
                call("Chrome"),
                call("VSCode"),
                call("Terminal"),
                call("Chrome")
            ]
            assert self.callback_mock.call_args_list == expected_calls
            assert self.monitor.current_app == "Chrome"
    
    def test_integration_start_and_stop(self):
        """Integration test for starting and stopping monitor"""
        with patch('src.saver.monitors.app_monitor.get_active_window') as mock_get_active_window:
            mock_get_active_window.side_effect = ["App1", "App2"]
            
            # Start the monitor
            self.monitor.start()
            assert self.monitor.running is True
            assert self.monitor.thread is not None
            
            # Let it run briefly
            time.sleep(0.1)
            
            # Stop the monitor
            self.monitor.stop()
            assert self.monitor.running is False
            
            # Thread should be joined and no longer alive
            if self.monitor.thread:
                assert not self.monitor.thread.is_alive()
    
    def test_multiple_start_calls_ignored(self):
        """Test that multiple start calls don't create multiple threads"""
        with patch('threading.Thread') as mock_thread_class:
            mock_thread = MagicMock()
            mock_thread_class.return_value = mock_thread
            
            # First start
            self.monitor.start()
            assert mock_thread_class.call_count == 1
            
            # Second start should be ignored
            self.monitor.start()
            assert mock_thread_class.call_count == 1
    
    def test_stop_without_start(self):
        """Test that stop works correctly without start being called"""
        self.monitor.stop()
        
        assert self.monitor.running is False
    
    def test_custom_poll_interval(self):
        """Test that custom poll interval is respected"""
        with patch('src.saver.monitors.app_monitor.get_active_window') as mock_get_active_window:
            callback = MagicMock()
            monitor = AppMonitor(callback)
            monitor.poll_interval = 0.5
            
            mock_get_active_window.return_value = "TestApp"
            monitor.running = True
            
            with patch('time.sleep') as mock_sleep:
                mock_sleep.side_effect = [Exception("Stop loop")]
                
                try:
                    monitor._monitor_loop()
                except Exception:
                    pass
            
            mock_sleep.assert_called_once_with(0.5)
    
    def test_daemon_thread_created(self):
        """Test that the monitoring thread is created as daemon"""
        with patch('threading.Thread') as mock_thread_class:
            self.monitor.start()
            
            mock_thread_class.assert_called_once_with(
                target=self.monitor._monitor_loop,
                daemon=True
            )
    
    def test_thread_lifecycle(self):
        """Test complete thread lifecycle"""
        with patch('threading.Thread') as mock_thread_class:
            mock_thread = MagicMock()
            mock_thread.is_alive.return_value = True
            mock_thread_class.return_value = mock_thread
            
            # Start
            self.monitor.start()
            assert self.monitor.thread == mock_thread
            mock_thread.start.assert_called_once()
            
            # Stop
            self.monitor.stop()
            mock_thread.join.assert_called_once_with(timeout=2.0)
    
    def test_error_handling_in_monitor_loop(self):
        """Test error handling doesn't crash the monitor loop"""
        with patch('src.saver.monitors.app_monitor.get_active_window') as mock_get_active_window:
            # First call raises exception, second succeeds
            mock_get_active_window.side_effect = [
                Exception("Test error"),
                "RecoveredApp"
            ]
            
            self.monitor.running = True
            
            with patch('time.sleep') as mock_sleep:
                mock_sleep.side_effect = [None, Exception("Stop loop")]
                
                try:
                    self.monitor._monitor_loop()
                except Exception:
                    pass
            
            # Should still detect the app after the error
            self.callback_mock.assert_called_once_with("RecoveredApp")
            assert self.monitor.current_app == "RecoveredApp"