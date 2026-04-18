"""
Slave Signal Receiver Module
Receives trading signals via MQTT and executes trades on multiple MT5 terminals
支持多个券商终端，每个账号独立进程
"""

import sys
import os
import json
import time
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
import MetaTrader5 as mt5

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.mqtt_client import MQTTClient
from common.account_reporter import AccountReporter
from common.utils import setup_logger, get_resource_path


class SlaveSignalReceiver:
    """从服务器信号接收器 - 支持多账号多终端"""

    def __init__(self, config_path: str = "config/slave_config.json", 
                 mt5_login: Optional[int] = None,
                 mt5_password: str = "",
                 mt5_server: str = ""):
        """
        初始化从服务器

        Args:
            config_path: 配置文件路径
            mt5_login: MT5 登录账号（可选，如果配置中未指定）
            mt5_password: MT5 密码（可选）
            mt5_server: MT5 服务器（可选）
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

        # 保存命令行参数（优先级高于配置）
        self.mt5_login_override = mt5_login
        self.mt5_password_override = mt5_password
        self.mt5_server_override = mt5_server

        # MT5 账号信息（从 Terminal 自动读取）
        self.mt5_account_id = None

        # 初始化账户上报器
        self._init_account_reporter()

    def _merge_config(self, base_dir: Path):
        """合并默认配置"""
        default_config = {
            'mqtt': {
                'broker': 'localhost',
                'port': 1883,
                'client_id': 'MT5_Slave_001',
                'topic_prefix': 'trademind/signals',
                'qos': 1,
                'keepalive': 60
            },
            'account_reporter': {
                'proxy_url': 'http://localhost:5000',
                'interval': 60
            },
            'common': {
                'follow_mode': 'both',
                'enable_alerts': True,
                'stop_alert_on_price': False,
                'reverse_trading': False,
                'magic_number': 999999,
                'slippage_points': 30,
                'lot_multiplier': 1.0,
                'max_lot': 100.0,
                'comment_prefix': 'TM_'
            },
            'risk_management': {
                'max_daily_loss': 1000.0,
                'max_drawdown_percent': 20.0,
                'max_positions': 10,
                'min_balance': 1000.0
            },
            'symbol_mapping': {},
            'logging': {
                'file': 'logs/slave.log',
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
            name="slave_signal_receiver",
            log_file=self.config['logging']['file'],
            level=getattr(self.config['logging'], 'level', 'INFO')
        )

        # 自动生成 Client ID（基于机器码）
        from common.utils import get_machine_code
        machine_code = get_machine_code()
        auto_client_id = f"{machine_code}_Slave"
        
        # 如果配置中没有指定 client_id，使用自动生成的
        if 'client_id' not in self.config.get('mqtt', {}):
            self.config.setdefault('mqtt', {})['client_id'] = auto_client_id
            self.logger.info(f"Auto-generated client_id: {auto_client_id}")

        # 初始化MQTT客户端
        self.mqtt_client = MQTTClient(self.config['mqtt'], is_master=False)

        # 设置消息回调
        self.mqtt_client.set_message_callback(self.on_message)

        # 风险管理器
        from slave.risk_manager import RiskManager
        self.risk_manager = RiskManager(self.config)

        # 品种映射器
        from slave.symbol_mapper import SymbolMapper
        self.symbol_mapper = SymbolMapper(self.config.get('symbol_mapping', {}))

        # 连接状态
        self.connected = False
        self.running = False

        self.logger.info("Slave Signal Receiver initialized")
        self.logger.info(f"Base directory: {base_dir}")

    def _init_account_reporter(self):
        """初始化账户上报器（强制启用，用户无感知）"""
        reporter_config = self.config.get('account_reporter', {})
        
        # 获取配置（默认启用，不可关闭）
        proxy_url = reporter_config.get('proxy_url', 'http://localhost:5000')
        interval = reporter_config.get('interval', 60)
        
        # 强制创建上报器，传入账户禁用回调
        self.account_reporter = AccountReporter(
            proxy_url=proxy_url,
            interval=interval,
            on_account_disabled=self._on_account_disabled
        )
        
        self.logger.debug(f"Account reporter initialized (interval={interval}s)")

    def _on_account_disabled(self, reason: str):
        """
        账户被禁用时的回调处理
        
        Args:
            reason: 禁用原因
        """
        # 终端输出
        print(f"\n{'='*60}")
        print(f"⚠️  账户已被禁用: {reason}")
        print(f"{'='*60}")
        
        self.logger.error(f"⚠️  ACCOUNT DISABLED: {reason}")
        self.logger.error("Stopping all trading activities...")
        
        # 1. 停止接收新信号
        self.running = False
        
        # 2. 断开 MQTT 连接
        if self.mqtt_client:
            self.logger.info("Disconnecting from MQTT...")
            self.mqtt_client.disconnect()
        
        # 3. 平仓所有持仓（可选，根据风控策略）
        try:
            positions = mt5.positions_get()
            if positions:
                self.logger.warning(f"Closing {len(positions)} open positions...")
                for position in positions:
                    self.logger.info(f"Position {position.ticket}: {position.type} {position.volume} {position.symbol}")
                    # 这里可以添加实际平仓逻辑
        except Exception as e:
            self.logger.error(f"Error checking positions: {e}")
        
        # 4. 终端提示
        print(f"\n⚠️  所有交易活动已停止")
        print(f"⚠️  程序将在 10 秒后退出...")
        print(f"{'='*60}\n")
        
        # 5. 退出程序
        self.logger.error("Program will exit in 10 seconds...")
        import sys
        time.sleep(10)
        sys.exit(1)

    def initialize_mt5(self) -> bool:
        """
        初始化MT5连接
        注意：不需要登录，直接读取当前 MT5 Terminal 中已登录的账号
        支持指定 Terminal 路径（不同券商的终端）
        """
        try:
            # 终端输出启动状态
            print(f"\n{'='*60}")
            print(f"🚀 启动 Slave 信号接收器...")
            print(f"{'='*60}")
            
            self.logger.info("Attempting to initialize MetaTrader5...")
            self.logger.info(f"Python executable: {sys.executable}")
            self.logger.info(f"Current working directory: {os.getcwd()}")
            
            # 获取 Terminal 路径（从配置或命令行参数）
            terminal_path = self.config.get('mt5_terminal_path')
            
            if terminal_path:
                self.logger.info(f"Connecting to MT5 Terminal: {terminal_path}")
                print(f"📡 连接 MT5 终端: {terminal_path}")
                initialized = mt5.initialize(path=terminal_path)
            else:
                self.logger.info("Connecting to default MT5 Terminal")
                print(f"📡 连接默认 MT5 终端")
                initialized = mt5.initialize()
            
            self.logger.info(f"MT5 initialize() returned: {initialized}")
            
            if not initialized:
                error_code, error_msg = mt5.last_error()
                self.logger.error(f"MT5 initialization failed!")
                self.logger.error(f"Error code: {error_code}")
                self.logger.error(f"Error message: {error_msg}")
                self.logger.error("Please ensure:")
                self.logger.error("1. MT5 Terminal is installed")
                self.logger.error("2. You are logged in to MT5")
                self.logger.error("3. MT5 Terminal is running")
                
                # 终端输出
                print(f"\n❌ MT5 初始化失败!")
                print(f"   错误码: {error_code}")
                print(f"   错误信息: {error_msg}")
                print(f"\n请确保:")
                print(f"1. 已安装 MT5 终端")
                print(f"2. MT5 终端已登录账号")
                print(f"3. MT5 终端正在运行")
                print(f"{'='*60}\n")
                return False

            # 直接读取当前登录的账号信息（不需要 login）
            account_info = mt5.account_info()
            if account_info is None:
                error_code, error_msg = mt5.last_error()
                self.logger.error("Failed to get account info.")
                self.logger.error(f"Error code: {error_code}")
                self.logger.error(f"Error message: {error_msg}")
                self.logger.error("Please ensure you are logged in to MT5 Terminal.")
                
                # 终端输出
                print(f"\n❌ 无法获取账户信息!")
                print(f"   错误码: {error_code}")
                print(f"   错误信息: {error_msg}")
                print(f"\n请确保 MT5 终端已登录账号")
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
            self.logger.info(f"  净值: ${account_info.equity:.2f}")
            self.logger.info("="*60)
            
            # 设置 MQTT 认证信息（使用 MT5 账号作为 username）
            self.mqtt_client.set_credentials_from_mt5(self.mt5_account_id)
            
            # 自动启动账户上报器（静默运行）
            if self.account_reporter:
                self.account_reporter.start(mt5_account_id=self.mt5_account_id)
            
            return True

        except Exception as e:
            self.logger.error(f"Error initializing MT5: {e}", exc_info=True)
            print(f"\n❌ MT5 初始化异常: {e}")
            print(f"{'='*60}\n")
            return False

    def connect_mqtt(self) -> bool:
        """连接到MQTT代理"""
        try:
            print(f"\n🔌 连接 MQTT 服务器...")
            
            # 使用 strategy_id 订阅（统一频道）
            strategy_id = self.config.get('strategy_id')
            if not strategy_id:
                self.logger.error("strategy_id not configured!")
                self.logger.error("Please add 'strategy_id' to config (e.g., 'STRATEGY_001')")
                print(f"❌ 未配置 strategy_id!")
                print(f"   请在配置文件中添加:")
                print(f'   "strategy_id": "STRATEGY_001"')
                return False

            topic = f"{self.config['mqtt']['topic_prefix']}/{strategy_id}/#"
            success = self.mqtt_client.connect_and_subscribe(topic)
            
            if success:
                self.connected = True
                self.logger.info(f"Subscribed to strategy: {strategy_id}")
                print(f"✅ MQTT 连接成功!")
                print(f"   订阅策略: {strategy_id}")
            else:
                print(f"❌ MQTT 连接失败!")
                self.logger.error("MQTT connection failed!")
            
            return success

        except Exception as e:
            self.logger.error(f"Error connecting to MQTT: {e}", exc_info=True)
            print(f"❌ MQTT 连接异常: {e}")
            return False

    def on_message(self, topic: str, payload: Dict[str, Any]):
        """
        处理接收到的消息

        Args:
            topic: MQTT主题
            payload: 消息内容
        """
        try:
            signal_type = payload.get('signal_type')
            
            if signal_type == 'order':
                self.handle_order_signal(payload)
            elif signal_type == 'modify':
                self.handle_modify_signal(payload)
            elif signal_type == 'close':
                self.handle_close_signal(payload)
            else:
                self.logger.warning(f"Unknown signal type: {signal_type}")

        except Exception as e:
            self.logger.error(f"Error processing message: {e}", exc_info=True)

    def handle_order_signal(self, payload: Dict[str, Any]):
        """处理订单信号"""
        try:
            # === 风控检查 ===
            if not self.risk_manager.check_risk_limits():
                reason = self.risk_manager.risk_status.blocked_reason
                self.logger.warning(f"Risk limits exceeded: {reason}")
                print(f"\n📥 收到交易信号: {payload.get('symbol', 'UNKNOWN')}")
                print(f"   ⚠️  风控限制，忽略信号: {reason}")
                return
            
            allowed, filter_reason = self.risk_manager.check_order_filter(payload)
            if not allowed:
                self.logger.info(f"Order filtered: {filter_reason}")
                print(f"\n📥 收到交易信号: {payload.get('symbol', 'UNKNOWN')}")
                print(f"   ⚠️  订单被过滤: {filter_reason}")
                return

            order_type = payload.get('order_type')
            symbol = payload.get('symbol')
            volume = payload.get('volume', 0.01)
            price = payload.get('price', 0.0)
            sl = payload.get('sl', 0.0)
            tp = payload.get('tp', 0.0)
            magic = payload.get('magic', 0)
            comment = payload.get('comment', '')
            master_ticket = payload.get('ticket', 0)

            print(f"\n📥 收到交易信号: {symbol}")

            # === 品种映射 ===
            mapped_symbol, symbol_lot_multiplier = self.risk_manager.check_symbol_mapping(symbol)
            if not mapped_symbol:
                self.logger.error(f"Symbol mapping failed for: {symbol}")
                print(f"   ❌ 品种映射失败: {symbol}")
                return

            # === 手数计算 ===
            try:
                account_info = mt5.account_info()
                slave_balance = account_info.balance if account_info else 0.0
            except:
                slave_balance = 0.0
            
            order_index = len(self.risk_manager.processed_orders)
            calculated_lot = self.risk_manager.calculate_lot_size(
                master_volume=volume,
                slave_balance=slave_balance,
                order_index=order_index
            )
            
            adjusted_volume = calculated_lot * symbol_lot_multiplier
            
            if abs(adjusted_volume - volume) > 0.001:
                print(f"   📊 手数调整: {volume} → {adjusted_volume:.2f}")

            # === 执行交易 ===
            result = self.execute_order(
                order_type=order_type,
                symbol=mapped_symbol,
                volume=adjusted_volume,
                price=price,
                sl=sl,
                tp=tp,
                magic=magic,
                comment=comment
            )

            if result:
                self.logger.info(f"Order executed: {mapped_symbol} {adjusted_volume}")
                print(f"   ✅ 订单执行成功: {mapped_symbol} {adjusted_volume}")
                
                if master_ticket:
                    self.risk_manager.mark_order_processed(master_ticket, result)
            else:
                self.logger.error(f"Order execution failed: {mapped_symbol}")
                print(f"   ❌ 订单执行失败: {mapped_symbol}")

        except Exception as e:
            self.logger.error(f"Error handling order signal: {e}", exc_info=True)
            print(f"   ❌ 处理订单信号异常: {e}")

    def execute_order(self, order_type: int, symbol: str, volume: float,
                     price: float = 0.0, sl: float = 0.0, tp: float = 0.0,
                     magic: int = 0, comment: str = '') -> Optional[int]:
        """
        执行订单

        Returns:
            int: 订单号（成功）或 None（失败）
        """
        try:
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "type_filling": mt5.ORDER_FILLING_IOC,
                "deviation": self.config.get('common', {}).get('slippage_points', 30),
                "magic": magic if magic != 0 else self.config.get('common', {}).get('magic_number', 999999),
                "comment": comment if comment else self.config.get('common', {}).get('comment_prefix', 'TM_'),
            }

            if price > 0:
                request["price"] = price
            if sl > 0:
                request["sl"] = sl
            if tp > 0:
                request["tp"] = tp

            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"Order failed: {result.comment} (code: {result.retcode})")
                print(f"   ❌ 订单失败: {result.comment} (代码: {result.retcode})")
                return None

            self.logger.info(f"Order sent: ticket={result.order}")
            print(f"   📤 订单已发送: ticket={result.order}")
            return result.order

        except Exception as e:
            self.logger.error(f"Error executing order: {e}", exc_info=True)
            print(f"   ❌ 执行订单异常: {e}")
            return None

    def handle_modify_signal(self, payload: Dict[str, Any]):
        """处理修改信号"""
        try:
            action = payload.get('action')
            ticket = payload.get('ticket')
            
            print(f"\n📥 收到修改信号: {action} ticket={ticket}")
            
            if not ticket:
                self.logger.error("Missing ticket in modify signal")
                print(f"   ❌ 缺少订单号")
                return
            
            if action == 'modify_pending':
                # 修改挂单
                price = payload.get('price', 0.0)
                sl = payload.get('sl', 0.0)
                tp = payload.get('tp', 0.0)
                
                request = {
                    "action": mt5.TRADE_ACTION_MODIFY,
                    "order": ticket,
                }
                
                if price > 0:
                    request["price"] = price
                if sl > 0:
                    request["sl"] = sl
                if tp > 0:
                    request["tp"] = tp
                
                result = mt5.order_send(request)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    self.logger.info(f"Pending order modified: ticket={ticket}")
                    print(f"   ✅ 挂单修改成功")
                else:
                    self.logger.error(f"Modify failed: {result.comment}")
                    print(f"   ❌ 挂单修改失败: {result.comment}")
            
            elif action == 'modify_position':
                # 修改持仓（止损/止盈）
                sl = payload.get('sl', 0.0)
                tp = payload.get('tp', 0.0)
                
                # 获取持仓信息
                positions = mt5.positions_get(ticket=ticket)
                if not positions:
                    self.logger.error(f"Position not found: {ticket}")
                    print(f"   ❌ 未找到持仓: {ticket}")
                    return
                
                pos = positions[0]
                
                request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "position": ticket,
                    "sl": sl if sl > 0 else pos.sl,
                    "tp": tp if tp > 0 else pos.tp,
                }
                
                result = mt5.order_send(request)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    self.logger.info(f"Position SL/TP modified: ticket={ticket}")
                    print(f"   ✅ 持仓止损/止盈修改成功")
                else:
                    self.logger.error(f"Modify SL/TP failed: {result.comment}")
                    print(f"   ❌ 修改止损/止盈失败: {result.comment}")
            
            elif action == 'delete_pending':
                # 删除挂单
                request = {
                    "action": mt5.TRADE_ACTION_REMOVE,
                    "order": ticket,
                }
                
                result = mt5.order_send(request)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    self.logger.info(f"Pending order deleted: ticket={ticket}")
                    print(f"   ✅ 挂单删除成功")
                else:
                    self.logger.error(f"Delete failed: {result.comment}")
                    print(f"   ❌ 挂单删除失败: {result.comment}")
        
        except Exception as e:
            self.logger.error(f"Error handling modify signal: {e}", exc_info=True)
            print(f"   ❌ 处理修改信号异常: {e}")

    def handle_close_signal(self, payload: Dict[str, Any]):
        """处理平仓信号"""
        try:
            action = payload.get('action')
            ticket = payload.get('ticket')
            
            print(f"\n📥 收到平仓信号: {action} ticket={ticket}")
            
            if not ticket:
                self.logger.error("Missing ticket in close signal")
                print(f"   ❌ 缺少订单号")
                return
            
            if action == 'position_close':
                # 平仓
                positions = mt5.positions_get(ticket=ticket)
                if not positions:
                    self.logger.error(f"Position not found: {ticket}")
                    print(f"   ❌ 未找到持仓: {ticket}")
                    return
                
                pos = positions[0]
                
                # 构建平仓请求
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": pos.symbol,
                    "volume": pos.volume,
                    "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                    "position": ticket,
                    "deviation": self.config.get('common', {}).get('slippage_points', 30),
                    "magic": pos.magic,
                    "comment": pos.comment,
                }
                
                result = mt5.order_send(request)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    self.logger.info(f"Position closed: ticket={ticket}")
                    print(f"   ✅ 平仓成功")
                else:
                    self.logger.error(f"Close failed: {result.comment}")
                    print(f"   ❌ 平仓失败: {result.comment}")
            
            elif action == 'delete_pending':
                # 删除挂单（已经在 handle_modify_signal 中处理）
                self.logger.info(f"Pending order delete signal received: {ticket}")
                print(f"   ℹ️  收到挂单删除信号")
        
        except Exception as e:
            self.logger.error(f"Error handling close signal: {e}", exc_info=True)
            print(f"   ❌ 处理平仓信号异常: {e}")

    def run(self):
        """运行从服务器"""
        self.logger.info("="*60)
        self.logger.info("Starting MT5 Slave Signal Receiver")
        self.logger.info("="*60)
        
        # 终端输出
        print(f"\n{'='*60}")
        print(f"📦 MT5 Slave 信号接收器")
        print(f"{'='*60}")

        # 初始化MT5
        if not self.initialize_mt5():
            self.logger.error("Failed to initialize MT5")
            print(f"\n❌ Slave 启动失败: MT5 初始化失败")
            print(f"{'='*60}\n")
            return

        # 连接MQTT
        if not self.connect_mqtt():
            self.logger.error("Failed to connect to MQTT")
            print(f"\n❌ Slave 启动失败: MQTT 连接失败")
            print(f"{'='*60}\n")
            return

        self.running = True
        self.logger.info("Slave receiver started successfully")
        self.logger.info("Heartbeat started (every 30 seconds)")
        
        # 终端输出启动成功
        print(f"\n✅ Slave 启动成功!")
        print(f"   账号: {self.mt5_account_id}")
        print(f"   MQTT: 已连接")
        print(f"   状态: 等待交易信号...")
        print(f"{'='*60}\n")
        
        # 记录启动时间
        self.start_time = time.time()
        
        # 创建心跳文件路径
        if getattr(sys, 'frozen', False):
            heartbeat_file = Path(sys.executable).parent / 'logs' / 'slave.heartbeat'
        else:
            heartbeat_file = Path(__file__).parent.parent / 'logs' / 'slave.heartbeat'

        try:
            last_heartbeat = time.time()
            heartbeat_interval = 30
            last_position_update = time.time()
            
            while self.running:
                current_time = time.time()
                
                if current_time - last_heartbeat >= heartbeat_interval:
                    elapsed = int(current_time - self.start_time)
                    hours = elapsed // 3600
                    minutes = (elapsed % 3600) // 60
                    seconds = elapsed % 60
                    
                    positions = mt5.positions_get()
                    position_count = len(positions) if positions else 0
                    total_lots = sum(pos.volume for pos in positions) if positions else 0
                    
                    self.risk_manager.update_position_count(position_count, total_lots)
                    
                    self.logger.info(f"💓 Heartbeat - {hours}h {minutes}m {seconds}s | "
                                   f"Account: {self.mt5_account_id} | "
                                   f"Positions: {position_count} ({total_lots:.2f} lots)")
                    
                    try:
                        heartbeat_file.parent.mkdir(exist_ok=True)
                        with open(heartbeat_file, 'w', encoding='utf-8') as f:
                            f.write(f"{current_time}\n")
                            f.write(f"account_id={self.mt5_account_id}\n")
                            f.write(f"mqtt_connected={self.connected}\n")
                            f.write(f"uptime={elapsed}\n")
                            f.write(f"master_account={self.config.get('master_account', 'N/A')}\n")
                            f.write(f"positions={position_count}\n")
                            f.write(f"total_lots={total_lots:.2f}\n")
                    except Exception as e:
                        self.logger.debug(f"Failed to write heartbeat file: {e}")
                    
                    last_heartbeat = current_time
                
                if current_time - last_position_update >= 5.0:
                    try:
                        positions = mt5.positions_get()
                        if positions is not None:
                            position_count = len(positions)
                            total_lots = sum(pos.volume for pos in positions)
                            self.risk_manager.update_position_count(position_count, total_lots)
                    except:
                        pass
                    last_position_update = current_time
                
                time.sleep(1)
                
                if not self.mqtt_client.is_connected():
                    self.logger.warning("MQTT disconnected, reconnecting...")
                    print(f"⚠️  MQTT 断开连接，正在重连...")
                    self.connect_mqtt()
        except KeyboardInterrupt:
            self.logger.info("Shutdown requested by user")
            print(f"\n⚠️  收到关闭信号，正在停止...")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}", exc_info=True)
            print(f"\n❌ 发生错误: {e}")
        finally:
            self.shutdown()

    def shutdown(self):
        """关闭服务"""
        self.logger.info("Shutting down...")
        print(f"\n{'='*60}")
        print(f"⏹️  Slave 正在关闭...")
        self.running = False
        
        # 停止账户上报器
        if self.account_reporter:
            self.account_reporter.stop()
        
        # 断开MQTT
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        
        # 关闭MT5
        mt5.shutdown()
        
        self.logger.info("Shutdown complete")
        print(f"✅ Slave 已关闭")
        print(f"{'='*60}\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='MT5 Slave Signal Receiver')
    parser.add_argument('--config', type=str, default='config/slave_config.json',
                       help='Configuration file path')
    parser.add_argument('--mt5-login', type=int, default=None,
                       help='MT5 login account (optional, overrides config)')
    parser.add_argument('--mt5-password', type=str, default='',
                       help='MT5 password (optional)')
    parser.add_argument('--mt5-server', type=str, default='',
                       help='MT5 server (optional)')
    
    args = parser.parse_args()
    
    receiver = SlaveSignalReceiver(
        config_path=args.config,
        mt5_login=args.mt5_login,
        mt5_password=args.mt5_password,
        mt5_server=args.mt5_server
    )
    receiver.run()


if __name__ == "__main__":
    main()