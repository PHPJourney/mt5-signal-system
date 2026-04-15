"""
MQTT Authentication Bridge for MT5 Signal System
在独立MQTT Broker上实现授权认证和访问控制
"""

import paho.mqtt.client as mqtt
import json
import hashlib
import time
from datetime import datetime
from typing import Dict, Optional, List
from master.auth_manager import LicenseManager
from common.utils import setup_logger


class MQTTAuthBridge:
    """
    MQTT 认证桥接器
    
    架构:
    Master Server → Auth Bridge (验证+加密) → MQTT Broker → Slave Servers
    """

    def __init__(self, broker_host: str, broker_port: int = 1883,
                 license_manager: LicenseManager = None):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.license_manager = license_manager or LicenseManager()
        self.logger = setup_logger("mqtt_bridge", "logs/mqtt_bridge.log")

        # 主服务器客户端 (发布信号)
        self.master_client = mqtt.Client(client_id="master_bridge")
        self.master_client.on_connect = self._on_master_connect
        self.master_client.on_publish = self._on_master_publish

        # 已认证的从服务器会话
        self.authenticated_sessions = {}  # {client_id: session_info}

        # 信号加密密钥 (每个License唯一)
        self.encryption_keys = {}

        self.logger.info(f"MQTT Auth Bridge initialized")
        self.logger.info(f"Broker: {broker_host}:{broker_port}")

    def _on_master_connect(self, client, userdata, flags, rc):
        """主服务器连接成功"""
        if rc == 0:
            self.logger.info("Master bridge connected to MQTT broker")
        else:
            self.logger.error(f"Master bridge connection failed: {rc}")

    def _on_master_publish(self, client, userdata, mid):
        """消息发布成功"""
        self.logger.debug(f"Signal published: mid={mid}")

    def start(self):
        """启动桥接器"""
        try:
            self.master_client.connect(self.broker_host, self.broker_port, 60)
            self.master_client.loop_start()
            self.logger.info("MQTT Auth Bridge started")
        except Exception as e:
            self.logger.error(f"Failed to start bridge: {e}")
            raise

    def stop(self):
        """停止桥接器"""
        self.master_client.loop_stop()
        self.master_client.disconnect()
        self.logger.info("MQTT Auth Bridge stopped")

    def authenticate_slave(self, client_id: str, license_key: str,
                          client_ip: str = "") -> Dict:
        """
        认证从服务器
        
        Args:
            client_id: 从服务器客户端ID
            license_key: License密钥
            client_ip: 客户端IP
            
        Returns:
            认证结果
        """
        # 验证License
        result = self.license_manager.validate_license(license_key, client_ip)

        if not result["valid"]:
            self.logger.warning(f"Authentication failed for {client_id}: "
                              f"{result['message']}")
            return result

        # 生成会话密钥 (用于信号加密)
        session_key = hashlib.sha256(
            f"{license_key}_{int(time.time())}".encode()
        ).hexdigest()[:16].upper()

        # 记录会话
        self.authenticated_sessions[client_id] = {
            "license_key": license_key,
            "session_key": session_key,
            "authenticated_at": datetime.now().isoformat(),
            "ip_address": client_ip,
            "features": result["data"]["features"]
        }

        # 更新连接数
        self.license_manager.update_connection_count(license_key, 1)

        # 订阅该客户端的专属主题
        subscribe_topic = f"mt5/signals/{license_key[:8]}"
        self.master_client.subscribe(subscribe_topic)

        self.logger.info(f"Slave authenticated: {client_id} "
                        f"(License: {license_key[:8]}...)")

        return {
            "success": True,
            "session_key": session_key,
            "subscribe_topic": subscribe_topic,
            "client_info": result["data"]
        }

    def publish_signal(self, signal_data: Dict, license_key: str) -> bool:
        """
        发布加密信号
        
        Args:
            signal_data: 信号数据
            license_key: 目标License密钥
            
        Returns:
            是否成功
        """
        try:
            # 加密信号数据
            encrypted_data = self._encrypt_signal(signal_data, license_key)

            # 发布到专属主题
            topic = f"mt5/signals/{license_key[:8]}"

            result = self.master_client.publish(
                topic,
                json.dumps(encrypted_data),
                qos=1
            )

            if result.rc == 0:
                self.logger.debug(f"Signal published to {topic}")
                return True
            else:
                self.logger.error(f"Failed to publish signal: {result.rc}")
                return False

        except Exception as e:
            self.logger.error(f"Error publishing signal: {e}")
            return False

    def broadcast_signal(self, signal_data: Dict) -> Dict:
        """
        广播信号给所有活跃的License
        
        Args:
            signal_data: 信号数据
            
        Returns:
            发送统计
        """
        stats = {"total": 0, "success": 0, "failed": 0}

        # 获取所有活跃的License
        active_licenses = [
            key for key, data in self.license_manager.licenses["clients"].items()
            if data["status"] == "active" and data["current_connections"] > 0
        ]

        for license_key in active_licenses:
            stats["total"] += 1
            if self.publish_signal(signal_data, license_key):
                stats["success"] += 1
            else:
                stats["failed"] += 1

        self.logger.info(f"Broadcast completed: {stats}")
        return stats

    def _encrypt_signal(self, signal_data: Dict, license_key: str) -> Dict:
        """
        加密信号数据 (简单XOR加密，生产环境建议使用AES)
        
        Args:
            signal_data: 原始信号
            license_key: License密钥
            
        Returns:
            加密后的数据
        """
        # 将数据转为JSON字符串
        json_str = json.dumps(signal_data)

        # 使用License密钥作为加密密钥
        key_bytes = license_key.encode('utf-8')
        data_bytes = json_str.encode('utf-8')

        # XOR加密
        encrypted_bytes = bytes([
            data_bytes[i] ^ key_bytes[i % len(key_bytes)]
            for i in range(len(data_bytes))
        ])

        # 转为Base64 (简化传输)
        import base64
        encrypted_b64 = base64.b64encode(encrypted_bytes).decode('utf-8')

        return {
            "encrypted": True,
            "data": encrypted_b64,
            "timestamp": datetime.now().isoformat(),
            "checksum": hashlib.md5(json_str.encode()).hexdigest()[:8]
        }

    def decrypt_signal(self, encrypted_data: Dict, license_key: str) -> Optional[Dict]:
        """
        解密信号数据
        
        Args:
            encrypted_data: 加密数据
            license_key: License密钥
            
        Returns:
            解密后的数据
        """
        try:
            if not encrypted_data.get("encrypted"):
                return encrypted_data

            import base64

            # Base64解码
            encrypted_bytes = base64.b64decode(encrypted_data["data"])

            # XOR解密
            key_bytes = license_key.encode('utf-8')
            decrypted_bytes = bytes([
                encrypted_bytes[i] ^ key_bytes[i % len(key_bytes)]
                for i in range(len(encrypted_bytes))
            ])

            # 转回JSON
            json_str = decrypted_bytes.decode('utf-8')
            signal_data = json.loads(json_str)

            # 验证校验和
            checksum = hashlib.md5(json_str.encode()).hexdigest()[:8]
            if checksum != encrypted_data.get("checksum"):
                self.logger.warning("Checksum verification failed")
                return None

            return signal_data

        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            return None

    def revoke_session(self, client_id: str):
        """撤销会话"""
        if client_id in self.authenticated_sessions:
            session = self.authenticated_sessions[client_id]
            license_key = session["license_key"]

            # 更新连接数
            self.license_manager.update_connection_count(license_key, -1)

            # 取消订阅
            topic = f"mt5/signals/{license_key[:8]}"
            self.master_client.unsubscribe(topic)

            # 删除会话
            del self.authenticated_sessions[client_id]

            self.logger.info(f"Session revoked: {client_id}")

    def get_active_sessions(self) -> List[Dict]:
        """获取活跃会话列表"""
        sessions = []
        for client_id, session in self.authenticated_sessions.items():
            sessions.append({
                "client_id": client_id,
                "license_key": session["license_key"][:8] + "...",
                "authenticated_at": session["authenticated_at"],
                "ip_address": session["ip_address"],
                "features": session["features"]
            })
        return sessions


class MosquittoACLGenerator:
    """
    Mosquitto ACL (访问控制列表) 配置生成器
    
    为每个License生成独立的ACL规则
    """

    def __init__(self, license_manager: LicenseManager):
        self.license_manager = license_manager
        self.logger = setup_logger("acl_generator", "logs/acl.log")

    def generate_acl_config(self, output_file: str = "config/mosquitto_acl.conf"):
        """
        生成Mosquitto ACL配置文件
        
        格式:
        user <username>
        topic readwrite <pattern>
        """
        lines = []
        lines.append("# Mosquitto ACL Configuration")
        lines.append(f"# Generated at: {datetime.now().isoformat()}")
        lines.append("")

        # 为每个License生成ACL规则
        for license_key, data in self.license_manager.licenses["clients"].items():
            if data["status"] != "active":
                continue

            client_prefix = license_key[:8]

            lines.append(f"# Client: {data['client_name']}")
            lines.append(f"user {client_prefix}")
            # 只能订阅自己的主题
            lines.append(f"topic read mt5/signals/{client_prefix}")
            # 可以发布心跳
            lines.append(f"topic write mt5/heartbeat/{client_prefix}")
            lines.append("")

        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        self.logger.info(f"ACL config generated: {output_file}")
        return output_file

    def generate_password_file(self, output_file: str = "config/mosquitto_passwd"):
        """
        生成Mosquitto密码文件
        
        注意: 实际使用时需要用 mosquitto_passwd 命令生成
        """
        lines = []
        lines.append("# Mosquitto Password File")
        lines.append(f"# Generated at: {datetime.now().isoformat()}")
        lines.append("# Use: mosquitto_passwd -b <file> <user> <password>")
        lines.append("")

        for license_key, data in self.license_manager.licenses["clients"].items():
            if data["status"] != "active":
                continue

            client_prefix = license_key[:8]
            # 使用License密钥作为密码
            lines.append(f"{client_prefix}:{license_key}")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        self.logger.info(f"Password file generated: {output_file}")
        return output_file

    def generate_mosquitto_conf(self, output_file: str = "config/mosquitto.conf"):
        """
        生成完整的Mosquitto配置文件
        """
        conf = """# Mosquitto Broker Configuration for MT5 Signal System
# Generated by ACL Generator

# 监听端口
listener 1883

# 禁用匿名访问
allow_anonymous false

# 密码文件
password_file /etc/mosquitto/config/mosquitto_passwd

# ACL文件
acl_file /etc/mosquitto/config/mosquitto_acl.conf

# 持久化
persistence true
persistence_location /var/lib/mosquitto/

# 日志
log_type all
log_dest file /var/log/mosquitto/mosquitto.log

# 最大连接数
max_connections -1

# QoS支持
max_qos 2
"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(conf)

        self.logger.info(f"Mosquitto config generated: {output_file}")
        return output_file
