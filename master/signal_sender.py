"""
Master Signal Sender Module
Monitors MT5 trades and broadcasts signals via MQTT
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
import MetaTrader5 as mt5

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.mqtt_client import MQTTClient
from common.account_reporter import AccountReporter
from common.utils import setup_logger, get_resource_path


class MasterSignalSender:
    """主服务器信号发送器（策略提供方）"""

    def __init__(self, config_path: str = "config/master_config.json"):
        """
        初始化主服务器

        Args:
            config_path: 配置文件路径
        """
        # 确定基础目录（支持 PyInstaller）
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent.parent

        # 加载配置
        config_file = base_dir / config_path
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # 合并默认配置
        self._merge_config(base_dir)

        # 确保日志文件路径是相对于 exe 目录
        if 'logging' in self.config and 'file' in self.config['logging']:
            log_file = self.config['logging']['file']
            if not os.path.isabs(log_file):
                self.config['logging']['file'] = str(base_dir / log_file)

        # 初始化所有组件
        self._init_components(base_dir)

        # 初始化账户上报器（只上报，不验证）
        self._init_account_reporter()

    def _merge_config(self, base_dir: Path):
        """合并默认配置"""
        default_config = {
            'mqtt': {
                'broker': 'localhost',
                'port': 1883,
                'client_id': 'MT5_Master_001',
                'topic_prefix': 'trademind/signals',
                'qos': 1,
                'keepalive': 60
            },
            'account_reporter': {
                'proxy_url': 'http://localhost:5000',
                'interval': 60
            },
            'common': {
                'magic_number': 123456,
                'slippage_points': 30,
                'comment_prefix': 'TM_'
            },
            'logging': {
                'file': 'logs/master.log',
                'level': 'INFO'
            }
        }

        # 递归合并配置
        def deep_merge(default: dict, custom: dict) -> dict:
            result = default.copy()
            for key, value in custom.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        self.config = deep_merge(default_config, self.config)

    def _init_components(self, base_dir: Path):
        """初始化所有组件"""
        # 设置日志
        self.logger = setup_logger(
            name="master_signal_sender",
            log_file=self.config['logging']['file'],
            level=getattr(self.config['logging'], 'level', 'INFO')
        )

        # 自动生成 Client ID（基于机器码）
        from common.utils import get_machine_code
        machine_code = get_machine_code()
        auto_client_id = f"{machine_code}_Master"
        
        # 如果配置中没有指定 client_id，使用自动生成的
        if 'client_id' not in self.config.get('mqtt', {}):
            self.config.setdefault('mqtt', {})['client_id'] = auto_client_id
            self.logger.info(f"Auto-generated client_id: {auto_client_id}")

        # 初始化MQTT客户端
        self.mqtt_client = MQTTClient(self.config['mqtt'], is_master=True)

        # MT5账户ID（从 Terminal 自动读取）
        self.mt5_account_id = None

        # 运行状态
        self.running = False
        self.connected = False

        self.logger.info("Master Signal Sender initialized")
        self.logger.info(f"Base directory: {base_dir}")

    def _init_account_reporter(self):
        """
        初始化账户上报器（只上报，不验证）
        
        注意：Master 端只上报账户信息用于监控，不进行验证和过期检查
        """
        reporter_config = self.config.get('account_reporter', {})
        
        # 获取配置
        proxy_url = reporter_config.get('proxy_url', 'http://localhost:5000')
        interval = reporter_config.get('interval', 60)
        
        # 创建上报器，不传入 on_account_disabled 回调（不进行验证）
        self.account_reporter = AccountReporter(
            proxy_url=proxy_url,
            interval=interval
            # 注意：没有 on_account_disabled 参数，所以不会触发断开
        )
        
        self.logger.debug(f"Account reporter initialized (monitoring only, interval={interval}s)")

    def initialize_mt5(self) -> bool:
        """
        初始化MT5连接
        注意：不需要登录，直接读取当前 MT5 Terminal 中已登录的账号
        """
        try:
            # 终端输出启动状态
            print(f"\n{'='*60}")
            print(f"🚀 启动 Master 信号发送器...")
            print(f"{'='*60}")
            
            # 记录启动时间
            self.start_time = time.time()
            
            # 连接到默认 Terminal
            print(f"📡 连接 MT5 终端...")
            if not mt5.initialize():
                error_code, error_msg = mt5.last_error()
                self.logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                print(f"\n❌ MT5 初始化失败!")
                print(f"   错误码: {error_code}")
                print(f"   错误信息: {error_msg}")
                print(f"{'='*60}\n")
                return False

            # 读取当前登录的账号信息
            account_info = mt5.account_info()
            if account_info is None:
                self.logger.error("Failed to get account info.")
                self.logger.error("Please ensure:")
                self.logger.error("1. MT5 Terminal is installed")
                self.logger.error("2. You are logged in to MT5")
                self.logger.error("3. MT5 Terminal is running")
                
                print(f"\n❌ 无法获取账户信息!")
                print(f"\n请确保:")
                print(f"1. 已安装 MT5 终端")
                print(f"2. MT5 终端已登录账号")
                print(f"3. MT5 终端正在运行")
                print(f"{'='*60}\n")
                return False

            self.mt5_account_id = account_info.login
            
            # 终端输出账户信息
            print(f"\n✅ MT5 连接成功!")
            print(f"   账号: {self.mt5_account_id}")
            print(f"   券商: {account_info.company}")
            print(f"   服务器: {account_info.server}")
            print(f"   余额: ${account_info.balance:.2f}")
            print(f"   净值: ${account_info.equity:.2f}")
            print(f"{'='*60}\n")
            
            self.logger.info("="*60)
            self.logger.info(f"✓ 检测到 MT5 账号: {self.mt5_account_id}")
            self.logger.info(f"  券商: {account_info.company}")
            self.logger.info(f"  服务器: {account_info.server}")
            self.logger.info(f"  余额: ${account_info.balance:.2f}")
            self.logger.info("="*60)
            
            # 设置 MQTT 认证信息（使用 MT5 账号作为 username）
            self.mqtt_client.set_credentials_from_mt5(self.mt5_account_id)
            
            # 启动账户上报器（只上报，不验证）
            if self.account_reporter:
                self.account_reporter.start(mt5_account_id=self.mt5_account_id)
                self.logger.info("Account reporter started (monitoring mode)")
            
            return True

        except Exception as e:
            self.logger.error(f"Error initializing MT5: {e}", exc_info=True)
            print(f"\n❌ MT5 初始化异常: {e}")
            print(f"{'='*60}\n")
            import traceback
            self.logger.error(f"Traceback:\n{traceback.format_exc()}")
            return False

    def connect_mqtt(self) -> bool:
        """连接到MQTT代理"""
        try:
            print(f"\n🔌 连接 MQTT 服务器...")
            success = self.mqtt_client.connect()
            if success:
                self.connected = True
                self.logger.info("Connected to MQTT broker")
                print(f"✅ MQTT 连接成功!")
            else:
                print(f"❌ MQTT 连接失败!")
            return success
        except Exception as e:
            self.logger.error(f"Error connecting to MQTT: {e}")
            print(f"❌ MQTT 连接异常: {e}")
            return False

    def send_signal(self, signal_data: Dict[str, Any]) -> bool:
        """
        发送交易信号
        
        Args:
            signal_data: 信号数据
            
        Returns:
            bool: 是否发送成功
        """
        if not self.connected:
            self.logger.warning("Not connected to MQTT, cannot send signal")
            print(f"⚠️  无法发送信号: MQTT 未连接")
            return False
        
        try:
            # 使用 strategy_id 作为主题（而不是 MT5 账号）
            strategy_id = self.config.get('strategy_id', 'DEFAULT')
            topic = f"{self.mqtt_client.topic_prefix}/{strategy_id}/trade"
            payload = json.dumps(signal_data, ensure_ascii=False)
            
            success = self.mqtt_client.publish(topic, payload, qos=1)
            
            if success:
                action = signal_data.get('action', 'UNKNOWN')
                symbol = signal_data.get('symbol', 'UNKNOWN')
                volume = signal_data.get('volume', 0)
                self.logger.info(f"✓ Signal sent: {action} {symbol} {volume} [Strategy: {strategy_id}]")
                print(f"📤 信号已发送: {action} {symbol} {volume}")
            else:
                self.logger.error("✗ Failed to send signal")
                print(f"❌ 信号发送失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending signal: {e}", exc_info=True)
            print(f"❌ 信号发送异常: {e}")
            return False

    def run(self):
        """运行主循环 - 自适应轮询策略"""
        self.logger.info("Starting Master Signal Sender...")
        self.running = True
        
        print(f"\n{'='*60}")
        print(f"📦 MT5 Master 信号发送器")
        print(f"{'='*60}")
        
        if not self.initialize_mt5():
            self.logger.error("Failed to initialize MT5")
            print(f"\n❌ Master 启动失败: MT5 初始化失败")
            print(f"{'='*60}\n")
            return
        
        if not self.connect_mqtt():
            self.logger.error("Failed to connect to MQTT")
            print(f"\n❌ Master 启动失败: MQTT 连接失败")
            print(f"{'='*60}\n")
            return
        
        self.logger.info("Master Signal Sender is running...")
        self.logger.info("Adaptive polling strategy activated")
        self.logger.info("- Orders/Positions: 0.1s (ultra-high frequency)")
        self.logger.info("- History deals: 1.0s (medium frequency)")
        self.logger.info("- Account info: 5.0s (low frequency)")
        
        print(f"\n✅ Master 启动成功!")
        print(f"   账号: {self.mt5_account_id}")
        print(f"   MQTT: 已连接")
        print(f"   监控策略: 自适应轮询（0.1s/1s/5s）")
        print(f"{'='*60}\n")
        
        # 心跳文件路径
        if getattr(sys, 'frozen', False):
            heartbeat_file = Path(sys.executable).parent / 'logs' / 'master.heartbeat'
        else:
            heartbeat_file = Path(__file__).parent.parent / 'logs' / 'master.heartbeat'
        
        try:
            last_heartbeat = time.time()
            last_history_check = time.time()
            last_account_check = time.time()
            
            # 订单监控状态
            last_orders = {}
            last_positions = {}
            last_deals = set()
            last_history_orders = set()
            
            # 检测是否有活跃交易（用于动态调整频率）
            has_active_trading = False
            
            while self.running:
                current_time = time.time()
                
                # === 1. 心跳日志（30 秒）===
                if current_time - last_heartbeat >= 30:
                    elapsed = int(current_time - self.start_time)
                    hours = elapsed // 3600
                    minutes = (elapsed % 3600) // 60
                    seconds = elapsed % 60
                    
                    self.logger.info(f"💓 Heartbeat - {hours}h {minutes}m {seconds}s | "
                                   f"Account: {self.mt5_account_id} | "
                                   f"MQTT: {'Connected' if self.connected else 'Disconnected'} | "
                                   f"Active Trading: {has_active_trading}")
                    
                    try:
                        heartbeat_file.parent.mkdir(exist_ok=True)
                        with open(heartbeat_file, 'w', encoding='utf-8') as f:
                            f.write(f"{current_time}\n")
                            f.write(f"account_id={self.mt5_account_id}\n")
                            f.write(f"mqtt_connected={self.connected}\n")
                            f.write(f"uptime={elapsed}\n")
                            f.write(f"active_trading={has_active_trading}\n")
                    except Exception as e:
                        self.logger.debug(f"Failed to write heartbeat file: {e}")
                    
                    last_heartbeat = current_time
                
                # === 2. 实时监控挂单和持仓（0.1 秒 - 超高频）===
                trading_detected = self.monitor_trades_ultra_fast(last_orders, last_positions)
                if trading_detected:
                    has_active_trading = True
                
                # === 3. 监控历史成交（1 秒 - 中频）===
                if current_time - last_history_check >= 1.0:
                    self.monitor_history_deals(last_deals, last_history_orders)
                    last_history_check = current_time
                
                # === 4. 监控账户信息（5 秒 - 低频）===
                if current_time - last_account_check >= 5.0:
                    self.check_account_status()
                    last_account_check = current_time
                
                # === 5. 如果没有活跃交易，降低频率到 0.5 秒 ===
                sleep_time = 0.1 if has_active_trading else 0.5
                time.sleep(sleep_time)
                
                # 重置活跃交易标志（如果一段时间没有检测到变化）
                if has_active_trading and current_time - last_heartbeat > 10:
                    has_active_trading = False
                
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
            print(f"\n⚠️  收到关闭信号，正在停止...")
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}", exc_info=True)
            print(f"\n❌ 发生错误: {e}")
        finally:
            self.shutdown()

    def monitor_trades_ultra_fast(self, last_orders: dict, last_positions: dict) -> bool:
        """
        超高频监控挂单和持仓（0.1 秒间隔）
        
        Returns:
            bool: 是否检测到交易活动
        """
        trading_detected = False
        
        try:
            # 1. 监控挂单
            orders = mt5.orders_get()
            if orders:
                current_orders = {order.ticket: order for order in orders}
                trading_detected = True
                
                # 新挂单
                for ticket, order in current_orders.items():
                    if ticket not in last_orders:
                        self.logger.info(f"🆕 NEW PENDING ORDER: {ticket}")
                        print(f"📋 [0.1s] 新挂单: {order.symbol} {self._order_type_to_str(order.type)} "
                              f"vol={order.volume_current} price={order.price_open}")
                        
                        self.send_signal({
                            'signal_type': 'order',
                            'action': 'pending_order',
                            'order_type': order.type,
                            'symbol': order.symbol,
                            'volume': order.volume_current,
                            'price': order.price_open,
                            'sl': order.sl,
                            'tp': order.tp,
                            'magic': order.magic,
                            'comment': order.comment,
                            'ticket': ticket,
                            'timestamp': time.time()
                        })
                
                # 挂单修改
                for ticket, order in current_orders.items():
                    if ticket in last_orders:
                        last_order = last_orders[ticket]
                        changes = []
                        
                        if abs(order.price_open - last_order.price_open) > 0.00001:
                            changes.append(f"price:{last_order.price_open:.5f}→{order.price_open:.5f}")
                        if abs(order.sl - last_order.sl) > 0.00001:
                            changes.append(f"SL:{last_order.sl:.5f}→{order.sl:.5f}")
                        if abs(order.tp - last_order.tp) > 0.00001:
                            changes.append(f"TP:{last_order.tp:.5f}→{order.tp:.5f}")
                        
                        if changes:
                            self.logger.info(f"✏️ PENDING MODIFIED: {ticket}")
                            print(f"✏️ [0.1s] 挂单修改: {order.symbol} #{ticket} | {', '.join(changes)}")
                            
                            self.send_signal({
                                'signal_type': 'modify',
                                'action': 'modify_pending',
                                'ticket': ticket,
                                'symbol': order.symbol,
                                'price': order.price_open,
                                'sl': order.sl,
                                'tp': order.tp,
                                'timestamp': time.time()
                            })
                
                # 挂单删除
                for ticket in last_orders:
                    if ticket not in current_orders:
                        self.logger.info(f"🗑️ PENDING DELETED: {ticket}")
                        print(f"🗑️ [0.1s] 挂单删除: #{ticket}")
                        
                        self.send_signal({
                            'signal_type': 'close',
                            'action': 'delete_pending',
                            'ticket': ticket,
                            'timestamp': time.time()
                        })
                
                last_orders.clear()
                last_orders.update(current_orders)
            
            # 2. 监控持仓
            positions = mt5.positions_get()
            if positions:
                current_positions = {pos.ticket: pos for pos in positions}
                trading_detected = True
                
                # 新开仓
                for ticket, pos in current_positions.items():
                    if ticket not in last_positions:
                        self.logger.info(f"🚀 NEW POSITION: {ticket}")
                        print(f"📈 [0.1s] 新开仓: {pos.symbol} {self._position_type_to_str(pos.type)} "
                              f"vol={pos.volume} price={pos.price_open:.5f}")
                        
                        self.send_signal({
                            'signal_type': 'order',
                            'action': 'position_open',
                            'order_type': pos.type,
                            'symbol': pos.symbol,
                            'volume': pos.volume,
                            'price': pos.price_open,
                            'sl': pos.sl,
                            'tp': pos.tp,
                            'magic': pos.magic,
                            'comment': pos.comment,
                            'ticket': ticket,
                            'timestamp': time.time()
                        })
                
                # 持仓修改（SL/TP）
                for ticket, pos in current_positions.items():
                    if ticket in last_positions:
                        last_pos = last_positions[ticket]
                        changes = []
                        
                        if abs(pos.sl - last_pos.sl) > 0.00001:
                            changes.append(f"SL:{last_pos.sl:.5f}→{pos.sl:.5f}")
                        if abs(pos.tp - last_pos.tp) > 0.00001:
                            changes.append(f"TP:{last_pos.tp:.5f}→{pos.tp:.5f}")
                        
                        if changes:
                            self.logger.info(f"✏️ POSITION MODIFIED: {ticket}")
                            print(f"✏️ [0.1s] 持仓修改: {pos.symbol} #{ticket} | {', '.join(changes)}")
                            
                            self.send_signal({
                                'signal_type': 'modify',
                                'action': 'modify_position',
                                'ticket': ticket,
                                'symbol': pos.symbol,
                                'sl': pos.sl,
                                'tp': pos.tp,
                                'timestamp': time.time()
                            })
                
                # 持仓修改（手数变化 = 部分平仓）
                for ticket, pos in current_positions.items():
                    if ticket in last_positions:
                        last_pos = last_positions[ticket]
                        
                        # 检测部分平仓（手数减少）
                        if pos.volume < last_pos.volume:
                            closed_volume = last_pos.volume - pos.volume
                            self.logger.info(f"📊 PARTIAL CLOSE: {ticket} vol={closed_volume}")
                            print(f"📊 [0.1s] 部分平仓: {pos.symbol} #{ticket} 平{closed_volume} 剩{pos.volume}")
                            
                            self.send_signal({
                                'signal_type': 'close',
                                'action': 'partial_close',
                                'ticket': ticket,
                                'symbol': pos.symbol,
                                'volume': closed_volume,  # 平仓数量
                                'remaining_volume': pos.volume,  # 剩余数量
                                'timestamp': time.time()
                            })
                
                # 平仓
                for ticket in last_positions:
                    if ticket not in current_positions:
                        self.logger.info(f"📉 POSITION CLOSED: {ticket}")
                        print(f"📉 [0.1s] 平仓: #{ticket}")
                        
                        deal_info = self._get_close_deal_info(ticket)
                        
                        self.send_signal({
                            'signal_type': 'close',
                            'action': 'close_position',
                            'ticket': ticket,
                            'close_price': deal_info.get('price', 0),
                            'profit': deal_info.get('profit', 0),
                            'commission': deal_info.get('commission', 0),
                            'swap': deal_info.get('swap', 0),
                            'timestamp': time.time()
                        })
                
                last_positions.clear()
                last_positions.update(current_positions)
            
            return trading_detected
            
        except Exception as e:
            self.logger.error(f"Error in ultra-fast monitoring: {e}", exc_info=True)
            return False

    def check_account_status(self):
        """检查账户状态（余额、净值等）"""
        try:
            account_info = mt5.account_info()
            if account_info:
                self.logger.info(f"💰 Account: Balance=${account_info.balance:.2f} "
                               f"Equity=${account_info.equity:.2f} "
                               f"Profit=${account_info.profit:.2f}")
        except Exception as e:
            self.logger.debug(f"Failed to check account status: {e}")

    def monitor_history_deals(self, last_deals: set, last_history_orders: set):
        """
        监控历史成交记录（检测挂单成交、部分成交等）
        
        Args:
            last_deals: 已处理的成交单 ID 集合
            last_history_orders: 已处理的历史订单 ID 集合
        """
        try:
            # 获取最近的成交记录（过去 10 秒）
            from datetime import datetime, timedelta
            time_from = datetime.now() - timedelta(seconds=10)
            time_to = datetime.now()
            
            deals = mt5.history_deals_get(time_from, time_to)
            if deals:
                for deal in deals:
                    if deal.deal not in last_deals:
                        last_deals.add(deal.deal)
                        
                        # 判断成交类型
                        if deal.entry == mt5.DEAL_ENTRY_IN:
                            # 开仓成交
                            self.logger.info(f"💰 Deal IN: {deal.symbol} deal={deal.deal} volume={deal.volume}")
                            print(f"💰 成交开仓: {deal.symbol} vol={deal.volume} price={deal.price}")
                        
                        elif deal.entry == mt5.DEAL_ENTRY_OUT:
                            # 平仓成交
                            self.logger.info(f"💸 Deal OUT: {deal.symbol} deal={deal.deal} profit={deal.profit}")
                            print(f"💸 成交平仓: {deal.symbol} profit=${deal.profit:.2f}")
                        
                        elif deal.entry == mt5.DEAL_ENTRY_INOUT:
                            # 反向开仓（先平后开）
                            self.logger.info(f"🔄 Deal INOUT: {deal.symbol} deal={deal.deal}")
                            print(f"🔄 反向开仓: {deal.symbol}")
            
            # 限制集合大小，避免内存泄漏
            if len(last_deals) > 1000:
                # 保留最近 500 个
                deals_list = sorted(last_deals)[-500:]
                last_deals.clear()
                last_deals.update(deals_list)
            
        except Exception as e:
            self.logger.error(f"Error monitoring history deals: {e}", exc_info=True)

    def _get_close_deal_info(self, position_ticket: int) -> dict:
        """获取平仓成交的详细信息"""
        try:
            from datetime import datetime, timedelta
            time_from = datetime.now() - timedelta(seconds=30)
            time_to = datetime.now()
            
            deals = mt5.history_deals_get(time_from, time_to)
            if deals:
                for deal in deals:
                    if deal.position_id == position_ticket and deal.entry == mt5.DEAL_ENTRY_OUT:
                        return {
                            'price': deal.price,
                            'profit': deal.profit,
                            'commission': deal.commission,
                            'swap': deal.swap
                        }
        except Exception as e:
            self.logger.debug(f"Failed to get close deal info: {e}")
        
        return {}

    def _order_type_to_str(self, order_type: int) -> str:
        """将订单类型转换为字符串"""
        type_map = {
            0: "BUY",
            1: "SELL",
            2: "BUY_LIMIT",
            3: "SELL_LIMIT",
            4: "BUY_STOP",
            5: "SELL_STOP"
        }
        return type_map.get(order_type, f"UNKNOWN({order_type})")

    def _position_type_to_str(self, position_type: int) -> str:
        """将持仓类型转换为字符串"""
        return "BUY" if position_type == 0 else "SELL"

    def shutdown(self):
        """关闭服务"""
        self.logger.info("Shutting down Master Signal Sender...")
        print(f"\n{'='*60}")
        print(f"⏹️  Master 正在关闭...")
        self.running = False
        
        # 停止账户上报器
        if self.account_reporter:
            self.account_reporter.stop()
        
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        
        mt5.shutdown()
        self.logger.info("Master Signal Sender stopped")
        print(f"✅ Master 已关闭")
        print(f"{'='*60}\n")


def main():
    """主函数"""
    sender = MasterSignalSender()
    sender.run()


if __name__ == "__main__":
    main()











