"""
账户状态上报器（内部使用，用户无感知）

功能：
- 定期上报账户状态到收费系统
- 检测账户有效性（可选）
- 静默运行，不影响主业务流程
"""

import threading
import time
from typing import Optional, Callable
import requests
import MetaTrader5 as mt5
from common.utils import setup_logger


class AccountReporter:
    """
    账户状态上报器
    
    定期上报账户状态，可选检查账户有效性
    """
    
    def __init__(
        self,
        proxy_url: str = "http://localhost:5000",
        interval: int = 60,
        mt5_account_id: Optional[int] = None,
        on_account_disabled: Optional[Callable] = None
    ):
        """
        初始化上报器
        
        Args:
            proxy_url: Auth Proxy 地址
            interval: 上报间隔（秒）
            mt5_account_id: MT5 账号 ID
            on_account_disabled: 账户被禁用时的回调函数（可选）
        """
        self.proxy_url = proxy_url.rstrip('/')
        self.interval = interval
        self.mt5_account_id = mt5_account_id
        self.on_account_disabled = on_account_disabled
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.logger = setup_logger("account_reporter", "logs/reporter.log")
        
    def start(self, mt5_account_id: Optional[int] = None):
        """
        启动上报器（后台线程）
        
        Args:
            mt5_account_id: MT5 账号 ID（如果未在初始化时提供）
        """
        if mt5_account_id:
            self.mt5_account_id = mt5_account_id
        
        if not self.mt5_account_id:
            self.logger.warning("Cannot start reporter: no account ID")
            return
        
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._report_loop, daemon=True)
        self.thread.start()
        self.logger.info(f"Account reporter started for {self.mt5_account_id} (interval: {self.interval}s)")
        
    def stop(self):
        """停止上报器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.logger.info("Account reporter stopped")
        
    def _report_loop(self):
        """上报循环（后台运行）"""
        while self.running:
            try:
                should_continue = self._report_once()
                
                # 如果检测到账户被禁用，退出循环
                if not should_continue:
                    self.logger.warning(f"Account {self.mt5_account_id} disabled, stopping reporter")
                    break
                    
            except Exception as e:
                # 静默处理错误，不中断循环
                self.logger.debug(f"Report error (will retry): {e}")
            
            # 等待下一个周期
            time.sleep(self.interval)
    
    def _report_once(self) -> bool:
        """
        执行一次上报
        
        Returns:
            bool: 是否继续运行（False 表示账户被禁用）
        """
        try:
            # 确保 MT5 连接
            if not mt5.initialize():
                self.logger.debug("MT5 not available, skip report")
                return True
            
            # 获取账户信息
            account_info = mt5.account_info()
            if not account_info:
                self.logger.debug("No account info, skip report")
                return True
            
            # 构建上报数据
            payload = {
                "account": self.mt5_account_id,
                "balance": account_info.balance,
                "equity": account_info.equity,
                "margin": account_info.margin,
                "marginFree": account_info.margin_free,
                "symbol": "",
                "ea": "TradeMind-Follow-System-trademind-follow"
            }
            
            # 发送到 Auth Proxy
            response = requests.post(
                f"{self.proxy_url}/api/report",
                json=payload,
                timeout=3
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # 检查账户状态（如果 Auth Proxy 返回了状态）
                if not result.get('ok', True):
                    reason = result.get('reason', 'Unknown')
                    self.logger.warning(f"Account {self.mt5_account_id} disabled: {reason}")
                    
                    # 触发断开回调
                    if self.on_account_disabled:
                        self.logger.info(f"Triggering disconnect callback for account {self.mt5_account_id}")
                        self.on_account_disabled(reason)
                    
                    return False  # 停止上报
                
                self.logger.debug(f"Reported account {self.mt5_account_id}: balance=${account_info.balance:.2f}")
                return True
            else:
                self.logger.debug(f"Report failed: HTTP {response.status_code}")
                return True
                
        except requests.exceptions.RequestException as e:
            self.logger.debug(f"Network error: {e}")
            return True  # 网络错误不停止
        except Exception as e:
            self.logger.debug(f"Unexpected error: {e}")
            return True


if __name__ == "__main__":
    # 测试代码
    def on_disabled(reason):
        print(f"⚠️  Account disabled: {reason}")
        print("Disconnecting...")
    
    reporter = AccountReporter(
        interval=10,
        on_account_disabled=on_disabled
    )
    reporter.start(mt5_account_id=123456)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        reporter.stop()
        print("\nStopped")