"""
Symbol Mapping Module for MT5 Signal System
Handles mapping between different broker symbol names
"""

from typing import Dict, Optional
import MetaTrader5 as mt5
from common.utils import setup_logger


class SymbolMapper:
    """交易品种映射管理器"""

    def __init__(self, mapping_config: Dict[str, str]):
        """
        初始化符号映射器

        Args:
            mapping_config: 映射配置字典 {master_symbol: slave_symbol}
        """
        self.mapping = mapping_config
        self.reverse_mapping = {v: k for k, v in mapping_config.items()}
        self.logger = setup_logger("symbol_mapper", "logs/symbol_mapper.log")

        # 缓存可用的交易品种
        self.available_symbols = set()
        self._refresh_available_symbols()

        self.logger.info(f"Symbol mapper initialized with {len(self.mapping)} mappings")

    def _refresh_available_symbols(self):
        """刷新可用交易品种列表"""
        try:
            symbols = mt5.symbols_get()
            if symbols:
                self.available_symbols = {s.name for s in symbols}
                self.logger.debug(f"Found {len(self.available_symbols)} available symbols")
        except Exception as e:
            self.logger.error(f"Error refreshing symbols: {e}")

    def map_symbol(self, master_symbol: str) -> Optional[str]:
        """
        将主服务器符号映射为从服务器符号

        Args:
            master_symbol: 主服务器交易品种名称

        Returns:
            从服务器交易品种名称,如果无法映射则返回None
        """
        # 首先查找显式映射
        if master_symbol in self.mapping:
            mapped_symbol = self.mapping[master_symbol]

            # 检查映射后的品种是否可用
            if mapped_symbol in self.available_symbols:
                return mapped_symbol
            else:
                self.logger.warning(f"Mapped symbol '{mapped_symbol}' not available. "
                                  f"Refreshing symbol list...")
                self._refresh_available_symbols()
                if mapped_symbol in self.available_symbols:
                    return mapped_symbol
                else:
                    self.logger.error(f"Mapped symbol '{mapped_symbol}' still not available")
                    return None

        # 如果没有显式映射,尝试直接使用原名称
        if master_symbol in self.available_symbols:
            self.logger.debug(f"No mapping found for '{master_symbol}', using as-is")
            return master_symbol

        # 尝试常见变体
        alternative = self._find_alternative_symbol(master_symbol)
        if alternative:
            self.logger.info(f"Found alternative symbol: {master_symbol} -> {alternative}")
            return alternative

        self.logger.warning(f"Cannot map symbol: {master_symbol}")
        return None

    def _find_alternative_symbol(self, symbol: str) -> Optional[str]:
        """
        查找替代的交易品种名称

        Args:
            symbol: 原始交易品种名称

        Returns:
            找到的替代品种名称
        """
        symbol_upper = symbol.upper()

        # 常见变体映射
        alternatives = {
            'XAUUSD': ['GOLD', 'XAUUSDm', 'Gold'],
            'XAGUSD': ['SILVER', 'XAGUSDm', 'Silver'],
            'BTCUSD': ['BITCOIN', 'BTC', 'Bitcoin', 'BTCUSDm'],
            'ETHUSD': ['ETHEREUM', 'ETH', 'Ethereum'],
            'US30': ['DJI30', 'DJ30', 'US30m', 'DowJones'],
            'NAS100': ['NDX100', 'NAS100m', 'Nasdaq'],
            'SPX500': ['SP500', 'SPX500m', 'SPX'],
            'EURUSD': ['EURUSDm', 'EURUSD.pro'],
            'GBPUSD': ['GBPUSDm', 'GBPUSD.pro'],
            'USDJPY': ['USDJPYm', 'USDJPY.pro'],
        }

        if symbol_upper in alternatives:
            for alt in alternatives[symbol_upper]:
                if alt in self.available_symbols:
                    return alt

        return None

    def get_symbol_info(self, symbol: str) -> Optional[dict]:
        """
        获取交易品种信息

        Args:
            symbol: 交易品种名称

        Returns:
            品种信息字典
        """
        try:
            info = mt5.symbol_info(symbol)
            if info is None:
                return None

            return {
                'name': info.name,
                'description': info.description,
                'point': info.point,
                'digits': info.digits,
                'spread': info.spread,
                'trade_contract_size': info.trade_contract_size,
                'volume_min': info.volume_min,
                'volume_max': info.volume_max,
                'volume_step': info.volume_step,
            }
        except Exception as e:
            self.logger.error(f"Error getting symbol info for {symbol}: {e}")
            return None

    def check_spread(self, symbol: str, max_spread_points: float) -> bool:
        """
        检查点差是否在允许范围内

        Args:
            symbol: 交易品种
            max_spread_points: 最大允许点差(点数)

        Returns:
            点差是否在允许范围内
        """
        try:
            info = mt5.symbol_info(symbol)
            if info is None:
                self.logger.warning(f"Cannot get symbol info for {symbol}")
                return False

            if info.point == 0:
                return True

            current_spread = info.spread
            spread_in_points = current_spread / info.point

            if spread_in_points > max_spread_points:
                self.logger.warning(f"Spread too high for {symbol}: "
                                  f"{spread_in_points:.1f} points (max: {max_spread_points})")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking spread for {symbol}: {e}")
            return False

    def add_mapping(self, master_symbol: str, slave_symbol: str):
        """
        添加新的映射关系

        Args:
            master_symbol: 主服务器品种
            slave_symbol: 从服务器品种
        """
        self.mapping[master_symbol] = slave_symbol
        self.reverse_mapping[slave_symbol] = master_symbol
        self.logger.info(f"Added mapping: {master_symbol} -> {slave_symbol}")

    def remove_mapping(self, master_symbol: str):
        """
        移除映射关系

        Args:
            master_symbol: 主服务器品种
        """
        if master_symbol in self.mapping:
            slave_symbol = self.mapping.pop(master_symbol)
            self.reverse_mapping.pop(slave_symbol, None)
            self.logger.info(f"Removed mapping: {master_symbol}")

    def get_all_mappings(self) -> Dict[str, str]:
        """获取所有映射关系"""
        return self.mapping.copy()
