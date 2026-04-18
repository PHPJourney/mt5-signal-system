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
            
            # 方法1: 尝试通过 MT5 Python API 连接获取信息（最可靠）
            terminal_info = MT5Detector._try_connect_mt5_api(exe_path)
            if terminal_info:
                print(f"[OK] 通过 MT5 API 获取终端信息成功")
                terminal_info['path'] = exe_path
                terminal_info['pid'] = proc.pid
                return terminal_info
            
            # 方法2: 从命令行参数获取
            cmdline_info = MT5Detector._parse_cmdline(proc)
            if cmdline_info['login'] != "未知":
                login = cmdline_info['login']
                server = cmdline_info['server']
            
            # 方法3: 从配置文件获取信息（Windows 专用）
            config_info = MT5Detector._parse_config_files(exe_path)
            if config_info['broker'] != "未知券商":
                broker_name = config_info['broker']
            if config_info['login'] != "未知":
                login = config_info['login']
            if config_info['server'] != "未知":
                server = config_info['server']
            
            # 清理所有字段的不可见字符
            broker_name = ''.join(c for c in broker_name if ord(c) > 31).strip() or "未知券商"
            login = ''.join(c for c in login if ord(c) > 31).strip() or "未知"
            server = ''.join(c for c in server if ord(c) > 31).strip() or "未知"
            
            print(f"[INFO] 终端信息 - 路径: {exe_path}")
            print(f"         券商: {broker_name}, 账号: {login}, 服务器: {server}")
            
            return {
                'pid': proc.pid,
                'path': exe_path,
                'broker': broker_name,
                'login': login,
                'server': server,
                'name': f"{broker_name} - 账号: {login}"
            }
            
        except Exception as e:
            print(f"[ERROR] 获取终端信息失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def _try_connect_mt5_api(terminal_path):
        """尝试通过 MT5 Python API 连接终端获取信息"""
        try:
            import MetaTrader5 as mt5
            
            # 初始化 MT5（不登录，只连接终端）
            if not mt5.initialize(path=terminal_path, login=0, password="", server=""):
                return None
            
            # 获取账户信息
            account_info = mt5.account_info()
            if account_info:
                return {
                    'broker': account_info.company or "未知券商",
                    'login': str(account_info.login) if account_info.login else "未知",
                    'server': account_info.server or "未知"
                }
            
            mt5.shutdown()
            return None
            
        except Exception as e:
            print(f"[DEBUG] MT5 API 连接失败: {e}")
            return None
    
    @staticmethod
    def _parse_cmdline(proc):
        """从命令行参数解析终端信息"""
        result = {'login': "未知", 'server': "未知"}
        
        try:
            cmdline = proc.info.get('cmdline', [])
            if not cmdline:
                cmdline = proc.cmdline()
            if not cmdline:
                return result
            
            cmd_str = ' '.join(cmdline)
            print(f"[DEBUG] MT5 cmdline: {cmd_str[:200]}")
            
            # 查找 server 参数
            server_match = re.search(r'/server:([^\s]+)', cmd_str)
            if server_match:
                result['server'] = server_match.group(1)
                print(f"[DEBUG] Found server from cmdline: {result['server']}")
            
            # 查找 login 参数
            login_match = re.search(r'/login:(\d+)', cmd_str)
            if login_match:
                result['login'] = login_match.group(1)
                print(f"[DEBUG] Found login from cmdline: {result['login']}")
                
        except Exception as e:
            print(f"[DEBUG] Failed to parse cmdline: {e}")
        
        return result
    
    @staticmethod
    def _parse_config_files(exe_path):
        """从配置文件解析终端信息"""
        result = {'broker': "未知券商", 'login': "未知", 'server': "未知"}
        
        try:
            # MT5 配置文件路径
            config_dir = Path(exe_path).parent / "config"
            
            if not config_dir.exists():
                print(f"[DEBUG] Config directory does not exist: {config_dir}")
                return result
            
            print(f"[DEBUG] Config directory exists: {config_dir}")
            
            # 读取 common.ini
            common_ini = config_dir / "common.ini"
            if common_ini.exists():
                print(f"[DEBUG] Found common.ini")
                try:
                    with open(common_ini, 'rb') as f:
                        raw_content = f.read()
                        print(f"[DEBUG] common.ini size: {len(raw_content)} bytes")
                        
                        # 尝试 UTF-16 LE
                        try:
                            content = raw_content.decode('utf-16-le')
                            print(f"[DEBUG] Decoded as UTF-16 LE")
                        except:
                            content = raw_content.decode('utf-8', errors='ignore')
                            print(f"[DEBUG] Decoded as UTF-8")
                        
                        print(f"[DEBUG] common.ini preview: {content[:500]}")
                        
                        # 查找券商名称
                        name_match = re.search(r'(?:Company|Server|Broker)\s*=\s*(.+)', content, re.IGNORECASE)
                        if name_match:
                            result['broker'] = name_match.group(1).strip()
                            result['broker'] = ''.join(c for c in result['broker'] if ord(c) > 31)
                            print(f"[DEBUG] Found broker: {result['broker']}")
                except Exception as e:
                    print(f"[DEBUG] Error reading common.ini: {e}")
            
            # 读取 accounts.dat
            accounts_dat = config_dir / "accounts.dat"
            if accounts_dat.exists():
                print(f"[DEBUG] Found accounts.dat")
                try:
                    with open(accounts_dat, 'rb') as f:
                        raw_content = f.read()
                        print(f"[DEBUG] accounts.dat size: {len(raw_content)} bytes")
                        
                        try:
                            content = raw_content.decode('utf-16-le')
                        except:
                            content = raw_content.decode('utf-8', errors='ignore')
                        
                        print(f"[DEBUG] accounts.dat preview: {content[:500]}")
                        
                        # 查找登录信息
                        login_match = re.search(r'(?:Login|Account)\s*=\s*(\d+)', content, re.IGNORECASE)
                        server_match = re.search(r'(?:Server)\s*=\s*(.+?)(?:\r?\n|$)', content, re.IGNORECASE)
                        
                        if login_match:
                            result['login'] = login_match.group(1)
                            print(f"[DEBUG] Found login: {result['login']}")
                        
                        if server_match:
                            srv = server_match.group(1).strip()
                            srv = ''.join(c for c in srv if ord(c) > 31)
                            if srv:
                                result['server'] = srv
                                print(f"[DEBUG] Found server: {result['server']}")
                except Exception as e:
                    print(f"[DEBUG] Error reading accounts.dat: {e}")
                    
        except Exception as e:
            print(f"[DEBUG] Error parsing config files: {e}")
            import traceback
            traceback.print_exc()
        
        return result