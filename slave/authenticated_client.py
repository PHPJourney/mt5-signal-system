"""
Authenticated MQTT Client for Slave Server
带认证的MQTT客户端，支持License验证和信号解密
"""

import paho.mqtt.client as mqtt
import json
import base64
import hashlib
from datetime import datetime
from typing import Dict, Optional, Callable
from common.utils import setup_logger


class AuthenticatedMQTTClient:
    """
    带认证的MQTT客户端
    
    功能:
    1. 使用License密钥认证
    2. 接收加密信号
    3. 自动解密
    4. 心跳保活
    """

    def __init__(self, broker_host: str, broker_port: int,
                 client_id: str, license_key: str):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        self.license_key = license_key
        self.logger = setup_logger("auth_client", "logs/auth_client.log")

        # 创建MQTT客户端
        self.client = mqtt.Client(client_id=self.client_id)

        # 设置认证 (使用License密钥前8位作为用户名，完整密钥作为密码)
        username = self.license_key[:8]
        self.client.username_pw_set(username, self.license_key)

        # 设置回调
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        # 会话密钥 (认证成功后获取)
        self.session_key = None
        self.subscribed_topic = None

        # 消息回调
        self.message_callback: Optional[Callable] = None

        # 连接状态
        self.connected = False
        self.authenticated = False

    def _on_connect(self, client, userdata, flags, rc):
        """连接成功回调"""
        if rc == 0:
            self.connected = True
            self.logger.info(f"Connected to MQTT broker: {self.broker_host}")

            # 发送认证请求
            self._send_auth_request()
        else:
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorised"
            }
            self.logger.error(f"Connection failed: {error_messages.get(rc, f'Code {rc}')}")

    def _on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        self.connected = False
        self.authenticated = False
        self.logger.warning(f"Disconnected from MQTT broker (code: {rc})")

    def _on_message(self, client, userdata, msg):
        """收到消息回调"""
        try:
            payload = json.loads(msg.payload.decode('utf-8'))

            # 检查是否是加密数据
            if payload.get("encrypted"):
                # 解密信号
                decrypted = self._decrypt_signal(payload)
                if decrypted and self.message_callback:
                    self.message_callback(decrypted)
                else:
                    self.logger.warning("Failed to decrypt signal")
            else:
                # 未加密数据 (如认证成功消息)
                if self.message_callback:
                    self.message_callback(payload)

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")

    def _send_auth_request(self):
        """发送认证请求"""
        auth_data = {
            "type": "AUTH_REQUEST",
            "client_id": self.client_id,
            "license_key": self.license_key,
            "timestamp": datetime.now().isoformat()
        }

        topic = "mt5/auth/request"
        self.client.publish(topic, json.dumps(auth_data), qos=1)
        self.logger.info("Authentication request sent")

    def _decrypt_signal(self, encrypted_data: Dict) -> Optional[Dict]:
        """
        解密信号数据
        
        Args:
            encrypted_data: 加密数据
            
        Returns:
            解密后的数据
        """
        try:
            # 使用License密钥解密
            key_bytes = self.license_key.encode('utf-8')
            encrypted_bytes = base64.b64decode(encrypted_data["data"])

            # XOR解密
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

    def connect(self):
        """连接到MQTT Broker"""
        try:
            self.logger.info(f"Connecting to {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()

            # 等待连接
            import time
            timeout = 10
            start_time = time.time()
            while not self.connected and time.time() - start_time < timeout:
                time.sleep(0.1)

            if not self.connected:
                raise TimeoutError("Connection timeout")

        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            raise

    def disconnect(self):
        """断开连接"""
        self.client.loop_stop()
        self.client.disconnect()
        self.logger.info("Disconnected from MQTT broker")

    def set_message_callback(self, callback: Callable):
        """设置消息回调"""
        self.message_callback = callback

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected

    def is_authenticated(self) -> bool:
        """检查认证状态"""
        return self.authenticated

    def send_heartbeat(self):
        """发送心跳"""
        if self.connected:
            heartbeat = {
                "type": "HEARTBEAT",
                "client_id": self.client_id,
                "timestamp": datetime.now().isoformat()
            }
            topic = f"mt5/heartbeat/{self.license_key[:8]}"
            self.client.publish(topic, json.dumps(heartbeat), qos=0)
