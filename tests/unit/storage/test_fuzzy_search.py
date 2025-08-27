import pytest
from datetime import datetime
from src.saver.storage.sqlite_handler import StorageHandler


class TestFuzzySearch:
    """Test fuzzy search functionality"""
    
    @pytest.fixture
    def temp_storage(self, temp_db_path):
        """Create temporary storage handler for testing"""
        handler = StorageHandler(temp_db_path)
        return handler
    
    @pytest.fixture
    def sample_captures(self, temp_storage):
        """Insert sample data for testing"""
        captures = [
            {
                "app_name": "VSCode",
                "content": "def calculate_fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
                "start_time": datetime.now(),
                "end_time": datetime.now(),
                "char_count": 80,
                "word_count": 12
            },
            {
                "app_name": "Terminal",
                "content": "python manage.py migrate --fake-initial",
                "start_time": datetime.now(),
                "end_time": datetime.now(),
                "char_count": 40,
                "word_count": 4
            },
            {
                "app_name": "Slack",
                "content": "Hey team, the authentication bug is fixed. The JWT token validation was failing",
                "start_time": datetime.now(),
                "end_time": datetime.now(),
                "char_count": 85,
                "word_count": 14
            },
            {
                "app_name": "Chrome",
                "content": "Stack Overflow: How to implement rate limiting in Flask applications using Redis",
                "start_time": datetime.now(),
                "end_time": datetime.now(),
                "char_count": 80,
                "word_count": 12
            },
            {
                "app_name": "Notes",
                "content": "Meeting notes: Discussed database migration strategy. Need to backup prod data first.",
                "start_time": datetime.now(),
                "end_time": datetime.now(),
                "char_count": 90,
                "word_count": 13
            },
            {
                "app_name": "Terminal",
                "content": "git commit -m 'Fix authentication middleware bug in user login'",
                "start_time": datetime.now(),
                "end_time": datetime.now(),
                "char_count": 60,
                "word_count": 10
            }
        ]
        
        for capture in captures:
            temp_storage.save_capture(capture)
        
        return captures
    
    def test_exact_match_search(self, temp_storage, sample_captures):
        """Test exact word matching"""
        results = temp_storage.fuzzy_search("fibonacci")
        
        assert len(results) == 1
        assert "fibonacci" in results[0]["content"].lower()
        assert results[0]["app_name"] == "VSCode"
    
    def test_partial_word_search(self, temp_storage, sample_captures):
        """Test searching with partial words"""
        results = temp_storage.fuzzy_search("auth")
        
        assert len(results) == 2  # Should find "authentication" mentions
        app_names = [r["app_name"] for r in results]
        assert "Slack" in app_names
        assert "Terminal" in app_names
    
    def test_case_insensitive_search(self, temp_storage, sample_captures):
        """Test case insensitive search"""
        results_lower = temp_storage.fuzzy_search("python")
        results_upper = temp_storage.fuzzy_search("PYTHON")
        results_mixed = temp_storage.fuzzy_search("Python")
        
        assert len(results_lower) == len(results_upper) == len(results_mixed) == 1
        assert all("python" in r["content"].lower() for r in results_lower)
    
    def test_multi_word_search(self, temp_storage, sample_captures):
        """Test searching for multiple words"""
        results = temp_storage.fuzzy_search("database migration")
        
        assert len(results) == 1
        assert "database" in results[0]["content"].lower()
        assert "migration" in results[0]["content"].lower()
        assert results[0]["app_name"] == "Notes"
    
    def test_fuzzy_typo_tolerance(self, temp_storage, sample_captures):
        """Test tolerance for typos/misspellings"""
        # "authenitcation" instead of "authentication" - try lower min_score
        results = temp_storage.fuzzy_search("authenitcation", min_score=0.1)
        
        # Should still find authentication-related content
        assert len(results) >= 1
        content_lower = " ".join([r["content"].lower() for r in results])
        assert "authentication" in content_lower or "auth" in content_lower
    
    def test_search_with_special_characters(self, temp_storage, sample_captures):
        """Test search with code symbols and special characters"""
        results = temp_storage.fuzzy_search("--fake-initial")
        
        assert len(results) == 1
        assert "--fake-initial" in results[0]["content"]
        assert results[0]["app_name"] == "Terminal"
    
    def test_empty_search_query(self, temp_storage, sample_captures):
        """Test behavior with empty search query"""
        results = temp_storage.fuzzy_search("")
        
        assert len(results) == 0
    
    def test_no_results_found(self, temp_storage, sample_captures):
        """Test when no matches are found"""
        results = temp_storage.fuzzy_search("nonexistent_unique_term_xyz")
        
        assert len(results) == 0
    
    def test_search_result_ranking(self, temp_storage, sample_captures):
        """Test that results are ranked by relevance"""
        # Add a capture with multiple instances of search term
        temp_storage.save_capture({
            "app_name": "VSCode", 
            "content": "authentication authentication authentication system design",
            "start_time": datetime.now(),
            "end_time": datetime.now(),
            "char_count": 55,
            "word_count": 5
        })
        
        results = temp_storage.fuzzy_search("authentication")
        
        assert len(results) >= 2
        # The capture with multiple instances should rank higher
        assert results[0]["content"].count("authentication") >= results[1]["content"].count("authentication")
    
    def test_search_with_limit(self, temp_storage, sample_captures):
        """Test search with result limit"""
        results_no_limit = temp_storage.fuzzy_search("a")  # Should match multiple
        results_with_limit = temp_storage.fuzzy_search("a", limit=2)
        
        assert len(results_with_limit) <= 2
        assert len(results_with_limit) <= len(results_no_limit)
    
    def test_search_by_app_filter(self, temp_storage, sample_captures):
        """Test filtering search results by app"""
        all_results = temp_storage.fuzzy_search("git")
        terminal_results = temp_storage.fuzzy_search("git", app_filter="Terminal")
        
        assert len(terminal_results) <= len(all_results)
        assert all(r["app_name"] == "Terminal" for r in terminal_results)
    
    def test_search_recent_captures_priority(self, temp_storage, sample_captures):
        """Test that recent captures get higher priority"""
        # Add an older capture
        old_capture = {
            "app_name": "VSCode",
            "content": "old fibonacci implementation with bugs",
            "start_time": datetime(2020, 1, 1),
            "end_time": datetime(2020, 1, 1),
            "char_count": 40,
            "word_count": 6
        }
        temp_storage.save_capture(old_capture)
        
        results = temp_storage.fuzzy_search("fibonacci")
        
        assert len(results) == 2
        # More recent capture should come first (assuming equal relevance)
        assert results[0]["created_at"] > results[1]["created_at"]
    
    def test_search_performance_large_dataset(self, temp_storage):
        """Test search performance with larger dataset"""
        # Insert many captures
        import time
        
        for i in range(100):
            temp_storage.save_capture({
                "app_name": f"App{i % 10}",
                "content": f"This is capture number {i} with some random content about testing performance",
                "start_time": datetime.now(),
                "end_time": datetime.now(),
                "char_count": 70,
                "word_count": 12
            })
        
        start_time = time.time()
        results = temp_storage.fuzzy_search("testing")
        end_time = time.time()
        
        assert len(results) == 50  # Default limit is 50
        assert (end_time - start_time) < 1.0  # Should complete within 1 second
    
    def test_search_content_snippet_extraction(self, temp_storage, sample_captures):
        """Test that search results include relevant content snippets"""
        results = temp_storage.fuzzy_search("authentication bug")
        
        assert len(results) >= 1
        # Should include snippet with highlighted/relevant portion
        result = results[0]
        assert "snippet" in result  # Should contain extracted snippet
        assert len(result["snippet"]) <= 200  # Reasonable snippet length
        assert "authentication" in result["snippet"].lower()
    
    def test_search_metadata_preservation(self, temp_storage, sample_captures):
        """Test that all metadata is preserved in search results"""
        results = temp_storage.fuzzy_search("fibonacci")
        
        assert len(results) == 1
        result = results[0]
        
        # Should contain all original fields
        required_fields = ["id", "app_name", "content", "start_time", "end_time", 
                          "char_count", "word_count", "created_at"]
        for field in required_fields:
            assert field in result
        
        # Should contain search-specific fields
        search_fields = ["relevance_score", "snippet"]
        for field in search_fields:
            assert field in result