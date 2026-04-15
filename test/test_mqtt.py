"""
MQTT Connection Test Tool
Test MQTT broker connectivity and message flow
"""

import sys
import os
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.mqtt_client import MQTTClient
from common.utils import load_config


def test_mqtt_connection():
    """测试MQTT连接"""
    print("=" * 50)
    print("MQTT Connection Test")
    print("=" * 50)

    # 加载配置
    config_path = "config/slave_config.json"
    if not os.path.exists(config_path):
        print(f"错误: 配置文件不存在: {config_path}")
        return False

    config = load_config(config_path)

    print(f"\n配置信息:")
    print(f"  Broker: {config['mqtt']['broker']}")
    print(f"  Port: {config['mqtt']['port']}")
    print(f"  Client ID: {config['mqtt']['client_id']}")
    print(f"  Topic: {config['mqtt']['topic_prefix']}")

    # 创建客户端
    client = MQTTClient(config, is_master=False)

    try:
        print("\n正在连接...")
        client.connect()

        if client.is_connected():
            print("✓ 连接成功!")

            # 测试消息收发
            print("\n测试消息发送...")
            test_message = json.dumps({
                "test": True,
                "timestamp": time.time(),
                "message": "Hello from test tool"
            })

            success = client.publish("test", test_message)
            if success:
                print("✓ 消息发送成功!")
            else:
                print("✗ 消息发送失败")

            time.sleep(1)
            client.disconnect()
            print("\n✓ 测试完成!")
            return True
        else:
            print("✗ 连接失败")
            return False

    except Exception as e:
        print(f"✗ 错误: {e}")
        return False


def test_symbol_mapping():
    """测试品种映射"""
    print("\n" + "=" * 50)
    print("Symbol Mapping Test")
    print("=" * 50)

    config = load_config("config/slave_config.json")
    mapping = config.get('symbol_mapping', {})

    print(f"\n配置的映射关系:")
    for master, slave in mapping.items():
        print(f"  {master:15} -> {slave}")

    print(f"\n总计: {len(mapping)} 个映射")


if __name__ == "__main__":
    test_mqtt_connection()
    test_symbol_mapping()
