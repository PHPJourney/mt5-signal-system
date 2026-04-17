# ui/dashboard.py
"""仪表板模块"""
import tkinter as tk
from tkinter import ttk, messagebox
from common.i18n import _


class DashboardTab:
    """仪表板选项卡"""
    
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text=_("TAB_DASHBOARD"))
        
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
        
        title_label = ttk.Label(title_frame, text=_("DASHBOARD_TITLE"), 
                               font=('Arial', 16, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        # 系统状态（exe 独立运行，无需外部 Python）
        env_label = ttk.Label(title_frame, 
                             text=_("STANDALONE_MODE"),
                             foreground="green")
        env_label.pack(side=tk.RIGHT)

        # 系统状态
        status_frame = ttk.LabelFrame(main_frame, text=_("SYSTEM_STATUS"), padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 10))

        # Master 状态
        if self.enable_master:
            self.master_status_frame = ttk.Frame(status_frame)
            self.master_status_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(self.master_status_frame, text=_("MASTER_ENGINE"), 
                     width=20).pack(side=tk.LEFT, padx=5)
            self.master_status_label = ttk.Label(self.master_status_frame, 
                                                text=_("STATUS_STOPPED"), foreground="red")
            self.master_status_label.pack(side=tk.LEFT, padx=5)
            
            # 按钮框架
            master_btn_frame = ttk.Frame(self.master_status_frame)
            master_btn_frame.pack(side=tk.RIGHT)
            
            self.master_start_btn = ttk.Button(master_btn_frame, 
                                               text=_("BTN_START"), 
                                               command=self.start_master)
            self.master_start_btn.pack(side=tk.LEFT, padx=2)
            
            self.master_stop_btn = ttk.Button(master_btn_frame, 
                                              text=_("BTN_STOP"), 
                                              command=self.stop_master,
                                              state=tk.DISABLED)
            self.master_stop_btn.pack(side=tk.LEFT, padx=2)

        # Slave 状态
        if self.enable_slave:
            self.slave_status_frame = ttk.Frame(status_frame)
            self.slave_status_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(self.slave_status_frame, text=_("SLAVE_NODE"), 
                     width=20).pack(side=tk.LEFT, padx=5)
            self.slave_status_label = ttk.Label(self.slave_status_frame, 
                                               text=_("STATUS_STOPPED"), foreground="red")
            self.slave_status_label.pack(side=tk.LEFT, padx=5)
            
            # 按钮框架
            slave_btn_frame = ttk.Frame(self.slave_status_frame)
            slave_btn_frame.pack(side=tk.RIGHT)
            
            self.slave_start_btn = ttk.Button(slave_btn_frame, 
                                              text=_("BTN_START"), 
                                              command=self.start_slave)
            self.slave_start_btn.pack(side=tk.LEFT, padx=2)
            
            self.slave_stop_btn = ttk.Button(slave_btn_frame, 
                                             text=_("BTN_STOP"), 
                                             command=self.stop_slave,
                                             state=tk.DISABLED)
            self.slave_stop_btn.pack(side=tk.LEFT, padx=2)

        # MT5 终端检测
        self.create_mt5_section(main_frame)

        # 刷新按钮
        refresh_frame = ttk.Frame(main_frame)
        refresh_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(refresh_frame, text=_("BTN_REFRESH"), 
                  command=self.refresh_status).pack(side=tk.RIGHT)

        # 初始刷新
        self.refresh_status()
    
    def create_mt5_section(self, parent):
        """创建 MT5 终端检测区域"""
        mt5_frame = ttk.LabelFrame(parent, text=_("MT5_TERMINAL"), padding="10")
        mt5_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.mt5_listbox = tk.Listbox(mt5_frame, height=5)
        self.mt5_listbox.pack(fill=tk.X, pady=5)
        
        ttk.Button(mt5_frame, text=_("BTN_DETECT_MT5"), 
                  command=self.detect_mt5).pack()

    def detect_mt5(self):
        """检测 MT5 终端"""
        self.mt5_listbox.delete(0, tk.END)
        terminals = self.app.mt5_detector.detect_terminals()
        
        if terminals:
            for terminal in terminals:
                # 显示: 券商 - 账号 | 服务器
                display = f"{terminal.get('broker', 'Unknown')} - 账号:{terminal.get('login', 'N/A')} | 服务器:{terminal.get('server', 'N/A')}"
                self.mt5_listbox.insert(tk.END, display)
        else:
            self.mt5_listbox.insert(tk.END, _("NO_MT5_DETECTED"))
    
    def refresh_status(self):
        """刷新状态"""
        self.detect_mt5()
        
        # 更新 Master 状态（根据 process_manager 的标记）
        if hasattr(self, 'master_status_label'):
            if self.app.process_manager.master_running:
                self.master_status_label.config(text=_("STATUS_RUNNING"), foreground="green")
                self.master_start_btn.config(state=tk.DISABLED)
                self.master_stop_btn.config(state=tk.NORMAL)
            else:
                self.master_status_label.config(text=_("STATUS_STOPPED"), foreground="red")
                self.master_start_btn.config(state=tk.NORMAL)
                self.master_stop_btn.config(state=tk.DISABLED)
        
        # 更新 Slave 状态（根据 process_manager 的标记）
        if hasattr(self, 'slave_status_label'):
            if self.app.process_manager.slave_running:
                self.slave_status_label.config(text=_("STATUS_RUNNING"), foreground="green")
                self.slave_start_btn.config(state=tk.DISABLED)
                self.slave_stop_btn.config(state=tk.NORMAL)
            else:
                self.slave_status_label.config(text=_("STATUS_STOPPED"), foreground="red")
                self.slave_start_btn.config(state=tk.NORMAL)
                self.slave_stop_btn.config(state=tk.DISABLED)

    def start_master(self):
        """启动 Master"""
        config_path = self.app.config_manager.config_dir / "master_config.json"
        result = self.app.process_manager.start_master(config_path)
        
        if result['success']:
            self.master_status_label.config(text=_("STATUS_RUNNING"), foreground="green")
            self.master_start_btn.config(state=tk.DISABLED)
            self.master_stop_btn.config(state=tk.NORMAL)
            self.app.update_status(_("MSG_MASTER_STARTED"))
        else:
            messagebox.showerror(_("MSG_ERROR"), result['error'])
    
    def stop_master(self):
        """停止 Master"""
        result = self.app.process_manager.stop_master()
        
        if result['success']:
            self.master_status_label.config(text=_("STATUS_STOPPED"), foreground="red")
            self.master_start_btn.config(state=tk.NORMAL)
            self.master_stop_btn.config(state=tk.DISABLED)
            self.app.update_status(_("MSG_MASTER_STOPPED"))
        else:
            messagebox.showwarning(_("MSG_WARNING"), result['error'])
    
    def start_slave(self):
        """启动 Slave"""
        config_path = self.app.config_manager.config_dir / "slave_config.json"
        result = self.app.process_manager.start_slave(config_path)
        
        if result['success']:
            self.slave_status_label.config(text=_("STATUS_RUNNING"), foreground="green")
            self.slave_start_btn.config(state=tk.DISABLED)
            self.slave_stop_btn.config(state=tk.NORMAL)
            self.app.update_status(_("MSG_SLAVE_STARTED"))
        else:
            messagebox.showerror(_("MSG_ERROR"), result['error'])
    
    def stop_slave(self):
        """停止 Slave"""
        result = self.app.process_manager.stop_slave()
        
        if result['success']:
            self.slave_status_label.config(text=_("STATUS_STOPPED"), foreground="red")
            self.slave_start_btn.config(state=tk.NORMAL)
            self.slave_stop_btn.config(state=tk.DISABLED)
            self.app.update_status(_("MSG_SLAVE_STOPPED"))
        else:
            messagebox.showwarning(_("MSG_WARNING"), result['error'])