from .platform import (
    get_system_type, is_macos, is_windows, is_linux,
    get_active_window, get_active_window_macos, 
    get_active_window_windows, get_active_window_linux
)

__all__ = [
    "get_system_type", "is_macos", "is_windows", "is_linux",
    "get_active_window", "get_active_window_macos", 
    "get_active_window_windows", "get_active_window_linux"
]