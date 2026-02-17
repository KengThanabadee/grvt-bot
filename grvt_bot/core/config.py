"""
Configuration Manager for GRVT Bot

Supports loading configuration from:
1. YAML files
2. Environment variables
3. Python dictionary (backward compatibility)
"""

import os
import copy
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
            'loop_interval': 1,
        },
        'risk': {
            'active_track': 'normal',
            'fail_closed': True,
            'kill_switch': False,
            'threshold_action': 'flatten_halt',
            'risk_per_trade_pct': 0.25,
            'min_notional_safety_factor': 1.05,
            'tracks': {
                'normal': {
                    'max_drawdown_pct': 5.0,
                    'profit_target_pct': 5.0,
                },
                'low_vol': {
                    'max_drawdown_pct': 2.0,
                    'profit_target_pct': 2.0,
                },
            },
        },
        'ops': {
            'data_close_buffer_seconds': 2,
            'state_file': 'state/runtime_state.json',
            'lock_file': 'state/runtime.lock',
            'halt_on_reconcile_mismatch': True,
            'startup_mismatch_policy': 'adopt_continue',
            'error_backoff_seconds': 2,
            'max_repeated_errors': 20,
            'repeated_error_window_seconds': 300,
        },
        'execution': {
            'close_mode': 'reduce_only_twap_slice',
            'liquidity_usage_pct': 0.20,
            'orderbook_levels': 20,
            'max_slippage_bps': 20,
            'close_min_slice_qty': 0.01,
            'close_retry_interval_seconds': 2,
            'close_max_retries': 20,
            'close_max_duration_seconds': 90,
            'close_no_progress_retries': 3,
            'position_qty_tolerance': 0.000001,
            'fail_halt_on_close_failure': True,
        },
        'alerts': {
            'enabled': True,
            'telegram_enabled': False,
            'telegram_bot_token': '',
            'telegram_chat_id': '',
        },
    }
    
    def __init__(self, config_path: Optional[str] = None, config_dict: Optional[Dict] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to YAML config file
            config_dict: Dictionary with config values (for backward compatibility)
        """
        # Deep copy avoids cross-instance mutation of nested dictionaries.
        self.config = copy.deepcopy(self.DEFAULT_CONFIG)
        
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
            yaml_config = yaml.safe_load(f) or {}
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
            'RISK_ACTIVE_TRACK': ('risk', 'active_track'),
            'RISK_FAIL_CLOSED': ('risk', 'fail_closed'),
            'RISK_KILL_SWITCH': ('risk', 'kill_switch'),
            'RISK_PER_TRADE_PCT': ('risk', 'risk_per_trade_pct'),
            'RISK_MIN_NOTIONAL_SAFETY_FACTOR': ('risk', 'min_notional_safety_factor'),
            'OPS_DATA_CLOSE_BUFFER_SECONDS': ('ops', 'data_close_buffer_seconds'),
            'OPS_STATE_FILE': ('ops', 'state_file'),
            'OPS_LOCK_FILE': ('ops', 'lock_file'),
            'OPS_STARTUP_MISMATCH_POLICY': ('ops', 'startup_mismatch_policy'),
            'OPS_ERROR_BACKOFF_SECONDS': ('ops', 'error_backoff_seconds'),
            'OPS_MAX_REPEATED_ERRORS': ('ops', 'max_repeated_errors'),
            'OPS_REPEATED_ERROR_WINDOW_SECONDS': ('ops', 'repeated_error_window_seconds'),
            'EXECUTION_CLOSE_MODE': ('execution', 'close_mode'),
            'EXECUTION_LIQUIDITY_USAGE_PCT': ('execution', 'liquidity_usage_pct'),
            'EXECUTION_ORDERBOOK_LEVELS': ('execution', 'orderbook_levels'),
            'EXECUTION_MAX_SLIPPAGE_BPS': ('execution', 'max_slippage_bps'),
            'EXECUTION_CLOSE_MIN_SLICE_QTY': ('execution', 'close_min_slice_qty'),
            'EXECUTION_CLOSE_RETRY_INTERVAL_SECONDS': ('execution', 'close_retry_interval_seconds'),
            'EXECUTION_CLOSE_MAX_RETRIES': ('execution', 'close_max_retries'),
            'EXECUTION_CLOSE_MAX_DURATION_SECONDS': ('execution', 'close_max_duration_seconds'),
            'EXECUTION_CLOSE_NO_PROGRESS_RETRIES': ('execution', 'close_no_progress_retries'),
            'EXECUTION_POSITION_QTY_TOLERANCE': ('execution', 'position_qty_tolerance'),
            'EXECUTION_FAIL_HALT_ON_CLOSE_FAILURE': ('execution', 'fail_halt_on_close_failure'),
            'ALERTS_ENABLED': ('alerts', 'enabled'),
            'ALERTS_TELEGRAM_ENABLED': ('alerts', 'telegram_enabled'),
            'ALERTS_TELEGRAM_BOT_TOKEN': ('alerts', 'telegram_bot_token'),
            'ALERTS_TELEGRAM_CHAT_ID': ('alerts', 'telegram_chat_id'),
        }

        int_keys = {
            'leverage',
            'order_size_usdt',
            'loop_interval',
            'data_close_buffer_seconds',
            'error_backoff_seconds',
            'max_repeated_errors',
            'repeated_error_window_seconds',
            'orderbook_levels',
            'max_slippage_bps',
            'close_retry_interval_seconds',
            'close_max_retries',
            'close_max_duration_seconds',
            'close_no_progress_retries',
        }
        float_keys = {
            'risk_per_trade_pct',
            'min_notional_safety_factor',
            'liquidity_usage_pct',
            'close_min_slice_qty',
            'position_qty_tolerance',
        }
        bool_keys = {
            'fail_closed',
            'kill_switch',
            'enabled',
            'telegram_enabled',
            'fail_halt_on_close_failure',
        }

        for env_var, (section, key) in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                if key in int_keys:
                    value = int(value)
                elif key in float_keys:
                    value = float(value)
                elif key in bool_keys:
                    value = self._to_bool(value)
                self.config[section][key] = value

    @staticmethod
    def _to_bool(value: Any) -> bool:
        """Convert common string/int representations to bool."""
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}

    def _merge_config(self, new_config: Dict[str, Any], base: Optional[Dict[str, Any]] = None) -> None:
        """Recursively merge new config into existing config."""
        target = self.config if base is None else base

        for key, value in new_config.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                self._merge_config(value, base=target[key])
                continue
            target[key] = value
    
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

    @property
    def RISK_ACTIVE_TRACK(self) -> str:
        return self.get('risk', 'active_track')

    @property
    def RISK_FAIL_CLOSED(self) -> bool:
        return bool(self.get('risk', 'fail_closed', True))

    @property
    def RISK_KILL_SWITCH(self) -> bool:
        return bool(self.get('risk', 'kill_switch', False))

    @property
    def RISK_PER_TRADE_PCT(self) -> float:
        return float(self.get('risk', 'risk_per_trade_pct', 0.25))

    @property
    def DATA_CLOSE_BUFFER_SECONDS(self) -> int:
        return int(self.get('ops', 'data_close_buffer_seconds', 2))

    @property
    def STATE_FILE(self) -> str:
        return str(self.get('ops', 'state_file', 'state/runtime_state.json'))

    @property
    def LOCK_FILE(self) -> str:
        return str(self.get('ops', 'lock_file', 'state/runtime.lock'))

    @property
    def ERROR_BACKOFF_SECONDS(self) -> int:
        return int(self.get('ops', 'error_backoff_seconds', 2))

    @property
    def MAX_REPEATED_ERRORS(self) -> int:
        return int(self.get('ops', 'max_repeated_errors', 20))

    @property
    def REPEATED_ERROR_WINDOW_SECONDS(self) -> int:
        return int(self.get('ops', 'repeated_error_window_seconds', 300))

    @property
    def STARTUP_MISMATCH_POLICY(self) -> str:
        return str(self.get('ops', 'startup_mismatch_policy', 'adopt_continue'))

    @property
    def EXECUTION_CLOSE_MODE(self) -> str:
        return str(self.get('execution', 'close_mode', 'reduce_only_twap_slice'))

    @property
    def EXECUTION_LIQUIDITY_USAGE_PCT(self) -> float:
        return float(self.get('execution', 'liquidity_usage_pct', 0.20))

    @property
    def EXECUTION_ORDERBOOK_LEVELS(self) -> int:
        return int(self.get('execution', 'orderbook_levels', 20))

    @property
    def EXECUTION_MAX_SLIPPAGE_BPS(self) -> int:
        return int(self.get('execution', 'max_slippage_bps', 20))

    @property
    def EXECUTION_CLOSE_MIN_SLICE_QTY(self) -> float:
        return float(self.get('execution', 'close_min_slice_qty', 0.01))

    @property
    def EXECUTION_CLOSE_RETRY_INTERVAL_SECONDS(self) -> int:
        return int(self.get('execution', 'close_retry_interval_seconds', 2))

    @property
    def EXECUTION_CLOSE_MAX_RETRIES(self) -> int:
        return int(self.get('execution', 'close_max_retries', 20))

    @property
    def EXECUTION_CLOSE_MAX_DURATION_SECONDS(self) -> int:
        return int(self.get('execution', 'close_max_duration_seconds', 90))

    @property
    def EXECUTION_CLOSE_NO_PROGRESS_RETRIES(self) -> int:
        return int(self.get('execution', 'close_no_progress_retries', 3))

    @property
    def EXECUTION_POSITION_QTY_TOLERANCE(self) -> float:
        return float(self.get('execution', 'position_qty_tolerance', 0.000001))

    @property
    def EXECUTION_FAIL_HALT_ON_CLOSE_FAILURE(self) -> bool:
        return bool(self.get('execution', 'fail_halt_on_close_failure', True))
    
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
        safe_config = copy.deepcopy(self.config)
        if 'grvt' in safe_config:
            for key in ['api_key', 'private_key']:
                if key in safe_config['grvt'] and safe_config['grvt'][key]:
                    safe_config['grvt'][key] = '***MASKED***'
        if 'alerts' in safe_config and safe_config['alerts'].get('telegram_bot_token'):
            safe_config['alerts']['telegram_bot_token'] = '***MASKED***'
        return f"ConfigManager({safe_config})"
