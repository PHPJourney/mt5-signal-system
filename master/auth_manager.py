"""
License and Authentication Manager for TradeMind MT5
Manages client authorization and access control
"""

import json
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List
from common.utils import setup_logger


class LicenseManager:
    """许可证管理器"""

    def __init__(self, license_file: str = "config/licenses.json"):
        self.license_file = Path(license_file)
        self.logger = setup_logger("license_manager", "logs/license.log")
        self.licenses = self._load_licenses()

    def _load_licenses(self) -> Dict:
        """加载许可证数据库"""
        if self.license_file.exists():
            try:
                with open(self.license_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load licenses: {e}")
                return {"clients": {}, "blacklist": []}
        else:
            # 创建默认许可证文件
            default_data = {
                "clients": {},
                "blacklist": [],
                "created_at": datetime.now().isoformat()
            }
            self._save_licenses(default_data)
            return default_data

    def _save_licenses(self):
        """保存许可证数据库"""
        try:
            self.license_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.license_file, 'w', encoding='utf-8') as f:
                json.dump(self.licenses, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save licenses: {e}")

    def generate_license_key(self, client_name: str, days_valid: int = 365,
                            max_connections: int = 1, features: Dict = None) -> str:
        """
        生成许可证密钥

        Args:
            client_name: 客户名称
            days_valid: 有效天数
            max_connections: 最大连接数
            features: 功能权限

        Returns:
            许可证密钥
        """
        # 生成唯一密钥
        raw_key = f"{client_name}_{int(time.time())}_{secrets.token_hex(16)}"
        license_key = hashlib.sha256(raw_key.encode()).hexdigest()[:32].upper()

        # 计算过期时间
        expire_date = (datetime.now() + timedelta(days=days_valid)).isoformat()

        # 默认功能
        if features is None:
            features = {
                "copy_trading": True,
                "reverse_trading": True,
                "symbol_mapping": True,
                "risk_management": True
            }

        # 存储许可证
        self.licenses["clients"][license_key] = {
            "client_name": client_name,
            "license_key": license_key,
            "created_at": datetime.now().isoformat(),
            "expire_date": expire_date,
            "max_connections": max_connections,
            "current_connections": 0,
            "features": features,
            "status": "active",
            "last_used": None,
            "ip_addresses": []
        }

        self._save_licenses()
        self.logger.info(f"Generated license for {client_name}: {license_key}")

        return license_key

    def validate_license(self, license_key: str, client_ip: str = "") -> Dict:
        """
        验证许可证

        Args:
            license_key: 许可证密钥
            client_ip: 客户端IP地址

        Returns:
            验证结果 {valid: bool, message: str, data: dict}
        """
        # 检查是否在黑名单中
        if license_key in self.licenses.get("blacklist", []):
            return {
                "valid": False,
                "message": "License has been revoked",
                "error_code": "REVOKED"
            }

        # 查找许可证
        if license_key not in self.licenses["clients"]:
            return {
                "valid": False,
                "message": "Invalid license key",
                "error_code": "INVALID_KEY"
            }

        license_data = self.licenses["clients"][license_key]

        # 检查状态
        if license_data["status"] != "active":
            return {
                "valid": False,
                "message": f"License is {license_data['status']}",
                "error_code": "INACTIVE"
            }

        # 检查过期时间
        expire_date = datetime.fromisoformat(license_data["expire_date"])
        if datetime.now() > expire_date:
            license_data["status"] = "expired"
            self._save_licenses()
            return {
                "valid": False,
                "message": "License has expired",
                "error_code": "EXPIRED"
            }

        # 检查连接数
        if license_data["current_connections"] >= license_data["max_connections"]:
            return {
                "valid": False,
                "message": f"Max connections ({license_data['max_connections']}) reached",
                "error_code": "MAX_CONNECTIONS"
            }

        # 更新使用信息
        license_data["last_used"] = datetime.now().isoformat()
        if client_ip and client_ip not in license_data["ip_addresses"]:
            license_data["ip_addresses"].append(client_ip)

        self._save_licenses()

        return {
            "valid": True,
            "message": "License validated successfully",
            "data": {
                "client_name": license_data["client_name"],
                "expire_date": license_data["expire_date"],
                "max_connections": license_data["max_connections"],
                "features": license_data["features"]
            }
        }

    def revoke_license(self, license_key: str) -> bool:
        """吊销许可证"""
        if license_key in self.licenses["clients"]:
            self.licenses["clients"][license_key]["status"] = "revoked"
            if license_key not in self.licenses.get("blacklist", []):
                self.licenses.setdefault("blacklist", []).append(license_key)
            self._save_licenses()
            self.logger.warning(f"License revoked: {license_key}")
            return True
        return False

    def update_connection_count(self, license_key: str, delta: int):
        """更新连接数"""
        if license_key in self.licenses["clients"]:
            self.licenses["clients"][license_key]["current_connections"] += delta
            if self.licenses["clients"][license_key]["current_connections"] < 0:
                self.licenses["clients"][license_key]["current_connections"] = 0
            self._save_licenses()

    def list_licenses(self) -> List[Dict]:
        """列出所有许可证"""
        result = []
        for key, data in self.licenses["clients"].items():
            result.append({
                "client_name": data["client_name"],
                "license_key": key,
                "status": data["status"],
                "expire_date": data["expire_date"],
                "connections": f"{data['current_connections']}/{data['max_connections']}",
                "last_used": data["last_used"]
            })
        return result

    def get_license_info(self, license_key: str) -> Optional[Dict]:
        """获取许可证详细信息"""
        return self.licenses["clients"].get(license_key)


class AuthenticatedMQTTBroker:
    """
    带认证的MQTT Broker封装
    基于paho-mqtt实现简单的认证层
    """

    def __init__(self, license_manager: LicenseManager):
        self.license_manager = license_manager
        self.logger = setup_logger("mqtt_auth", "logs/mqtt_auth.log")
        self.authorized_clients = {}  # {client_id: license_key}

    def authenticate_client(self, client_id: str, license_key: str,
                          client_ip: str = "") -> Dict:
        """
        认证客户端

        Args:
            client_id: 客户端ID
            license_key: 许可证密钥
            client_ip: 客户端IP

        Returns:
            认证结果
        """
        # 验证许可证
        result = self.license_manager.validate_license(license_key, client_ip)

        if result["valid"]:
            # 记录授权的客户端
            self.authorized_clients[client_id] = {
                "license_key": license_key,
                "authenticated_at": datetime.now().isoformat(),
                "ip_address": client_ip
            }

            # 更新连接数
            self.license_manager.update_connection_count(license_key, 1)

            self.logger.info(f"Client authenticated: {client_id} "
                           f"(License: {license_key[:8]}...)")

            return {
                "success": True,
                "message": "Authentication successful",
                "client_info": result["data"]
            }
        else:
            self.logger.warning(f"Authentication failed for {client_id}: "
                              f"{result['message']}")
            return {
                "success": False,
                "message": result["message"],
                "error_code": result.get("error_code", "UNKNOWN")
            }

    def deauthenticate_client(self, client_id: str):
        """取消客户端认证"""
        if client_id in self.authorized_clients:
            license_key = self.authorized_clients[client_id]["license_key"]
            self.license_manager.update_connection_count(license_key, -1)
            del self.authorized_clients[client_id]
            self.logger.info(f"Client deauthenticated: {client_id}")

    def is_authorized(self, client_id: str) -> bool:
        """检查客户端是否已授权"""
        return client_id in self.authorized_clients

    def get_authorized_clients(self) -> List[Dict]:
        """获取所有已授权的客户端"""
        result = []
        for client_id, info in self.authorized_clients.items():
            result.append({
                "client_id": client_id,
                "license_key": info["license_key"][:8] + "...",
                "authenticated_at": info["authenticated_at"],
                "ip_address": info["ip_address"]
            })
        return result
