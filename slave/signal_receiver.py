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
        """
        执行新开仓信号

        Args:
            signal: 交易信号
        """
        # 映射交易品种
        slave_symbol = self.symbol_mapper.map_symbol(signal.symbol)
        if slave_symbol is None:
            self.logger.error(f"Cannot map symbol: {signal.symbol}")
            return

        # 检查是否可以交易
        max_spread = self.config.get('risk_management', {}).get('max_spread_points', 50)
        can_trade, reason = self.risk_manager.can_trade(slave_symbol, max_spread)
        if not can_trade:
            self.logger.warning(f"Trading blocked: {reason}")
            return

        # 计算手数
        symbol_info = self.symbol_mapper.get_symbol_info(slave_symbol)
        if symbol_info is None:
            self.logger.error(f"Cannot get symbol info for {slave_symbol}")
            return

        lot_size = self.risk_manager.calculate_lot_size(
            master_volume=signal.volume,
            multiplier=self.multiplier,
            min_lot=self.trading_config.get('min_lot_size', 0.01),
            max_lot=self.trading_config.get('max_lot_size', 10.0),
            lot_step=self.trading_config.get('lot_step', 0.01),
            symbol=slave_symbol
        )

        # 确定订单类型(支持反向交易)
        order_type = signal.order_type
        if self.reverse_trading:
            if order_type == OrderType.BUY.value:
                order_type = OrderType.SELL.value
            elif order_type == OrderType.SELL.value:
                order_type = OrderType.BUY.value
            self.logger.info(f"Reverse trading: {signal.order_type} -> {order_type}")

        # 执行下单
        result = self._place_order(
            symbol=slave_symbol,
            order_type=order_type,
            volume=lot_size,
            sl=signal.sl,
            tp=signal.tp,
            comment=f"Copy:{signal.ticket}"
        )

        if result:
            self.processed_tickets[signal.ticket] = result
            self.logger.info(f"Order executed: Master ticket {signal.ticket} -> "
                           f"Slave ticket {result}")
        else:
            self.logger.error(f"Failed to execute order for signal {signal.ticket}")

    def _execute_close_order(self, signal: TradingSignal):
        """
        执行平仓信号

        Args:
            signal: 交易信号
        """
        # 查找对应的从服务器订单
        slave_ticket = self.processed_tickets.get(signal.ticket)
        if slave_ticket is None:
            self.logger.warning(f"No matching slave ticket for master ticket: {signal.ticket}")
            return

        # 平仓
        success = self._close_position(slave_ticket)
        if success:
            del self.processed_tickets[signal.ticket]
            self.logger.info(f"Position closed: Slave ticket {slave_ticket}")
        else:
            self.logger.error(f"Failed to close position: {slave_ticket}")

    def _execute_modify_order(self, signal: TradingSignal):
        """
        执行修改订单信号

        Args:
            signal: 交易信号
        """
        slave_ticket = self.processed_tickets.get(signal.ticket)
        if slave_ticket is None:
            self.logger.warning(f"No matching slave ticket for master ticket: {signal.ticket}")
            return

        # 修改订单(SL/TP)
        success = self._modify_position(
            ticket=slave_ticket,
            sl=signal.sl,
            tp=signal.tp
        )

        if success:
            self.logger.info(f"Position modified: Slave ticket {slave_ticket}")
        else:
            self.logger.error(f"Failed to modify position: {slave_ticket}")

    def _place_order(self, symbol: str, order_type: str, volume: float,
                    sl: Optional[float] = None, tp: Optional[float] = None,
                    comment: str = "") -> Optional[int]:
        """
        下单

        Args:
            symbol: 交易品种
            order_type: 订单类型 (BUY/SELL)
            volume: 手数
            sl: 止损价格
            tp: 止盈价格
            comment: 注释

        Returns:
            订单号,失败返回None
        """
        try:
            # 获取当前价格
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                self.logger.error(f"Cannot get tick for {symbol}")
                return None

            # 准备订单请求
            if order_type == OrderType.BUY.value:
                price = tick.ask
                order_action = mt5.ORDER_TYPE_BUY
            elif order_type == OrderType.SELL.value:
                price = tick.bid
                order_action = mt5.ORDER_TYPE_SELL
            else:
                self.logger.error(f"Unsupported order type: {order_type}")
                return None

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_action,
                "price": price,
                "deviation": self.slippage,
                "magic": self.magic_number,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # 添加SL和TP
            if sl and sl > 0:
                request["sl"] = sl
            if tp and tp > 0:
                request["tp"] = tp

            # 发送订单
            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"Order failed: {result.comment} (code: {result.retcode})")
                return None

            self.logger.info(f"Order placed: Ticket={result.order}, "
                           f"Symbol={symbol}, Type={order_type}, Volume={volume}")
            return result.order

        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return None

    def _close_position(self, ticket: int) -> bool:
        """
        平仓

        Args:
            ticket: 订单号

        Returns:
            是否成功
        """
        try:
            # 获取持仓信息
            position = mt5.positions_get(ticket=ticket)
            if position is None or len(position) == 0:
                self.logger.warning(f"Position not found: {ticket}")
                return False

            pos = position[0]

            # 准备平仓请求
            if pos.type == mt5.ORDER_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(pos.symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(pos.symbol).ask

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": order_type,
                "position": ticket,
                "price": price,
                "deviation": self.slippage,
                "magic": self.magic_number,
                "comment": f"Close:{ticket}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # 发送平仓请求
            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"Close failed: {result.comment} (code: {result.retcode})")
                return False

            self.logger.info(f"Position closed: Ticket={ticket}")
            return True

        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return False

    def _modify_position(self, ticket: int, sl: Optional[float] = None,
                        tp: Optional[float] = None) -> bool:
        """
        修改持仓(SL/TP)

        Args:
            ticket: 订单号
            sl: 新止损价格
            tp: 新止盈价格

        Returns:
            是否成功
        """
        try:
            # 获取持仓信息
            position = mt5.positions_get(ticket=ticket)
            if position is None or len(position) == 0:
                self.logger.warning(f"Position not found: {ticket}")
                return False

            pos = position[0]

            # 准备修改请求
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": pos.symbol,
                "sl": sl if sl and sl > 0 else pos.sl,
                "tp": tp if tp and tp > 0 else pos.tp,
                "position": ticket,
            }

            # 发送修改请求
            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"Modify failed: {result.comment} (code: {result.retcode})")
                return False

            self.logger.info(f"Position modified: Ticket={ticket}, SL={sl}, TP={tp}")
            return True

        except Exception as e:
            self.logger.error(f"Error modifying position: {e}")
            return False

    def run(self):
        """运行从服务器"""
        self.logger.info("Starting Slave Signal Receiver...")

        # 初始化MT5
        if not self.initialize_mt5():
            self.logger.error("Failed to initialize MT5. Exiting.")
            return

        # 连接MQTT
        self.connect_mqtt()

        try:
            self.logger.info("Slave server running. Waiting for signals...")

            # 主循环 - 保持运行并定期检查风险状态
            while True:
                # 检查风险状态
                risk_status = self.risk_manager.get_risk_status()
                if not risk_status.trading_enabled:
                    self.logger.warning(f"Trading disabled: {risk_status.blocked_reason}")

                time.sleep(1)

        except KeyboardInterrupt:
            self.logger.info("Slave server stopped by user")
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """清理资源"""
        self.logger.info("Cleaning up resources...")
        self.mqtt_client.disconnect()
        mt5.shutdown()
        self.logger.info("Cleanup completed")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='MT5 Slave Signal Receiver')
    parser.add_argument('--config', type=str, default='config/slave_config.json',
                       help='Path to configuration file')
    args = parser.parse_args()

    receiver = SlaveSignalReceiver(args.config)
    receiver.run()


if __name__ == "__main__":
    main()
