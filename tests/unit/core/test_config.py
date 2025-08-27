import pytest
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open

from src.saver.core.config import Config


class TestConfig:
    """Test Config class"""
    
    def test_load_default_config_when_file_missing(self):
        """Test loading default config when file doesn't exist"""
        with patch('pathlib.Path.exists', return_value=False):
            config = Config("nonexistent.yaml")
            
            # Check that default values are loaded
            assert config.config["capture"]["save_interval_seconds"] == 300
            assert config.config["capture"]["min_chars_threshold"] == 10
            assert config.config["capture"]["enabled"] is True
            assert config.config["apps"]["mode"] == "include"
            assert "1Password" in config.config["apps"]["exclude_list"]
    
    def test_load_custom_config_file(self, temp_config_file):
        """Test loading custom config file"""
        config = Config(str(temp_config_file))
        
        assert config.config["capture"]["save_interval_seconds"] == 5
        assert config.config["capture"]["min_chars_threshold"] == 2
        assert config.config["apps"]["mode"] == "exclude"
        assert "TestExcludedApp" in config.config["apps"]["exclude_list"]
    
    def test_merge_with_defaults(self, tmp_path):
        """Test that custom config merges with defaults"""
        # Create partial config
        partial_config = {
            "capture": {
                "save_interval_seconds": 600
                # Missing other capture settings
            }
            # Missing apps section entirely
        }
        
        config_file = tmp_path / "partial.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(partial_config, f)
            
        config = Config(str(config_file))
        
        # Custom value should be used
        assert config.config["capture"]["save_interval_seconds"] == 600
        
        # Default values should be preserved
        assert config.config["capture"]["min_chars_threshold"] == 10
        assert config.config["capture"]["enabled"] is True
        assert config.config["apps"]["mode"] == "include"
        assert "1Password" in config.config["apps"]["exclude_list"]
    
    def test_malformed_yaml_uses_defaults(self, tmp_path):
        """Test that malformed YAML falls back to defaults"""
        malformed_file = tmp_path / "malformed.yaml"
        with open(malformed_file, 'w') as f:
            f.write("invalid: yaml: content: [unclosed")
            
        config = Config(str(malformed_file))
        
        # Should fall back to defaults
        assert config.config["capture"]["save_interval_seconds"] == 300
        assert config.config["apps"]["mode"] == "include"
    
    def test_should_capture_app_include_mode(self):
        """Test app filtering in include mode"""
        config_data = {
            "apps": {
                "mode": "include",
                "include_list": ["AllowedApp1", "AllowedApp2"],
                "exclude_list": []
            }
        }
        
        with patch.object(Config, '_load_config', return_value=config_data):
            config = Config()
            
            assert config.should_capture_app("AllowedApp1") is True
            assert config.should_capture_app("AllowedApp2") is True
            assert config.should_capture_app("NotInList") is False
            assert config.should_capture_app("") is False
            assert config.should_capture_app(None) is False
    
    def test_should_capture_app_exclude_mode(self):
        """Test app filtering in exclude mode"""
        config_data = {
            "apps": {
                "mode": "exclude",
                "include_list": [],
                "exclude_list": ["BlockedApp1", "BlockedApp2"]
            }
        }
        
        with patch.object(Config, '_load_config', return_value=config_data):
            config = Config()
            
            assert config.should_capture_app("BlockedApp1") is False
            assert config.should_capture_app("BlockedApp2") is False
            assert config.should_capture_app("AllowedApp") is True
            assert config.should_capture_app("") is False
            assert config.should_capture_app(None) is False
    
    def test_should_capture_app_empty_name(self):
        """Test that empty app names are never captured"""
        config = Config()
        
        assert config.should_capture_app("") is False
        assert config.should_capture_app(None) is False
    
    def test_get_save_interval(self):
        """Test getting save interval"""
        config_data = {
            "capture": {"save_interval_seconds": 120}
        }
        
        with patch.object(Config, '_load_config', return_value=config_data):
            config = Config()
            assert config.get_save_interval() == 120
    
    def test_get_min_chars_threshold(self):
        """Test getting minimum characters threshold"""
        config_data = {
            "capture": {"min_chars_threshold": 5}
        }
        
        with patch.object(Config, '_load_config', return_value=config_data):
            config = Config()
            assert config.get_min_chars_threshold() == 5
    
    def test_is_capture_enabled(self):
        """Test checking if capture is enabled"""
        # Test enabled
        config_data = {"capture": {"enabled": True}}
        with patch.object(Config, '_load_config', return_value=config_data):
            config = Config()
            assert config.is_capture_enabled() is True
            
        # Test disabled
        config_data = {"capture": {"enabled": False}}
        with patch.object(Config, '_load_config', return_value=config_data):
            config = Config()
            assert config.is_capture_enabled() is False
    
    def test_get_database_path(self):
        """Test getting database path"""
        config_data = {
            "storage": {"database_path": "custom/path/db.sqlite"}
        }
        
        with patch.object(Config, '_load_config', return_value=config_data):
            config = Config()
            assert config.get_database_path() == "custom/path/db.sqlite"
    
    def test_get_cleanup_days(self):
        """Test getting cleanup days"""
        config_data = {
            "storage": {"auto_cleanup_days": 60}
        }
        
        with patch.object(Config, '_load_config', return_value=config_data):
            config = Config()
            assert config.get_cleanup_days() == 60
    
    def test_save_config(self, tmp_path):
        """Test saving config to file"""
        config_file = tmp_path / "test_save.yaml"
        config = Config()
        config.config_path = config_file
        
        # Modify some config
        config.config["capture"]["save_interval_seconds"] = 999
        
        config.save_config()
        
        # Verify file was saved
        assert config_file.exists()
        
        # Verify content
        with open(config_file, 'r') as f:
            saved_config = yaml.safe_load(f)
            assert saved_config["capture"]["save_interval_seconds"] == 999
    
    def test_save_config_creates_directory(self, tmp_path):
        """Test that save_config creates parent directories"""
        nested_path = tmp_path / "nested" / "dir" / "config.yaml"
        config = Config()
        config.config_path = nested_path
        
        config.save_config()
        
        assert nested_path.exists()
        assert nested_path.parent.exists()
    
    def test_save_config_handles_write_error(self, tmp_path):
        """Test that save_config handles write errors gracefully"""
        config = Config()
        config.config_path = Path("/invalid/path/that/cannot/be/written")
        
        # Should not raise an exception
        config.save_config()
    
    def test_deep_merge_functionality(self):
        """Test that _merge_with_defaults performs deep merge"""
        user_config = {
            "capture": {
                "save_interval_seconds": 600,  # Override default
                # min_chars_threshold missing - should use default
            },
            "apps": {
                "mode": "exclude",  # Override default
                "include_list": ["CustomApp"],  # Override default
                # exclude_list missing - should use default
            },
            "new_section": {
                "new_key": "new_value"
            }
        }
        
        config = Config()
        result = config._merge_with_defaults(user_config)
        
        # Check that user values override defaults
        assert result["capture"]["save_interval_seconds"] == 600
        assert result["apps"]["mode"] == "exclude"
        assert result["apps"]["include_list"] == ["CustomApp"]
        
        # Check that missing values use defaults
        assert result["capture"]["min_chars_threshold"] == 10  # Default
        assert result["capture"]["enabled"] is True  # Default
        assert "1Password" in result["apps"]["exclude_list"]  # Default
        
        # Check that new sections are added
        assert result["new_section"]["new_key"] == "new_value"
    
    def test_config_path_initialization(self):
        """Test that config path is properly initialized"""
        # Test with default path
        config = Config()
        assert config.config_path == Path("config.yaml")
        
        # Test with custom path
        custom_path = "custom/config.yaml"
        config = Config(custom_path)
        assert config.config_path == Path(custom_path)
    
    def test_file_read_error_handling(self, tmp_path):
        """Test handling of file read errors"""
        # Create a directory with the same name as config file
        # This will cause a read error
        config_path = tmp_path / "config.yaml"
        config_path.mkdir()  # Create directory instead of file
        
        config = Config(str(config_path))
        
        # Should fall back to defaults without crashing
        assert config.config["capture"]["save_interval_seconds"] == 300