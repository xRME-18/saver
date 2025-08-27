import platform
from typing import Optional


def get_system_type() -> str:
    """Get the current operating system type"""
    return platform.system()


def is_macos() -> bool:
    """Check if running on macOS"""
    return platform.system() == "Darwin"


def is_windows() -> bool:
    """Check if running on Windows"""
    return platform.system() == "Windows"


def is_linux() -> bool:
    """Check if running on Linux"""
    return platform.system() == "Linux"


def get_active_window_macos() -> Optional[str]:
    """Get active window on macOS using Quartz API"""
    try:
        from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
        window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
        for window in window_list:
            if window.get('kCGWindowLayer', 0) == 0:  # Normal window layer
                owner_name = window.get('kCGWindowOwnerName', '')
                if owner_name:
                    return owner_name
    except Exception:
        # Fallback to NSWorkspace
        try:
            from AppKit import NSWorkspace
            workspace = NSWorkspace.sharedWorkspace()
            active_app = workspace.frontmostApplication()
            return active_app.localizedName() if active_app else None
        except Exception:
            return None
    return None


def get_active_window_windows() -> Optional[str]:
    """Get active window on Windows"""
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


def get_active_window_linux() -> Optional[str]:
    """Get active window on Linux"""
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


def get_active_window() -> Optional[str]:
    """Get active window for current platform"""
    system = get_system_type()
    
    if system == "Darwin":
        return get_active_window_macos()
    elif system == "Windows":
        return get_active_window_windows()
    elif system == "Linux":
        return get_active_window_linux()
    else:
        return None