import pytest
from datetime import datetime
from src.saver.storage.models import CaptureSession, AppStatistics, SystemStatistics


class TestCaptureSession:
    """Test CaptureSession dataclass"""
    
    def test_init_with_all_fields(self):
        """Test CaptureSession initialization with all fields"""
        start_time = datetime(2024, 1, 1, 12, 0, 0)
        end_time = datetime(2024, 1, 1, 12, 5, 0)
        created_at = datetime(2024, 1, 1, 12, 10, 0)
        
        session = CaptureSession(
            id=123,
            app_name="TestApp",
            content="Hello world",
            start_time=start_time,
            end_time=end_time,
            char_count=11,
            word_count=2,
            created_at=created_at
        )
        
        assert session.id == 123
        assert session.app_name == "TestApp"
        assert session.content == "Hello world"
        assert session.start_time == start_time
        assert session.end_time == end_time
        assert session.char_count == 11
        assert session.word_count == 2
        assert session.created_at == created_at
    
    def test_init_with_minimal_fields(self):
        """Test CaptureSession with minimal required fields"""
        session = CaptureSession(
            app_name="TestApp",
            content="Hello"
        )
        
        assert session.id is None
        assert session.app_name == "TestApp"
        assert session.content == "Hello"
        assert isinstance(session.start_time, datetime)
        assert isinstance(session.end_time, datetime)
        assert isinstance(session.created_at, datetime)
        assert session.char_count == 5  # Auto-calculated
        assert session.word_count == 1  # Auto-calculated
    
    def test_init_with_defaults(self):
        """Test CaptureSession default values are set"""
        session = CaptureSession()
        
        assert session.id is None
        assert session.app_name == ""
        assert session.content == ""
        assert isinstance(session.start_time, datetime)
        assert isinstance(session.end_time, datetime)
        assert isinstance(session.created_at, datetime)
        assert session.char_count == 0
        assert session.word_count == 0
    
    def test_char_count_calculation(self):
        """Test automatic character count calculation"""
        session = CaptureSession(content="Hello world!")
        assert session.char_count == 12
        
        session = CaptureSession(content="")
        assert session.char_count == 0
        
        session = CaptureSession(content="Test with emojis 🚀🎉")
        assert session.char_count == len("Test with emojis 🚀🎉")
    
    def test_word_count_calculation(self):
        """Test automatic word count calculation"""
        session = CaptureSession(content="Hello world")
        assert session.word_count == 2
        
        session = CaptureSession(content="One")
        assert session.word_count == 1
        
        session = CaptureSession(content="")
        assert session.word_count == 0
        
        session = CaptureSession(content="   ")  # Only whitespace
        assert session.word_count == 0
        
        session = CaptureSession(content="Multiple   spaces   between")
        assert session.word_count == 3
        
        session = CaptureSession(content="Line1\nLine2\nLine3")
        assert session.word_count == 3
    
    def test_explicit_counts_override_calculation(self):
        """Test that explicit counts override auto-calculation"""
        session = CaptureSession(
            content="Hello world",  # Would be 11 chars, 2 words
            char_count=100,
            word_count=50
        )
        
        assert session.char_count == 100
        assert session.word_count == 50
    
    def test_dataclass_equality(self):
        """Test dataclass equality comparison"""
        session1 = CaptureSession(
            app_name="TestApp",
            content="Hello",
            char_count=5,
            word_count=1
        )
        
        session2 = CaptureSession(
            app_name="TestApp", 
            content="Hello",
            char_count=5,
            word_count=1
        )
        
        # Times will be different, so they won't be equal
        assert session1.app_name == session2.app_name
        assert session1.content == session2.content


class TestAppStatistics:
    """Test AppStatistics dataclass"""
    
    def test_init_with_all_fields(self):
        """Test AppStatistics initialization"""
        last_capture = datetime(2024, 1, 1, 12, 0, 0)
        
        stats = AppStatistics(
            app_name="TestApp",
            capture_count=10,
            total_characters=500,
            total_words=100,
            last_capture=last_capture
        )
        
        assert stats.app_name == "TestApp"
        assert stats.capture_count == 10
        assert stats.total_characters == 500
        assert stats.total_words == 100
        assert stats.last_capture == last_capture
    
    def test_dataclass_behavior(self):
        """Test that AppStatistics behaves as a dataclass"""
        stats1 = AppStatistics(
            app_name="TestApp",
            capture_count=5,
            total_characters=250,
            total_words=50,
            last_capture=datetime(2024, 1, 1)
        )
        
        stats2 = AppStatistics(
            app_name="TestApp",
            capture_count=5,
            total_characters=250,
            total_words=50,
            last_capture=datetime(2024, 1, 1)
        )
        
        assert stats1 == stats2
        assert str(stats1)  # Should have string representation


class TestSystemStatistics:
    """Test SystemStatistics dataclass"""
    
    def test_init_with_defaults(self):
        """Test SystemStatistics default initialization"""
        stats = SystemStatistics()
        
        assert stats.total_captures == 0
        assert stats.unique_apps == 0
        assert stats.total_characters == 0
        assert stats.total_words == 0
        assert stats.top_apps == []
    
    def test_init_with_all_fields(self):
        """Test SystemStatistics with all fields"""
        app_stats = AppStatistics(
            app_name="TestApp",
            capture_count=5,
            total_characters=100,
            total_words=20,
            last_capture=datetime(2024, 1, 1)
        )
        
        stats = SystemStatistics(
            total_captures=10,
            unique_apps=3,
            total_characters=500,
            total_words=100,
            top_apps=[app_stats]
        )
        
        assert stats.total_captures == 10
        assert stats.unique_apps == 3
        assert stats.total_characters == 500
        assert stats.total_words == 100
        assert len(stats.top_apps) == 1
        assert stats.top_apps[0] == app_stats
    
    def test_post_init_behavior(self):
        """Test that __post_init__ sets default top_apps"""
        # Create without top_apps
        stats1 = SystemStatistics(total_captures=5)
        assert stats1.top_apps == []
        
        # Create with None top_apps
        stats2 = SystemStatistics(total_captures=5, top_apps=None)
        assert stats2.top_apps == []
        
        # Create with existing top_apps
        app_stats = AppStatistics("TestApp", 1, 10, 2, datetime.now())
        stats3 = SystemStatistics(total_captures=5, top_apps=[app_stats])
        assert len(stats3.top_apps) == 1