import yaml
from pathlib import Path
from typing import Dict, List, Any


class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return self._get_default_config()
            
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                return self._merge_with_defaults(config)
        except Exception as e:
            print(f"Error loading config: {e}")
            return self._get_default_config()
            
    def _get_default_config(self) -> Dict[str, Any]:
        return {
            "capture": {
                "save_interval_seconds": 300,  # 5 minutes
                "min_chars_threshold": 10,
                "enabled": True
            },
            "apps": {
                "mode": "include",  # "include" or "exclude"
                "include_list": [
                    "Chrome",
                    "Safari",
                    "Firefox",
                    "Visual Studio Code",
                    "TextEdit",
                    "Notes",
                    "Slack",
                    "Discord",
                    "Terminal",
                    "iTerm2",
                    "Finder",
                    "Mail"
                ],
                "exclude_list": [
                    "1Password",
                    "Keychain Access",
                    "Activity Monitor",
                    "System Preferences",
                    "Calculator"
                ]
            },
            "storage": {
                "database_path": "data/captures.db",
                "auto_cleanup_days": 30
            },
            "security": {
                "exclude_password_fields": True,
                "pause_on_secure_input": True
            }
        }
        
    def _merge_with_defaults(self, user_config: Dict[str, Any]) -> Dict[str, Any]:
        defaults = self._get_default_config()
        
        def deep_merge(default: Dict, user: Dict) -> Dict:
            result = default.copy()
            for key, value in user.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
            
        return deep_merge(defaults, user_config)
        
    def save_config(self):
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
        except Exception as e:
            print(f"Error saving config: {e}")
            
    def should_capture_app(self, app_name: str) -> bool:
        if not app_name:
            return False
            
        mode = self.config["apps"]["mode"]
        include_list = self.config["apps"]["include_list"]
        exclude_list = self.config["apps"]["exclude_list"]
        
        if mode == "include":
            return app_name in include_list
        else:  # exclude mode
            return app_name not in exclude_list
            
    def get_save_interval(self) -> int:
        return self.config["capture"]["save_interval_seconds"]
        
    def get_min_chars_threshold(self) -> int:
        return self.config["capture"]["min_chars_threshold"]
        
    def is_capture_enabled(self) -> bool:
        return self.config["capture"]["enabled"]
        
    def get_database_path(self) -> str:
        return self.config["storage"]["database_path"]
        
    def get_cleanup_days(self) -> int:
        return self.config["storage"]["auto_cleanup_days"]