# ui/dashboard.py
"""仪表板模块"""
import tkinter as tk
from tkinter import ttk


class DashboardTab:
    """仪表板选项卡"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        # 读取配置中的 enabled 状态
        master_config = app.config_manager.load_config("master_config")
        slave_config = app.config_manager.load_config("slave_config")
        self.enable_master = master_config.get('enabled', True)
        self.enable_slave = slave_config.get('enabled', True)
        
        self.create_ui()

    def create_ui(self):
        """创建仪表板界面"""
        # 主框架
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(main_frame, text="TradeMind MT5 - 控制面板", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))

        # 系统状态
        status_frame = ttk.LabelFrame(main_frame, text="系统状态", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 10))

        # Master 状态
        if self.enable_master:
            self.master_status_frame = ttk.Frame(status_frame)
            self.master_status_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(self.master_status_frame, text="Master 策略引擎:", 
                     width=15).pack(side=tk.LEFT, padx=5)
            self.master_status_label = ttk.Label(self.master_status_frame, 
                                                text="未启动", foreground="red")
            self.master_status_label.pack(side=tk.LEFT, padx=5)
            
            self.master_start_btn = ttk.Button(self.master_status_frame, 
                                               text="启动", 
                                               command=self.start_master)
            self.master_start_btn.pack(side=tk.RIGHT, padx=5)

        # Slave 状态
        if self.enable_slave:
            self.slave_status_frame = ttk.Frame(status_frame)
            self.slave_status_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(self.slave_status_frame, text="Slave 执行节点:", 
                     width=15).pack(side=tk.LEFT, padx=5)
            self.slave_status_label = ttk.Label(self.slave_status_frame, 
                                               text="未启动", foreground="red")
            self.slave_status_label.pack(side=tk.LEFT, padx=5)
            
            self.slave_start_btn = ttk.Button(self.slave_status_frame, 
                                              text="启动", 
                                              command=self.start_slave)
            self.slave_start_btn.pack(side=tk.RIGHT, padx=5)

        # MT5 终端检测
        self.create_mt5_section(main_frame)

        # 刷新按钮
        refresh_frame = ttk.Frame(main_frame)
        refresh_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(refresh_frame, text="刷新状态", 
                  command=self.refresh_status).pack(side=tk.RIGHT)

        # 初始刷新
        self.refresh_status()
    
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
