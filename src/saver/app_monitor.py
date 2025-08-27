import platform
import threading
import time
from typing import Callable, Optional


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
        system = platform.system()
        
        if system == "Darwin":
            return self._get_active_app_macos()
        elif system == "Windows":
            return self._get_active_app_windows()
        elif system == "Linux":
            return self._get_active_app_linux()
        else:
            return None
            
    def _get_active_app_macos(self) -> Optional[str]:
        # Try multiple methods for macOS app detection
        
        # Use Quartz method for more accurate active window detection
        try:
            from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
            window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
            for window in window_list:
                if window.get('kCGWindowLayer', 0) == 0:  # Normal window layer
                    owner_name = window.get('kCGWindowOwnerName', '')
                    if owner_name:
                        return owner_name
        except Exception as e:
            # Fallback to NSWorkspace if Quartz fails
            try:
                from AppKit import NSWorkspace
                workspace = NSWorkspace.sharedWorkspace()
                active_app = workspace.frontmostApplication()
                return active_app.localizedName() if active_app else None
            except Exception:
                return None
        
        return None
            
    def _get_active_app_windows(self) -> Optional[str]:
        try:
            import win32gui
            import win32process
            import psutil
            
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process = psutil.Process(pid)
                return process.name()
        except Exception:
            return None
            
    def _get_active_app_linux(self) -> Optional[str]:
        try:
            import subprocess
            result = subprocess.run(
                ["xdotool", "getwindowfocus", "getwindowname"], 
                capture_output=True, 
                text=True,
                timeout=1
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None
            
    def get_current_app(self) -> str:
        return self.current_app