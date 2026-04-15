#!/bin/bash
# MT5 Signal System - Management Panel Launcher

echo "========================================"
echo "  MT5 Signal System - Management Panel"
echo "========================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3，请先安装 Python 3.8+"
    exit 1
fi

echo "[信息] Python 版本: $(python3 --version)"
echo ""

# 安装依赖
echo "[检查] 正在检查依赖..."
pip3 install psutil 2>/dev/null || pip install psutil 2>/dev/null

# 尝试安装 ttkbootstrap（可选，用于美化主题）
if ! pip3 show ttkbootstrap &>/dev/null; then
    echo "[提示] ttkbootstrap 未安装，将使用默认主题"
    echo "[提示] 如需美化界面，请运行: pip install ttkbootstrap"
fi

echo ""
echo "[启动] 正在启动管理面板..."
echo ""

python3 mt5_manager.py
