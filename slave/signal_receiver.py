"""
Slave Server - Signal Receiver and Trade Executor Module
Enhanced version with comprehensive risk control and filtering
对标言成EA 71个参数功能
"""

import sys
import os
import time
import json
import threading
import MetaTrader5 as mt5
from typing import Dict, Optional, List
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.mqtt_client import MQTTClient
from common.models import SignalMessage, TradingSignal, SignalType, OrderType
from common.utils import load_config, setup_logger, normalize_lot_size, get_base_dir
from slave.symbol_mapper import SymbolMapper
from slave.risk_manager import RiskManager


def get_default_slave_config() -> dict:
    """获取默认 Slave 配置 - 完整覆盖所有代码使用的配置字段"""
    return {
        # 基础开关
        'enabled': True,
        
        # MQTT 配置
        'mqtt': {
            'broker': 'localhost',
            'port': 1883,
            'username': 'slave',
            'password': '',
            'client_id': 'slave_001',
            'topic_prefix': 'mt5/signal'
        },
        
        # MT5 配置
        'mt5': {
            'terminal_path': '',
            'auto_select': True
        },
        
        # 订阅配置
        'subscription': {
            'master_id': 'master_001'
        },
        
        # 日志配置
        'logging': {
            'file': 'logs/slave.log',
            'level': 'INFO'
        },
        
        # 常用设置
        'common': {
            'follow_mode': 'both',  # both/long_only/short_only
            'enable_alerts': True,
            'stop_alert_on_price': False,
            'reverse_trading': False,
            'magic_number': 999999,
            'slippage_points': 30,
            'comment_prefix': 'TM_'
        },
        
        # 安全设置
        'security': {
            'allow_auto_trading': True,
            'allow_dll_import': False
        },
        
        # 风险管理（手数模式 + 风险控制）
        'risk': {
            # 风险控制参数
            'max_drawdown_percent': 10.0,
            'max_drawdown_usd': 1000.0,
            'max_profit_percent': 20.0,
            'max_profit_usd': 2000.0,
            'session_loss_usd': 0.0,
            'session_profit_usd': 0.0,
            'cooldown_minutes': 0,
            'max_positions': 3,
            'max_total_lots': 10.0,
            
            # 手数计算模式
            'lot_mode': 'multiplier',  # multiplier/balance_ratio/fixed/fixed_per_usd/incremental
            'lot_multiplier': 1.0,
            'fixed_lot': 0.1,
            'balance_ratio': 1.0,
            'usd_per_lot': 1000.0,
            'incremental_base': 0.01,
            'incremental_step': 0.01,
            
            # 手数限制
            'min_lot': 0.01,
            'max_lot': 888.8,
            'skip_lot_less_than': 0.01,
            'skip_lot_greater_than': 888.8
        },
        
        # 过滤规则
        'filter': {
            'follow_buy': True,
            'follow_sell': True,
            'follow_market_orders': True,
            'follow_pending_orders': False,
            'follow_old_orders': False,
            'max_order_age_minutes': 0.0,
            'allow_duplicate_follow': False,
            'follow_close': True,
            'follow_sl_tp': False,
            'require_profit_points': 0,
            'require_loss_points': 0,
            'max_price_deviation_points': 0,
            'allowed_magics': [],
            'required_comments': [],
            'allowed_hours_start': '00:00:00',
            'allowed_hours_end': '23:59:59',
            'whitelist_symbols': [],
            'blacklist_symbols': []
        },
        
        # 追踪止损
        'trailing_stop': {
            'enabled': False,
            'profit_points': 0,
            'trail_points': 0
        },
        
        # 符号映射
        'symbol_mapping': {},
        
        # 高级设置
        'advanced': {
            'refresh_interval_ms': 150,
            'auto_clear_traces': True,
            'disconnect_alert_seconds': 30,
            'custom_comment': ''
        }
    }


class SlaveSignalReceiver:
    """从服务器信号接收器 - 增强版（对标言成EA）"""

    def __init__(self, config_path: str = "config/slave_config.json"):
        """
        初始化从服务器

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
            use_defaults = not self._is_config_complete(self.config, get_default_slave_config())
            if use_defaults:
                print(f"Warning: Config file is incomplete, merging defaults for missing fields")
        
        if use_defaults:
            # 合并默认配置（递归合并嵌套字典）
            default_config = get_default_slave_config()
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

        # 初始化高级风险管理器（传递完整配置）
        self.risk_manager = RiskManager(self.config)

        # 配置分区
        self.filter_config = self.config.get('filter', {})
        self.security_config = self.config.get('security', {})
        self.common_config = self.config.get('common', {})
        self.trailing_config = self.config.get('trailing_stop', {})
        
        # 交易基础配置
        self.reverse_trading = self.common_config.get('reverse_trading', False)
        self.magic_number = self.config.get('magic_number', 999999)
        self.slippage = self.config.get('slippage_points', 30)

        # 跟踪已处理的订单
        self.processed_tickets: Dict[int, int] = {}  # {master_ticket: slave_ticket}
        self.order_index = 0  # 订单序号（用于递增手数模式）

        # MT5连接状态
        self.mt5_initialized = False
        
        # 追踪止损线程
        self.trailing_thread = None
        self.trailing_stop_running = False

        self.logger.info("=" * 60)
        self.logger.info("Slave Signal Receiver (Enhanced) initialized")
        self.logger.info(f"Lot mode: {self.config.get('risk', {}).get('lot_mode', 'multiplier')}")
        self.logger.info(f"Follow mode: {self.common_config.get('follow_mode', 'both')}")
        self.logger.info(f"Auto trading: {self.security_config.get('allow_auto_trading', True)}")
        self.logger.info(f"Risk management: ENABLED")
        self.logger.info(f"Order filtering: ENABLED")
        self.logger.info("=" * 60)

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
            
            # 同步余额到风险管理器
            self.risk_manager.initial_balance = account_info.balance
            self.risk_manager.daily_start_balance = account_info.balance
            self.risk_manager.session_start_balance = account_info.balance
            
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
            # 检查安全开关
            if not self.security_config.get('allow_auto_trading', True):
                self.logger.warning("Auto trading is disabled, ignoring signals")
                return

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
        if not self.mt5_initialized:
            self.logger.error("MT5 not initialized, cannot process signal")
            return
        
        try:
            # 构建信号字典用于过滤
            signal_dict = {
                'type': 'BUY' if signal.order_type == OrderType.BUY else 'SELL',
                'order_type': 'market' if signal.order_type in [OrderType.BUY, OrderType.SELL] else 'pending',
                'symbol': signal.symbol,
                'volume': signal.volume,
                'price': signal.price or 0,
                'timestamp': datetime.fromtimestamp(signal.timestamp).isoformat() if signal.timestamp else datetime.now().isoformat(),
                'profit_points': getattr(signal, 'profit', 0),
                'magic': signal.magic or 0,
                'comment': signal.comment or '',
                'ticket': signal.ticket or 0
            }
            
            # 执行订单过滤
            allowed, reason = self.risk_manager.check_order_filter(signal_dict)
            if not allowed:
                self.logger.info(f"[FILTER] Signal ignored: {reason} (ticket={signal.ticket})")
                return

            # 执行风险限制检查
            if not self.risk_manager.check_risk_limits():
                self.logger.warning(f"[RISK] Risk limit reached, ignoring signal (ticket={signal.ticket})")
                return

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
        """执行新开仓信号 - 增强版（5种手数模式）"""
        try:
            # 符号映射（支持专用倍数）
            mapped_symbol, symbol_multiplier = self.risk_manager.check_symbol_mapping(signal.symbol)
            
            # 计算手数（使用配置的5种模式之一）
            account_info = mt5.account_info()
            slave_balance = account_info.balance if account_info else 0
            master_balance = getattr(signal, 'master_balance', 0)
            
            volume = self.risk_manager.calculate_lot_size(
                master_volume=signal.volume,
                master_balance=master_balance,
                slave_balance=slave_balance,
                order_index=self.order_index
            )
            
            # 应用符号专用倍数
            volume *= symbol_multiplier
            
            self.logger.info(f"[LOT] Calculation: master={signal.volume}, "
                           f"slave={volume}, "
                           f"mode={self.config.get('risk', {}).get('lot_mode')}, "
                           f"symbol_multiplier={symbol_multiplier}")
            
            # 反向交易
            if self.reverse_trading:
                order_type = OrderType.SELL if signal.order_type == OrderType.BUY else OrderType.BUY
            else:
                order_type = signal.order_type
            
            # 构建订单请求
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": mapped_symbol,
                "volume": volume,
                "type": mt5.ORDER_TYPE_BUY if order_type == OrderType.BUY else mt5.ORDER_TYPE_SELL,
                "slippage": self.slippage,
                "magic": self.magic_number,
                "comment": f"Slave:{signal.master_ticket}",
                "type_filling": mt5.ORDER_FILLING_FOK,
            }
            
            # 添加止损止盈
            if signal.sl > 0:
                request["sl"] = signal.sl
            if signal.tp > 0:
                request["tp"] = signal.tp
            
            # 发送订单
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.processed_tickets[signal.master_ticket] = result.order
                
                # 标记订单已处理（用于重复检测）
                self.risk_manager.mark_order_processed(signal.master_ticket, result.order)
                
                self.order_index += 1  # 递增订单序号（用于递增手数模式）
                
                # 更新持仓统计到风险管理器
                self._update_position_stats()
                
                self.logger.info(f"[OK] Order executed: {mapped_symbol} {order_type} "
                               f"vol={volume} ticket={result.order} "
                               f"(master={signal.master_ticket})")
            else:
                self.logger.error(f"[FAIL] Order failed: {result.comment} (retcode={result.retcode})")

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
            positions = mt5.positions_get(ticket=slave_ticket)
            if not positions:
                self.logger.warning(f"Position {slave_ticket} not found")
                return
            
            position = positions[0]
            symbol = position.symbol
            
            # 反向平仓
            close_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": position.volume,
                "type": close_type,
                "position": slave_ticket,
                "slippage": self.slippage,
                "magic": self.magic_number,
                "comment": f"Close:{signal.master_ticket}",
                "type_filling": mt5.ORDER_FILLING_FOK,
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.logger.info(f"[OK] Position closed: {symbol} ticket={slave_ticket}")
                del self.processed_tickets[signal.master_ticket]
                
                # 更新持仓统计到风险管理器
                self._update_position_stats()
            else:
                self.logger.error(f"[FAIL] Close failed: {result.comment}")

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
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": signal.symbol,
                "sl": signal.sl,
                "tp": signal.tp,
                "position": slave_ticket,
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.logger.info(f"[OK] Order modified: ticket={slave_ticket} "
                               f"sl={signal.sl} tp={signal.tp}")
            else:
                self.logger.error(f"[FAIL] Modify failed: {result.comment}")

        except Exception as e:
            self.logger.error(f"Error executing modify order: {e}")

    def _update_position_stats(self):
        """更新持仓统计到风险管理器"""
        try:
            positions = mt5.positions_get()
            if positions:
                count = len(positions)
                total_lots = sum(pos.volume for pos in positions)
                self.risk_manager.update_position_count(count, total_lots)
                self.logger.debug(f"[STATS] Positions: {count}, Total lots: {total_lots:.2f}")
            else:
                self.risk_manager.update_position_count(0, 0.0)
        except Exception as e:
            self.logger.error(f"Error updating position stats: {e}")

    def _check_trailing_stops(self):
        """检查并执行追踪止损"""
        if not self.trailing_config.get('enabled', False):
            return
        
        try:
            positions = mt5.positions_get()
            if not positions:
                return
            
            for position in positions:
                # 只处理我们自己的持仓
                if position.magic != self.magic_number:
                    continue
                
                # 计算当前盈利点数
                if position.type == mt5.ORDER_TYPE_BUY:
                    current_price = mt5.symbol_info_tick(position.symbol).bid
                    profit_points = (current_price - position.price_open) / position.point
                else:
                    current_price = mt5.symbol_info_tick(position.symbol).ask
                    profit_points = (position.price_open - current_price) / position.point
                
                # 检查是否需要触发追踪止损
                trailing_result = self.risk_manager.check_trailing_stop(
                    position.ticket, 
                    profit_points
                )
                
                if trailing_result and trailing_result.get('triggered'):
                    trail_points = trailing_result['trail_points']
                    
                    # 计算新的止损价
                    if position.type == mt5.ORDER_TYPE_BUY:
                        new_sl = current_price - (trail_points * position.point)
                        if new_sl > position.sl:  # 只允许向上移动
                            self._modify_position_sl(position.ticket, new_sl, position.tp)
                    else:
                        new_sl = current_price + (trail_points * position.point)
                        if new_sl < position.sl or position.sl == 0:  # 只允许向下移动
                            self._modify_position_sl(position.ticket, new_sl, position.tp)
        
        except Exception as e:
            self.logger.error(f"Error checking trailing stops: {e}")

    def _modify_position_sl(self, ticket: int, new_sl: float, tp: float):
        """修改持仓止损"""
        try:
            position = mt5.positions_get(ticket=ticket)[0]
            
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": position.symbol,
                "sl": new_sl,
                "tp": tp,
                "position": ticket,
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.logger.info(f"[TRAILING] SL updated: ticket={ticket}, new_sl={new_sl:.5f}")
            else:
                self.logger.error(f"[TRAILING] Failed to update SL: {result.comment}")
        
        except Exception as e:
            self.logger.error(f"Error modifying position SL: {e}")

    def run(self):
        """主运行循环"""
        self.logger.info("Starting Slave Signal Receiver (Enhanced)...")
        
        # 初始化MT5
        if not self.initialize_mt5():
            self.logger.error("Failed to initialize MT5. Exiting.")
            return

        # 连接MQTT
        self.connect_mqtt()

        # 启动MQTT循环
        try:
            # 启动追踪止损检查线程（只启动一次）
            if not self.trailing_stop_running:
                self.trailing_stop_running = True
                self.trailing_thread = threading.Thread(target=self._trailing_stop_worker, daemon=True)
                self.trailing_thread.start()
                self.logger.info("Trailing stop checker thread started")
            
            self.mqtt_client.start_loop()
        except KeyboardInterrupt:
            self.logger.info("Slave Signal Receiver stopped by user")
        except Exception as e:
            self.logger.error(f"Slave Signal Receiver error: {e}")
        finally:
            self.trailing_stop_running = False
            mt5.shutdown()
            self.mqtt_client.disconnect()

    def _trailing_stop_worker(self):
        """追踪止损工作线程"""
        while self.trailing_stop_running:
            try:
                time.sleep(10)  # 每10秒检查一次
                self._check_trailing_stops()
            except Exception as e:
                self.logger.error(f"Error in trailing stop worker: {e}")

def main():
    """入口函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MT5 Slave Signal Receiver (Enhanced)')
    parser.add_argument('--config', default='config/slave_config.json',
                       help='Path to configuration file')
    args = parser.parse_args()
    
    receiver = SlaveSignalReceiver(args.config)
    receiver.run()


if __name__ == "__main__":
    main()