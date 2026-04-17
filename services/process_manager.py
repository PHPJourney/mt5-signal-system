# services/process_manager.py
"""进程管理服务"""
import subprocess
import sys
import time
from pathlib import Path


class ProcessManager:
    """管理 Master 和 Slave 进程"""
    
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.master_process = None
        self.slave_process = None
        self.master_running = False
        self.slave_running = False
    
    def _check_process_alive(self, process):
        """
        检查进程是否仍然存活
        
        Args:
            process: subprocess.Popen 对象
            
        Returns:
            bool: True=进程存活, False=进程已退出
        """
        if process is None:
            return False
        
        # poll() 返回 None 表示进程仍在运行
        # 返回退出码表示进程已退出
        return process.poll() is None
    
    def start_master(self, config_path):
        """启动 Master 服务"""
        if self.master_running and self._check_process_alive(self.master_process):
            return {'success': False, 'error': 'Master 已在运行'}
        
        try:
            # 查找 Master exe
            master_exe = self._find_executable("MT5_Master")
            if not master_exe:
                return {'success': False, 'error': f'找不到 Master 可执行文件 (尝试过: MT5_Master_Panel.exe, MT5_Master.exe)'}
            
            # 启动进程（不捕获输出，让它在独立终端显示）
            self.master_process = subprocess.Popen(
                [str(master_exe), '--config', str(config_path)],
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
            
            self.master_running = True
            return {'success': True, 'pid': self.master_process.pid}
            
        except Exception as e:
            self.master_running = False
            return {'success': False, 'error': str(e)}
    
    def stop_master(self):
        """停止 Master 服务"""
        if not self.master_running:
            return {'success': False, 'error': 'Master 未在运行'}
        
        try:
            if self.master_process:
                self.master_process.terminate()
                try:
                    self.master_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.master_process.kill()
                    self.master_process.wait()
            
            self.master_running = False
            self.master_process = None
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def start_slave(self, config_path):
        """启动 Slave 服务"""
        if self.slave_running and self._check_process_alive(self.slave_process):
            return {'success': False, 'error': 'Slave 已在运行'}
        
        try:
            # 查找 Slave exe
            slave_exe = self._find_executable("MT5_Slave")
            if not slave_exe:
                return {'success': False, 'error': f'找不到 Slave 可执行文件 (尝试过: MT5_Slave_Panel.exe, MT5_Slave.exe)'}
            
            # 启动进程（不捕获输出，让它在独立终端显示）
            self.slave_process = subprocess.Popen(
                [str(slave_exe), '--config', str(config_path)],
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
            
            self.slave_running = True
            return {'success': True, 'pid': self.slave_process.pid}
            
        except Exception as e:
            self.slave_running = False
            return {'success': False, 'error': str(e)}
    
    def stop_slave(self):
        """停止 Slave 服务"""
        if not self.slave_running:
            return {'success': False, 'error': 'Slave 未在运行'}
        
        try:
            if self.slave_process:
                self.slave_process.terminate()
                try:
                    self.slave_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.slave_process.kill()
                    self.slave_process.wait()
            
            self.slave_running = False
            self.slave_process = None
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def check_all_processes(self):
        """
        检查所有进程的真实状态
        优先使用心跳文件检测，其次使用 poll() 检测
        """
        import time
        
        # 检查 Master 进程
        master_alive = False
        if self.master_process:
            # 方法1: 检查进程是否存活
            if self._check_process_alive(self.master_process):
                master_alive = True
            else:
                self.master_running = False
                self.master_process = None
        
        # 方法2: 检查心跳文件（更可靠）
        master_heartbeat = self.base_dir / 'logs' / 'master.heartbeat'
        if master_heartbeat.exists():
            try:
                with open(master_heartbeat, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        last_heartbeat_time = float(lines[0].strip())
                        current_time = time.time()
                        # 如果心跳文件在 60 秒内更新过，认为进程存活
                        if current_time - last_heartbeat_time < 60:
                            master_alive = True
                            self.master_running = True
                            # 只有心跳文件有效时才标记为运行
                        else:
                            # 心跳超时，进程可能卡死
                            self.master_running = False
                            self.master_process = None
            except Exception:
                pass
        
        if not master_alive:
            self.master_running = False
        
        # 检查 Slave 进程
        slave_alive = False
        if self.slave_process:
            # 方法1: 检查进程是否存活
            if self._check_process_alive(self.slave_process):
                slave_alive = True
            else:
                self.slave_running = False
                self.slave_process = None
        
        # 方法2: 检查心跳文件（更可靠）
        slave_heartbeat = self.base_dir / 'logs' / 'slave.heartbeat'
        if slave_heartbeat.exists():
            try:
                with open(slave_heartbeat, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        last_heartbeat_time = float(lines[0].strip())
                        current_time = time.time()
                        # 如果心跳文件在 60 秒内更新过，认为进程存活
                        if current_time - last_heartbeat_time < 60:
                            slave_alive = True
                            self.slave_running = True
                        else:
                            # 心跳超时，进程可能卡死
                            self.slave_running = False
                            self.slave_process = None
            except Exception:
                pass
        
        if not slave_alive:
            self.slave_running = False
    
    def _find_executable(self, name):
        """查找可执行文件"""
        possible_names = [
            f"{name}_Panel.exe",     # GitHub Actions 打包的实际名称
            f"{name}.exe",
            name,
        ]
        
        for exe_name in possible_names:
            exe_path = self.base_dir / exe_name
            if exe_path.exists():
                return exe_path
        
        return None