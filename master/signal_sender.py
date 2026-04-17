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
            # 发送到 {topic_prefix}/{mt5_account_id}/trade
            topic = f"{self.mqtt_client.topic_prefix}/{self.mt5_account_id}/trade"
            payload = json.dumps(signal_data, ensure_ascii=False)
            
            success = self.mqtt_client.publish(topic, payload, qos=1)
            
            if success:
                action = signal_data.get('action', 'UNKNOWN')
                symbol = signal_data.get('symbol', 'UNKNOWN')
                volume = signal_data.get('volume', 0)
                self.logger.info(f"✓ Signal sent: {action} {symbol} {volume}")
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
        """运行主循环"""
        self.logger.info("Starting Master Signal Sender...")
        self.running = True
        
        print(f"\n{'='*60}")
        print(f"📦 MT5 Master 信号发送器")
        print(f"{'='*60}")
        
        # 初始化 MT5
        if not self.initialize_mt5():
            self.logger.error("Failed to initialize MT5")
            print(f"\n❌ Master 启动失败: MT5 初始化失败")
            print(f"{'='*60}\n")
            return
        
        # 连接 MQTT
        if not self.connect_mqtt():
            self.logger.error("Failed to connect to MQTT")
            print(f"\n❌ Master 启动失败: MQTT 连接失败")
            print(f"{'='*60}\n")
            return
        
        self.logger.info("Master Signal Sender is running...")
        self.logger.info("Heartbeat started (every 30 seconds)")
        
        # 终端输出启动成功
        print(f"\n✅ Master 启动成功!")
        print(f"   账号: {self.mt5_account_id}")
        print(f"   MQTT: 已连接")
        print(f"   状态: 正在监控交易信号...")
        print(f"{'='*60}\n")
        
        # 创建心跳文件路径
        if getattr(sys, 'frozen', False):
            heartbeat_file = Path(sys.executable).parent / 'logs' / 'master.heartbeat'
        else:
            heartbeat_file = Path(__file__).parent.parent / 'logs' / 'master.heartbeat'
        
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
                                   f"Account: {self.mt5_account_id} | MQTT: {'Connected' if self.connected else 'Disconnected'}")
                    
                    # 写入心跳文件（用于外部检测进程存活）
                    try:
                        heartbeat_file.parent.mkdir(exist_ok=True)
                        with open(heartbeat_file, 'w', encoding='utf-8') as f:
                            f.write(f"{current_time}\n")
                            f.write(f"account_id={self.mt5_account_id}\n")
                            f.write(f"mqtt_connected={self.connected}\n")
                            f.write(f"uptime={elapsed}\n")
                    except Exception as e:
                        self.logger.debug(f"Failed to write heartbeat file: {e}")
                    
                    last_heartbeat = current_time
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
            print(f"\n⚠️  收到关闭信号，正在停止...")
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}", exc_info=True)
            print(f"\n❌ 发生错误: {e}")
        finally:
            self.shutdown()

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