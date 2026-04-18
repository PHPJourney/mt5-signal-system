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

    def _check_authorization(self) -> dict:
        """
        检查服务授权状态
        
        Returns:
            dict: {'authorized': bool, 'message': str, 'status': str}
        """
        try:
            # 获取代理服务器 URL
            proxy_url = self.config.get('account_reporter', {}).get('proxy_url', 'http://localhost:5000')
            
            # 如果没有 MT5 账号信息，跳过验证
            if not self.mt5_account_id:
                return {
                    'authorized': True,
                    'message': 'Unable to verify - no account info',
                    'status': 'unknown'
                }
            
            # 调用验证接口
            import requests
            
            verify_url = f"{proxy_url.rstrip('/')}/mt5/verify"
            
            payload = {
                'account': self.mt5_account_id,
                'ea': 'TradeMind-Follow-System-trademind-follow'
            }
            
            self.logger.debug(f"Checking authorization: {verify_url}")
            
            response = requests.post(verify_url, json=payload, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                
                # 检查授权状态
                if result.get('authorized', False):
                    return {
                        'authorized': True,
                        'message': 'Authorization valid',
                        'expire_date': result.get('expire_date', ''),
                        'status': 'valid'
                    }
                else:
                    # 未授权或已过期
                    status = result.get('status', 'invalid')
                    
                    if status == 'expired':
                        return {
                            'authorized': False,
                            'message': '服务已过期，请续费',
                            'status': 'expired'
                        }
                    else:
                        return {
                            'authorized': False,
                            'message': '服务未授权，请购买',
                            'status': 'invalid'
                        }
            else:
                # 验证接口不可用，默认允许（避免误杀）
                self.logger.warning(f"Auth server returned status {response.status_code}, allowing by default")
                return {
                    'authorized': True,
                    'message': 'Auth server unavailable, allowing by default',
                    'status': 'unknown'
                }
                
        except Exception as e:
            # 网络错误或其他异常，默认允许
            self.logger.warning(f"Authorization check failed with error: {e}, allowing by default")
            return {
                'authorized': True,
                'message': f'Auth error: {str(e)}, allowing by default',
                'status': 'unknown'
            }

    def initialize_mt5(self) -> bool:
        """
        初始化MT5连接
        注意：不需要登录，直接读取当前 MT5 Terminal 中已登录的账号
        支持指定 Terminal 路径（不同券商的终端）
        """
        try:
            # === 授权检测 ===
            print(f"\n{'='*60}")
            print(f"🚀 启动 Slave 信号接收器...")
            print(f"{'='*60}")
            
            print(f"\n🔐 正在验证服务授权...")
            self.logger.info("Checking service authorization...")
            
            auth_result = self._check_authorization()
            
            if not auth_result['authorized']:
                print(f"\n{'='*60}")
                print(f"⚠️  {auth_result['message']}")
                print(f"{'='*60}")
                
                self.logger.warning(f"Authorization check failed: {auth_result['message']}")
                self.logger.info("Please visit https://mt5data.cidhub.com to purchase or renew service")
                
                print(f"\n⏳ 程序将在 10 秒后退出...")
                print(f"🔗 请访问: https://mt5data.cidhub.com")
                print(f"{'='*60}\n")
                
                import sys
                time.sleep(10)
                sys.exit(1)
            
            print(f"✅ 授权验证成功")
            print(f"{'='*60}\n")
            
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
            self.logger.error(f"Exception during MT5 initialization: {e}", exc_info=True)
            print(f"\n❌ MT5 初始化异常: {str(e)}")
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

        Args:
            order_type: MT5 订单类型
                - 市价单: ORDER_TYPE_BUY (0), ORDER_TYPE_SELL (1)
                - 挂单: ORDER_TYPE_BUY_LIMIT (2), ORDER_TYPE_SELL_LIMIT (3),
                       ORDER_TYPE_BUY_STOP (4), ORDER_TYPE_SELL_STOP (5)
            symbol: 交易品种
            volume: 交易量
            price: 挂单价格（市价单可为 0）
            sl: 止损价格
            tp: 止盈价格
            magic: Magic Number
            comment: 订单注释

        Returns:
            int: 订单号（成功）或 None（失败）
        """
        try:
            # 获取品种信息，验证是否存在
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                self.logger.error(f"Symbol {symbol} not found")
                print(f"   ❌ 品种不存在: {symbol}")
                return None
            
            if not symbol_info.visible:
                self.logger.error(f"Symbol {symbol} not visible in Market Watch")
                print(f"   ❌ 品种未在市场报价中: {symbol}")
                if not mt5.symbol_select(symbol, True):
                    self.logger.error(f"Failed to select symbol {symbol}")
                    print(f"   ❌ 无法选择品种: {symbol}")
                    return None
                self.logger.info(f"Symbol {symbol} added to Market Watch")
                print(f"   ℹ️  已添加品种到市场报价: {symbol}")
            
            # 规范化手数
            volume = self._normalize_volume(symbol, volume)
            
            # 判断是市价单还是挂单
            is_market_order = order_type in [mt5.ORDER_TYPE_BUY, mt5.ORDER_TYPE_SELL]
            is_pending_order = order_type in [
                mt5.ORDER_TYPE_BUY_LIMIT, mt5.ORDER_TYPE_SELL_LIMIT,
                mt5.ORDER_TYPE_BUY_STOP, mt5.ORDER_TYPE_SELL_STOP,
                mt5.ORDER_TYPE_BUY_STOP_LIMIT, mt5.ORDER_TYPE_SELL_STOP_LIMIT
            ]
            
            # 构建订单请求
            request = {
                "action": mt5.TRADE_ACTION_DEAL if is_market_order else mt5.TRADE_ACTION_PENDING,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "deviation": self.config.get('common', {}).get('slippage_points', 30),
                "magic": magic if magic != 0 else self.config.get('common', {}).get('magic_number', 999999),
                "comment": comment if comment else self.config.get('common', {}).get('comment_prefix', 'TM_'),
            }
            
            # 市价单：不需要 price，MT5 会使用当前市场价格
            # 挂单：必须设置 price
            if is_pending_order:
                if price <= 0:
                    self.logger.error(f"Pending order requires price > 0")
                    print(f"   ❌ 挂单必须设置价格")
                    return None
                
                request["price"] = price
                
                # 挂单的止损止盈是相对于挂单价格的偏移（点数）
                # MT5 Python API 中，挂单的 SL/TP 是绝对价格
                if sl > 0:
                    request["sl"] = sl
                if tp > 0:
                    request["tp"] = tp
                
                print(f"   📋 挂单信息: {symbol} | 类型: {order_type} | 价格: {price}")
            else:
                # 市价单：获取当前价格用于显示
                tick = mt5.symbol_info_tick(symbol)
                if tick is None:
                    self.logger.error(f"Failed to get tick for {symbol}")
                    print(f"   ❌ 无法获取价格: {symbol}")
                    return None
                
                current_price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid
                
                # 市价单不设置 price 字段（MT5 自动使用市场价格）
                # 但止损止盈是绝对价格
                if sl > 0:
                    request["sl"] = sl
                if tp > 0:
                    request["tp"] = tp
                
                print(f"   💰 市价单信息: {symbol} | 类型: {'BUY' if order_type == mt5.ORDER_TYPE_BUY else 'SELL'} | 当前价: {current_price}")
            
            # 尝试不同的填充模式
            filling_modes = []
            
            if is_market_order:
                # 市价单常用填充模式
                filling_modes = [
                    mt5.ORDER_FILLING_FOK,
                    mt5.ORDER_FILLING_IOC,
                    mt5.ORDER_FILLING_RETURN
                ]
            else:
                # 挂单不需要填充模式，设置为 0
                filling_modes = [0]
            
            last_error = None
            for filling_mode in filling_modes:
                if filling_mode > 0:
                    request["type_filling"] = filling_mode
                elif "type_filling" in request:
                    del request["type_filling"]
                
                try:
                    result = mt5.order_send(request)
                    
                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                        self.logger.info(f"Order sent: ticket={result.order}, volume={result.volume}, price={result.price}")
                        print(f"   ✅ 订单已发送: ticket={result.order}")
                        return result.order
                    else:
                        last_error = f"{result.comment} (code: {result.retcode})"
                        self.logger.debug(f"Order failed: {last_error}")
                        
                except Exception as e:
                    last_error = str(e)
                    self.logger.debug(f"Order send exception: {e}")
            
            # 所有尝试都失败
            self.logger.error(f"Order failed: {last_error}")
            print(f"   ❌ 订单失败: {last_error}")
            return None

        except Exception as e:
            self.logger.error(f"Error executing order: {e}", exc_info=True)
            print(f"   ❌ 执行订单异常: {e}")
            return None
    
    def _normalize_volume(self, symbol: str, volume: float) -> float:
        """规范化手数到品种允许的范围"""
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return volume
            
            min_lot = symbol_info.volume_min
            max_lot = symbol_info.volume_max
            step_lot = symbol_info.volume_step
            
            # 限制在最小和最大手数之间
            volume = max(min_lot, min(volume, max_lot))
            
            # 按步长规范化
            volume = round(volume / step_lot) * step_lot
            
            # 保留 2 位小数
            volume = round(volume, 2)
            
            return volume
            
        except Exception as e:
            self.logger.debug(f"Failed to normalize volume: {e}")
            return volume

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
        """
        处理平仓信号（支持所有平仓类型）
        
        支持的操作:
        - close_position: 平指定订单（完全或部分）
        - partial_close: 部分平仓
        - close_all_buy: 平所有多单
        - close_all_sell: 平所有空单
        - close_all: 平所有仓位
        - limit_close: 限价平仓（挂单）
        """
        try:
            action = payload.get('action')
            ticket = payload.get('ticket')
            
            print(f"\n📥 收到平仓信号: {action} ticket={ticket}")
            
            # 1. 平指定订单（完全平仓）
            if action == 'close_position':
                self._close_single_position(ticket, payload)
            
            # 2. 部分平仓
            elif action == 'partial_close':
                self._partial_close_position(ticket, payload)
            
            # 3. 平所有多单
            elif action == 'close_all_buy':
                self._close_positions_by_type(mt5.ORDER_TYPE_BUY)
            
            # 4. 平所有空单
            elif action == 'close_all_sell':
                self._close_positions_by_type(mt5.ORDER_TYPE_SELL)
            
            # 5. 平所有仓位
            elif action == 'close_all':
                self._close_all_positions()
            
            # 6. 限价平仓（挂单平仓）
            elif action == 'limit_close':
                self._limit_close_position(ticket, payload)
            
            else:
                self.logger.warning(f"Unknown close action: {action}")
                print(f"   ⚠️  未知的平仓操作: {action}")
        
        except Exception as e:
            self.logger.error(f"Error handling close signal: {e}", exc_info=True)
            print(f"   ❌ 处理平仓信号异常: {e}")
    
    def _close_single_position(self, ticket: int, payload: Dict[str, Any]):
        """平指定订单（完全平仓）"""
        try:
            # 获取持仓信息
            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                self.logger.error(f"Position not found: {ticket}")
                print(f"   ❌ 未找到持仓: {ticket}")
                return
            
            pos = positions[0]
            
            # 构建反向平仓订单
            close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,  # 完全平仓使用全部手数
                "type": close_type,
                "position": ticket,  # 关联原订单
                "deviation": self.config.get('common', {}).get('slippage_points', 30),
                "magic": pos.magic,
                "comment": "Close " + (payload.get('comment') or ''),
            }
            
            # 市价平仓不设置 price
            # 如果需要设置 SL/TP（用于部分平仓后的剩余仓位），可以添加
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.logger.info(f"Position closed: ticket={ticket}, volume={pos.volume}")
                print(f"   ✅ 平仓成功: #{ticket} vol={pos.volume}")
            else:
                self.logger.error(f"Close failed: {result.comment} (code: {result.retcode})")
                print(f"   ❌ 平仓失败: {result.comment}")
                
        except Exception as e:
            self.logger.error(f"Error closing position {ticket}: {e}", exc_info=True)
            print(f"   ❌ 平仓异常: {e}")
    
    def _partial_close_position(self, ticket: int, payload: Dict[str, Any]):
        """部分平仓"""
        try:
            # 获取持仓信息
            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                self.logger.error(f"Position not found: {ticket}")
                print(f"   ❌ 未找到持仓: {ticket}")
                return
            
            pos = positions[0]
            partial_volume = payload.get('volume', pos.volume / 2)  # 默认平一半
            
            # 验证平仓数量
            if partial_volume <= 0 or partial_volume >= pos.volume:
                self.logger.error(f"Invalid partial volume: {partial_volume}")
                print(f"   ❌ 无效的平仓数量: {partial_volume}")
                return
            
            # 构建反向平仓订单
            close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": partial_volume,
                "type": close_type,
                "position": ticket,
                "deviation": self.config.get('common', {}).get('slippage_points', 30),
                "magic": pos.magic,
                "comment": f"Partial Close {partial_volume}",
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                remaining = pos.volume - partial_volume
                self.logger.info(f"Partial close: ticket={ticket}, vol={partial_volume}, remaining={remaining}")
                print(f"   ✅ 部分平仓成功: #{ticket} 平{partial_volume} 剩{remaining}")
            else:
                self.logger.error(f"Partial close failed: {result.comment}")
                print(f"   ❌ 部分平仓失败: {result.comment}")
                
        except Exception as e:
            self.logger.error(f"Error partial closing position {ticket}: {e}", exc_info=True)
            print(f"   ❌ 部分平仓异常: {e}")
    
    def _close_positions_by_type(self, position_type: int):
        """平仓指定类型的所有仓位（多单或空单）"""
        try:
            positions = mt5.positions_get()
            if not positions:
                print(f"   ℹ️  无持仓可平")
                return
            
            closed_count = 0
            type_name = "BUY" if position_type == mt5.ORDER_TYPE_BUY else "SELL"
            
            for pos in positions:
                if pos.type == position_type:
                    close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
                    
                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": pos.symbol,
                        "volume": pos.volume,
                        "type": close_type,
                        "position": pos.ticket,
                        "deviation": self.config.get('common', {}).get('slippage_points', 30),
                        "magic": pos.magic,
                        "comment": f"Close All {type_name}",
                    }
                    
                    result = mt5.order_send(request)
                    
                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                        closed_count += 1
                        self.logger.info(f"Closed {type_name}: ticket={pos.ticket}")
                    else:
                        self.logger.error(f"Failed to close {type_name} #{pos.ticket}: {result.comment}")
            
            self.logger.info(f"Closed {closed_count} {type_name} positions")
            print(f"   ✅ 已平 {closed_count} 个 {type_name} 仓位")
            
        except Exception as e:
            self.logger.error(f"Error closing {type_name} positions: {e}", exc_info=True)
            print(f"   ❌ 平仓异常: {e}")
    
    def _close_all_positions(self):
        """平所有仓位"""
        try:
            positions = mt5.positions_get()
            if not positions:
                print(f"   ℹ️  无持仓可平")
                return
            
            closed_count = 0
            
            for pos in positions:
                close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
                
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": pos.symbol,
                    "volume": pos.volume,
                    "type": close_type,
                    "position": pos.ticket,
                    "deviation": self.config.get('common', {}).get('slippage_points', 30),
                    "magic": pos.magic,
                    "comment": "Close All",
                }
                
                result = mt5.order_send(request)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    closed_count += 1
                    self.logger.info(f"Closed: ticket={pos.ticket}")
                else:
                    self.logger.error(f"Failed to close #{pos.ticket}: {result.comment}")
            
            self.logger.info(f"Closed all {closed_count} positions")
            print(f"   ✅ 已平所有 {closed_count} 个仓位")
            
        except Exception as e:
            self.logger.error(f"Error closing all positions: {e}", exc_info=True)
            print(f"   ❌ 全平异常: {e}")
    
    def _limit_close_position(self, ticket: int, payload: Dict[str, Any]):
        """限价平仓（挂单平仓）"""
        try:
            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                self.logger.error(f"Position not found: {ticket}")
                print(f"   ❌ 未找到持仓: {ticket}")
                return
            
            pos = positions[0]
            limit_price = payload.get('price', 0.0)
            
            if limit_price <= 0:
                self.logger.error("Limit close requires price > 0")
                print(f"   ❌ 限价平仓必须设置价格")
                return
            
            # 构建限价平仓挂单
            close_type = (mt5.ORDER_TYPE_SELL_LIMIT if pos.type == mt5.ORDER_TYPE_BUY 
                         else mt5.ORDER_TYPE_BUY_LIMIT)
            
            request = {
                "action": mt5.TRADE_ACTION_PENDING,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": close_type,
                "price": limit_price,
                "deviation": self.config.get('common', {}).get('slippage_points', 30),
                "magic": pos.magic,
                "comment": "Limit Close",
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.logger.info(f"Limit close order placed: ticket={result.order}, price={limit_price}")
                print(f"   ✅ 限价平仓挂单成功: #{result.order} price={limit_price}")
            else:
                self.logger.error(f"Limit close failed: {result.comment}")
                print(f"   ❌ 限价平仓失败: {result.comment}")
                
        except Exception as e:
            self.logger.error(f"Error limit closing position {ticket}: {e}", exc_info=True)
            print(f"   ❌ 限价平仓异常: {e}")
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