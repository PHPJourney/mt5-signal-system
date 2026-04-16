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
from common.utils import load_config, setup_logger, get_base_dir


def get_default_master_config() -> dict:
    """获取默认 Master 配置"""
    return {
        'enabled': True,
        'mqtt': {
            'broker': 'localhost',
            'port': 1883,
            'username': 'master',
            'password': '',
            'client_id': 'master_001',
            'topic_prefix': 'mt5/signal'
        },
        'mt5': {
            'terminal_path': '',
            'auto_select': True
        },
        'logging': {
            'file': 'logs/master.log',
            'level': 'INFO'
        },
        'signal': {
            'broadcast_interval': 1,
            'include_positions': True,
            'include_orders': True
        }
    }


class MasterSignalSender:
    """主服务器信号发送器"""

    def __init__(self, config_path: str = "config/master_config.json"):
        """
        初始化主服务器

        Args:
            config_path: 配置文件路径
        """
        # 获取 exe 所在目录作为基础路径
        base_dir = get_base_dir()
        
        # 解析配置文件路径（相对于 exe 目录）
        if not os.path.isabs(config_path):
            config_path = str(base_dir / config_path)
        
        # 加载配置
        self.config = load_config(config_path)
        
        # 如果配置为空或不完整，使用默认配置
        if not self.config:
            print(f"Warning: Config file not found: {config_path}")
            self.config = {}
            use_defaults = True
        else:
            # 检查配置是否完整（递归检查）
            use_defaults = not self._is_config_complete(self.config, get_default_master_config())
            if use_defaults:
                print(f"Warning: Config file is incomplete, merging defaults for missing fields")
        
        if use_defaults:
            # 合并默认配置（递归合并嵌套字典）
            default_config = get_default_master_config()
            self._merge_config(self.config, default_config)
            
            # 确保日志目录存在
            log_dir = base_dir / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
        
        # 确保日志文件路径是相对于 exe 目录
        if 'logging' in self.config and 'file' in self.config['logging']:
            log_file = self.config['logging']['file']
            if not os.path.isabs(log_file):
                self.config['logging']['file'] = str(base_dir / log_file)
    
    def _is_config_complete(self, config: dict, template: dict) -> bool:
        """递归检查配置是否完整"""
        for key, value in template.items():
            if key not in config:
                return False
            if isinstance(value, dict):
                if not isinstance(config[key], dict):
                    return False
                if not self._is_config_complete(config[key], value):
                    return False
        return True
    
    def _merge_config(self, target: dict, source: dict):
        """递归合并配置字典"""
        for key, value in source.items():
            if key not in target:
                target[key] = value
            elif isinstance(value, dict) and isinstance(target.get(key), dict):
                # 递归合并嵌套字典
                self._merge_config(target[key], value)

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
        self.logger.info(f"Base directory: {base_dir}")
        self.logger.info(f"Config path: {config_path}")

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
        if not self.mt5_initialized or not self.mt5:
            self.logger.error("MT5 not initialized")
            return []
        
        positions = []
        try:
            mt5_positions = self.mt5.positions_get()
            if mt5_positions is None:
                return positions

            for pos in mt5_positions:
                position_info = PositionInfo(
                    ticket=pos.ticket,
                    symbol=pos.symbol,
                    order_type="BUY" if pos.type == self.mt5.ORDER_TYPE_BUY else "SELL",
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
        if not self.mt5_initialized or not self.mt5:
            self.logger.error("MT5 not initialized")
            return []
        
        orders = []
        try:
            mt5_orders = self.mt5.orders_get()
            if mt5_orders is None:
                return orders

            for order in mt5_orders:
                order_info = OrderInfo(
                    ticket=order.ticket,
                    symbol=order.symbol,
                    order_type="BUY" if order.type == self.mt5.ORDER_TYPE_BUY else "SELL",
                    volume=order.volume_current,
                    price_open=order.price_open,
                    price_current=order.price_current,
                    sl=order.sl,
                    tp=order.tp,
                    time_setup=int(order.time_setup),
                    magic=order.magic,
                    comment=order.comment
                )
                orders.append(order_info)

        except Exception as e:
            self.logger.error(f"Error getting pending orders: {e}")

        return orders

    def check_for_new_signals(self):
        """检查新的持仓变化并发送信号"""
        try:
            positions = self.get_positions()
            orders = self.get_pending_orders()

            # 处理新持仓
            for pos in positions:
                if pos.ticket not in self.sent_tickets:
                    self.logger.info(f"New position detected: {pos.symbol} {pos.order_type} "
                                   f"vol={pos.volume} ticket={pos.ticket}")
                    
                    signal = TradingSignal(
                        signal_type=SignalType.NEW_ORDER.value,
                        symbol=pos.symbol,
                        order_type=pos.order_type,
                        volume=pos.volume,
                        price=pos.price_open,
                        sl=pos.sl,
                        tp=pos.tp,
                        master_ticket=pos.ticket,
                        magic=pos.magic,
                        comment=pos.comment
                    )
                    
                    self.send_signal(signal)
                    self.sent_tickets.add(pos.ticket)

            # 处理关闭的持仓
            # （需要维护一个持仓快照来检测关闭）
            # 这里简化处理，实际应该对比上一次的状态

        except Exception as e:
            self.logger.error(f"Error checking for new signals: {e}")

    def send_signal(self, signal: TradingSignal):
        """
        发送交易信号

        Args:
            signal: 交易信号
        """
        try:
            message = SignalMessage(
                master_id=self.config['mqtt']['client_id'],
                timestamp=int(datetime.now().timestamp()),
                signals=[signal.to_dict()]
            )
            
            self.mqtt_client.publish("signals", message.to_json())
            self.logger.info(f"Signal sent: {signal.symbol} {signal.order_type} "
                           f"ticket={signal.master_ticket}")

        except Exception as e:
            self.logger.error(f"Error sending signal: {e}")

    def run(self):
        """主运行循环"""
        self.logger.info("Starting Master Signal Sender...")
        
        # 初始化MT5
        if not self.initialize_mt5():
            self.logger.error("Failed to initialize MT5. Exiting.")
            return

        # 连接MQTT
        self.connect_mqtt()

        # 主循环
        check_interval = self.config.get('signal', {}).get('check_interval', 1)
        
        try:
            while True:
                self.check_for_new_signals()
                time.sleep(check_interval)
        except KeyboardInterrupt:
            self.logger.info("Master Signal Sender stopped by user")
        except Exception as e:
            self.logger.error(f"Master Signal Sender error: {e}")
        finally:
            self.mt5.shutdown()
            self.mqtt_client.disconnect()


def main():
    """入口函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MT5 Master Signal Sender')
    parser.add_argument('--config', default='config/master_config.json',
                       help='Path to configuration file')
    args = parser.parse_args()
    
    sender = MasterSignalSender(args.config)
    sender.run()


if __name__ == "__main__":
    main()