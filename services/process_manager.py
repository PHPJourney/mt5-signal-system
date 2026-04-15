# services/process_manager.py
"""进程管理服务"""
import subprocess
import sys
from pathlib import Path


class ProcessManager:
    """管理 Master 和 Slave 进程"""
    
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.master_process = None
        self.slave_process = None
        self.master_running = False
        self.slave_running = False
    
    def start_master(self, config_path):
        """启动 Master 服务"""
        if self.master_running:
            return {'success': False, 'error': 'Master 已在运行'}
        
        try:
            # 查找 Master exe
            master_exe = self._find_executable("MT5_Master")
            if not master_exe:
                return {'success': False, 'error': '找不到 MT5_Master.exe'}
            
            # 启动进程
            self.master_process = subprocess.Popen(
                [str(master_exe), '--config', str(config_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
            
            self.master_running = True
            return {'success': True, 'pid': self.master_process.pid}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop_master(self):
        """停止 Master 服务"""
        if not self.master_running:
            return {'success': False, 'error': 'Master 未在运行'}
        
        try:
            if self.master_process:
                self.master_process.terminate()
                self.master_process.wait(timeout=5)
            
            self.master_running = False
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def start_slave(self, config_path):
        """启动 Slave 服务"""
        if self.slave_running:
            return {'success': False, 'error': 'Slave 已在运行'}
        
        try:
            # 查找 Slave exe
            slave_exe = self._find_executable("MT5_Slave")
            if not slave_exe:
                return {'success': False, 'error': '找不到 MT5_Slave.exe'}
            
            # 启动进程
            self.slave_process = subprocess.Popen(
                [str(slave_exe), '--config', str(config_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
            
            self.slave_running = True
            return {'success': True, 'pid': self.slave_process.pid}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop_slave(self):
        """停止 Slave 服务"""
        if not self.slave_running:
            return {'success': False, 'error': 'Slave 未在运行'}
        
        try:
            if self.slave_process:
                self.slave_process.terminate()
                self.slave_process.wait(timeout=5)
            
            self.slave_running = False
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _find_executable(self, name):
        """查找可执行文件"""
        possible_names = [
            f"{name}.exe",
            name,
        ]
        
        for exe_name in possible_names:
            exe_path = self.base_dir / exe_name
            if exe_path.exists():
                return exe_path
        
        return None
