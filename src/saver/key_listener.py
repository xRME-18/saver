import threading
from pynput import keyboard
from typing import Callable, Optional


class KeyListener:
    def __init__(self, on_key_callback: Callable[[str], None]):
        self.on_key_callback = on_key_callback
        self.listener: Optional[keyboard.Listener] = None
        self.running = False
        
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
        pass