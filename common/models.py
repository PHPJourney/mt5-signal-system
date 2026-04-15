"""
Data models for MT5 Signal System
Defines all message structures used in communication
"""

from enum import Enum
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List
import json
import time


class SignalType(Enum):
    """信号类型枚举"""
    NEW_ORDER = "NEW_ORDER"          # 新订单
    CLOSE_ORDER = "CLOSE_ORDER"      # 平仓
    MODIFY_ORDER = "MODIFY_ORDER"    # 修改订单
    HEARTBEAT = "HEARTBEAT"          # 心跳
    STATUS = "STATUS"                # 状态报告


class OrderType(Enum):
    """订单类型枚举"""
    BUY = "BUY"                      # 买入
    SELL = "SELL"                    # 卖出
    BUY_LIMIT = "BUY_LIMIT"          # 限价买入
    SELL_LIMIT = "SELL_LIMIT"        # 限价卖出
    BUY_STOP = "BUY_STOP"            # 止损买入
    SELL_STOP = "SELL_STOP"          # 止损卖出


@dataclass
class PositionInfo:
    """持仓信息"""
    ticket: int                      # 订单号
    symbol: str                      # 交易品种
    order_type: str                  # 订单类型 (BUY/SELL)
    volume: float                    # 手数
    price_open: float                # 开仓价格
    price_current: float             # 当前价格
    sl: float                        # 止损价格
    tp: float                        # 止盈价格
    profit: float                    # 盈亏
    swap: float                      # 库存费
    commission: float                # 佣金
    magic: int                       # 魔术数字
    comment: str                     # 注释
    time_create: int                 # 创建时间戳

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'PositionInfo':
        return cls(**data)


@dataclass
class OrderInfo:
    """挂单信息"""
    ticket: int                      # 订单号
    symbol: str                      # 交易品种
    order_type: str                  # 订单类型
    volume: float                    # 手数
    price_open: float                # 开仓价格
    sl: float                        # 止损价格
    tp: float                        # 止盈价格
    price_current: float             # 当前价格
    time_expiration: int             # 过期时间
    magic: int                       # 魔术数字
    comment: str                     # 注释

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'OrderInfo':
        return cls(**data)


@dataclass
class TradingSignal:
    """交易信号"""
    signal_type: str                 # 信号类型
    symbol: str                      # 交易品种
    order_type: Optional[str] = None # 订单类型
    volume: Optional[float] = None   # 手数
    price: Optional[float] = None    # 价格
    sl: Optional[float] = None       # 止损
    tp: Optional[float] = None       # 止盈
    ticket: Optional[int] = None     # 订单号(用于平仓/修改)
    magic: Optional[int] = None      # 魔术数字
    comment: Optional[str] = None    # 注释
    timestamp: Optional[float] = None # 时间戳

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'TradingSignal':
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'TradingSignal':
        return cls.from_dict(json.loads(json_str))


@dataclass
class SignalMessage:
    """完整的信号消息"""
    signal_type: str                 # 信号类型
    master_id: str                   # 主服务器ID
    signals: List[dict]              # 交易信号列表
    positions: Optional[List[dict]] = None  # 持仓列表
    orders: Optional[List[dict]] = None     # 挂单列表
    timestamp: Optional[float] = None       # 时间戳

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.positions is None:
            self.positions = []
        if self.orders is None:
            self.orders = []

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'SignalMessage':
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_json(cls, json_str: str) -> 'SignalMessage':
        return cls.from_dict(json.loads(json_str))


@dataclass
class RiskStatus:
    """风险管理状态"""
    daily_loss: float = 0.0          # 当日亏损
    max_daily_loss: float = 0.0      # 最大日亏损限制
    trading_enabled: bool = True     # 是否允许交易
    last_reset_date: str = ""        # 上次重置日期
    blocked_reason: str = ""         # 阻止原因

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'RiskStatus':
        return cls(**data)
