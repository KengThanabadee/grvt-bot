"""
Configuration Manager for GRVT Bot

Supports loading configuration from:
1. YAML files
2. Environment variables
3. Python dictionary (backward compatibility)
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """Manages bot configuration from multiple sources."""
    
    DEFAULT_CONFIG = {
        'grvt': {
            'env': 'testnet',
            'api_key': '',
            'private_key': '',
            'trading_account_id': '',
            'sub_account_id': '0',
        },
        'trading': {
            'symbol': 'BTC_USDT_Perp',
            'leverage': 10,
            'order_size_usdt': 500,
            'loop_interval': 60,
        }
    }
    
    def __init__(self, config_path: Optional[str] = None, config_dict: Optional[Dict] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to YAML config file
            config_dict: Dictionary with config values (for backward compatibility)
        """
        self.config = self.DEFAULT_CONFIG.copy()
        
        # Load from YAML file if provided
        if config_path:
            self.load_from_yaml(config_path)
        
        # Load from dictionary if provided
        if config_dict:
            self.load_from_dict(config_dict)
        
        # Override with environment variables
        self.load_from_env()
    
    def load_from_yaml(self, config_path: str) -> None:
        """Load configuration from YAML file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            yaml_config = yaml.safe_load(f)
            self._merge_config(yaml_config)
    
    def load_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """Load configuration from dictionary."""
        self._merge_config(config_dict)
    
    def load_from_env(self) -> None:
        """Load configuration from environment variables."""
        env_mapping = {
            'GRVT_ENV': ('grvt', 'env'),
            'GRVT_API_KEY': ('grvt', 'api_key'),
            'GRVT_PRIVATE_KEY': ('grvt', 'private_key'),
            'GRVT_TRADING_ACCOUNT_ID': ('grvt', 'trading_account_id'),
            'GRVT_SUB_ACCOUNT_ID': ('grvt', 'sub_account_id'),
            'SYMBOL': ('trading', 'symbol'),
            'LEVERAGE': ('trading', 'leverage'),
            'ORDER_SIZE_USDT': ('trading', 'order_size_usdt'),
            'MAIN_LOOP_INTERVAL': ('trading', 'loop_interval'),
        }
        
        for env_var, (section, key) in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert to appropriate type
                if key in ['leverage', 'order_size_usdt', 'loop_interval']:
                    value = int(value)
                self.config[section][key] = value
    
    def _merge_config(self, new_config: Dict[str, Any]) -> None:
        """Recursively merge new config into existing config."""
        for key, value in new_config.items():
            if isinstance(value, dict) and key in self.config:
                self.config[key].update(value)
            else:
                self.config[key] = value
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(section, {}).get(key, default)
    
    def set(self, section: str, key: str, value: Any) -> None:
        """Set a configuration value."""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
    
    # Convenience properties for backward compatibility
    @property
    def GRVT_ENV(self) -> str:
        return self.get('grvt', 'env')
    
    @property
    def GRVT_API_KEY(self) -> str:
        return self.get('grvt', 'api_key')
    
    @property
    def GRVT_PRIVATE_KEY(self) -> str:
        return self.get('grvt', 'private_key')
    
    @property
    def GRVT_TRADING_ACCOUNT_ID(self) -> str:
        return self.get('grvt', 'trading_account_id')
    
    @property
    def GRVT_SUB_ACCOUNT_ID(self) -> str:
        return self.get('grvt', 'sub_account_id')
    
    @property
    def SYMBOL(self) -> str:
        return self.get('trading', 'symbol')
    
    @property
    def LEVERAGE(self) -> int:
        return self.get('trading', 'leverage')
    
    @property
    def ORDER_SIZE_USDT(self) -> int:
        return self.get('trading', 'order_size_usdt')
    
    @property
    def MAIN_LOOP_INTERVAL(self) -> int:
        return self.get('trading', 'loop_interval')
    
    def validate(self) -> bool:
        """Validate that required configuration values are set."""
        required = [
            ('grvt', 'api_key'),
            ('grvt', 'private_key'),
            ('grvt', 'trading_account_id'),
        ]
        
        for section, key in required:
            value = self.get(section, key)
            if not value or value == '':
                raise ValueError(f"Missing required config: {section}.{key}")
        
        return True
    
    def __repr__(self) -> str:
        # Mask sensitive data
        safe_config = self.config.copy()
        if 'grvt' in safe_config:
            for key in ['api_key', 'private_key']:
                if key in safe_config['grvt'] and safe_config['grvt'][key]:
                    safe_config['grvt'][key] = '***MASKED***'
        return f"ConfigManager({safe_config})"
