#!/bin/bash
# 启动从服务器脚本

echo "================================"
echo "MT5 Signal System - Slave Server"
echo "================================"
echo ""

# 检查配置文件
if [ ! -f "config/slave_config.json" ]; then
    echo "错误: 配置文件不存在: config/slave_config.json"
    exit 1
fi

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装"
    exit 1
fi

# 检查依赖
echo "检查依赖..."
python3 -c "import MetaTrader5" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "警告: MetaTrader5 模块未安装"
    echo "运行: pip install -r requirements.txt"
    exit 1
fi

python3 -c "import paho.mqtt.client" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "警告: paho-mqtt 模块未安装"
    echo "运行: pip install -r requirements.txt"
    exit 1
fi

echo "启动从服务器..."
echo ""

python3 slave/signal_receiver.py --config config/slave_config.json
