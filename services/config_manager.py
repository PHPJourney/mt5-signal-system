"""配置管理服务"""
import json
from pathlib import Path


class ConfigManager:
    """管理配置文件"""
    
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.config_dir = self.base_dir / "config"
        self.config_dir.mkdir(exist_ok=True)
    
    def load_config(self, config_name):
        """加载配置文件"""
        config_path = self.config_dir / f"{config_name}.json"
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return self._get_default_config(config_name)
        except Exception as e:
            print(f"加载配置失败: {e}")
            return self._get_default_config(config_name)
    
    def save_config(self, config_name, config):
        """保存配置文件"""
        config_path = self.config_dir / f"{config_name}.json"
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            print(f"✓ 配置已保存: {config_path}")
            return True
        except Exception as e:
            print(f"✗ 保存配置失败: {e}")
            return False
    
    def _get_default_config(self, config_name):
        """获取默认配置"""
        if config_name == "master_config":
            return {
                "enabled": True,
                "mqtt": {
                    "broker": "localhost",
                    "port": 1883,
                    "username": "master",
                    "password": "",
                    "client_id": "master_001"
                },
                "mt5": {
                    "terminal_path": "",
                    "auto_select": True
                },
                "signal": {
                    "symbols": ["EURUSD", "GBPUSD", "USDJPY"],
                    "max_positions": 5,
                    "lot_size": 0.01
                }
            }
        elif config_name == "slave_config":
            return {
                "enabled": True,
                "mqtt": {
                    "broker": "localhost",
                    "port": 1883,
                    "username": "slave",
                    "password": "",
                    "client_id": "slave_001"
                },
                "mt5": {
                    "terminal_path": "",
                    "auto_select": True
                },
                "subscription": {
                    "master_id": "master_001"
                },
                "risk": {
                    "max_drawdown": 10,
                    "max_positions": 3,
                    "lot_multiplier": 1.0
                }
            }
        else:
            return {}