from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CaptureSession:
    """Represents a text capture session"""
    id: Optional[int] = None
    app_name: str = ""
    content: str = ""
    start_time: datetime = None
    end_time: datetime = None
    char_count: int = 0
    word_count: int = 0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()
        if self.end_time is None:
            self.end_time = datetime.now()
        if self.created_at is None:
            self.created_at = datetime.now()
        if not self.char_count:
            self.char_count = len(self.content)
        if not self.word_count:
            self.word_count = len(self.content.split()) if self.content.strip() else 0


@dataclass
class AppStatistics:
    """Statistics for a specific app"""
    app_name: str
    capture_count: int
    total_characters: int
    total_words: int
    last_capture: datetime


@dataclass
class SystemStatistics:
    """Overall system statistics"""
    total_captures: int = 0
    unique_apps: int = 0
    total_characters: int = 0
    total_words: int = 0
    top_apps: list[AppStatistics] = None
    
    def __post_init__(self):
        if self.top_apps is None:
            self.top_apps = []