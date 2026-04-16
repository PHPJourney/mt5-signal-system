"""
MQTT Client Module for TradeMind MT5
Handles MQTT communication between master and slave servers
"""

import paho.mqtt.client as mqtt
import json
import time
from typing import Callable, Optional, Dict, Any
from common.utils import setup_logger


class MQTTClient:
    """MQTT客户端封装类"""

    def __init__(self, config: Dict[str, Any], is_master: bool = True):
        """
        初始化MQTT客户端

        Args:
            config: MQTT配置字典
            is_master: 是否为主服务器
        """
        self.config = config
        self.is_master = is_master
        self.logger = setup_logger(
            "mqtt_client",
            f"logs/mqtt_{'master' if is_master else 'slave'}.log",
            config.get('logging', {}).get('level', 'INFO')
        )

        # MQTT配置
        self.broker = config['mqtt']['broker']
        self.port = config['mqtt'].get('port', 1883)
        self.username = config['mqtt'].get('username', '')
        self.password = config['mqtt'].get('password', '')
        self.client_id = config['mqtt']['client_id']
        self.topic_prefix = config['mqtt'].get('topic_prefix', 'mt5/signal')

        # 创建MQTT客户端
        self.client = mqtt.Client(client_id=self.client_id)

        # 设置认证
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        # 设置回调
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish

        # 消息回调函数
        self.message_callback: Optional[Callable] = None

        # 连接状态
        self.connected = False

    def _on_connect(self, client, userdata, flags, rc):
        """连接成功回调"""
        if rc == 0:
            self.connected = True
            self.logger.info(f"Successfully connected to MQTT broker: {self.broker}:{self.port}")

            # 订阅主题(从服务器需要订阅)
            if not self.is_master:
                subscribe_topic = f"{self.topic_prefix}/#"
                self.client.subscribe(subscribe_topic)
                self.logger.info(f"Subscribed to topic: {subscribe_topic}")
        else:
            self.logger.error(f"Failed to connect with code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        self.connected = False
        self.logger.warning(f"Disconnected from MQTT broker with code: {rc}")

    def _on_message(self, client, userdata, msg):
        """收到消息回调"""
        try:
            payload = msg.payload.decode('utf-8')
            self.logger.debug(f"Received message on {msg.topic}: {payload[:200]}")

            if self.message_callback:
                self.message_callback(msg.topic, payload)
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")

    def _on_publish(self, client, userdata, mid):
        """发布消息回调"""
        self.logger.debug(f"Message published with mid: {mid}")

    def connect(self):
        """连接到MQTT broker"""
        try:
            self.logger.info(f"Connecting to MQTT broker: {self.broker}:{self.port}")
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()

            # 等待连接
            timeout = 10
            start_time = time.time()
            while not self.connected and time.time() - start_time < timeout:
                time.sleep(0.1)

            if not self.connected:
                raise TimeoutError("Connection timeout")

        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT broker: {e}")
            raise

    def disconnect(self):
        """断开MQTT连接"""
        self.client.loop_stop()
        self.client.disconnect()
        self.logger.info("Disconnected from MQTT broker")

    def publish(self, topic: str, message: str, qos: int = 1, retain: bool = False):
        """
        发布消息

        Args:
            topic: 主题
            message: 消息内容
            qos: QoS级别 (0, 1, 2)
            retain: 是否保留消息
        """
        if not self.connected:
            self.logger.warning("Not connected to MQTT broker")
            return False

        try:
            full_topic = f"{self.topic_prefix}/{topic}"
            result = self.client.publish(full_topic, message, qos=qos, retain=retain)
            self.logger.debug(f"Published to {full_topic}")
            return result.rc == 0
        except Exception as e:
            self.logger.error(f"Failed to publish message: {e}")
            return False

    def set_message_callback(self, callback: Callable):
        """
        设置消息回调函数

        Args:
            callback: 回调函数,接收(topic, payload)参数
        """
        self.message_callback = callback

    def subscribe(self, topic: str, qos: int = 1):
        """
        订阅主题

        Args:
            topic: 主题
            qos: QoS级别
        """
        if not self.connected:
            self.logger.warning("Not connected to MQTT broker")
            return

        full_topic = f"{self.topic_prefix}/{topic}"
        self.client.subscribe(full_topic, qos=qos)
        self.logger.info(f"Subscribed to: {full_topic}")

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.connected
