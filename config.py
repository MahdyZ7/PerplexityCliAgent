import os
import yaml
from pathlib import Path
from typing import Dict, Any

DEFAULT_CONFIG = {
    "api": {
        "url": "https://api.preplixity.com/v1/translate",
        "timeout": 30
    },
    "history": {
        "enabled": True,
        "file": "~/.bash_history",
        "max_entries": 1000
    },
    "display": {
        "copy_to_clipboard": True,
        "syntax_theme": "monokai"
    }
}

class Config:
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "nlbash"
        self.config_file = self.config_dir / "config.yaml"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default if not exists"""
        if not self.config_file.exists():
            self._create_default_config()
        
        try:
            with open(self.config_file, 'r') as f:
                user_config = yaml.safe_load(f)
                # Merge with defaults to ensure all required fields exist
                return self._merge_configs(DEFAULT_CONFIG, user_config or {})
        except Exception as e:
            print(f"Warning: Could not load config file, using defaults. Error: {e}")
            return DEFAULT_CONFIG.copy()

    def _create_default_config(self) -> None:
        """Create default configuration file"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_file, 'w') as f:
            yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False)

    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Recursively merge user config with defaults"""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'api.url')"""
        try:
            value = self.config
            for k in key.split('.'):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def update(self, key: str, value: Any) -> None:
        """Update configuration value and save to file"""
        keys = key.split('.')
        current = self.config
        
        # Navigate to the correct nested level
        for k in keys[:-1]:
            current = current.setdefault(k, {})
        
        # Update the value
        current[keys[-1]] = value
        
        # Save to file
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)

config = Config()
