import pytest
from unittest.mock import patch, MagicMock
import sys
from io import StringIO

from src.saver.cli import interactive_search


class TestInteractiveSearch:
    """Test interactive search console functionality"""
    
    @pytest.fixture
    def mock_storage(self):
        """Mock storage handler for testing"""
        with patch('src.saver.cli.StorageHandler') as mock:
            storage_instance = MagicMock()
            mock.return_value = storage_instance
            
            # Mock search results
            storage_instance.fuzzy_search.return_value = [
                {
                    'id': 1,
                    'app_name': 'TestApp',
                    'content': 'Test content for searching',
                    'relevance_score': 0.95,
                    'snippet': 'Test content for searching',
                    'created_at': '2025-01-01T12:00:00'
                }
            ]
            
            # Mock statistics
            storage_instance.get_statistics.return_value = {
                'total_captures': 100,
                'unique_apps': 5,
                'total_characters': 5000,
                'total_words': 1000,
                'top_apps': [
                    {'app': 'TestApp', 'captures': 50},
                    {'app': 'VSCode', 'captures': 30}
                ]
            }
            
            # Mock recent captures
            storage_instance.get_recent_captures.return_value = [
                {
                    'app_name': 'TestApp',
                    'content': 'Recent test content',
                    'created_at': '2025-01-01T12:00:00'
                }
            ]
            
            yield storage_instance
    
    def test_interactive_search_basic_query(self, mock_storage, capsys):
        """Test basic search query in interactive mode"""
        user_inputs = ['test query', ':quit']
        
        with patch('builtins.input', side_effect=user_inputs):
            interactive_search()
        
        captured = capsys.readouterr()
        
        # Check that search was called
        mock_storage.fuzzy_search.assert_called_with('test query', limit=10, app_filter=None)
        
        # Check output contains search results
        assert "🔍 Searching for: 'test query'..." in captured.out
        assert "✅ Found 1 results:" in captured.out
        assert "TestApp" in captured.out
        assert "Test content for searching" in captured.out
    
    def test_interactive_search_empty_results(self, mock_storage, capsys):
        """Test search with no results"""
        user_inputs = ['nonexistent', ':quit']
        mock_storage.fuzzy_search.return_value = []
        
        with patch('builtins.input', side_effect=user_inputs):
            interactive_search()
        
        captured = capsys.readouterr()
        
        assert "❌ No results found for 'nonexistent'" in captured.out
        assert "💡 Try different search terms" in captured.out
    
    def test_interactive_search_limit_command(self, mock_storage, capsys):
        """Test setting result limit"""
        user_inputs = [':limit 5', 'test', ':quit']
        
        with patch('builtins.input', side_effect=user_inputs):
            interactive_search()
        
        captured = capsys.readouterr()
        
        # Check limit was set
        assert "✓ Result limit set to 5" in captured.out
        
        # Check search was called with new limit
        mock_storage.fuzzy_search.assert_called_with('test', limit=5, app_filter=None)
    
    def test_interactive_search_app_filter_command(self, mock_storage, capsys):
        """Test setting app filter"""
        user_inputs = [':app VSCode', 'test', ':quit']
        
        with patch('builtins.input', side_effect=user_inputs):
            interactive_search()
        
        captured = capsys.readouterr()
        
        # Check app filter was set
        assert "✓ Filtering by app: VSCode" in captured.out
        
        # Check search was called with app filter
        mock_storage.fuzzy_search.assert_called_with('test', limit=10, app_filter='VSCode')
    
    def test_interactive_search_clear_command(self, mock_storage, capsys):
        """Test clearing filters"""
        user_inputs = [':limit 20', ':app TestApp', ':clear', 'test', ':quit']
        
        with patch('builtins.input', side_effect=user_inputs):
            interactive_search()
        
        captured = capsys.readouterr()
        
        # Check filters were cleared
        assert "✓ Filters cleared" in captured.out
        
        # Check search was called with default values
        mock_storage.fuzzy_search.assert_called_with('test', limit=10, app_filter=None)
    
    def test_interactive_search_stats_command(self, mock_storage, capsys):
        """Test statistics command"""
        user_inputs = [':stats', ':quit']
        
        with patch('builtins.input', side_effect=user_inputs):
            interactive_search()
        
        captured = capsys.readouterr()
        
        # Check statistics were displayed
        assert "📊 Database Statistics:" in captured.out
        assert "Total captures: 100" in captured.out
        assert "Unique apps: 5" in captured.out
        assert "Total characters: 5,000" in captured.out
        assert "TestApp: 50 captures" in captured.out
    
    def test_interactive_search_recent_command(self, mock_storage, capsys):
        """Test recent captures command"""
        user_inputs = [':recent', ':quit']
        
        with patch('builtins.input', side_effect=user_inputs):
            interactive_search()
        
        captured = capsys.readouterr()
        
        # Check recent captures were displayed
        assert "📋 1 Most Recent Captures:" in captured.out
        assert "TestApp" in captured.out
        assert "Recent test content" in captured.out
        
        # Check method was called with default limit
        mock_storage.get_recent_captures.assert_called_with(5)
    
    def test_interactive_search_recent_with_limit(self, mock_storage, capsys):
        """Test recent captures command with custom limit"""
        user_inputs = [':recent 10', ':quit']
        
        with patch('builtins.input', side_effect=user_inputs):
            interactive_search()
        
        captured = capsys.readouterr()
        
        # Check method was called with custom limit
        mock_storage.get_recent_captures.assert_called_with(10)
    
    def test_interactive_search_help_command(self, mock_storage, capsys):
        """Test help command"""
        user_inputs = [':help', ':quit']
        
        with patch('builtins.input', side_effect=user_inputs):
            interactive_search()
        
        captured = capsys.readouterr()
        
        # Check help text is displayed
        assert "<search query>     - Search your captures" in captured.out
        assert ":limit <number>    - Set result limit" in captured.out
        assert ":app <name>        - Filter by app name" in captured.out
        assert ":quit              - Exit console" in captured.out
    
    def test_interactive_search_invalid_command(self, mock_storage, capsys):
        """Test invalid command handling"""
        user_inputs = [':invalid', ':quit']
        
        with patch('builtins.input', side_effect=user_inputs):
            interactive_search()
        
        captured = capsys.readouterr()
        
        assert "❌ Unknown command: invalid" in captured.out
    
    def test_interactive_search_invalid_limit(self, mock_storage, capsys):
        """Test invalid limit value"""
        user_inputs = [':limit abc', ':quit']
        
        with patch('builtins.input', side_effect=user_inputs):
            interactive_search()
        
        captured = capsys.readouterr()
        
        assert "❌ Invalid number format" in captured.out
    
    def test_interactive_search_keyboard_interrupt(self, mock_storage, capsys):
        """Test graceful handling of Ctrl+C"""
        with patch('builtins.input', side_effect=KeyboardInterrupt):
            interactive_search()
        
        captured = capsys.readouterr()
        
        assert "👋 Goodbye!" in captured.out
    
    def test_interactive_search_eof_error(self, mock_storage, capsys):
        """Test graceful handling of EOF (Ctrl+D)"""
        with patch('builtins.input', side_effect=EOFError):
            interactive_search()
        
        captured = capsys.readouterr()
        
        assert "👋 Goodbye!" in captured.out
    
    def test_interactive_search_empty_input(self, mock_storage, capsys):
        """Test handling of empty input"""
        user_inputs = ['', '   ', 'test', ':quit']
        
        with patch('builtins.input', side_effect=user_inputs):
            interactive_search()
        
        # Should not crash and should process 'test' query
        mock_storage.fuzzy_search.assert_called_once_with('test', limit=10, app_filter=None)
    
    def test_interactive_search_filter_display_in_prompt(self, mock_storage, capsys):
        """Test that filters are displayed in the prompt"""
        user_inputs = [':limit 5', ':app VSCode', 'test', ':quit']
        
        # Capture the input prompts by mocking input with a side effect that records prompts
        prompts = []
        def mock_input(prompt):
            prompts.append(prompt)
            return user_inputs.pop(0)
        
        with patch('builtins.input', side_effect=mock_input):
            interactive_search()
        
        # Check that prompt shows filters
        assert any('limit=5' in prompt and 'app=VSCode' in prompt for prompt in prompts)
    
    def test_interactive_search_multiple_results_formatting(self, mock_storage, capsys):
        """Test formatting of multiple search results"""
        user_inputs = ['test', ':quit']
        
        # Mock multiple results with different scores
        mock_storage.fuzzy_search.return_value = [
            {
                'id': 1,
                'app_name': 'VSCode',
                'content': 'High relevance test content',
                'relevance_score': 0.95,
                'snippet': 'High relevance test content',
                'created_at': '2025-01-01T12:00:00.123456'
            },
            {
                'id': 2,
                'app_name': 'Terminal',
                'content': 'Medium relevance content',
                'relevance_score': 0.65,
                'snippet': 'Medium relevance content',
                'created_at': '2025-01-01T11:30:00'
            },
            {
                'id': 3,
                'app_name': 'Notes',
                'content': 'Lower relevance match',
                'relevance_score': 0.35,
                'snippet': 'Lower relevance match',
                'created_at': '2025-01-01T10:00:00'
            }
        ]
        
        with patch('builtins.input', side_effect=user_inputs):
            interactive_search()
        
        captured = capsys.readouterr()
        
        # Check that all results are displayed
        assert "✅ Found 3 results:" in captured.out
        assert "🟢 [VSCode] Score: 0.950" in captured.out  # High score - green
        assert "🟡 [Terminal] Score: 0.650" in captured.out  # Medium score - yellow
        assert "🟠 [Notes] Score: 0.350" in captured.out  # Low score - orange
        
        # Check date/time formatting
        assert "📅 2025-01-01 ⏰ 12:00:00" in captured.out
        assert "📅 2025-01-01 ⏰ 11:30:00" in captured.out
    
    def test_interactive_search_exception_handling(self, mock_storage, capsys):
        """Test handling of unexpected exceptions"""
        user_inputs = ['test', ':quit']
        mock_storage.fuzzy_search.side_effect = Exception("Database error")
        
        with patch('builtins.input', side_effect=user_inputs):
            interactive_search()
        
        captured = capsys.readouterr()
        
        assert "❌ Error: Database error" in captured.out
        # Should continue running after error
        assert "👋 Goodbye!" in captured.out