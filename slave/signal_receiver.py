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

        # 初始化MQTT客户端
        self.mqtt_client = MQTTClient(self.config['mqtt'], is_master=False)

        # 设置消息回调
        self.mqtt_client.set_message_callback(self.on_message)

        # 风险管理器
        from slave.risk_manager import RiskManager
        self.risk_manager = RiskManager(self.config.get('risk_management', {}))

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
        
        # 4. 退出程序
        self.logger.error("Program will exit in 5 seconds...")
        import sys
        time.sleep(5)
        sys.exit(1)

    def initialize_mt5(self) -> bool:
        """
        初始化MT5连接
        注意：不需要登录，直接读取当前 MT5 Terminal 中已登录的账号
        支持指定 Terminal 路径（不同券商的终端）
        """
        try:
            self.logger.info("Attempting to initialize MetaTrader5...")
            self.logger.info(f"Python executable: {sys.executable}")
            self.logger.info(f"Current working directory: {os.getcwd()}")
            
            # 获取 Terminal 路径（从配置或命令行参数）
            terminal_path = self.config.get('mt5_terminal_path')
            
            if terminal_path:
                self.logger.info(f"Connecting to MT5 Terminal: {terminal_path}")
                initialized = mt5.initialize(path=terminal_path)
            else:
                self.logger.info("Connecting to default MT5 Terminal")
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
                return False

            # 直接读取当前登录的账号信息（不需要 login）
            account_info = mt5.account_info()
            if account_info is None:
                error_code, error_msg = mt5.last_error()
                self.logger.error("Failed to get account info.")
                self.logger.error(f"Error code: {error_code}")
                self.logger.error(f"Error message: {error_msg}")
                self.logger.error("Please ensure you are logged in to MT5 Terminal.")
                return False

            self.mt5_account_id = account_info.login
            
            self.logger.info("="*60)
            self.logger.info(f"✓ 检测到 MT5 账号: {self.mt5_account_id}")
            self.logger.info(f"  券商: {account_info.server}")
            self.logger.info(f"  余额: ${account_info.balance:.2f}")
            self.logger.info("="*60)
            
            # 设置 MQTT 认证信息（使用 MT5 账号作为 username）
            self.mqtt_client.set_credentials_from_mt5(self.mt5_account_id)
            
            # 自动启动账户上报器（静默运行）
            if self.account_reporter:
                self.account_reporter.start(mt5_account_id=self.mt5_account_id)
            
            return True

        except Exception as e:
            self.logger.error(f"Error initializing MT5: {e}", exc_info=True)
            return False

    def connect_mqtt(self) -> bool:
        """连接到MQTT代理"""
        try:
            # 订阅主账户的主题
            master_account = self.config.get('master_account')
            if not master_account:
                self.logger.error("master_account not configured!")
                return False

            topic = f"{self.config['mqtt']['topic_prefix']}/{master_account}/#"
            success = self.mqtt_client.connect_and_subscribe(topic)
            
            if success:
                self.connected = True
                self.logger.info(f"Subscribed to master account: {master_account}")
            
            return success

        except Exception as e:
            self.logger.error(f"Error connecting to MQTT: {e}", exc_info=True)
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
            order_type = payload.get('order_type')
            symbol = payload.get('symbol')
            volume = payload.get('volume', 0.01)
            price = payload.get('price', 0.0)
            sl = payload.get('sl', 0.0)
            tp = payload.get('tp', 0.0)
            magic = payload.get('magic', 0)
            comment = payload.get('comment', '')

            # 检查是否允许交易此类型
            follow_mode = self.config.get('common', {}).get('follow_mode', 'both')
            if follow_mode == 'buy_only' and order_type in [mt5.ORDER_TYPE_SELL, mt5.ORDER_TYPE_SELL_LIMIT, mt5.ORDER_TYPE_SELL_STOP]:
                self.logger.info(f"Ignoring SELL signal (mode: {follow_mode})")
                return
            elif follow_mode == 'sell_only' and order_type in [mt5.ORDER_TYPE_BUY, mt5.ORDER_TYPE_BUY_LIMIT, mt5.ORDER_TYPE_BUY_STOP]:
                self.logger.info(f"Ignoring BUY signal (mode: {follow_mode})")
                return

            # 映射品种
            mapped_symbol = self.symbol_mapper.map_symbol(symbol)
            if not mapped_symbol:
                self.logger.error(f"Symbol mapping failed for: {symbol}")
                return

            # 应用手数乘数
            lot_multiplier = self.config.get('common', {}).get('lot_multiplier', 1.0)
            adjusted_volume = volume * lot_multiplier
            
            max_lot = self.config.get('common', {}).get('max_lot', 100.0)
            if adjusted_volume > max_lot:
                self.logger.warning(f"Volume {adjusted_volume} exceeds max_lot {max_lot}, capping")
                adjusted_volume = max_lot

            # 执行交易
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
                self.logger.info(f"Order executed successfully: {order_type} {mapped_symbol} {adjusted_volume}")
            else:
                self.logger.error(f"Order execution failed: {order_type} {mapped_symbol}")

        except Exception as e:
            self.logger.error(f"Error handling order signal: {e}", exc_info=True)

    def execute_order(self, order_type: int, symbol: str, volume: float,
                     price: float = 0.0, sl: float = 0.0, tp: float = 0.0,
                     magic: int = 0, comment: str = '') -> bool:
        """
        执行订单

        Args:
            order_type: 订单类型
            symbol: 交易品种
            volume: 手数
            price: 价格（市价单为0）
            sl: 止损
            tp: 止盈
            magic: Magic Number
            comment: 注释

        Returns:
            bool: 是否成功
        """
        try:
            # 准备请求
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

            # 添加价格相关字段
            if price > 0:
                request["price"] = price
            if sl > 0:
                request["sl"] = sl
            if tp > 0:
                request["tp"] = tp

            # 发送订单
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"Order failed: {result.comment} (code: {result.retcode})")
                return False

            self.logger.info(f"Order sent: ticket={result.order}, retcode={result.retcode}")
            return True

        except Exception as e:
            self.logger.error(f"Error executing order: {e}", exc_info=True)
            return False

    def handle_modify_signal(self, payload: Dict[str, Any]):
        """处理修改信号"""
        self.logger.info(f"Modify signal received: {payload}")
        # TODO: 实现订单修改逻辑

    def handle_close_signal(self, payload: Dict[str, Any]):
        """处理平仓信号"""
        self.logger.info(f"Close signal received: {payload}")
        # TODO: 实现平仓逻辑

    def run(self):
        """运行从服务器"""
        self.logger.info("="*60)
        self.logger.info("Starting MT5 Slave Signal Receiver")
        self.logger.info("="*60)

        # 初始化MT5
        if not self.initialize_mt5():
            self.logger.error("Failed to initialize MT5")
            return

        # 连接MQTT
        if not self.connect_mqtt():
            self.logger.error("Failed to connect to MQTT")
            return

        self.running = True
        self.logger.info("Slave receiver started successfully")
        self.logger.info("Heartbeat started (every 30 seconds)")
        
        # 记录启动时间
        self.start_time = time.time()
        
        # 创建心跳文件路径
        if getattr(sys, 'frozen', False):
            heartbeat_file = Path(sys.executable).parent / 'logs' / 'slave.heartbeat'
        else:
            heartbeat_file = Path(__file__).parent.parent / 'logs' / 'slave.heartbeat'

        try:
            last_heartbeat = time.time()
            heartbeat_interval = 30  # 每 30 秒输出一次心跳
            
            while self.running:
                current_time = time.time()
                
                # 每 30 秒输出一次心跳日志
                if current_time - last_heartbeat >= heartbeat_interval:
                    elapsed = int(current_time - self.start_time)
                    hours = elapsed // 3600
                    minutes = (elapsed % 3600) // 60
                    seconds = elapsed % 60
                    
                    self.logger.info(f"💓 Heartbeat - Running for {hours}h {minutes}m {seconds}s | "
                                   f"Account: {self.mt5_account_id} | MQTT: {'Connected' if self.connected else 'Disconnected'} | "
                                   f"Master: {self.config.get('master_account', 'N/A')}")
                    
                    # 写入心跳文件（用于外部检测进程存活）
                    try:
                        heartbeat_file.parent.mkdir(exist_ok=True)
                        with open(heartbeat_file, 'w', encoding='utf-8') as f:
                            f.write(f"{current_time}\n")
                            f.write(f"account_id={self.mt5_account_id}\n")
                            f.write(f"mqtt_connected={self.connected}\n")
                            f.write(f"uptime={elapsed}\n")
                            f.write(f"master_account={self.config.get('master_account', 'N/A')}\n")
                    except Exception as e:
                        self.logger.debug(f"Failed to write heartbeat file: {e}")
                    
                    last_heartbeat = current_time
                
                time.sleep(1)
                
                # 定期重连
                if not self.mqtt_client.is_connected():
                    self.logger.warning("MQTT disconnected, reconnecting...")
                    self.connect_mqtt()
                    
        except KeyboardInterrupt:
            self.logger.info("Shutdown requested by user")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}", exc_info=True)
        finally:
            self.shutdown()

    def shutdown(self):
        """关闭服务"""
        self.logger.info("Shutting down...")
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