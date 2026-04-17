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
            print(f"[MT5探测器] 配置文件目录: {config_dir}")
            print(f"[MT5探测器] config_dir.exists(): {config_dir.exists()}")
            
            if config_dir.exists():
                # 读取 common.ini (MT5 使用 UTF-16 LE 编码)
                common_ini = config_dir / "common.ini"
                print(f"[MT5探测器] common.ini 存在: {common_ini.exists()}")
                
                if common_ini.exists():
                    try:
                        with open(common_ini, 'rb') as f:
                            raw_content = f.read()
                            print(f"[MT5探测器] common.ini 文件大小: {len(raw_content)} 字节")
                            # 尝试 UTF-16 LE
                            try:
                                content = raw_content.decode('utf-16-le')
                                print(f"[MT5探测器] 使用 UTF-16 LE 解码成功")
                            except:
                                content = raw_content.decode('utf-8', errors='ignore')
                                print(f"[MT5探测器] 使用 UTF-8 解码")
                            
                            name_match = re.search(r'Company\s*=\s*(.+)', content)
                            if name_match:
                                broker_name = name_match.group(1).strip()
                                print(f"[MT5探测器] 券商名称: {broker_name}")
                            else:
                                print(f"[MT5探测器] 未找到 Company 字段")
                    except Exception as e:
                        print(f"[MT5探测器] 读取 common.ini 失败: {e}")
                
                # 读取 accounts.dat
                accounts_dat = config_dir / "accounts.dat"
                print(f"[MT5探测器] accounts.dat 存在: {accounts_dat.exists()}")
                
                if accounts_dat.exists():
                    try:
                        with open(accounts_dat, 'rb') as f:
                            raw_content = f.read()
                            print(f"[MT5探测器] accounts.dat 文件大小: {len(raw_content)} 字节")
                            try:
                                content = raw_content.decode('utf-16-le')
                                print(f"[MT5探测器] accounts.dat 使用 UTF-16 LE 解码")
                            except:
                                content = raw_content.decode('utf-8', errors='ignore')
                                print(f"[MT5探测器] accounts.dat 使用 UTF-8 解码")
                            
                            login_match = re.search(r'Login\s*=\s*(\d+)', content)
                            server_match = re.search(r'Server\s*=\s*(.+?)(?:\r?\n|$)', content)
                            
                            if login_match:
                                login = login_match.group(1)
                                print(f"[MT5探测器] 账号: {login}")
                            else:
                                print(f"[MT5探测器] 未找到 Login 字段")
                                
                            if server_match:
                                srv = server_match.group(1).strip()
                                if srv and srv != "未知":
                                    server = srv
                                    print(f"[MT5探测器] 服务器: {server}")
                                else:
                                    print(f"[MT5探测器] Server 字段为空")
                            else:
                                print(f"[MT5探测器] 未找到 Server 字段")
                    except Exception as e:
                        print(f"[MT5探测器] 读取 accounts.dat 失败: {e}")
            
            return {
                'pid': proc.pid,
                'path': exe_path,
                'broker': broker_name,
                'login': login,
                'server': server,
                'name': f"{broker_name} - 账号: {login}"
            }
            
        except Exception as e:
            print(f"获取终端信息失败: {e}")
            import traceback
            traceback.print_exc()
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