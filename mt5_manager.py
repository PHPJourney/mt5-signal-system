"""
TradeMind MT5 - 智能交易策略管理平台
最终整合版本
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import subprocess
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
if getattr(sys, 'frozen', False):
    project_root = Path(sys.executable).parent
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
    """TradeMind MT5 智能交易策略管理系统主应用"""

    def __init__(self, root):
        self.root = root
        self.root.title("TradeMind MT5 - 智能交易策略管理")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # 设置窗口图标（PNG 格式）
        self.setup_icon()

        # 基础路径（兼容 PyInstaller）
        if getattr(sys, 'frozen', False):
            self.base_dir = Path(sys.executable).parent
        else:
            self.base_dir = Path(__file__).parent

        # 目录
        self.config_dir = self.base_dir / "config"
        self.logs_dir = self.base_dir / "logs"
        
        self.config_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

        # 初始化服务
        self.config_manager = ConfigManager(self.base_dir)
        self.process_manager = ProcessManager(self.base_dir)
        self.mt5_detector = MT5Detector()

        # 加载配置
        self.master_config = self.config_manager.load_config("master_config")
        self.slave_config = self.config_manager.load_config("slave_config")

        # 创建界面
        self.create_menu_bar()
        self.create_main_ui()

    def setup_icon(self):
        """设置窗口图标（使用 PNG 格式）"""
        try:
            if getattr(sys, 'frozen', False):
                icon_path = Path(sys.executable).parent / "icon.png"
            else:
                icon_path = Path(__file__).parent / "icon.png"
            
            if icon_path.exists():
                icon = tk.PhotoImage(file=str(icon_path))
                self.root.iconphoto(True, icon)
        except Exception as e:
            # 图标加载失败不影响主程序
            pass

    def create_menu_bar(self):
        """创建顶部菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="打开配置文件夹", command=self.open_config_folder)
        file_menu.add_command(label="打开日志文件夹", command=self.open_logs_folder)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)

        # 工具菜单（移除 Python 安装选项，exe 已包含运行时）
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="清理日志", command=self.clear_logs)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)

    def create_main_ui(self):
        """创建主界面"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 始终显示所有选项卡
        DashboardTab(self.notebook, self)
        MasterConfigTab(self.notebook, self)
        SlaveConfigTab(self.notebook, self)
        MonitoringTab(self.notebook, self)
        LogsTab(self.notebook, self)

    def update_status(self, message):
        """更新状态栏消息"""
        if hasattr(self, 'status_var'):
            self.status_var.set(message)

    # ===== 菜单功能实现 =====

    def open_config_folder(self):
        """打开配置文件夹"""
        if sys.platform == 'win32':
            os.startfile(str(self.config_dir))
        elif sys.platform == 'darwin':
            subprocess.run(['open', str(self.config_dir)])
        else:
            subprocess.run(['xdg-open', str(self.config_dir)])

    def open_logs_folder(self):
        """打开日志文件夹"""
        if sys.platform == 'win32':
            os.startfile(str(self.logs_dir))
        elif sys.platform == 'darwin':
            subprocess.run(['open', str(self.logs_dir)])
        else:
            subprocess.run(['xdg-open', str(self.logs_dir)])

    def clear_logs(self):
        """清理日志文件"""
        if not self.logs_dir.exists():
            messagebox.showinfo("提示", "日志文件夹不存在")
            return
        
        try:
            for log_file in self.logs_dir.glob("*.log"):
                log_file.unlink()
            messagebox.showinfo("成功", "日志文件已清理")
        except Exception as e:
            messagebox.showerror("错误", f"清理失败: {e}")

    def show_about(self):
        """显示关于对话框"""
        messagebox.showinfo(
            "关于 TradeMind MT5",
            "TradeMind MT5 v1.0\n\n"
            "智能交易策略管理平台\n\n"
            "功能：\n"
            "- Master 策略引擎管理\n"
            "- Slave 执行节点管理\n"
            "- MQTT 信号分发\n"
            "- 实时监控和日志\n\n"
            "© 2024 TradeMind"
        )


def main():
    """入口函数"""
    root = tk.Tk()
    app = MT5ManagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()