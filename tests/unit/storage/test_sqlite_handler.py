import pytest
import sqlite3
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.saver.storage.sqlite_handler import StorageHandler


class TestStorageHandler:
    """Test StorageHandler class"""
    
    def test_init_creates_database_and_tables(self, tmp_path):
        """Test that initialization creates database file and required tables"""
        db_path = tmp_path / "test.db"
        handler = StorageHandler(str(db_path))
        
        assert db_path.exists()
        assert handler.db_path == db_path
        assert isinstance(handler.lock, type(threading.RLock()))
        
        # Check that tables were created
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check captures table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='captures'")
        assert cursor.fetchone() is not None
        
        # Check indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_app_name'")
        assert cursor.fetchone() is not None
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_created_at'")
        assert cursor.fetchone() is not None
        
        conn.close()
    
    def test_init_creates_parent_directories(self, tmp_path):
        """Test that initialization creates parent directories if they don't exist"""
        nested_path = tmp_path / "nested" / "dir" / "test.db"
        handler = StorageHandler(str(nested_path))
        
        assert nested_path.exists()
        assert nested_path.parent.exists()
    
    def test_save_capture_success(self, temp_db_path):
        """Test successful capture saving"""
        handler = StorageHandler(temp_db_path)
        
        buffer_info = {
            "app_name": "TestApp",
            "content": "Hello world",
            "start_time": datetime(2024, 1, 1, 12, 0, 0),
            "end_time": datetime(2024, 1, 1, 12, 5, 0),
            "char_count": 11,
            "word_count": 2
        }
        
        result = handler.save_capture(buffer_info)
        assert result is True
        
        # Verify data was saved
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM captures")
        row = cursor.fetchone()
        conn.close()
        
        assert row is not None
        assert row[1] == "TestApp"  # app_name
        assert row[2] == "Hello world"  # content
        assert row[5] == 11  # char_count
        assert row[6] == 2  # word_count
    
    def test_save_capture_with_datetime_conversion(self, temp_db_path):
        """Test that datetime objects are properly converted to ISO format"""
        handler = StorageHandler(temp_db_path)
        
        start_time = datetime(2024, 1, 1, 12, 0, 0)
        end_time = datetime(2024, 1, 1, 12, 5, 0)
        
        buffer_info = {
            "app_name": "TestApp",
            "content": "Test content",
            "start_time": start_time,
            "end_time": end_time,
            "char_count": 12,
            "word_count": 2
        }
        
        handler.save_capture(buffer_info)
        
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT start_time, end_time FROM captures")
        row = cursor.fetchone()
        conn.close()
        
        assert row[0] == start_time.isoformat()
        assert row[1] == end_time.isoformat()
    
    def test_save_capture_handles_exception(self, temp_db_path):
        """Test that save_capture handles exceptions gracefully"""
        handler = StorageHandler(temp_db_path)
        
        # Malformed buffer_info missing required keys
        buffer_info = {"incomplete": "data"}
        
        result = handler.save_capture(buffer_info)
        assert result is False
    
    def test_save_capture_database_error(self, temp_db_path):
        """Test save_capture handles database connection errors"""
        handler = StorageHandler(temp_db_path)
        
        # Create valid buffer info
        buffer_info = {
            "app_name": "TestApp",
            "content": "Test content",
            "start_time": datetime(2024, 1, 1, 12, 0, 0),
            "end_time": datetime(2024, 1, 1, 12, 5, 0),
            "char_count": 12,
            "word_count": 2
        }
        
        # Simulate database connection error by using invalid path
        handler.db_path = Path("/invalid/path/that/does/not/exist.db")
        
        result = handler.save_capture(buffer_info)
        assert result is False
    
    def test_save_multiple_captures_success(self, temp_db_path):
        """Test saving multiple captures"""
        handler = StorageHandler(temp_db_path)
        
        captures = {
            "App1": {
                "app_name": "App1",
                "content": "Content 1",
                "start_time": datetime(2024, 1, 1, 12, 0, 0),
                "end_time": datetime(2024, 1, 1, 12, 5, 0),
                "char_count": 9,
                "word_count": 2
            },
            "App2": {
                "app_name": "App2",
                "content": "Content 2",
                "start_time": datetime(2024, 1, 1, 13, 0, 0),
                "end_time": datetime(2024, 1, 1, 13, 5, 0),
                "char_count": 9,
                "word_count": 2
            }
        }
        
        saved_count = handler.save_multiple_captures(captures)
        assert saved_count == 2
        
        # Verify both captures were saved
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM captures")
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count == 2
    
    def test_save_multiple_captures_partial_failure(self, temp_db_path):
        """Test saving multiple captures with some failures"""
        handler = StorageHandler(temp_db_path)
        
        captures = {
            "ValidApp": {
                "app_name": "ValidApp",
                "content": "Valid content",
                "start_time": datetime(2024, 1, 1, 12, 0, 0),
                "end_time": datetime(2024, 1, 1, 12, 5, 0),
                "char_count": 13,
                "word_count": 2
            },
            "InvalidApp": {
                "incomplete": "data"  # Missing required fields
            }
        }
        
        saved_count = handler.save_multiple_captures(captures)
        assert saved_count == 1  # Only one should succeed
    
    def test_get_recent_captures_success(self, temp_db_path):
        """Test retrieving recent captures"""
        handler = StorageHandler(temp_db_path)
        
        # Add test data
        for i in range(3):
            buffer_info = {
                "app_name": f"TestApp{i}",
                "content": f"Content {i}",
                "start_time": datetime(2024, 1, 1, 12, i, 0),
                "end_time": datetime(2024, 1, 1, 12, i+1, 0),
                "char_count": 9 + i,
                "word_count": 2
            }
            handler.save_capture(buffer_info)
        
        results = handler.get_recent_captures(limit=2)
        
        assert len(results) == 2
        assert results[0]["app_name"] == "TestApp2"  # Most recent first
        assert results[1]["app_name"] == "TestApp1"
        assert "id" in results[0]
        assert "created_at" in results[0]
    
    def test_get_recent_captures_default_limit(self, temp_db_path):
        """Test get_recent_captures with default limit"""
        handler = StorageHandler(temp_db_path)
        
        # Add one capture
        buffer_info = {
            "app_name": "TestApp",
            "content": "Test content",
            "start_time": datetime(2024, 1, 1, 12, 0, 0),
            "end_time": datetime(2024, 1, 1, 12, 5, 0),
            "char_count": 12,
            "word_count": 2
        }
        handler.save_capture(buffer_info)
        
        results = handler.get_recent_captures()  # Default limit=50
        assert len(results) == 1
    
    def test_get_recent_captures_empty_database(self, temp_db_path):
        """Test get_recent_captures with empty database"""
        handler = StorageHandler(temp_db_path)
        
        results = handler.get_recent_captures()
        assert results == []
    
    def test_get_recent_captures_handles_exception(self, temp_db_path):
        """Test get_recent_captures handles database errors"""
        handler = StorageHandler(temp_db_path)
        
        # Simulate database error by using invalid path
        handler.db_path = Path("/invalid/path.db")
        
        results = handler.get_recent_captures()
        assert results == []
    
    def test_get_captures_by_app_success(self, temp_db_path):
        """Test retrieving captures by specific app"""
        handler = StorageHandler(temp_db_path)
        
        # Add captures for different apps
        apps = ["App1", "App2", "App1", "App3"]
        for i, app in enumerate(apps):
            buffer_info = {
                "app_name": app,
                "content": f"Content {i}",
                "start_time": datetime(2024, 1, 1, 12, i, 0),
                "end_time": datetime(2024, 1, 1, 12, i+1, 0),
                "char_count": 9 + i,
                "word_count": 2
            }
            handler.save_capture(buffer_info)
        
        results = handler.get_captures_by_app("App1")
        
        assert len(results) == 2
        assert all(r["app_name"] == "App1" for r in results)
        assert results[0]["content"] == "Content 2"  # Most recent first
        assert results[1]["content"] == "Content 0"
    
    def test_get_captures_by_app_with_limit(self, temp_db_path):
        """Test get_captures_by_app with custom limit"""
        handler = StorageHandler(temp_db_path)
        
        # Add multiple captures for same app
        for i in range(5):
            buffer_info = {
                "app_name": "TestApp",
                "content": f"Content {i}",
                "start_time": datetime(2024, 1, 1, 12, i, 0),
                "end_time": datetime(2024, 1, 1, 12, i+1, 0),
                "char_count": 9 + i,
                "word_count": 2
            }
            handler.save_capture(buffer_info)
        
        results = handler.get_captures_by_app("TestApp", limit=3)
        assert len(results) == 3
    
    def test_get_captures_by_app_nonexistent_app(self, temp_db_path):
        """Test get_captures_by_app for nonexistent app"""
        handler = StorageHandler(temp_db_path)
        
        results = handler.get_captures_by_app("NonExistentApp")
        assert results == []
    
    def test_get_captures_by_app_handles_exception(self, temp_db_path):
        """Test get_captures_by_app handles database errors"""
        handler = StorageHandler(temp_db_path)
        
        # Simulate database error
        handler.db_path = Path("/invalid/path.db")
        
        results = handler.get_captures_by_app("TestApp")
        assert results == []
    
    def test_get_statistics_success(self, temp_db_path):
        """Test getting statistics from populated database"""
        handler = StorageHandler(temp_db_path)
        
        # Add test data
        test_data = [
            ("App1", "Content 1", 10, 2),
            ("App1", "Content 2", 15, 3),
            ("App2", "Content 3", 8, 2),
            ("App3", "Content 4", 20, 4),
            ("App1", "Content 5", 12, 3),
        ]
        
        for app, content, chars, words in test_data:
            buffer_info = {
                "app_name": app,
                "content": content,
                "start_time": datetime(2024, 1, 1, 12, 0, 0),
                "end_time": datetime(2024, 1, 1, 12, 5, 0),
                "char_count": chars,
                "word_count": words
            }
            handler.save_capture(buffer_info)
        
        stats = handler.get_statistics()
        
        assert stats["total_captures"] == 5
        assert stats["unique_apps"] == 3
        assert stats["total_characters"] == 65  # 10+15+8+20+12
        assert stats["total_words"] == 14  # 2+3+2+4+3
        assert len(stats["top_apps"]) == 3
        assert stats["top_apps"][0]["app"] == "App1"  # Most captures (3)
        assert stats["top_apps"][0]["captures"] == 3
    
    def test_get_statistics_empty_database(self, temp_db_path):
        """Test getting statistics from empty database"""
        handler = StorageHandler(temp_db_path)
        
        stats = handler.get_statistics()
        
        assert stats["total_captures"] == 0
        assert stats["unique_apps"] == 0
        assert stats["total_characters"] == 0
        assert stats["total_words"] == 0
        assert stats["top_apps"] == []
    
    def test_get_statistics_handles_exception(self, temp_db_path):
        """Test get_statistics handles database errors"""
        handler = StorageHandler(temp_db_path)
        
        # Simulate database error
        handler.db_path = Path("/invalid/path.db")
        
        stats = handler.get_statistics()
        assert stats == {}
    
    def test_thread_safety_concurrent_saves(self, temp_db_path):
        """Test that concurrent saves are handled safely"""
        handler = StorageHandler(temp_db_path)
        num_threads = 5
        saves_per_thread = 10
        
        def save_worker(thread_id):
            for i in range(saves_per_thread):
                buffer_info = {
                    "app_name": f"App{thread_id}",
                    "content": f"Content {thread_id}-{i}",
                    "start_time": datetime(2024, 1, 1, 12, 0, 0),
                    "end_time": datetime(2024, 1, 1, 12, 5, 0),
                    "char_count": 10,
                    "word_count": 2
                }
                handler.save_capture(buffer_info)
        
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=save_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify all saves completed successfully
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM captures")
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count == num_threads * saves_per_thread
    
    def test_database_schema_correctness(self, temp_db_path):
        """Test that the database schema is created correctly"""
        handler = StorageHandler(temp_db_path)
        
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Check table schema
        cursor.execute("PRAGMA table_info(captures)")
        columns = cursor.fetchall()
        
        expected_columns = {
            "id": "INTEGER",
            "app_name": "TEXT",
            "content": "TEXT", 
            "start_time": "TEXT",
            "end_time": "TEXT",
            "char_count": "INTEGER",
            "word_count": "INTEGER",
            "created_at": "TEXT"
        }
        
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            assert col_name in expected_columns
            assert expected_columns[col_name] == col_type
        
        conn.close()
    
    def test_lock_usage(self, temp_db_path):
        """Test that StorageHandler properly uses locks"""
        handler = StorageHandler(temp_db_path)
        
        # This is more of a smoke test - verify lock exists and is correct type
        assert isinstance(handler.lock, type(threading.RLock()))
        
        # Test that operations work normally (if there were race conditions
        # they would show up in the concurrent test)
        buffer_info = {
            "app_name": "TestApp",
            "content": "Test content",
            "start_time": datetime(2024, 1, 1, 12, 0, 0),
            "end_time": datetime(2024, 1, 1, 12, 5, 0),
            "char_count": 12,
            "word_count": 2
        }
        
        result = handler.save_capture(buffer_info)
        assert result is True