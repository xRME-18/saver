import threading
import time
from typing import Callable, Optional

from ..utils.platform import get_active_window


class AppMonitor:
    def __init__(self, on_app_change_callback: Callable[[str], None]):
        self.on_app_change_callback = on_app_change_callback
        self.current_app = ""
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.poll_interval = 1.0
        
    def start(self):
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
            
    def _monitor_loop(self):
        while self.running:
            try:
                app_name = self._get_active_app()
                # Debug: print all detected apps (uncomment to see all apps)
                # print(f"DEBUG: Current app detected: {app_name}")
                
                if app_name and app_name != self.current_app:
                    old_app = self.current_app
                    self.current_app = app_name
                    self.on_app_change_callback(app_name)
                    
            except Exception as e:
                print(f"DEBUG: Error in app monitor: {e}")
                
            time.sleep(self.poll_interval)
            
    def _get_active_app(self) -> Optional[str]:
        return get_active_window()
            
    def get_current_app(self) -> str:
        return self.current_app