# ui/dashboard.py
"""仪表板模块"""
import tkinter as tk
from tkinter import ttk


class DashboardTab:
    """仪表板选项卡"""
    
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="📊 仪表板")
        
        self.create_ui()
    
    def create_ui(self):
        """创建仪表板界面"""
        # 标题
        title_label = ttk.Label(
            self.frame,
            text="MT5 信号管理系统",
            font=("Microsoft YaHei", 18, "bold")
        )
        title_label.pack(pady=20)

        # 显示安装模式
        mode_text = []
        if self.app.install_config.get('enable_master', True):
            mode_text.append("Master")
        if self.app.install_config.get('enable_slave', True):
            mode_text.append("Slave")
        
        mode_label = ttk.Label(
            self.frame,
            text=f"运行模式: {' + '.join(mode_text)}",
            font=("Microsoft YaHei", 12),
            foreground="blue"
        )
        mode_label.pack(pady=5)

        # 状态卡片容器
        status_frame = ttk.Frame(self.frame)
        status_frame.pack(fill=tk.X, padx=20, pady=10)

        # Master 状态卡片
        if self.app.install_config.get('enable_master', True):
            master_card = ttk.LabelFrame(status_frame, text="Master Server", padding=15)
            master_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            self.master_status_label = ttk.Label(
                master_card,
                text="● 已停止",
                font=("Microsoft YaHei", 12),
                foreground="red"
            )
            self.master_status_label.pack(pady=5)

            ttk.Button(
                master_card,
                text="启动 Master",
                command=self.start_master,
                width=15
            ).pack(pady=5)

            ttk.Button(
                master_card,
                text="停止 Master",
                command=self.stop_master,
                width=15
            ).pack(pady=5)

        # Slave 状态卡片
        if self.app.install_config.get('enable_slave', True):
            slave_card = ttk.LabelFrame(status_frame, text="Slave Server", padding=15)
            slave_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            self.slave_status_label = ttk.Label(
                slave_card,
                text="● 已停止",
                font=("Microsoft YaHei", 12),
                foreground="red"
            )
            self.slave_status_label.pack(pady=5)

            ttk.Button(
                slave_card,
                text="启动 Slave",
                command=self.start_slave,
                width=15
            ).pack(pady=5)

            ttk.Button(
                slave_card,
                text="停止 Slave",
                command=self.stop_slave,
                width=15
            ).pack(pady=5)
    
    def start_master(self):
        """启动 Master"""
        config_path = self.app.config_manager.config_dir / "master_config.json"
        result = self.app.process_manager.start_master(config_path)
        
        if result['success']:
            self.master_status_label.config(text="● 运行中", foreground="green")
            self.app.update_status("Master 服务已启动")
        else:
            from tkinter import messagebox
            messagebox.showerror("错误", result['error'])
    
    def stop_master(self):
        """停止 Master"""
        result = self.app.process_manager.stop_master()
        
        if result['success']:
            self.master_status_label.config(text="● 已停止", foreground="red")
            self.app.update_status("Master 服务已停止")
        else:
            from tkinter import messagebox
            messagebox.showwarning("警告", result['error'])
    
    def start_slave(self):
        """启动 Slave"""
        config_path = self.app.config_manager.config_dir / "slave_config.json"
        result = self.app.process_manager.start_slave(config_path)
        
        if result['success']:
            self.slave_status_label.config(text="● 运行中", foreground="green")
            self.app.update_status("Slave 服务已启动")
        else:
            from tkinter import messagebox
            messagebox.showerror("错误", result['error'])
    
    def stop_slave(self):
        """停止 Slave"""
        result = self.app.process_manager.stop_slave()
        
        if result['success']:
            self.slave_status_label.config(text="● 已停止", foreground="red")
            self.app.update_status("Slave 服务已停止")
        else:
            from tkinter import messagebox
            messagebox.showwarning("警告", result['error'])
