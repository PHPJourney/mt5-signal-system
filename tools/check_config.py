#!/usr/bin/env python3
"""
配置文件检查工具
验证客户端配置是否正确
"""

import json
import sys
from pathlib import Path


def check_config(config_file: str) -> bool:
    """检查配置文件"""
    print(f"检查配置文件: {config_file}")
    print("=" * 60)
    
    # 读取配置
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"✗ 文件不存在: {config_file}")
        return False
    except json.JSONDecodeError as e:
        print(f"✗ JSON 格式错误: {e}")
        return False
    
    print("✓ JSON 格式正确")
    print()
    
    # 检查必需字段
    errors = []
    warnings = []
    
    # MQTT 配置
    if 'mqtt' not in config:
        errors.append("缺少 'mqtt' 配置段")
    else:
        mqtt = config['mqtt']
        
        if 'broker' not in mqtt:
            errors.append("mqtt.broker 未配置")
        elif mqtt['broker'] in ['localhost', '127.0.0.1']:
            warnings.append("mqtt.broker 使用本地地址，请确认是否正确")
        
        if 'port' not in mqtt:
            warnings.append("mqtt.port 未配置，将使用默认值 1883")
        
        if 'client_id' not in mqtt:
            warnings.append("mqtt.client_id 未配置，将使用默认值")
        
        if 'topic_prefix' not in mqtt:
            warnings.append("mqtt.topic_prefix 未配置，将使用默认值 trademind/signals")
        
        # 注意：username 和 password 不需要在配置中指定，会从 MT5 自动获取
        if 'username' in mqtt or 'password' in mqtt:
            warnings.append("⚠️  mqtt.username/password 不需要配置（将从 MT5 自动获取）")
    
    # 账户上报器配置（强制启用，用户无感知）
    if 'account_reporter' not in config:
        warnings.append("缺少 'account_reporter' 配置段，将使用默认配置")
    else:
        reporter = config['account_reporter']
        
        if 'proxy_url' not in reporter:
            warnings.append("account_reporter.proxy_url 未配置，默认为 http://localhost:5000")
        
        if 'interval' in reporter:
            interval = reporter['interval']
            if not isinstance(interval, int) or interval < 10:
                warnings.append("account_reporter.interval 建议设置为 >= 10 秒")
        
        # 检查是否有 enabled 字段（不应该有）
        if 'enabled' in reporter:
            warnings.append("⚠️  account_reporter.enabled 不需要配置（强制启用）")
    
    # 通用配置
    if 'common' not in config:
        warnings.append("缺少 'common' 配置段，将使用默认配置")
    
    # 日志配置
    if 'logging' not in config:
        warnings.append("缺少 'logging' 配置段，将使用默认配置")
    
    # 显示结果
    print("检查结果:")
    print("-" * 60)
    
    if errors:
        print("\n❌ 错误 (必须修复):")
        for i, error in enumerate(errors, 1):
            print(f"   {i}. {error}")
    
    if warnings:
        print("\n⚠️  警告 (建议检查):")
        for i, warning in enumerate(warnings, 1):
            print(f"   {i}. {warning}")
    
    if not errors and not warnings:
        print("\n✅ 配置检查通过！")
    
    print()
    
    # 显示关键配置
    print("关键配置摘要:")
    print("-" * 60)
    if 'mqtt' in config:
        mqtt = config['mqtt']
        print(f"  MQTT Broker: {mqtt.get('broker', '未配置')}:{mqtt.get('port', 1883)}")
        print(f"  Client ID:   {mqtt.get('client_id', '未配置')}")
        print(f"  Topic:       {mqtt.get('topic_prefix', 'trademind/signals')}/#")
        print(f"  Username:    [从 MT5 自动获取]")
    
    if 'account_reporter' in config:
        reporter = config['account_reporter']
        print(f"  账户上报:    强制启用（后台运行）")
        print(f"  Proxy URL:   {reporter.get('proxy_url', 'http://localhost:5000')}")
        print(f"  上报间隔:    {reporter.get('interval', 60)} 秒")
    
    print()
    
    return len(errors) == 0


def main():
    """主函数"""
    if len(sys.argv) > 1:
        config_files = sys.argv[1:]
    else:
        # 默认检查两个配置文件
        config_files = ['config/master_config.json', 'config/slave_config.json']
    
    all_passed = True
    
    for config_file in config_files:
        if not check_config(config_file):
            all_passed = False
        print()
    
    if all_passed:
        print("=" * 60)
        print("✅ 所有配置文件检查通过！")
        print("=" * 60)
        sys.exit(0)
    else:
        print("=" * 60)
        print("❌ 配置文件存在错误，请修复后重试")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()