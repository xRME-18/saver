import pytest
from unittest.mock import MagicMock, patch, call

from src.saver.monitors.key_listener import KeyListener


class TestKeyListener:
    """Test KeyListener class"""
    
    def setup_method(self):
        """Setup for each test"""
        self.callback_mock = MagicMock()
        self.listener = KeyListener(self.callback_mock)
    
    def test_init_sets_callback_and_initial_state(self):
        """Test that initialization sets up callback and initial state"""
        callback = MagicMock()
        listener = KeyListener(callback)
        
        assert listener.on_key_callback == callback
        assert listener.listener is None
        assert listener.running is False
        assert listener.modifiers_pressed == {
            'cmd': False,
            'alt': False, 
            'ctrl': False,
            'shift': False
        }
    
    def test_start_creates_and_starts_listener(self, mock_keyboard_listener):
        """Test that start creates and starts keyboard listener"""
        self.listener.start()
        
        assert self.listener.running is True
        assert self.listener.listener is not None
        mock_keyboard_listener.start.assert_called_once()
    
    def test_start_when_already_running(self, mock_keyboard_listener):
        """Test that start does nothing when already running"""
        self.listener.start()
        mock_keyboard_listener.start.reset_mock()
        
        self.listener.start()  # Call again
        
        mock_keyboard_listener.start.assert_not_called()
    
    def test_stop_when_running(self, mock_keyboard_listener):
        """Test stop functionality when listener is running"""
        self.listener.start()
        
        self.listener.stop()
        
        assert self.listener.running is False
        assert self.listener.listener is None
        mock_keyboard_listener.stop.assert_called_once()
    
    def test_stop_when_not_running(self):
        """Test that stop does nothing when not running"""
        # Don't start the listener first
        self.listener.stop()
        
        assert self.listener.running is False
        assert self.listener.listener is None
    
    def test_stop_when_no_listener(self):
        """Test stop when running flag is True but no listener exists"""
        self.listener.running = True
        self.listener.listener = None
        
        self.listener.stop()
        
        # Should return early without changing state when no listener exists
        assert self.listener.running is True
    
    def test_on_press_regular_character(self, mock_keyboard_key):
        """Test _on_press with regular character"""
        key_mock = MagicMock()
        key_mock.char = 'a'
        
        self.listener._on_press(key_mock)
        
        self.callback_mock.assert_called_once_with('a')
    
    def test_on_press_space_key(self, mock_keyboard_key):
        """Test _on_press with space key"""
        self.listener._on_press(mock_keyboard_key.space)
        
        self.callback_mock.assert_called_once_with(' ')
    
    def test_on_press_enter_key(self, mock_keyboard_key):
        """Test _on_press with enter key"""
        self.listener._on_press(mock_keyboard_key.enter)
        
        self.callback_mock.assert_called_once_with('\n')
    
    def test_on_press_tab_key(self, mock_keyboard_key):
        """Test _on_press with tab key"""
        self.listener._on_press(mock_keyboard_key.tab)
        
        self.callback_mock.assert_called_once_with('\t')
    
    def test_on_press_key_without_char(self):
        """Test _on_press with key that has no char attribute"""
        key_mock = MagicMock(spec=[])  # No char attribute
        
        self.listener._on_press(key_mock)
        
        self.callback_mock.assert_not_called()
    
    def test_on_press_key_with_none_char(self):
        """Test _on_press with key that has char=None"""
        key_mock = MagicMock()
        key_mock.char = None
        
        self.listener._on_press(key_mock)
        
        self.callback_mock.assert_not_called()
    
    def test_on_press_handles_exception(self):
        """Test that _on_press handles exceptions gracefully"""
        # Create a mock that raises an exception when accessed
        key_mock = MagicMock()
        key_mock.char = None
        self.callback_mock.side_effect = Exception("Test exception")
        
        # Should not raise exception
        self.listener._on_press(key_mock)
    
    def test_on_release_calls_update_modifier_state(self, mock_keyboard_key):
        """Test that _on_release calls _update_modifier_state"""
        with patch.object(self.listener, '_update_modifier_state') as mock_update:
            self.listener._on_release(mock_keyboard_key.cmd)
            
            mock_update.assert_called_once_with(mock_keyboard_key.cmd, False)
    
    def test_on_release_handles_exception(self):
        """Test that _on_release handles exceptions gracefully"""
        with patch.object(self.listener, '_update_modifier_state', 
                         side_effect=Exception("Test exception")):
            # Should not raise exception
            self.listener._on_release(MagicMock())
    
    def test_update_modifier_state_cmd_keys(self, mock_keyboard_key):
        """Test _update_modifier_state with command keys"""
        test_cases = [
            (mock_keyboard_key.cmd, 'cmd'),
            (mock_keyboard_key.cmd_l, 'cmd'),
            (mock_keyboard_key.cmd_r, 'cmd')
        ]
        
        for key, modifier in test_cases:
            self.listener.modifiers_pressed[modifier] = False
            self.listener._update_modifier_state(key, True)
            assert self.listener.modifiers_pressed[modifier] is True
            
            self.listener._update_modifier_state(key, False)
            assert self.listener.modifiers_pressed[modifier] is False
    
    def test_update_modifier_state_alt_keys(self, mock_keyboard_key):
        """Test _update_modifier_state with alt keys"""
        test_cases = [
            (mock_keyboard_key.alt, 'alt'),
            (mock_keyboard_key.alt_l, 'alt'),
            (mock_keyboard_key.alt_r, 'alt')
        ]
        
        for key, modifier in test_cases:
            self.listener.modifiers_pressed[modifier] = False
            self.listener._update_modifier_state(key, True)
            assert self.listener.modifiers_pressed[modifier] is True
            
            self.listener._update_modifier_state(key, False)
            assert self.listener.modifiers_pressed[modifier] is False
    
    def test_update_modifier_state_ctrl_keys(self, mock_keyboard_key):
        """Test _update_modifier_state with control keys"""
        test_cases = [
            (mock_keyboard_key.ctrl, 'ctrl'),
            (mock_keyboard_key.ctrl_l, 'ctrl'),
            (mock_keyboard_key.ctrl_r, 'ctrl')
        ]
        
        for key, modifier in test_cases:
            self.listener.modifiers_pressed[modifier] = False
            self.listener._update_modifier_state(key, True)
            assert self.listener.modifiers_pressed[modifier] is True
            
            self.listener._update_modifier_state(key, False)
            assert self.listener.modifiers_pressed[modifier] is False
    
    def test_update_modifier_state_shift_keys(self, mock_keyboard_key):
        """Test _update_modifier_state with shift keys"""
        test_cases = [
            (mock_keyboard_key.shift, 'shift'),
            (mock_keyboard_key.shift_l, 'shift'),
            (mock_keyboard_key.shift_r, 'shift')
        ]
        
        for key, modifier in test_cases:
            self.listener.modifiers_pressed[modifier] = False
            self.listener._update_modifier_state(key, True)
            assert self.listener.modifiers_pressed[modifier] is True
            
            self.listener._update_modifier_state(key, False)
            assert self.listener.modifiers_pressed[modifier] is False
    
    def test_update_modifier_state_non_modifier_key(self):
        """Test _update_modifier_state with non-modifier key"""
        key_mock = MagicMock()
        key_mock.char = 'a'  # Regular key, not a modifier
        
        initial_state = self.listener.modifiers_pressed.copy()
        self.listener._update_modifier_state(key_mock, True)
        
        assert self.listener.modifiers_pressed == initial_state
    
    def test_should_skip_key_no_modifiers(self):
        """Test _should_skip_key when no modifiers are pressed"""
        assert self.listener._should_skip_key() is False
    
    def test_should_skip_key_cmd_pressed(self):
        """Test _should_skip_key when command key is pressed"""
        self.listener.modifiers_pressed['cmd'] = True
        assert self.listener._should_skip_key() is True
    
    def test_should_skip_key_alt_pressed(self):
        """Test _should_skip_key when alt key is pressed"""
        self.listener.modifiers_pressed['alt'] = True
        assert self.listener._should_skip_key() is True
    
    def test_should_skip_key_ctrl_pressed(self):
        """Test _should_skip_key when control key is pressed"""
        self.listener.modifiers_pressed['ctrl'] = True
        assert self.listener._should_skip_key() is True
    
    def test_should_skip_key_shift_only(self):
        """Test _should_skip_key when only shift is pressed (should not skip)"""
        self.listener.modifiers_pressed['shift'] = True
        assert self.listener._should_skip_key() is False
    
    def test_should_skip_key_multiple_modifiers(self):
        """Test _should_skip_key with multiple modifiers pressed"""
        self.listener.modifiers_pressed['cmd'] = True
        self.listener.modifiers_pressed['shift'] = True
        assert self.listener._should_skip_key() is True
    
    def test_on_press_skips_when_modifier_pressed(self, mock_keyboard_key):
        """Test that _on_press skips callback when modifiers are pressed"""
        self.listener.modifiers_pressed['cmd'] = True
        
        key_mock = MagicMock()
        key_mock.char = 'a'
        
        self.listener._on_press(key_mock)
        
        self.callback_mock.assert_not_called()
    
    def test_on_press_allows_shift_combinations(self, mock_keyboard_key):
        """Test that _on_press allows text with shift (capitalization)"""
        self.listener.modifiers_pressed['shift'] = True
        
        key_mock = MagicMock()
        key_mock.char = 'A'
        
        self.listener._on_press(key_mock)
        
        self.callback_mock.assert_called_once_with('A')
    
    def test_modifier_state_tracking_integration(self, mock_keyboard_key):
        """Test integration of modifier state tracking with key press"""
        # Simulate pressing Command key
        self.listener._on_press(mock_keyboard_key.cmd)
        assert self.listener.modifiers_pressed['cmd'] is True
        
        # Now try to type 'a' - should be skipped
        key_mock = MagicMock()
        key_mock.char = 'a'
        self.listener._on_press(key_mock)
        self.callback_mock.assert_not_called()
        
        # Release Command key
        self.listener._on_release(mock_keyboard_key.cmd)
        assert self.listener.modifiers_pressed['cmd'] is False
        
        # Now 'a' should be captured
        self.listener._on_press(key_mock)
        self.callback_mock.assert_called_once_with('a')
    
    def test_special_keys_sequence(self, mock_keyboard_key):
        """Test sequence of special keys"""
        special_keys = [
            (mock_keyboard_key.space, ' '),
            (mock_keyboard_key.enter, '\n'),
            (mock_keyboard_key.tab, '\t')
        ]
        
        expected_calls = []
        for key, expected_char in special_keys:
            self.listener._on_press(key)
            expected_calls.append(call(expected_char))
        
        assert self.callback_mock.call_args_list == expected_calls
    
    def test_mixed_character_sequence(self, mock_keyboard_key):
        """Test mixed sequence of characters and special keys"""
        # Simulate typing "hello world\n"
        sequence = [
            ('h', 'h'), ('e', 'e'), ('l', 'l'), ('l', 'l'), ('o', 'o'),
            ('w', 'w'), ('o', 'o'), ('r', 'r'), ('l', 'l'), ('d', 'd'),
        ]
        
        expected_calls = []
        # First type regular characters
        for key, expected_char in sequence:
            key_mock = MagicMock()
            key_mock.char = key
            self.listener._on_press(key_mock)
            expected_calls.append(call(expected_char))
        
        # Then add space and enter
        self.listener._on_press(mock_keyboard_key.space)
        expected_calls.append(call(' '))
        
        self.listener._on_press(mock_keyboard_key.enter)
        expected_calls.append(call('\n'))
        
        assert self.callback_mock.call_args_list == expected_calls
    
    def test_listener_lifecycle(self, mock_keyboard_listener):
        """Test complete lifecycle of starting and stopping listener"""
        # Initial state
        assert self.listener.running is False
        assert self.listener.listener is None
        
        # Start listener
        self.listener.start()
        assert self.listener.running is True
        assert self.listener.listener is not None
        mock_keyboard_listener.start.assert_called_once()
        
        # Stop listener
        self.listener.stop()
        assert self.listener.running is False
        assert self.listener.listener is None
        mock_keyboard_listener.stop.assert_called_once()
    
    def test_multiple_start_stop_cycles(self, mock_keyboard_listener):
        """Test multiple start/stop cycles work correctly"""
        # First cycle
        self.listener.start()
        assert self.listener.running is True
        self.listener.stop()
        assert self.listener.running is False
        
        # Second cycle - should work normally
        mock_keyboard_listener.reset_mock()
        self.listener.start()
        assert self.listener.running is True
        mock_keyboard_listener.start.assert_called_once()
        
        self.listener.stop()
        assert self.listener.running is False