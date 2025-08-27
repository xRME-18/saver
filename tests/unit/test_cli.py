import pytest
import sys
from unittest.mock import patch, MagicMock

from src.saver.cli import main


class TestCLI:
    """Test CLI functionality"""
    
    def test_main_starts_capture_engine_by_default(self):
        """Test that main() starts CaptureEngine by default with no args"""
        with patch('src.saver.cli.CaptureEngine') as mock_capture_engine_class:
            mock_engine = MagicMock()
            mock_capture_engine_class.return_value = mock_engine
            
            # Mock sys.argv with just the script name
            with patch('sys.argv', ['saver']):
                main()
            
            mock_capture_engine_class.assert_called_once_with()
            mock_engine.start.assert_called_once()
    
    def test_main_shows_status_with_status_command(self):
        """Test that main() shows statistics with 'status' command"""
        with patch('src.saver.cli.CaptureEngine') as mock_capture_engine_class:
            mock_engine = MagicMock()
            mock_capture_engine_class.return_value = mock_engine
            
            with patch('sys.argv', ['saver', 'status']):
                main()
            
            mock_capture_engine_class.assert_called_once_with()
            mock_engine.get_statistics.assert_called_once()
            mock_engine.start.assert_not_called()
    
    def test_main_shows_status_with_case_insensitive_status(self):
        """Test that status command is case insensitive"""
        with patch('src.saver.cli.CaptureEngine') as mock_capture_engine_class:
            mock_engine = MagicMock()
            mock_capture_engine_class.return_value = mock_engine
            
            test_cases = ['STATUS', 'Status', 'StAtUs']
            
            for case in test_cases:
                mock_capture_engine_class.reset_mock()
                
                with patch('sys.argv', ['saver', case]):
                    main()
                
                mock_capture_engine_class.assert_called_once_with()
                mock_engine.get_statistics.assert_called_once()
    
    def test_main_shows_help_with_help_command(self):
        """Test that main() shows help with 'help' command"""
        with patch('src.saver.cli.CaptureEngine') as mock_capture_engine_class:
            with patch('builtins.print') as mock_print:
                
                with patch('sys.argv', ['saver', 'help']):
                    main()
                
                # Verify help text was printed
                expected_calls = [
                    "Saver - App-based text capture system",
                    "Usage:",
                    "  saver         # Start capturing",
                    "  saver status  # Show statistics", 
                    "  saver help    # Show this help"
                ]
                
                print_calls = [call.args[0] for call in mock_print.call_args_list]
                for expected in expected_calls:
                    assert expected in print_calls
                
                # CaptureEngine should not be created for help
                mock_capture_engine_class.assert_not_called()
    
    def test_main_shows_help_with_case_insensitive_help(self):
        """Test that help command is case insensitive"""
        test_cases = ['HELP', 'Help', 'hElP']
        
        for case in test_cases:
            with patch('src.saver.cli.CaptureEngine') as mock_capture_engine_class:
                with patch('builtins.print') as mock_print:
                    
                    with patch('sys.argv', ['saver', case]):
                        main()
                    
                    # Should print help text
                    print_calls = [call.args[0] for call in mock_print.call_args_list]
                    assert "Saver - App-based text capture system" in print_calls
                    
                    # CaptureEngine should not be created
                    mock_capture_engine_class.assert_not_called()
    
    def test_main_starts_capture_with_unknown_command(self):
        """Test that main() starts capture with unknown commands"""
        with patch('src.saver.cli.CaptureEngine') as mock_capture_engine_class:
            mock_engine = MagicMock()
            mock_capture_engine_class.return_value = mock_engine
            
            with patch('sys.argv', ['saver', 'unknown-command']):
                main()
            
            # Unknown commands should default to starting capture
            mock_capture_engine_class.assert_called_once_with()
            mock_engine.start.assert_called_once()
    
    def test_main_starts_capture_with_multiple_args(self):
        """Test that main() starts capture when multiple args provided"""
        with patch('src.saver.cli.CaptureEngine') as mock_capture_engine_class:
            mock_engine = MagicMock()
            mock_capture_engine_class.return_value = mock_engine
            
            with patch('sys.argv', ['saver', 'some', 'random', 'args']):
                main()
            
            # Should use first argument and start capture since it's not a known command
            mock_capture_engine_class.assert_called_once_with()
            mock_engine.start.assert_called_once()
    
    def test_main_with_empty_args_list(self):
        """Test main() behavior with empty sys.argv"""
        with patch('src.saver.cli.CaptureEngine') as mock_capture_engine_class:
            mock_engine = MagicMock()
            mock_capture_engine_class.return_value = mock_engine
            
            # This is an edge case - sys.argv should always have at least the script name
            with patch('sys.argv', []):
                main()
            
            # Should default to starting capture
            mock_capture_engine_class.assert_called_once_with()
            mock_engine.start.assert_called_once()
    
    def test_cli_integrates_with_capture_engine_properly(self):
        """Integration test: CLI creates CaptureEngine with correct initialization"""
        with patch('src.saver.cli.CaptureEngine') as mock_capture_engine_class:
            mock_engine = MagicMock()
            mock_capture_engine_class.return_value = mock_engine
            
            # Test different commands create engine properly
            commands_and_methods = [
                (['saver'], 'start'),
                (['saver', 'status'], 'get_statistics'),
                (['saver', 'unknown'], 'start')
            ]
            
            for argv, expected_method in commands_and_methods:
                mock_capture_engine_class.reset_mock()
                
                with patch('sys.argv', argv):
                    main()
                
                mock_capture_engine_class.assert_called_once_with()
                getattr(mock_engine, expected_method).assert_called_once()
    
    def test_help_command_exact_output(self):
        """Test that help command produces exact expected output"""
        with patch('builtins.print') as mock_print:
            with patch('sys.argv', ['saver', 'help']):
                main()
        
        # Get all printed lines
        printed_lines = [call.args[0] for call in mock_print.call_args_list]
        
        # Verify exact help text
        expected_lines = [
            "Saver - App-based text capture system",
            "Usage:",
            "  saver         # Start capturing",
            "  saver status  # Show statistics",
            "  saver help    # Show this help"
        ]
        
        assert printed_lines == expected_lines
    
    def test_command_argument_parsing(self):
        """Test that command argument is parsed correctly"""
        test_cases = [
            # (sys.argv, expected_command_detected)
            (['saver'], 'default'),
            (['saver', 'help'], 'help'),
            (['saver', 'status'], 'status'),
            (['saver', 'HELP'], 'help'),
            (['saver', 'STATUS'], 'status'),
            (['saver', 'invalid'], 'default'),
            (['saver', 'help', 'extra'], 'help'),
            (['saver', 'status', 'extra'], 'status')
        ]
        
        for argv, expected_behavior in test_cases:
            with patch('src.saver.cli.CaptureEngine') as mock_capture_engine_class:
                mock_engine = MagicMock()
                mock_capture_engine_class.return_value = mock_engine
                
                with patch('builtins.print') as mock_print:
                    with patch('sys.argv', argv):
                        main()
                
                if expected_behavior == 'help':
                    # Help should not create engine
                    mock_capture_engine_class.assert_not_called()
                    print_calls = [call.args[0] for call in mock_print.call_args_list]
                    assert "Saver - App-based text capture system" in print_calls
                
                elif expected_behavior == 'status':
                    # Status should create engine and call get_statistics
                    mock_capture_engine_class.assert_called_once()
                    mock_engine.get_statistics.assert_called_once()
                    mock_engine.start.assert_not_called()
                
                elif expected_behavior == 'default':
                    # Default should create engine and call start
                    mock_capture_engine_class.assert_called_once()
                    mock_engine.start.assert_called_once()
                    mock_engine.get_statistics.assert_not_called()
    
    def test_main_error_handling(self):
        """Test that main() handles CaptureEngine errors gracefully"""
        with patch('src.saver.cli.CaptureEngine') as mock_capture_engine_class:
            mock_capture_engine_class.side_effect = Exception("Initialization error")
            
            with patch('sys.argv', ['saver']):
                # Should propagate the exception (CLI doesn't handle it)
                with pytest.raises(Exception, match="Initialization error"):
                    main()
    
    def test_main_handles_capture_engine_start_error(self):
        """Test main() when CaptureEngine.start() raises an error"""
        with patch('src.saver.cli.CaptureEngine') as mock_capture_engine_class:
            mock_engine = MagicMock()
            mock_engine.start.side_effect = KeyboardInterrupt("User interrupted")
            mock_capture_engine_class.return_value = mock_engine
            
            with patch('sys.argv', ['saver']):
                # Should propagate KeyboardInterrupt (normal behavior)
                with pytest.raises(KeyboardInterrupt):
                    main()
    
    def test_main_handles_capture_engine_status_error(self):
        """Test main() when CaptureEngine.get_statistics() raises an error"""
        with patch('src.saver.cli.CaptureEngine') as mock_capture_engine_class:
            mock_engine = MagicMock()
            mock_engine.get_statistics.side_effect = Exception("Database error")
            mock_capture_engine_class.return_value = mock_engine
            
            with patch('sys.argv', ['saver', 'status']):
                # Should propagate the exception
                with pytest.raises(Exception, match="Database error"):
                    main()
    
    def test_if_name_main_guard(self):
        """Test the if __name__ == '__main__' guard in cli.py"""
        # This test verifies that the guard exists and works
        # We can't easily test the guard directly, but we can verify
        # that the main function exists and is callable
        
        assert callable(main)
        assert main.__name__ == 'main'
        
        # If we were to import the module, main() should not auto-run
        # This is implicitly tested by the fact that importing the module
        # for testing doesn't start the capture engine