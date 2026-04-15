"""
Master Server - Signal Sender Module
Monitors MT5 trades and broadcasts signals via MQTT
"""

import sys
import os
import time
import MetaTrader5 as mt5
from typing import List, Dict, Optional
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.mqtt_client import MQTTClient
from common.models import SignalMessage, TradingSignal, PositionInfo, OrderInfo, SignalType
from common.utils import load_config, setup_logger


class MasterSignalSender:
    """主服务器信号发送器"""

    def __init__(self, config_path: str = "config/master_config.json"):
        """
        初始化主服务器

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        self.config = load_config(config_path)
        self.logger = setup_logger(
            "master_server",
            self.config['logging']['file'],
            self.config['logging']['level']
        )

        # 初始化MQTT客户端
        self.mqtt_client = MQTTClient(self.config, is_master=True)

        # 跟踪已发送的订单
        self.sent_tickets: set = set()

        # MT5连接状态
        self.mt5_initialized = False

        self.logger.info("Master Signal Sender initialized")

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
                           f"Server: {account_info.server}")
            self.mt5_initialized = True
            return True

        except Exception as e:
            self.logger.error(f"Error initializing MT5: {e}")
            return False

    def connect_mqtt(self):
        """连接到MQTT broker"""
        self.mqtt_client.connect()
        self.logger.info("Connected to MQTT broker")

    def get_positions(self) -> List[PositionInfo]:
        """
        获取当前所有持仓

        Returns:
            持仓信息列表
        """
        positions = []
        try:
            mt5_positions = mt5.positions_get()
            if mt5_positions is None:
                return positions

            for pos in mt5_positions:
                position_info = PositionInfo(
                    ticket=pos.ticket,
                    symbol=pos.symbol,
                    order_type="BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL",
                    volume=pos.volume,
                    price_open=pos.price_open,
                    price_current=pos.price_current,
                    sl=pos.sl,
                    tp=pos.tp,
                    profit=pos.profit,
                    swap=pos.swap,
                    commission=pos.commission,
                    magic=pos.magic,
                    comment=pos.comment,
                    time_create=int(pos.time)
                )
                positions.append(position_info)

        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")

        return positions

    def get_pending_orders(self) -> List[OrderInfo]:
        """
        获取当前所有挂单

        Returns:
            挂单信息列表
        """
        orders = []
        try:
            mt5_orders = mt5.orders_get()
            if mt5_orders is None:
                return orders

            for order in mt5_orders:
                order_type_map = {
                    mt5.ORDER_TYPE_BUY_LIMIT: "BUY_LIMIT",
                    mt5.ORDER_TYPE_SELL_LIMIT: "SELL_LIMIT",
                    mt5.ORDER_TYPE_BUY_STOP: "BUY_STOP",
                    mt5.ORDER_TYPE_SELL_STOP: "SELL_STOP"
                }

                order_info = OrderInfo(
                    ticket=order.ticket,
                    symbol=order.symbol,
                    order_type=order_type_map.get(order.type, str(order.type)),
                    volume=order.volume_current,
                    price_open=order.price_open,
                    sl=order.sl,
                    tp=order.tp,
                    price_current=order.price_current,
                    time_expiration=int(order.time_expiration) if order.time_expiration else 0,
                    magic=order.magic,
                    comment=order.comment
                )
                orders.append(order_info)

        except Exception as e:
            self.logger.error(f"Error getting orders: {e}")

        return orders

    def detect_new_signals(self) -> List[TradingSignal]:
        """
        检测新的交易信号

        Returns:
            新信号列表
        """
        signals = []

        try:
            # 获取当前持仓
            current_positions = mt5.positions_get()
            if current_positions is None:
                return signals

            current_tickets = {pos.ticket for pos in current_positions}

            # 检测新开仓
            for pos in current_positions:
                if pos.ticket not in self.sent_tickets:
                    signal = TradingSignal(
                        signal_type=SignalType.NEW_ORDER.value,
                        symbol=pos.symbol,
                        order_type="BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL",
                        volume=pos.volume,
                        price=pos.price_open,
                        sl=pos.sl if pos.sl > 0 else None,
                        tp=pos.tp if pos.tp > 0 else None,
                        ticket=pos.ticket,
                        magic=pos.magic,
                        comment=pos.comment
                    )
                    signals.append(signal)
                    self.sent_tickets.add(pos.ticket)
                    self.logger.info(f"New position detected: Ticket={pos.ticket}, "
                                   f"Symbol={pos.symbol}, Type={'BUY' if pos.type == mt5.ORDER_TYPE_BUY else 'SELL'}")

            # 检测已平仓(从sent_tickets中移除不在当前持仓中的ticket)
            closed_tickets = self.sent_tickets - current_tickets
            for ticket in closed_tickets:
                signal = TradingSignal(
                    signal_type=SignalType.CLOSE_ORDER.value,
                    symbol="",
                    ticket=ticket
                )
                signals.append(signal)
                self.sent_tickets.discard(ticket)
                self.logger.info(f"Position closed: Ticket={ticket}")

            # 检测持仓修改(SL/TP变化)
            for pos in current_positions:
                if pos.ticket in self.sent_tickets:
                    # 这里可以添加更复杂的逻辑来检测SL/TP变化
                    pass

        except Exception as e:
            self.logger.error(f"Error detecting signals: {e}")

        return signals

    def send_signal_message(self, signals: List[TradingSignal],
                          positions: List[PositionInfo] = None,
                          orders: List[OrderInfo] = None):
        """
        发送信号消息

        Args:
            signals: 交易信号列表
            positions: 持仓信息列表
            orders: 挂单信息列表
        """
        if not signals and not self.config['signal'].get('include_positions', False):
            return

        try:
            message = SignalMessage(
                signal_type=SignalType.STATUS.value if not signals else SignalType.NEW_ORDER.value,
                master_id=self.config['mqtt']['client_id'],
                signals=[s.to_dict() for s in signals],
                positions=[p.to_dict() for p in positions] if positions else [],
                orders=[o.to_dict() for o in orders] if orders else []
            )

            json_message = message.to_json()
            success = self.mqtt_client.publish("signals", json_message)

            if success:
                self.logger.debug(f"Signal sent: {len(signals)} signals, "
                                f"{len(positions or [])} positions, "
                                f"{len(orders or [])} orders")
            else:
                self.logger.error("Failed to send signal")

        except Exception as e:
            self.logger.error(f"Error sending signal message: {e}")

    def run(self):
        """运行主服务器"""
        self.logger.info("Starting Master Signal Sender...")

        # 初始化MT5
        if not self.initialize_mt5():
            self.logger.error("Failed to initialize MT5. Exiting.")
            return

        # 连接MQTT
        self.connect_mqtt()

        try:
            send_interval = self.config['signal'].get('send_interval_ms', 100) / 1000.0
            self.logger.info(f"Signal sender running with interval: {send_interval}s")

            while True:
                # 检测新信号
                signals = self.detect_new_signals()

                # 获取持仓和挂单(如果配置启用)
                positions = None
                orders = None
                if self.config['signal'].get('include_positions', False):
                    positions = self.get_positions()
                if self.config['signal'].get('include_orders', False):
                    orders = self.get_pending_orders()

                # 发送信号
                if signals or positions or orders:
                    self.send_signal_message(signals, positions, orders)

                # 等待下一个周期
                time.sleep(send_interval)

        except KeyboardInterrupt:
            self.logger.info("Master server stopped by user")
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

    parser = argparse.ArgumentParser(description='MT5 Master Signal Sender')
    parser.add_argument('--config', type=str, default='config/master_config.json',
                       help='Path to configuration file')
    args = parser.parse_args()

    sender = MasterSignalSender(args.config)
    sender.run()


if __name__ == "__main__":
    main()
