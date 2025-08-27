import pytest
import threading
import time
from datetime import datetime
from unittest.mock import patch

from src.saver.core.buffer_manager import BufferManager


class TestBufferManager:
    """Test BufferManager class"""
    
    def test_init_creates_empty_buffers(self):
        """Test that BufferManager initializes with empty buffers"""
        manager = BufferManager()
        
        assert manager.buffers == {}
        assert manager.buffer_start_times == {}
        assert isinstance(manager.lock, type(threading.RLock()))
    
    def test_add_text_new_app(self, mock_datetime):
        """Test adding text for a new app creates buffer"""
        manager = BufferManager()
        
        manager.add_text("TestApp", "Hello")
        
        assert "TestApp" in manager.buffers
        assert manager.buffers["TestApp"] == "Hello"
        assert "TestApp" in manager.buffer_start_times
        assert manager.buffer_start_times["TestApp"] == mock_datetime.now.return_value
    
    def test_add_text_existing_app(self, mock_datetime):
        """Test adding text to existing app appends to buffer"""
        manager = BufferManager()
        
        manager.add_text("TestApp", "Hello")
        manager.add_text("TestApp", " world")
        
        assert manager.buffers["TestApp"] == "Hello world"
        # Start time should remain the same
        mock_datetime.now.assert_called_once()
    
    def test_add_text_empty_app_name(self):
        """Test adding text with empty app name is ignored"""
        manager = BufferManager()
        
        manager.add_text("", "Hello")
        manager.add_text(None, "Hello")
        
        assert manager.buffers == {}
        assert manager.buffer_start_times == {}
    
    def test_get_buffer_existing_app(self):
        """Test getting buffer for existing app"""
        manager = BufferManager()
        manager.add_text("TestApp", "Hello world")
        
        result = manager.get_buffer("TestApp")
        assert result == "Hello world"
    
    def test_get_buffer_nonexistent_app(self):
        """Test getting buffer for nonexistent app returns None"""
        manager = BufferManager()
        
        result = manager.get_buffer("NonExistentApp")
        assert result is None
    
    def test_get_buffer_info_with_content(self, mock_datetime):
        """Test getting buffer info for app with content"""
        manager = BufferManager()
        start_time = mock_datetime.now.return_value
        
        manager.add_text("TestApp", "Hello world test")
        
        with patch('src.saver.core.buffer_manager.datetime') as mock_dt_now:
            end_time = datetime(2024, 1, 1, 12, 10, 0)
            mock_dt_now.now.return_value = end_time
            
            result = manager.get_buffer_info("TestApp")
        
        assert result is not None
        assert result["app_name"] == "TestApp"
        assert result["content"] == "Hello world test"
        assert result["start_time"] == start_time
        assert result["end_time"] == end_time
        assert result["char_count"] == 16
        assert result["word_count"] == 3
    
    def test_get_buffer_info_nonexistent_app(self):
        """Test getting buffer info for nonexistent app returns None"""
        manager = BufferManager()
        
        result = manager.get_buffer_info("NonExistentApp")
        assert result is None
    
    def test_flush_buffer_with_content(self, mock_datetime):
        """Test flushing buffer with content returns info and clears buffer"""
        manager = BufferManager()
        manager.add_text("TestApp", "Hello world")
        
        result = manager.flush_buffer("TestApp")
        
        assert result is not None
        assert result["app_name"] == "TestApp"
        assert result["content"] == "Hello world"
        assert result["char_count"] == 11
        assert result["word_count"] == 2
        
        # Buffer should be cleared but app should still exist
        assert manager.buffers["TestApp"] == ""
        assert "TestApp" in manager.buffer_start_times
    
    def test_flush_buffer_empty_content(self):
        """Test flushing buffer with empty content returns None"""
        manager = BufferManager()
        manager.add_text("TestApp", "")
        
        result = manager.flush_buffer("TestApp")
        assert result is None
        
        # Test with whitespace only
        manager.add_text("TestApp2", "   ")
        result = manager.flush_buffer("TestApp2")
        assert result is None
    
    def test_flush_buffer_nonexistent_app(self):
        """Test flushing nonexistent app returns None"""
        manager = BufferManager()
        
        result = manager.flush_buffer("NonExistentApp")
        assert result is None
    
    def test_flush_all_buffers(self, mock_datetime):
        """Test flushing all buffers returns dict with all app data"""
        manager = BufferManager()
        
        manager.add_text("App1", "Hello from app1")
        manager.add_text("App2", "Hello from app2")
        manager.add_text("App3", "")  # This should be excluded
        
        results = manager.flush_all_buffers()
        
        assert len(results) == 2
        assert "App1" in results
        assert "App2" in results
        assert "App3" not in results
        
        assert results["App1"]["content"] == "Hello from app1"
        assert results["App2"]["content"] == "Hello from app2"
        
        # Buffers should be cleared
        assert manager.buffers["App1"] == ""
        assert manager.buffers["App2"] == ""
    
    def test_flush_all_buffers_empty(self):
        """Test flushing all buffers when empty returns empty dict"""
        manager = BufferManager()
        
        results = manager.flush_all_buffers()
        assert results == {}
    
    def test_clear_buffer(self):
        """Test clearing buffer removes app completely"""
        manager = BufferManager()
        manager.add_text("TestApp", "Hello world")
        
        assert "TestApp" in manager.buffers
        assert "TestApp" in manager.buffer_start_times
        
        manager.clear_buffer("TestApp")
        
        assert "TestApp" not in manager.buffers
        assert "TestApp" not in manager.buffer_start_times
    
    def test_clear_buffer_nonexistent_app(self):
        """Test clearing nonexistent buffer doesn't raise error"""
        manager = BufferManager()
        
        # Should not raise an exception
        manager.clear_buffer("NonExistentApp")
    
    def test_get_all_apps(self):
        """Test getting list of all apps with buffers"""
        manager = BufferManager()
        
        manager.add_text("App1", "Hello")
        manager.add_text("App2", "World")
        
        apps = manager.get_all_apps()
        
        assert set(apps) == {"App1", "App2"}
    
    def test_get_all_apps_empty(self):
        """Test getting all apps when no buffers exist"""
        manager = BufferManager()
        
        apps = manager.get_all_apps()
        assert apps == []
    
    def test_has_content_with_threshold(self):
        """Test has_content with minimum character threshold"""
        manager = BufferManager()
        
        manager.add_text("App1", "Hi")  # 2 chars
        manager.add_text("App2", "Hello world")  # 11 chars
        manager.add_text("App3", "   ")  # Whitespace only
        
        assert not manager.has_content("App1", min_chars=5)
        assert manager.has_content("App2", min_chars=5)
        assert not manager.has_content("App3", min_chars=1)
        assert not manager.has_content("NonExistent", min_chars=1)
    
    def test_has_content_default_threshold(self):
        """Test has_content with default threshold of 5 characters"""
        manager = BufferManager()
        
        manager.add_text("ShortApp", "Hi")  # 2 chars
        manager.add_text("LongApp", "Hello world")  # 11 chars
        
        assert not manager.has_content("ShortApp")  # Default min_chars=5
        assert manager.has_content("LongApp")
    
    def test_thread_safety_concurrent_adds(self):
        """Test that concurrent adds to buffers are thread-safe"""
        manager = BufferManager()
        num_threads = 10
        adds_per_thread = 100
        
        def add_text_worker(app_name, thread_id):
            for i in range(adds_per_thread):
                manager.add_text(app_name, f"t{thread_id}i{i} ")
        
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=add_text_worker, args=("TestApp", i))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Check that all text was added
        buffer_content = manager.get_buffer("TestApp")
        
        # Check that we got the expected number of 't' characters (one per add)
        assert buffer_content.count("t") == num_threads * adds_per_thread
        
        # Check that the length is reasonable (some adds might be shorter/longer)
        min_expected_length = num_threads * adds_per_thread * 4  # Minimum realistic length
        max_expected_length = num_threads * adds_per_thread * 8  # Maximum realistic length
        assert min_expected_length <= len(buffer_content) <= max_expected_length
    
    def test_word_count_edge_cases(self):
        """Test word counting with various edge cases"""
        manager = BufferManager()
        
        # Multiple spaces
        manager.add_text("App1", "word1    word2")
        info = manager.get_buffer_info("App1")
        assert info["word_count"] == 2
        
        # Tabs and newlines
        manager.clear_buffer("App1")
        manager.add_text("App1", "word1\tword2\nword3")
        info = manager.get_buffer_info("App1")
        assert info["word_count"] == 3
        
        # Special characters
        manager.clear_buffer("App1")
        manager.add_text("App1", "hello@world.com test123")
        info = manager.get_buffer_info("App1")
        assert info["word_count"] == 2
    
    def test_buffer_manager_lock_usage(self):
        """Test that buffer manager properly uses locks"""
        manager = BufferManager()
        
        # This is more of a smoke test - if there are race conditions
        # they would show up in the concurrent test above
        assert isinstance(manager.lock, type(threading.RLock()))
        
        # Test that operations work normally
        manager.add_text("TestApp", "Hello")
        assert manager.get_buffer("TestApp") == "Hello"