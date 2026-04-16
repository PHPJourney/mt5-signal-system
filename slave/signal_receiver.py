"""
Slave Server - Signal Receiver and Trade Executor Module
Receives signals from master server and executes trades
"""

import sys
import os
import time
import json
import MetaTrader5 as mt5
from typing import Dict, Optional, List
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.mqtt_client import MQTTClient
from common.models import SignalMessage, TradingSignal, SignalType, OrderType
from common.utils import load_config, setup_logger, normalize_lot_size
from slave.symbol_mapper import SymbolMapper
from slave.risk_manager import RiskManager


class SlaveSignalReceiver:
    """从服务器信号接收器"""

    def __init__(self, config_path: str = "config/slave_config.json"):
        """
        初始化从服务器

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        self.config = load_config(config_path)
        self.logger = setup_logger(
            "slave_server",
            self.config['logging']['file'],
            self.config['logging']['level']
        )

        # 初始化MQTT客户端
        self.mqtt_client = MQTTClient(self.config, is_master=False)

        # 初始化符号映射器
        self.symbol_mapper = SymbolMapper(
            self.config.get('symbol_mapping', {})
        )

        # 初始化风险管理器
        self.risk_manager = RiskManager(
            self.config.get('risk_management', {})
        )

        # 交易配置
        self.trading_config = self.config.get('trading', {})
        self.multiplier = self.trading_config.get('multiplier', 1.0)
        self.reverse_trading = self.trading_config.get('reverse_trading', False)
        self.magic_number = self.trading_config.get('magic_number', 999999)
        self.slippage = self.trading_config.get('slippage_points', 30)

        # 跟踪已处理的订单
        self.processed_tickets: Dict[int, int] = {}  # {master_ticket: slave_ticket}

        # MT5连接状态
        self.mt5_initialized = False

        self.logger.info("Slave Signal Receiver initialized")
        self.logger.info(f"Multiplier: {self.multiplier}x, "
                        f"Reverse: {self.reverse_trading}, "
                        f"Magic: {self.magic_number}")

    def initialize_mt5(self) -> bool:
        """
        初始化MT5连接

        Returns:
            是否成功初始化
        """
        try:
            if not mt5.initialize():
                self.logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False

            account_info = mt5.account_info()
            if account_info is None:
                self.logger.error("Failed to get account info")
                return False

            self.logger.info(f"MT5 connected - Account: {account_info.login}, "
                           f"Server: {account_info.server}, "
                           f"Balance: ${account_info.balance:.2f}")
            self.mt5_initialized = True
            return True

        except Exception as e:
            self.logger.error(f"Error initializing MT5: {e}")
            return False

    def connect_mqtt(self):
        """连接到MQTT broker并订阅主题"""
        self.mqtt_client.set_message_callback(self._on_signal_received)
        self.mqtt_client.connect()
        self.mqtt_client.subscribe("signals")
        self.logger.info("Connected to MQTT broker and subscribed to signals")

    def _on_signal_received(self, topic: str, payload: str):
        """
        收到信号消息回调

        Args:
            topic: MQTT主题
            payload: 消息内容
        """
        try:
            message = SignalMessage.from_json(payload)
            self.logger.info(f"Received signal: type={message.signal_type}, "
                           f"signals={len(message.signals)}")

            # 处理每个信号
            for signal_data in message.signals:
                signal = TradingSignal.from_dict(signal_data)
                self._process_signal(signal)

        except Exception as e:
            self.logger.error(f"Error processing signal message: {e}")

    def _process_signal(self, signal: TradingSignal):
        """
        处理单个交易信号

        Args:
            signal: 交易信号
        """
        if not self.mt5_initialized or not self.mt5:
            self.logger.error("MT5 not initialized, cannot process signal")
            return
        
        try:
            # 根据信号类型处理
            if signal.signal_type == SignalType.NEW_ORDER.value:
                self._execute_new_order(signal)
            elif signal.signal_type == SignalType.CLOSE_ORDER.value:
                self._execute_close_order(signal)
            elif signal.signal_type == SignalType.MODIFY_ORDER.value:
                self._execute_modify_order(signal)
            else:
                self.logger.warning(f"Unknown signal type: {signal.signal_type}")

        except Exception as e:
            self.logger.error(f"Error processing signal: {e}")

    def _execute_new_order(self, signal: TradingSignal):
        """执行新开仓信号"""
        try:
            # 符号映射
            symbol = self.symbol_mapper.map_symbol(signal.symbol)
            
            # 计算手数
            volume = normalize_lot_size(signal.volume * self.multiplier)
            
            # 反向交易
            if self.reverse_trading:
                order_type = OrderType.SELL if signal.order_type == OrderType.BUY else OrderType.BUY
            else:
                order_type = signal.order_type
            
            # 构建请求
            request = {
                "action": self.mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": self.mt5.ORDER_TYPE_BUY if order_type == OrderType.BUY else self.mt5.ORDER_TYPE_SELL,
                "slippage": self.slippage,
                "magic": self.magic_number,
                "comment": f"Slave:{signal.master_ticket}",
                "type_filling": self.mt5.ORDER_FILLING_FOK,
            }
            
            # 添加止损止盈
            if signal.sl > 0:
                request["sl"] = signal.sl
            if signal.tp > 0:
                request["tp"] = signal.tp
            
            # 发送订单
            result = self.mt5.order_send(request)
            
            if result.retcode == self.mt5.TRADE_RETCODE_DONE:
                self.processed_tickets[signal.master_ticket] = result.order
                self.logger.info(f"Order executed: {symbol} {order_type} "
                               f"vol={volume} ticket={result.order}")
            else:
                self.logger.error(f"Order failed: {result.comment} (retcode={result.retcode})")

        except Exception as e:
            self.logger.error(f"Error executing new order: {e}")

    def _execute_close_order(self, signal: TradingSignal):
        """执行平仓信号"""
        try:
            slave_ticket = self.processed_tickets.get(signal.master_ticket)
            if not slave_ticket:
                self.logger.warning(f"No slave ticket found for master ticket {signal.master_ticket}")
                return
            
            # 获取持仓信息
            positions = self.mt5.positions_get(ticket=slave_ticket)
            if not positions:
                self.logger.warning(f"Position {slave_ticket} not found")
                return
            
            position = positions[0]
            symbol = position.symbol
            
            # 反向平仓
            close_type = self.mt5.ORDER_TYPE_SELL if position.type == self.mt5.ORDER_TYPE_BUY else self.mt5.ORDER_TYPE_BUY
            
            request = {
                "action": self.mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": position.volume,
                "type": close_type,
                "position": slave_ticket,
                "slippage": self.slippage,
                "magic": self.magic_number,
                "comment": f"Close:{signal.master_ticket}",
                "type_filling": self.mt5.ORDER_FILLING_FOK,
            }
            
            result = self.mt5.order_send(request)
            
            if result.retcode == self.mt5.TRADE_RETCODE_DONE:
                self.logger.info(f"Position closed: {symbol} ticket={slave_ticket}")
                del self.processed_tickets[signal.master_ticket]
            else:
                self.logger.error(f"Close failed: {result.comment}")

        except Exception as e:
            self.logger.error(f"Error executing close order: {e}")

    def _execute_modify_order(self, signal: TradingSignal):
        """执行修改订单信号"""
        try:
            slave_ticket = self.processed_tickets.get(signal.master_ticket)
            if not slave_ticket:
                self.logger.warning(f"No slave ticket found for master ticket {signal.master_ticket}")
                return
            
            request = {
                "action": self.mt5.TRADE_ACTION_SLTP,
                "symbol": signal.symbol,
                "sl": signal.sl,
                "tp": signal.tp,
                "position": slave_ticket,
            }
            
            result = self.mt5.order_send(request)
            
            if result.retcode == self.mt5.TRADE_RETCODE_DONE:
                self.logger.info(f"Order modified: ticket={slave_ticket} "
                               f"sl={signal.sl} tp={signal.tp}")
            else:
                self.logger.error(f"Modify failed: {result.comment}")

        except Exception as e:
            self.logger.error(f"Error executing modify order: {e}")

    def run(self):
        """主运行循环"""
        self.logger.info("Starting Slave Signal Receiver...")
        
        # 初始化MT5
        if not self.initialize_mt5():
            self.logger.error("Failed to initialize MT5. Exiting.")
            return

        # 连接MQTT
        self.connect_mqtt()

        # 启动MQTT循环
        try:
            self.mqtt_client.start_loop()
        except KeyboardInterrupt:
            self.logger.info("Slave Signal Receiver stopped by user")
        except Exception as e:
            self.logger.error(f"Slave Signal Receiver error: {e}")
        finally:
            self.mt5.shutdown()
            self.mqtt_client.disconnect()


def main():
    """入口函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MT5 Slave Signal Receiver')
    parser.add_argument('--config', default='config/slave_config.json',
                       help='Path to configuration file')
    args = parser.parse_args()
    
    receiver = SlaveSignalReceiver(args.config)
    receiver.run()


if __name__ == "__main__":
    main()
