"""
MT5 Signal System - 综合管理面板
模块化版本
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入服务层
from services.mt5_detector import MT5Detector
from services.process_manager import ProcessManager
from services.config_manager import ConfigManager

# 导入 UI 组件
from ui.dashboard import DashboardTab
from ui.master_config import MasterConfigTab
from ui.slave_config import SlaveConfigTab
from ui.monitoring import MonitoringTab
from ui.logs import LogsTab


class MT5ManagerApp:
    """MT5 信号管理系统主应用"""

    def __init__(self, root):
        self.root = root
        self.root.title("MT5 Signal System - 管理平台")
        self.root.geometry("1200x800")

        # 基础路径
        if getattr(sys, 'frozen', False):
            self.base_dir = Path(sys.executable).parent
        else:
            self.base_dir = Path(__file__).parent

        # 初始化服务
        self.config_manager = ConfigManager(self.base_dir)
        self.process_manager = ProcessManager(self.base_dir)
        self.mt5_detector = MT5Detector()

        # 加载配置
        self.install_config = self.config_manager.load_install_config()
        self.master_config = self.config_manager.load_config("master_config")
        self.slave_config = self.config_manager.load_config("slave_config")

        # 创建界面
        self.create_main_ui()

    def create_main_ui(self):
        """创建主界面"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 根据安装配置创建选项卡
        enable_master = self.install_config.get('enable_master', True)
        enable_slave = self.install_config.get('enable_slave', True)

        # 仪表板
        DashboardTab(self.notebook, self)

        # Master 配置
        if enable_master:
            MasterConfigTab(self.notebook, self)

        # Slave 配置
        if enable_slave:
            SlaveConfigTab(self.notebook, self)

        # 监控
        if enable_master or enable_slave:
            MonitoringTab(self.notebook, self)

        # 日志
        LogsTab(self.notebook, self)

        # 状态栏
        self.create_status_bar()

    def create_status_bar(self):
        """创建状态栏"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(status_frame, text="就绪", anchor=tk.W)
        self.status_label.pack(fill=tk.X, padx=5, pady=2)

    def update_status(self, message):
        """更新状态栏"""
        self.status_label.config(text=message)


def main():
    """主入口"""
    root = tk.Tk()
    app = MT5ManagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()