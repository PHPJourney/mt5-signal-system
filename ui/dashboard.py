# ui/dashboard.py
"""仪表板模块"""
import tkinter as tk
from tkinter import ttk, messagebox


class DashboardTab:
    """仪表板选项卡"""
    
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="📊 仪表板")
        
        # 读取配置中的 enabled 状态
        master_config = app.config_manager.load_config("master_config")
        slave_config = app.config_manager.load_config("slave_config")
        self.enable_master = master_config.get('enabled', True)
        self.enable_slave = slave_config.get('enabled', True)
        
        self.create_ui()

    def create_ui(self):
        """创建仪表板界面"""
        # 主框架
        main_frame = ttk.Frame(self.frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题栏
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="TradeMind MT5 - 控制面板", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        # Python 环境状态
        if self.app.python_exe:
            env_label = ttk.Label(title_frame, 
                                 text=f"✓ Python: {self.app.python_exe}",
                                 foreground="green")
        else:
            env_label = ttk.Label(title_frame, 
                                 text="✗ Python 未安装",
                                 foreground="red")
        env_label.pack(side=tk.RIGHT)

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
            
            # 按钮框架
            master_btn_frame = ttk.Frame(self.master_status_frame)
            master_btn_frame.pack(side=tk.RIGHT)
            
            self.master_start_btn = ttk.Button(master_btn_frame, 
                                               text="启动", 
                                               command=self.start_master)
            self.master_start_btn.pack(side=tk.LEFT, padx=2)
            
            self.master_stop_btn = ttk.Button(master_btn_frame, 
                                              text="停止", 
                                              command=self.stop_master,
                                              state=tk.DISABLED)
            self.master_stop_btn.pack(side=tk.LEFT, padx=2)

        # Slave 状态
        if self.enable_slave:
            self.slave_status_frame = ttk.Frame(status_frame)
            self.slave_status_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(self.slave_status_frame, text="Slave 执行节点:", 
                     width=15).pack(side=tk.LEFT, padx=5)
            self.slave_status_label = ttk.Label(self.slave_status_frame, 
                                               text="未启动", foreground="red")
            self.slave_status_label.pack(side=tk.LEFT, padx=5)
            
            # 按钮框架
            slave_btn_frame = ttk.Frame(self.slave_status_frame)
            slave_btn_frame.pack(side=tk.RIGHT)
            
            self.slave_start_btn = ttk.Button(slave_btn_frame, 
                                              text="启动", 
                                              command=self.start_slave)
            self.slave_start_btn.pack(side=tk.LEFT, padx=2)
            
            self.slave_stop_btn = ttk.Button(slave_btn_frame, 
                                             text="停止", 
                                             command=self.stop_slave,
                                             state=tk.DISABLED)
            self.slave_stop_btn.pack(side=tk.LEFT, padx=2)

        # MT5 终端检测
        self.create_mt5_section(main_frame)

        # 刷新按钮
        refresh_frame = ttk.Frame(main_frame)
        refresh_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(refresh_frame, text="刷新状态", 
                  command=self.refresh_status).pack(side=tk.RIGHT)

        # 初始刷新
        self.refresh_status()
    
    def create_mt5_section(self, parent):
        """创建 MT5 终端检测区域"""
        mt5_frame = ttk.LabelFrame(parent, text="MT5 终端", padding="10")
        mt5_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.mt5_listbox = tk.Listbox(mt5_frame, height=5)
        self.mt5_listbox.pack(fill=tk.X, pady=5)
        
        ttk.Button(mt5_frame, text="检测 MT5 终端", 
                  command=self.detect_mt5).pack()

    def detect_mt5(self):
        """检测 MT5 终端"""
        self.mt5_listbox.delete(0, tk.END)
        terminals = self.app.mt5_detector.find_terminals()
        
        if terminals:
            for terminal in terminals:
                self.mt5_listbox.insert(tk.END, terminal.get('name', 'Unknown'))
        else:
            self.mt5_listbox.insert(tk.END, "未检测到 MT5 终端")

    def refresh_status(self):
        """刷新状态"""
        self.detect_mt5()
        
        # 更新 Master 状态
        if hasattr(self, 'master_status_label'):
            if self.app.process_manager.master_running:
                self.master_status_label.config(text="● 运行中", foreground="green")
                self.master_start_btn.config(state=tk.DISABLED)
                self.master_stop_btn.config(state=tk.NORMAL)
            else:
                self.master_status_label.config(text="● 已停止", foreground="red")
                self.master_start_btn.config(state=tk.NORMAL)
                self.master_stop_btn.config(state=tk.DISABLED)
        
        # 更新 Slave 状态
        if hasattr(self, 'slave_status_label'):
            if self.app.process_manager.slave_running:
                self.slave_status_label.config(text="● 运行中", foreground="green")
                self.slave_start_btn.config(state=tk.DISABLED)
                self.slave_stop_btn.config(state=tk.NORMAL)
            else:
                self.slave_status_label.config(text="● 已停止", foreground="red")
                self.slave_start_btn.config(state=tk.NORMAL)
                self.slave_stop_btn.config(state=tk.DISABLED)
    
    def start_master(self):
        """启动 Master"""
        config_path = self.app.config_manager.config_dir / "master_config.json"
        result = self.app.process_manager.start_master(config_path)
        
        if result['success']:
            self.master_status_label.config(text="● 运行中", foreground="green")
            self.master_start_btn.config(state=tk.DISABLED)
            self.master_stop_btn.config(state=tk.NORMAL)
            self.app.update_status("Master 服务已启动")
        else:
            messagebox.showerror("错误", result['error'])
    
    def stop_master(self):
        """停止 Master"""
        result = self.app.process_manager.stop_master()
        
        if result['success']:
            self.master_status_label.config(text="● 已停止", foreground="red")
            self.master_start_btn.config(state=tk.NORMAL)
            self.master_stop_btn.config(state=tk.DISABLED)
            self.app.update_status("Master 服务已停止")
        else:
            messagebox.showwarning("警告", result['error'])
    
    def start_slave(self):
        """启动 Slave"""
        config_path = self.app.config_manager.config_dir / "slave_config.json"
        result = self.app.process_manager.start_slave(config_path)
        
        if result['success']:
            self.slave_status_label.config(text="● 运行中", foreground="green")
            self.slave_start_btn.config(state=tk.DISABLED)
            self.slave_stop_btn.config(state=tk.NORMAL)
            self.app.update_status("Slave 服务已启动")
        else:
            messagebox.showerror("错误", result['error'])
    
    def stop_slave(self):
        """停止 Slave"""
        result = self.app.process_manager.stop_slave()
        
        if result['success']:
            self.slave_status_label.config(text="● 已停止", foreground="red")
            self.slave_start_btn.config(state=tk.NORMAL)
            self.slave_stop_btn.config(state=tk.DISABLED)
            self.app.update_status("Slave 服务已停止")
        else:
            messagebox.showwarning("警告", result['error'])