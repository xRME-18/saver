import threading
from pynput import keyboard
from typing import Callable, Optional


class KeyListener:
    def __init__(self, on_key_callback: Callable[[str], None]):
        self.on_key_callback = on_key_callback
        self.listener: Optional[keyboard.Listener] = None
        self.running = False
        
        # Track modifier key states
        self.modifiers_pressed = {
            'cmd': False,
            'alt': False,
            'ctrl': False,
            'shift': False
        }
        
    def start(self):
        if self.running:
            return
            
        self.running = True
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()
        
    def stop(self):
        if not self.running or not self.listener:
            return
            
        self.running = False
        self.listener.stop()
        self.listener = None
        
    def _on_press(self, key):
        try:
            # Track modifier key states
            self._update_modifier_state(key, True)
            
            # Skip capturing if any non-shift modifier is pressed
            if self._should_skip_key():
                return
                
            # Capture regular text input
            if hasattr(key, 'char') and key.char is not None:
                self.on_key_callback(key.char)
            elif key == keyboard.Key.space:
                self.on_key_callback(' ')
            elif key == keyboard.Key.enter:
                self.on_key_callback('\n')
            elif key == keyboard.Key.tab:
                self.on_key_callback('\t')
        except Exception as e:
            pass
            
    def _on_release(self, key):
        try:
            # Track modifier key states
            self._update_modifier_state(key, False)
        except Exception as e:
            pass
            
    def _update_modifier_state(self, key, is_pressed: bool):
        """Update the state of modifier keys"""
        if key == keyboard.Key.cmd or key == keyboard.Key.cmd_l or key == keyboard.Key.cmd_r:
            self.modifiers_pressed['cmd'] = is_pressed
        elif key == keyboard.Key.alt or key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            self.modifiers_pressed['alt'] = is_pressed
        elif key == keyboard.Key.ctrl or key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.modifiers_pressed['ctrl'] = is_pressed
        elif key == keyboard.Key.shift or key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
            self.modifiers_pressed['shift'] = is_pressed
            
    def _should_skip_key(self) -> bool:
        """Check if we should skip capturing based on modifier keys"""
        # Skip if Command, Alt, or Control are pressed
        # Allow Shift alone (for capitalization) but skip Shift+Cmd/Alt/Ctrl combinations
        return (
            self.modifiers_pressed['cmd'] or
            self.modifiers_pressed['alt'] or
            self.modifiers_pressed['ctrl']
        )