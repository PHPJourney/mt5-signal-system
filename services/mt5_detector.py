# services/mt5_detector.py
"""MT5 终端检测服务"""
import psutil
import re
import os
from pathlib import Path


class MT5Detector:
    """检测和获取 MT5 终端信息"""
    
    @staticmethod
    def detect_terminals():
        """检测系统中运行的所有 MT5 终端"""
        terminals = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
                try:
                    proc_name = proc.info['name']
                    if proc_name and 'terminal64.exe' in proc_name.lower():
                        exe_path = proc.info['exe']
                        if exe_path:
                            terminal_info = MT5Detector._get_terminal_info(proc)
                            if terminal_info:
                                terminals.append(terminal_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # 去重
            seen_paths = set()
            unique_terminals = []
            for term in terminals:
                if term['path'] not in seen_paths:
                    seen_paths.add(term['path'])
                    unique_terminals.append(term)
            
            return unique_terminals
            
        except Exception as e:
            print(f"检测 MT5 终端失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def _get_terminal_info(proc):
        """获取单个 MT5 终端的详细信息"""
        try:
            exe_path = proc.info['exe']
            if not exe_path:
                return None
            
            broker_name = "未知券商"
            login = "未知"
            server = "未知"
            
            # 方法1: 从命令行参数获取
            try:
                cmdline = proc.info.get('cmdline', [])
                if not cmdline:
                    cmdline = proc.cmdline()
                if cmdline:
                    cmd_str = ' '.join(cmdline)
                    # 查找 server 参数
                    server_match = re.search(r'/server:([^\s]+)', cmd_str)
                    if server_match:
                        server = server_match.group(1)
            except:
                pass
            
            # 方法2: 从配置文件获取信息
            config_dir = Path(exe_path).parent / "config"
            
            if config_dir.exists():
                # 读取 common.ini (MT5 使用 UTF-16 LE 编码)
                common_ini = config_dir / "common.ini"
                
                if common_ini.exists():
                    try:
                        with open(common_ini, 'rb') as f:
                            raw_content = f.read()
                            # 尝试 UTF-16 LE
                            try:
                                content = raw_content.decode('utf-16-le')
                            except:
                                content = raw_content.decode('utf-8', errors='ignore')
                            
                            # 尝试多种可能的字段名
                            name_match = re.search(r'(?:Company|Server|Broker)\s*=\s*(.+)', content, re.IGNORECASE)
                            if name_match:
                                broker_name = name_match.group(1).strip()
                                # 清理不可见字符
                                broker_name = ''.join(c for c in broker_name if ord(c) > 31)
                    except Exception as e:
                        pass
                
                # 读取 accounts.dat
                accounts_dat = config_dir / "accounts.dat"
                
                if accounts_dat.exists():
                    try:
                        with open(accounts_dat, 'rb') as f:
                            raw_content = f.read()
                            try:
                                content = raw_content.decode('utf-16-le')
                            except:
                                content = raw_content.decode('utf-8', errors='ignore')
                            
                            # 查找登录信息
                            login_match = re.search(r'(?:Login|Account)\s*=\s*(\d+)', content, re.IGNORECASE)
                            server_match = re.search(r'(?:Server)\s*=\s*(.+?)(?:\r?\n|$)', content, re.IGNORECASE)
                            
                            if login_match:
                                login = login_match.group(1)
                                
                            if server_match:
                                srv = server_match.group(1).strip()
                                # 清理不可见字符
                                srv = ''.join(c for c in srv if ord(c) > 31)
                                if srv and srv != "未知":
                                    server = srv
                    except Exception as e:
                        pass
            
            # 清理所有字段的不可见字符
            broker_name = ''.join(c for c in broker_name if ord(c) > 31).strip() or "未知券商"
            login = ''.join(c for c in login if ord(c) > 31).strip() or "未知"
            server = ''.join(c for c in server if ord(c) > 31).strip() or "未知"
            
            return {
                'pid': proc.pid,
                'path': exe_path,
                'broker': broker_name,
                'login': login,
                'server': server,
                'name': f"{broker_name} - 账号: {login}"
            }
            
        except Exception as e:
            return None
    
    @staticmethod
    def connect_to_terminal(terminal_path=None):
        """连接到指定的 MT5 终端
        
        Args:
            terminal_path: MT5 终端路径，如果为 None 则连接第一个可用的
            
        Returns:
            bool: 是否连接成功
        """
        try:
            import MetaTrader5 as mt5
            
            # 初始化 MT5
            if not mt5.initialize(path=terminal_path):
                print(f"MT5 初始化失败: {mt5.last_error()}")
                return False
            
            # 获取账户信息
            account_info = mt5.account_info()
            if account_info:
                print(f"[OK] 已连接到 MT5")
                print(f"  账号: {account_info.login}")
                print(f"  券商: {account_info.company}")
                print(f"  服务器: {account_info.server}")
                print(f"  余额: {account_info.balance}")
                return True
            else:
                print("[FAIL] 未检测到登录的账户")
                return False
                
        except ImportError:
            print("[FAIL] 未安装 MetaTrader5 包")
            print("  运行: pip install MetaTrader5")
            return False
        except Exception as e:
            print(f"连接 MT5 失败: {e}")
            return False
    
    @staticmethod
    def get_account_info():
        """获取当前连接的 MT5 账户信息"""
        try:
            import MetaTrader5 as mt5
            
            account_info = mt5.account_info()
            if account_info:
                return {
                    'login': account_info.login,
                    'company': account_info.company,
                    'server': account_info.server,
                    'balance': account_info.balance,
                    'equity': account_info.equity,
                    'profit': account_info.profit,
                    'margin': account_info.margin,
                    'free_margin': account_info.margin_free,
                }
            return None
        except Exception as e:
            print(f"获取账户信息失败: {e}")
            return None
    
    @staticmethod
    def send_order(symbol, order_type, volume, price=None, comment=""):
        """发送交易订单
        
        Args:
            symbol: 交易品种 (如 "EURUSD")
            order_type: 订单类型 ("BUY" 或 "SELL")
            volume: 手数
            price: 价格（市价单可为 None）
            comment: 注释
            
        Returns:
            dict: 订单结果
        """
        try:
            import MetaTrader5 as mt5
            
            # 确定订单类型
            if order_type.upper() == "BUY":
                action = mt5.ORDER_TYPE_BUY
            elif order_type.upper() == "SELL":
                action = mt5.ORDER_TYPE_SELL
            else:
                return {'success': False, 'error': f'未知的订单类型: {order_type}'}
            
            # 构建请求
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": action,
                "comment": comment,
            }
            
            # 如果是限价单，设置价格
            if price:
                request["price"] = price
            
            # 发送订单
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                return {
                    'success': True,
                    'order_id': result.order,
                    'deal_id': result.deal,
                    'volume': result.volume,
                    'price': result.price,
                }
            else:
                return {
                    'success': False,
                    'error': f"订单失败: {result.comment}",
                    'retcode': result.retcode
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}