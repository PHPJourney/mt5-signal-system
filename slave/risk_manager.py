"""
Risk Management Module for TradeMind MT5
Implements various risk control mechanisms
"""

import MetaTrader5 as mt5
from datetime import datetime, date
from typing import Dict, Optional
from common.models import RiskStatus
from common.utils import setup_logger


class RiskManager:
    """风险管理器"""

    def __init__(self, config: Dict):
        """
        初始化风险管理器

        Args:
            config: 风险管理配置
        """
        self.config = config
        self.logger = setup_logger("risk_manager", "logs/risk_manager.log")

        # 风险状态
        self.risk_status = RiskStatus(
            max_daily_loss=config.get('max_daily_loss_usd', 1000.0),
            last_reset_date=date.today().isoformat()
        )

        # 记录初始余额
        try:
            account_info = mt5.account_info()
            if account_info:
                self.initial_balance = account_info.balance
            else:
                self.initial_balance = 0.0
        except:
            self.initial_balance = 0.0
        
        self.daily_start_balance = self.initial_balance

        self.logger.info(f"Risk Manager initialized - Max daily loss: "
                        f"${self.risk_status.max_daily_loss:.2f}")

    def _get_account_balance(self) -> float:
        """获取账户余额"""
        try:
            account_info = mt5.account_info()
            if account_info:
                return account_info.balance
            return 0.0
        except Exception as e:
            self.logger.error(f"Error getting account balance: {e}")
            return 0.0

    def check_risk_limits(self) -> bool:
        """
        检查风险限制

        Returns:
            是否允许交易
        """
        if not self.config.get('enable_risk_management', True):
            return True

        # 检查每日亏损
        if not self._check_daily_loss():
            return False

        # 更新交易状态
        self.risk_status.trading_enabled = True
        self.risk_status.blocked_reason = ""

        return True

    def _check_daily_loss(self) -> bool:
        """
        检查每日亏损限制

        Returns:
            是否在限制范围内
        """
        today = date.today().isoformat()

        # 如果日期变更,重置日亏损
        if today != self.risk_status.last_reset_date:
            self._reset_daily_loss()

        # 计算当日亏损
        current_balance = self._get_account_balance()
        daily_loss = self.daily_start_balance - current_balance

        # 如果盈利,亏损为0
        self.risk_status.daily_loss = max(0, daily_loss)

        # 检查是否超过限制
        if self.risk_status.daily_loss >= self.risk_status.max_daily_loss:
            self.risk_status.trading_enabled = False
            self.risk_status.blocked_reason = (
                f"Daily loss limit reached: ${self.risk_status.daily_loss:.2f} / "
                f"${self.risk_status.max_daily_loss:.2f}"
            )
            self.logger.warning(self.risk_status.blocked_reason)
            return False

        return True

    def _reset_daily_loss(self):
        """重置每日亏损统计"""
        today = date.today().isoformat()
        self.risk_status.last_reset_date = today
        self.daily_start_balance = self._get_account_balance()
        self.risk_status.daily_loss = 0.0
        self.logger.info("Daily loss reset")

    def check_spread(self, symbol: str, max_spread_points: float) -> bool:
        """
        检查点差是否在允许范围内

        Args:
            symbol: 交易品种
            max_spread_points: 最大允许点差

        Returns:
            是否允许交易
        """
        if not self.config.get('enable_spread_filter', True):
            return True

        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                self.logger.warning(f"Cannot get tick info for {symbol}")
                return False

            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None or symbol_info.point == 0:
                return False

            spread_points = (tick.ask - tick.bid) / symbol_info.point

            if spread_points > max_spread_points:
                self.logger.warning(f"Spread too high for {symbol}: "
                                  f"{spread_points:.1f} points (max: {max_spread_points})")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking spread for {symbol}: {e}")
            return False

    def calculate_lot_size(self, master_volume: float, multiplier: float,
                          min_lot: float, max_lot: float, lot_step: float,
                          symbol: str) -> float:
        """
        计算实际下单手数

        Args:
            master_volume: 主服务器手数
            multiplier: 跟单倍数
            min_lot: 最小手数
            max_lot: 最大手数
            lot_step: 手数步长
            symbol: 交易品种

        Returns:
            计算后的手数
        """
        # 应用倍数
        calculated_lot = master_volume * multiplier

        # 限制在最大手数内
        if calculated_lot > max_lot:
            self.logger.warning(f"Lot size {calculated_lot} exceeds max {max_lot}, "
                              f"capping at max")
            calculated_lot = max_lot

        # 确保不低于最小手数
        if calculated_lot < min_lot:
            calculated_lot = min_lot

        # 按照步长取整
        normalized_lot = round(calculated_lot / lot_step) * lot_step

        # 再次确保在范围内
        final_lot = max(min_lot, min(normalized_lot, max_lot))

        self.logger.debug(f"Lot calculation: {master_volume} x {multiplier} = "
                         f"{calculated_lot} -> {final_lot} (normalized)")

        return final_lot

    def get_risk_status(self) -> RiskStatus:
        """获取当前风险状态"""
        # 更新当前亏损
        current_balance = self._get_account_balance()
        self.risk_status.daily_loss = max(0, self.daily_start_balance - current_balance)

        return self.risk_status

    def can_trade(self, symbol: str, max_spread_points: float) -> tuple:
        """
        综合检查是否可以交易

        Args:
            symbol: 交易品种
            max_spread_points: 最大允许点差

        Returns:
            (是否可以交易, 原因说明)
        """
        # 检查风险限制
        if not self.check_risk_limits():
            return False, self.risk_status.blocked_reason

        # 检查点差
        if not self.check_spread(symbol, max_spread_points):
            return False, f"Spread too high for {symbol}"

        return True, "OK"

    def reset_statistics(self):
        """手动重置统计信息"""
        self._reset_daily_loss()
        self.logger.info("Risk statistics manually reset")
