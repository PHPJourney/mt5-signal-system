"""
Utility functions for MT5 Signal System
"""

import json
import logging
import os
import math
from pathlib import Path
from typing import Dict, Any


def load_config(config_path: str) -> Dict[str, Any]:
    """
    加载JSON配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}")


def setup_logger(name: str, log_file: str, level: str = "INFO") -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        log_file: 日志文件路径
        level: 日志级别

    Returns:
        配置好的logger对象
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # 创建日志目录
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, level.upper()))

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))

    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def normalize_lot_size(lot: float, min_lot: float, max_lot: float, lot_step: float) -> float:
    """
    标准化手数值

    Args:
        lot: 原始手数
        min_lot: 最小手数
        max_lot: 最大手数
        lot_step: 手数步长

    Returns:
        标准化后的手数
    """
    # 限制在最小和最大范围内
    lot = max(min_lot, min(lot, max_lot))

    # 按照步长取整
    normalized = round(lot / lot_step) * lot_step

    # 再次确保在范围内
    return max(min_lot, min(normalized, max_lot))


def calculate_pip_value(symbol: str, point: float) -> float:
    """
    计算点值 (简化版本,实际应根据品种调整)

    Args:
        symbol: 交易品种
        point: 点大小

    Returns:
        点值
    """
    # JPY相关品种
    if 'JPY' in symbol.upper():
        return point * 100
    # 黄金
    elif 'XAU' in symbol.upper() or 'GOLD' in symbol.upper():
        return point * 100
    # 其他外汇品种
    else:
        return point * 10000


def get_spread_in_points(bid: float, ask: float, point: float) -> float:
    """
    计算点差(以点为单位)

    Args:
        bid: 买价
        ask: 卖价
        point: 点大小

    Returns:
        点差(点数)
    """
    if point == 0:
        return 0
    return (ask - bid) / point
