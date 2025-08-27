import threading
from typing import Dict, Optional
from datetime import datetime


class BufferManager:
    def __init__(self):
        self.buffers: Dict[str, str] = {}
        self.buffer_start_times: Dict[str, datetime] = {}
        self.lock = threading.RLock()
        
    def add_text(self, app_name: str, text: str):
        with self.lock:
            if not app_name:
                return
                
            if app_name not in self.buffers:
                self.buffers[app_name] = ""
                self.buffer_start_times[app_name] = datetime.now()
                
            self.buffers[app_name] += text
            
    def get_buffer(self, app_name: str) -> Optional[str]:
        with self.lock:
            return self.buffers.get(app_name)
            
    def get_buffer_info(self, app_name: str) -> Optional[Dict]:
        with self.lock:
            if app_name not in self.buffers:
                return None
                
            content = self.buffers[app_name]
            start_time = self.buffer_start_times.get(app_name, datetime.now())
            
            return {
                "app_name": app_name,
                "content": content,
                "start_time": start_time,
                "end_time": datetime.now(),
                "char_count": len(content),
                "word_count": len(content.split()) if content.strip() else 0
            }
            
    def flush_buffer(self, app_name: str) -> Optional[Dict]:
        with self.lock:
            buffer_info = self.get_buffer_info(app_name)
            
            if buffer_info and buffer_info["content"].strip():
                self.buffers[app_name] = ""
                self.buffer_start_times[app_name] = datetime.now()
                return buffer_info
                
            return None
            
    def flush_all_buffers(self) -> Dict[str, Dict]:
        with self.lock:
            result = {}
            apps_to_flush = list(self.buffers.keys())
            
            for app_name in apps_to_flush:
                buffer_info = self.flush_buffer(app_name)
                if buffer_info:
                    result[app_name] = buffer_info
                    
            return result
            
    def clear_buffer(self, app_name: str):
        with self.lock:
            if app_name in self.buffers:
                del self.buffers[app_name]
            if app_name in self.buffer_start_times:
                del self.buffer_start_times[app_name]
                
    def get_all_apps(self) -> list:
        with self.lock:
            return list(self.buffers.keys())
            
    def has_content(self, app_name: str, min_chars: int = 5) -> bool:
        with self.lock:
            content = self.buffers.get(app_name, "")
            return len(content.strip()) >= min_chars