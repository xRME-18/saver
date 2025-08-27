import pytest
import signal
import sys
import time
import threading
from unittest.mock import MagicMock, patch, call

from src.saver.core.capture import CaptureEngine


class TestCaptureEngine:
    """Test CaptureEngine class"""
    
    def setup_method(self):
        """Setup for each test"""
        # Mock all dependencies during initialization
        with patch('src.saver.core.capture.Config') as mock_config:
            with patch('src.saver.core.capture.BufferManager') as mock_buffer_manager:
                with patch('src.saver.core.capture.StorageHandler') as mock_storage_handler:
                    with patch('src.saver.core.capture.KeyListener') as mock_key_listener:
                        with patch('src.saver.core.capture.AppMonitor') as mock_app_monitor:
                            with patch('signal.signal'):
                                self.engine = CaptureEngine("test_config.yaml")
                                
                                # Store mock references
                                self.mock_config = mock_config.return_value
                                self.mock_buffer_manager = mock_buffer_manager.return_value  
                                self.mock_storage_handler = mock_storage_handler.return_value
                                self.mock_key_listener = mock_key_listener.return_value
                                self.mock_app_monitor = mock_app_monitor.return_value
    
    def test_init_creates_components_with_config(self):
        """Test that initialization creates all components with proper config"""
        with patch('src.saver.core.capture.Config') as mock_config_class:
            with patch('src.saver.core.capture.BufferManager') as mock_buffer_manager_class:
                with patch('src.saver.core.capture.StorageHandler') as mock_storage_handler_class:
                    with patch('src.saver.core.capture.KeyListener') as mock_key_listener_class:
                        with patch('src.saver.core.capture.AppMonitor') as mock_app_monitor_class:
                            with patch('signal.signal') as mock_signal:
                                
                                mock_config_class.return_value.get_database_path.return_value = "test.db"
                                
                                engine = CaptureEngine("custom_config.yaml")
                                
                                # Verify components were created with correct parameters
                                mock_config_class.assert_called_once_with("custom_config.yaml")
                                mock_buffer_manager_class.assert_called_once_with()
                                mock_storage_handler_class.assert_called_once_with("test.db")
                                mock_key_listener_class.assert_called_once_with(engine._on_key_press)
                                mock_app_monitor_class.assert_called_once_with(engine._on_app_change)
                                
                                # Verify signal handlers were registered
                                expected_signal_calls = [
                                    call(signal.SIGINT, engine._signal_handler),
                                    call(signal.SIGTERM, engine._signal_handler)
                                ]
                                mock_signal.assert_has_calls(expected_signal_calls)
                                
                                assert engine.running is False
                                assert engine.save_timer is None
    
    def test_signal_handler_calls_stop_and_exits(self):
        """Test signal handler performs clean shutdown"""
        with patch.object(self.engine, 'stop') as mock_stop:
            with patch('sys.exit') as mock_exit:
                
                self.engine._signal_handler(signal.SIGINT, None)
                
                mock_stop.assert_called_once()
                mock_exit.assert_called_once_with(0)
    
    def test_on_key_press_adds_text_when_app_should_be_captured(self):
        """Test _on_key_press adds text when current app should be captured"""
        self.mock_app_monitor.get_current_app.return_value = "TestApp"
        self.mock_config.should_capture_app.return_value = True
        
        self.engine._on_key_press("a")
        
        self.mock_app_monitor.get_current_app.assert_called_once()
        self.mock_config.should_capture_app.assert_called_once_with("TestApp")
        self.mock_buffer_manager.add_text.assert_called_once_with("TestApp", "a")
    
    def test_on_key_press_ignores_when_app_should_not_be_captured(self):
        """Test _on_key_press ignores text when app should not be captured"""
        self.mock_app_monitor.get_current_app.return_value = "BlockedApp"
        self.mock_config.should_capture_app.return_value = False
        
        self.engine._on_key_press("a")
        
        self.mock_app_monitor.get_current_app.assert_called_once()
        self.mock_config.should_capture_app.assert_called_once_with("BlockedApp")
        self.mock_buffer_manager.add_text.assert_not_called()
    
    def test_on_key_press_ignores_when_no_current_app(self):
        """Test _on_key_press ignores text when no current app"""
        self.mock_app_monitor.get_current_app.return_value = None
        
        self.engine._on_key_press("a")
        
        self.mock_config.should_capture_app.assert_not_called()
        self.mock_buffer_manager.add_text.assert_not_called()
    
    def test_on_key_press_ignores_when_empty_app_name(self):
        """Test _on_key_press ignores text when app name is empty"""
        self.mock_app_monitor.get_current_app.return_value = ""
        
        self.engine._on_key_press("a")
        
        self.mock_config.should_capture_app.assert_not_called()
        self.mock_buffer_manager.add_text.assert_not_called()
    
    def test_on_app_change_logs_app_and_capture_status(self):
        """Test _on_app_change logs app name and capture status"""
        self.mock_config.should_capture_app.return_value = True
        
        with patch('builtins.print') as mock_print:
            self.engine._on_app_change("NewApp")
            
            self.mock_config.should_capture_app.assert_called_once_with("NewApp")
            mock_print.assert_called_once_with("App changed to: NewApp (capturing: True)")
    
    def test_save_buffers_when_not_running(self):
        """Test _save_buffers returns early when not running"""
        self.engine.running = False
        
        self.engine._save_buffers()
        
        self.mock_buffer_manager.flush_all_buffers.assert_not_called()
    
    def test_save_buffers_filters_short_content(self):
        """Test _save_buffers filters out content below minimum threshold"""
        self.engine.running = True
        self.mock_config.get_min_chars_threshold.return_value = 5
        
        # Mock buffer data with varying content lengths
        mock_captures = {
            "App1": {"content": "Hi", "char_count": 2, "word_count": 1},      # Too short
            "App2": {"content": "Hello World", "char_count": 11, "word_count": 2},  # Long enough
            "App3": {"content": "   ", "char_count": 3, "word_count": 0},      # Whitespace only
        }
        self.mock_buffer_manager.flush_all_buffers.return_value = mock_captures
        self.mock_storage_handler.save_multiple_captures.return_value = 1
        
        with patch('builtins.print'):
            self.engine._save_buffers()
        
        # Should only save App2
        expected_filtered = {
            "App2": {"content": "Hello World", "char_count": 11, "word_count": 2}
        }
        self.mock_storage_handler.save_multiple_captures.assert_called_once_with(expected_filtered)
    
    def test_save_buffers_schedules_next_save_when_running(self):
        """Test _save_buffers schedules next save when still running"""
        self.engine.running = True
        self.mock_config.get_min_chars_threshold.return_value = 1
        self.mock_config.get_save_interval.return_value = 300
        self.mock_buffer_manager.flush_all_buffers.return_value = {}
        
        with patch('threading.Timer') as mock_timer:
            mock_timer_instance = MagicMock()
            mock_timer.return_value = mock_timer_instance
            
            with patch('builtins.print'):
                self.engine._save_buffers()
            
            mock_timer.assert_called_once_with(300, self.engine._save_buffers)
            mock_timer_instance.start.assert_called_once()
            assert mock_timer_instance.daemon is True
            assert self.engine.save_timer == mock_timer_instance
    
    def test_save_buffers_does_not_schedule_when_not_running(self):
        """Test _save_buffers doesn't schedule next save when stopped"""
        self.engine.running = False
        
        with patch('threading.Timer') as mock_timer:
            self.engine._save_buffers()
            
            mock_timer.assert_not_called()
    
    def test_save_buffers_with_no_content_to_save(self):
        """Test _save_buffers handles case with no content to save"""
        self.engine.running = True
        self.mock_config.get_save_interval.return_value = 300
        self.mock_buffer_manager.flush_all_buffers.return_value = {}
        
        with patch('threading.Timer') as mock_timer:
            with patch('builtins.print'):
                self.engine._save_buffers()
        
        self.mock_storage_handler.save_multiple_captures.assert_not_called()
    
    def test_start_when_capture_disabled(self):
        """Test start returns early when capture is disabled"""
        self.mock_config.is_capture_enabled.return_value = False
        
        with patch('builtins.print') as mock_print:
            self.engine.start()
        
        mock_print.assert_called_once_with("Capture is disabled in config")
        assert self.engine.running is False
        self.mock_app_monitor.start.assert_not_called()
        self.mock_key_listener.start.assert_not_called()
    
    def test_start_when_capture_enabled(self):
        """Test start initializes all components when capture is enabled"""
        self.mock_config.is_capture_enabled.return_value = True
        self.mock_config.get_save_interval.return_value = 300
        
        with patch('threading.Timer') as mock_timer:
            mock_timer_instance = MagicMock()
            mock_timer.return_value = mock_timer_instance
            
            with patch('builtins.print'):
                with patch('time.sleep', side_effect=[KeyboardInterrupt]):
                    try:
                        self.engine.start()
                    except KeyboardInterrupt:
                        pass
        
        assert self.engine.running is True
        self.mock_app_monitor.start.assert_called_once()
        self.mock_key_listener.start.assert_called_once()
        mock_timer.assert_called_once_with(300, self.engine._save_buffers)
        mock_timer_instance.start.assert_called_once()
    
    def test_start_main_loop_with_keyboard_interrupt(self):
        """Test start main loop handles KeyboardInterrupt gracefully"""
        self.mock_config.is_capture_enabled.return_value = True
        self.mock_config.get_save_interval.return_value = 300
        
        with patch('threading.Timer'):
            with patch('builtins.print'):
                with patch('time.sleep', side_effect=KeyboardInterrupt):
                    # Should not raise exception
                    self.engine.start()
    
    def test_start_main_loop_stops_when_running_false(self):
        """Test start main loop exits when running is set to False"""
        self.mock_config.is_capture_enabled.return_value = True
        self.mock_config.get_save_interval.return_value = 300
        
        def set_running_false(*args):
            self.engine.running = False
        
        with patch('threading.Timer'):
            with patch('builtins.print'):
                with patch('time.sleep', side_effect=set_running_false):
                    self.engine.start()
        
        assert self.engine.running is False
    
    def test_stop_when_not_running(self):
        """Test stop returns early when not running"""
        self.engine.running = False
        
        with patch('builtins.print'):
            self.engine.stop()
        
        self.mock_key_listener.stop.assert_not_called()
        self.mock_app_monitor.stop.assert_not_called()
    
    def test_stop_when_running(self):
        """Test stop performs cleanup when running"""
        self.engine.running = True
        mock_timer = MagicMock()
        self.engine.save_timer = mock_timer
        
        mock_captures = {
            "App1": {
                "content": "Test content",
                "char_count": 12,
                "word_count": 2
            }
        }
        self.mock_buffer_manager.flush_all_buffers.return_value = mock_captures
        self.mock_storage_handler.save_multiple_captures.return_value = 1
        
        with patch('builtins.print'):
            self.engine.stop()
        
        assert self.engine.running is False
        mock_timer.cancel.assert_called_once()
        self.mock_key_listener.stop.assert_called_once()
        self.mock_app_monitor.stop.assert_called_once()
        self.mock_buffer_manager.flush_all_buffers.assert_called_once()
        self.mock_storage_handler.save_multiple_captures.assert_called_once_with(mock_captures)
    
    def test_stop_with_no_timer(self):
        """Test stop works correctly when no timer is set"""
        self.engine.running = True
        self.engine.save_timer = None
        
        self.mock_buffer_manager.flush_all_buffers.return_value = {}
        
        with patch('builtins.print'):
            self.engine.stop()
        
        assert self.engine.running is False
    
    def test_stop_final_save_with_no_captures(self):
        """Test stop handles case with no final captures"""
        self.engine.running = True
        self.mock_buffer_manager.flush_all_buffers.return_value = {}
        
        with patch('builtins.print') as mock_print:
            self.engine.stop()
        
        self.mock_storage_handler.save_multiple_captures.assert_not_called()
        # Check that "No new content to save" was printed
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        assert "No new content to save" in print_calls
    
    def test_stop_final_save_shows_captured_content(self):
        """Test stop shows summary of captured content"""
        self.engine.running = True
        
        mock_captures = {
            "TestApp": {
                "content": "A" * 150,  # Long content to test truncation
                "char_count": 150,
                "word_count": 1
            },
            "ShortApp": {
                "content": "Short",
                "char_count": 5,
                "word_count": 1
            }
        }
        self.mock_buffer_manager.flush_all_buffers.return_value = mock_captures
        self.mock_storage_handler.save_multiple_captures.return_value = 2
        
        with patch('builtins.print') as mock_print:
            self.engine.stop()
        
        # Check that content summary was printed
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        assert any("=== Captured Content by App ===" in call for call in print_calls)
        assert any("TestApp:" in call for call in print_calls)
        assert any("Characters: 150" in call for call in print_calls)
        assert any("ShortApp:" in call for call in print_calls)
    
    def test_get_statistics_displays_comprehensive_stats(self):
        """Test get_statistics displays all relevant statistics"""
        mock_stats = {
            "total_captures": 100,
            "unique_apps": 5,
            "total_characters": 50000,
            "total_words": 8500,
            "top_apps": [
                {"app": "Chrome", "captures": 45},
                {"app": "VSCode", "captures": 30}
            ]
        }
        self.mock_storage_handler.get_statistics.return_value = mock_stats
        self.mock_buffer_manager.get_all_apps.return_value = ["CurrentApp1", "CurrentApp2"]
        
        with patch('builtins.print') as mock_print:
            self.engine.get_statistics()
        
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        
        # Check that all statistics were printed
        assert any("=== Saver Status ===" in call for call in print_calls)
        assert any("Total captures: 100" in call for call in print_calls)
        assert any("Unique apps: 5" in call for call in print_calls)
        assert any("Total characters: 50,000" in call for call in print_calls)
        assert any("Total words: 8,500" in call for call in print_calls)
        assert any("Active buffers: 2" in call for call in print_calls)
        assert any("Top apps by capture count:" in call for call in print_calls)
        assert any("Chrome: 45 captures" in call for call in print_calls)
        assert any("VSCode: 30 captures" in call for call in print_calls)
        assert any("Active apps with buffers: CurrentApp1, CurrentApp2" in call for call in print_calls)
    
    def test_get_statistics_with_empty_stats(self):
        """Test get_statistics handles empty/missing statistics"""
        self.mock_storage_handler.get_statistics.return_value = {}
        self.mock_buffer_manager.get_all_apps.return_value = []
        
        with patch('builtins.print') as mock_print:
            self.engine.get_statistics()
        
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        
        # Check default values are used
        assert any("Total captures: 0" in call for call in print_calls)
        assert any("Unique apps: 0" in call for call in print_calls)
        assert any("Total characters: 0" in call for call in print_calls)
        assert any("Active buffers: 0" in call for call in print_calls)
    
    def test_integration_key_press_to_buffer(self):
        """Integration test: key press -> buffer management"""
        self.mock_app_monitor.get_current_app.return_value = "TestApp"
        self.mock_config.should_capture_app.return_value = True
        
        # Simulate multiple key presses
        chars = ['h', 'e', 'l', 'l', 'o']
        for char in chars:
            self.engine._on_key_press(char)
        
        # Verify all characters were added to buffer
        expected_calls = [call("TestApp", char) for char in chars]
        assert self.mock_buffer_manager.add_text.call_args_list == expected_calls
    
    def test_integration_save_cycle(self):
        """Integration test: complete save cycle"""
        self.engine.running = True
        self.mock_config.get_min_chars_threshold.return_value = 3
        
        mock_captures = {
            "App1": {"content": "Hello World", "char_count": 11, "word_count": 2}
        }
        self.mock_buffer_manager.flush_all_buffers.return_value = mock_captures
        self.mock_storage_handler.save_multiple_captures.return_value = 1
        
        with patch('builtins.print'):
            with patch('threading.Timer') as mock_timer:
                self.engine._save_buffers()
        
        # Verify complete save cycle
        self.mock_buffer_manager.flush_all_buffers.assert_called_once()
        self.mock_config.get_min_chars_threshold.assert_called_once()
        self.mock_storage_handler.save_multiple_captures.assert_called_once_with(mock_captures)
        mock_timer.assert_called_once()
    
    def test_component_dependency_chain(self):
        """Test that all components are properly connected"""
        # This is verified during initialization, but let's check the references
        assert self.engine.config is self.mock_config
        assert self.engine.buffer_manager is self.mock_buffer_manager
        assert self.engine.storage_handler is self.mock_storage_handler
        assert self.engine.key_listener is self.mock_key_listener
        assert self.engine.app_monitor is self.mock_app_monitor
    
    def test_error_handling_in_save_buffers(self):
        """Test that errors in save operations propagate correctly"""
        self.engine.running = True
        self.mock_buffer_manager.flush_all_buffers.side_effect = Exception("Buffer error")
        
        # Should raise the exception since there's no error handling in _save_buffers
        with patch('builtins.print'):
            with pytest.raises(Exception, match="Buffer error"):
                self.engine._save_buffers()
    
    def test_daemon_timer_configuration(self):
        """Test that save timer is properly configured as daemon"""
        self.engine.running = True
        self.mock_config.get_save_interval.return_value = 300
        self.mock_buffer_manager.flush_all_buffers.return_value = {}
        
        with patch('threading.Timer') as mock_timer:
            mock_timer_instance = MagicMock()
            mock_timer.return_value = mock_timer_instance
            
            with patch('builtins.print'):
                self.engine._save_buffers()
            
            assert mock_timer_instance.daemon is True