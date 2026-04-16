"""
Risk Management Module for TradeMind MT5
Implements comprehensive risk control mechanisms
"""

import MetaTrader5 as mt5
from datetime import datetime, date, time
from typing import Dict, Optional, List
from common.models import RiskStatus
from common.utils import setup_logger


class RiskManager:
    """高级风险管理器"""

    def __init__(self, config: Dict):
        """
        初始化风险管理器

        Args:
            config: 风险管理配置
        """
        self.config = config
        self.logger = setup_logger("risk_manager", "logs/risk_manager.log")

        # 基础风险状态
        self.risk_status = RiskStatus(
            max_daily_loss=config.get('max_drawdown_usd', 1000.0),
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
        self.session_start_balance = self.initial_balance

        # 会话统计
        self.session_loss = 0.0
        self.session_profit = 0.0
        self.cooldown_until = None

        # 持仓跟踪
        self.position_count = 0
        self.total_lots = 0.0

        # 订单跟踪
        self.processed_orders = {}

        self.logger.info(f"Risk Manager initialized")
        self.logger.info(f"Max daily loss: ${self.risk_status.max_daily_loss:.2f}")
        self.logger.info(f"Max positions: {self.config.get('max_positions', 3)}")
        self.logger.info(f"Lot mode: {self.config.get('lot_mode', 'multiplier')}")

    def check_risk_limits(self) -> bool:
        """
        检查所有风险限制

        Returns:
            是否允许交易
        """
        if not self.config.get('enable_risk_management', True):
            return True

        # 检查冷却期
        if self.cooldown_until and datetime.now() < self.cooldown_until:
            remaining = (self.cooldown_until - datetime.now()).total_seconds() / 60
            self.logger.warning(f"Cooldown active: {remaining:.1f} minutes remaining")
            return False

        # 检查每日亏损
        if not self._check_daily_loss():
            return False

        # 检查每日盈利
        if not self._check_daily_profit():
            return False

        # 检查会话亏损
        if not self._check_session_loss():
            return False

        # 检查会话盈利
        if not self._check_session_profit():
            return False

        # 更新交易状态
        self.risk_status.trading_enabled = True
        self.risk_status.blocked_reason = ""

        return True

    def check_order_filter(self, signal: Dict) -> tuple:
        """
        检查订单过滤条件

        Args:
            signal: 信号数据

        Returns:
            (是否允许, 原因)
        """
        # 检查多空过滤
        follow_mode = self.config.get('follow_mode', 'both')
        if follow_mode == 'long_only' and signal.get('type') == 'SELL':
            return False, "Filter: Long only mode"
        if follow_mode == 'short_only' and signal.get('type') == 'BUY':
            return False, "Filter: Short only mode"

        # 检查时间过滤
        if not self._check_time_window():
            return False, "Filter: Outside allowed hours"

        # 检查订单年龄
        if not self._check_order_age(signal):
            return False, "Filter: Order too old"

        # 检查盈利/亏损过滤
        if not self._check_profit_loss_filter(signal):
            return False, "Filter: Profit/loss condition not met"

        # 检查 Magic 过滤
        if not self._check_magic_filter(signal):
            return False, "Filter: Magic number not allowed"

        # 检查注释过滤
        if not self._check_comment_filter(signal):
            return False, "Filter: Comment not matched"

        # 检查货币对过滤
        if not self._check_symbol_filter(signal.get('symbol', '')):
            return False, "Filter: Symbol not allowed"

        # 检查手数过滤
        if not self._check_lot_filter(signal.get('volume', 0)):
            return False, "Filter: Lot size out of range"

        # 检查持仓数量限制
        if not self._check_position_limits():
            return False, "Filter: Position limit reached"

        return True, "OK"

    def calculate_lot_size(self, master_volume: float, master_balance: float = 0,
                          slave_balance: float = 0, order_index: int = 0) -> float:
        """
        根据配置模式计算手数

        Args:
            master_volume: Master 手数
            master_balance: Master 余额
            slave_balance: Slave 余额
            order_index: 订单序号 (递增模式使用)

        Returns:
            计算后的手数
        """
        lot_mode = self.config.get('lot_mode', 'multiplier')

        if lot_mode == 'multiplier':
            # L1: 倍数模式
            calculated_lot = master_volume * self.config.get('lot_multiplier', 1.0)
        
        elif lot_mode == 'balance_ratio':
            # L2: 余额倍率模式
            if master_balance > 0:
                ratio = slave_balance / master_balance
                calculated_lot = master_volume * ratio * self.config.get('balance_ratio', 1.0)
            else:
                calculated_lot = master_volume
        
        elif lot_mode == 'fixed':
            # L3: 固定手数
            calculated_lot = self.config.get('fixed_lot', 0.1)
        
        elif lot_mode == 'fixed_per_usd':
            # L4: 余额大小模式 (每 N 美元 0.01 手)
            usd_per_lot = self.config.get('usd_per_lot', 1000.0)
            calculated_lot = (slave_balance / usd_per_lot) * 0.01
        
        elif lot_mode == 'incremental':
            # L5: 递增模式
            base = self.config.get('incremental_base', 0.01)
            step = self.config.get('incremental_step', 0.01)
            calculated_lot = base + (order_index * step)
        
        else:
            calculated_lot = master_volume

        # 应用最大/最小手数限制
        min_lot = self.config.get('min_lot', 0.01)
        max_lot = self.config.get('max_lot', 888.8)
        
        calculated_lot = max(min_lot, min(max_lot, calculated_lot))

        # 标准化到步长
        lot_step = 0.01
        calculated_lot = round(calculated_lot / lot_step) * lot_step

        self.logger.debug(f"Lot calculation [{lot_mode}]: {master_volume} -> {calculated_lot}")

        return calculated_lot

    def check_symbol_mapping(self, symbol: str) -> tuple:
        """
        检查并应用货币映射

        Args:
            symbol: 原始货币对

        Returns:
            (映射后的货币, 专用倍数)
        """
        mapping = self.config.get('symbol_mapping', {})
        
        if symbol in mapping:
            map_config = mapping[symbol]
            if isinstance(map_config, dict):
                target_symbol = map_config.get('target', symbol)
                lot_multiplier = map_config.get('lot_multiplier', 1.0)
                return target_symbol, lot_multiplier
            else:
                return map_config, 1.0
        
        return symbol, 1.0

    def check_trailing_stop(self, ticket: int, current_profit_points: float) -> Optional[Dict]:
        """
        检查追踪止损

        Args:
            ticket: 订单号
            current_profit_points: 当前盈利点数

        Returns:
            如果需要调整，返回 {sl: new_sl, tp: tp}，否则 None
        """
        if not self.config.get('trailing_stop', {}).get('enabled', False):
            return None

        profit_points = self.config.get('trailing_stop', {}).get('profit_points', 0)
        trail_points = self.config.get('trailing_stop', {}).get('trail_points', 0)

        if current_profit_points >= profit_points:
            # 启用追踪止损
            return {
                'triggered': True,
                'trail_points': trail_points
            }

        return None

    def _check_daily_loss(self) -> bool:
        """检查每日亏损限制"""
        today = date.today().isoformat()

        if today != self.risk_status.last_reset_date:
            self._reset_daily_loss()

        current_balance = self._get_account_balance()
        daily_loss = self.daily_start_balance - current_balance
        self.risk_status.daily_loss = max(0, daily_loss)

        if self.risk_status.daily_loss >= self.risk_status.max_daily_loss:
            self.risk_status.trading_enabled = False
            self.risk_status.blocked_reason = (
                f"Daily loss limit reached: ${self.risk_status.daily_loss:.2f} / "
                f"${self.risk_status.max_daily_loss:.2f}"
            )
            self.logger.warning(self.risk_status.blocked_reason)
            
            # 触发冷却期
            cooldown_minutes = self.config.get('cooldown_minutes', 0)
            if cooldown_minutes > 0:
                from datetime import timedelta
                self.cooldown_until = datetime.now() + timedelta(minutes=cooldown_minutes)
                self.logger.warning(f"Cooldown triggered: {cooldown_minutes} minutes")
            
            return False

        return True

    def _check_daily_profit(self) -> bool:
        """检查每日盈利限制"""
        max_profit_percent = self.config.get('max_profit_percent', 0)
        max_profit_usd = self.config.get('max_profit_usd', 0)

        if max_profit_percent == 0 and max_profit_usd == 0:
            return True

        current_balance = self._get_account_balance()
        daily_profit = current_balance - self.daily_start_balance

        if max_profit_usd > 0 and daily_profit >= max_profit_usd:
            self.risk_status.blocked_reason = (
                f"Daily profit limit reached: ${daily_profit:.2f} / ${max_profit_usd:.2f}"
            )
            self.logger.warning(self.risk_status.blocked_reason)
            return False

        if max_profit_percent > 0:
            profit_percent = (daily_profit / self.daily_start_balance) * 100
            if profit_percent >= max_profit_percent:
                self.risk_status.blocked_reason = (
                    f"Daily profit limit reached: {profit_percent:.2f}% / {max_profit_percent}%"
                )
                self.logger.warning(self.risk_status.blocked_reason)
                return False

        return True

    def _check_session_loss(self) -> bool:
        """检查会话亏损"""
        session_loss_limit = self.config.get('session_loss_usd', 0)
        if session_loss_limit == 0:
            return True

        current_balance = self._get_account_balance()
        self.session_loss = max(0, self.session_start_balance - current_balance)

        if self.session_loss >= session_loss_limit:
            self.risk_status.blocked_reason = (
                f"Session loss limit reached: ${self.session_loss:.2f} / ${session_loss_limit:.2f}"
            )
            self.logger.warning(self.risk_status.blocked_reason)
            return False

        return True

    def _check_session_profit(self) -> bool:
        """检查会话盈利"""
        session_profit_limit = self.config.get('session_profit_usd', 0)
        if session_profit_limit == 0:
            return True

        current_balance = self._get_account_balance()
        self.session_profit = max(0, current_balance - self.session_start_balance)

        if self.session_profit >= session_profit_limit:
            self.risk_status.blocked_reason = (
                f"Session profit limit reached: ${self.session_profit:.2f} / ${session_profit_limit:.2f}"
            )
            self.logger.warning(self.risk_status.blocked_reason)
            return False

        return True

    def _check_time_window(self) -> bool:
        """检查允许交易时间段"""
        start_str = self.config.get('allowed_hours_start', '00:00:00')
        end_str = self.config.get('allowed_hours_end', '23:59:59')

        if start_str == '00:00:00' and end_str == '23:59:59':
            return True

        current_time = datetime.now().time()
        start_time = datetime.strptime(start_str, '%H:%M:%S').time()
        end_time = datetime.strptime(end_str, '%H:%M:%S').time()

        return start_time <= current_time <= end_time

    def _check_order_age(self, signal: Dict) -> bool:
        """检查订单年龄"""
        max_age = self.config.get('max_order_age_minutes', 0)
        if max_age == 0:
            return True

        order_time_str = signal.get('timestamp', '')
        if not order_time_str:
            return True

        try:
            order_time = datetime.fromisoformat(order_time_str)
            age_minutes = (datetime.now() - order_time).total_seconds() / 60
            return age_minutes <= max_age
        except:
            return True

    def _check_profit_loss_filter(self, signal: Dict) -> bool:
        """检查盈利/亏损过滤"""
        require_profit = self.config.get('require_profit_points', 0)
        require_loss = self.config.get('require_loss_points', 0)

        if require_profit == 0 and require_loss == 0:
            return True

        profit_points = signal.get('profit_points', 0)

        if require_profit > 0 and profit_points < require_profit:
            return False

        if require_loss > 0 and profit_points > -require_loss:
            return False

        return True

    def _check_magic_filter(self, signal: Dict) -> bool:
        """检查 Magic 过滤"""
        allowed_magics = self.config.get('allowed_magics', [])
        if not allowed_magics:
            return True

        signal_magic = signal.get('magic', 0)
        return signal_magic in allowed_magics

    def _check_comment_filter(self, signal: Dict) -> bool:
        """检查注释过滤"""
        required_comments = self.config.get('required_comments', [])
        if not required_comments:
            return True

        signal_comment = signal.get('comment', '')
        return any(comment in signal_comment for comment in required_comments)

    def _check_symbol_filter(self, symbol: str) -> bool:
        """检查货币对过滤"""
        whitelist = self.config.get('whitelist_symbols', [])
        blacklist = self.config.get('blacklist_symbols', [])

        if whitelist and symbol not in whitelist:
            return False

        if blacklist and symbol in blacklist:
            return False

        return True

    def _check_lot_filter(self, volume: float) -> bool:
        """检查手数过滤"""
        min_lot = self.config.get('skip_lot_less_than', 0)
        max_lot = self.config.get('skip_lot_greater_than', 888.8)

        if min_lot > 0 and volume < min_lot:
            return False

        if max_lot < 888.8 and volume > max_lot:
            return False

        return True

    def _check_position_limits(self) -> bool:
        """检查持仓数量限制"""
        max_positions = self.config.get('max_positions', 0)
        max_total_lots = self.config.get('max_total_lots', 0)

        if max_positions > 0 and self.position_count >= max_positions:
            return False

        if max_total_lots > 0 and self.total_lots >= max_total_lots:
            return False

        return True

    def update_position_count(self, count: int, total_lots: float):
        """更新持仓统计"""
        self.position_count = count
        self.total_lots = total_lots

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

    def _reset_daily_loss(self):
        """重置每日亏损统计"""
        today = date.today().isoformat()
        self.risk_status.last_reset_date = today
        self.daily_start_balance = self._get_account_balance()
        self.risk_status.daily_loss = 0.0
        self.logger.info("Daily loss reset")

    def reset_session(self):
        """重置会话统计"""
        self.session_start_balance = self._get_account_balance()
        self.session_loss = 0.0
        self.session_profit = 0.0
        self.cooldown_until = None
        self.logger.info("Session statistics reset")

    def get_risk_status(self) -> Dict:
        """获取当前风险状态"""
        current_balance = self._get_account_balance()
        
        return {
            'trading_enabled': self.risk_status.trading_enabled,
            'blocked_reason': self.risk_status.blocked_reason,
            'daily_loss': self.risk_status.daily_loss,
            'session_loss': self.session_loss,
            'session_profit': self.session_profit,
            'position_count': self.position_count,
            'total_lots': self.total_lots,
            'current_balance': current_balance,
            'cooldown_until': self.cooldown_until.isoformat() if self.cooldown_until else None
        }