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

# 导入国际化模块
from common.i18n import init_i18n, _

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
        # 初始化国际化
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent
        init_i18n(base_dir)
        
        self.root = root
        self.root.title(_("APP_TITLE"))
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # 设置窗口图标（PNG 格式）
        self.setup_icon()

        # 基础路径（兼容 PyInstaller）
        self.base_dir = base_dir

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
        menubar.add_cascade(label=_("MENU_FILE"), menu=file_menu)
        file_menu.add_command(label=_("MENU_OPEN_CONFIG_FOLDER"), command=self.open_config_folder)
        file_menu.add_command(label=_("MENU_OPEN_LOGS_FOLDER"), command=self.open_logs_folder)
        file_menu.add_separator()
        file_menu.add_command(label=_("MENU_EXIT"), command=self.root.quit)

        # 工具菜单（移除 Python 安装选项，exe 已包含运行时）
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=_("MENU_TOOLS"), menu=tools_menu)
        tools_menu.add_command(label=_("MENU_CLEAR_LOGS"), command=self.clear_logs)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=_("MENU_HELP"), menu=help_menu)
        help_menu.add_command(label=_("MENU_ABOUT"), command=self.show_about)

    def create_main_ui(self):
        """创建主界面"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 始终显示所有选项卡
        self.dashboard_tab = DashboardTab(self.notebook, self)
        MasterConfigTab(self.notebook, self)
        SlaveConfigTab(self.notebook, self)
        self.monitoring_tab = MonitoringTab(self.notebook, self)
        LogsTab(self.notebook, self)
        
        # 启动定期进程状态检测（每 3 秒检查一次）
        self.schedule_process_check()

    def schedule_process_check(self):
        """定期检测进程真实状态"""
        try:
            # 检查进程状态
            self.process_manager.check_all_processes()
            
            # 刷新 UI 显示
            if hasattr(self, 'dashboard_tab'):
                self.dashboard_tab.refresh_status()
            
            if hasattr(self, 'monitoring_tab'):
                self.monitoring_tab.refresh_status()
                
        except Exception as e:
            pass
        finally:
            # 每 3 秒检查一次
            self.root.after(3000, self.schedule_process_check)

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
            messagebox.showinfo(_("MSG_INFO"), _("LOGS_NO_LOGS"))
            return
        
        try:
            for log_file in self.logs_dir.glob("*.log"):
                log_file.unlink()
            messagebox.showinfo(_("MSG_SUCCESS"), _("MSG_LOGS_CLEARED"))
        except Exception as e:
            messagebox.showerror(_("MSG_ERROR"), f"{_('CONFIG_ERROR')}: {e}")

    def show_about(self):
        """显示关于对话框"""
        messagebox.showinfo(
            _("ABOUT_TITLE"),
            _("ABOUT_TEXT")
        )


def main():
    """入口函数"""
    root = tk.Tk()
    app = MT5ManagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()