"""Master 配置模块"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from common.i18n import _


class MasterConfigTab:
    """Master 配置选项卡"""
    
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text=_("TAB_MASTER_CONFIG"))
        
        # 创建变量（先创建空变量）
        self._create_variables()
        
        # 加载配置到 UI
        self.load_config_to_ui()
        
        self.create_ui()
    
    def _create_variables(self):
        """创建 Tk 变量"""
        # MT5 终端
        self.mt5_terminal_var = tk.StringVar()
        self.mt5_path_var = tk.StringVar()
        
        # 策略ID
        self.strategy_id_var = tk.StringVar(value="STRATEGY_001")
        
        # MQTT
        self.broker_var = tk.StringVar()
        self.port_var = tk.IntVar()
        self.mqtt_user_var = tk.StringVar()
        self.mqtt_pass_var = tk.StringVar()
        self.client_id_var = tk.StringVar()
        
        # 账户上报
        self.reporter_proxy_var = tk.StringVar()
        self.reporter_interval_var = tk.IntVar()
        
        # 通用配置
        self.magic_number_var = tk.IntVar()
        self.slippage_points_var = tk.IntVar()
        self.comment_prefix_var = tk.StringVar()
    
    def load_config_to_ui(self):
        """从配置文件加载到 UI"""
        # 重新读取配置
        self.config = self.app.config_manager.load_config("master_config")
        self.app.master_config = self.config  # 同步到 app
        
        # 策略ID
        self.strategy_id_var.set(self.config.get('strategy_id', 'STRATEGY_001'))
        
        # MT5 终端
        self.mt5_path_var.set(self.config.get('mt5', {}).get('terminal_path', ''))
        
        # MQTT
        mqtt_config = self.config.get('mqtt', {})
        self.broker_var.set(mqtt_config.get('broker', 'localhost'))
        self.port_var.set(mqtt_config.get('port', 1883))
        self.mqtt_user_var.set(mqtt_config.get('username', ''))
        self.mqtt_pass_var.set(mqtt_config.get('password', ''))
        self.client_id_var.set(mqtt_config.get('client_id', 'master_001'))
        
        # 账户上报
        reporter_config = self.config.get('account_reporter', {})
        self.reporter_proxy_var.set(reporter_config.get('proxy_url', 'http://localhost:5000'))
        self.reporter_interval_var.set(reporter_config.get('interval', 60))
        
        # 通用配置
        common_config = self.config.get('common', {})
        self.magic_number_var.set(common_config.get('magic_number', 123456))
        self.slippage_points_var.set(common_config.get('slippage_points', 30))
        self.comment_prefix_var.set(common_config.get('comment_prefix', 'TM_'))
        
        print("✓ Master 配置已加载到 UI")
    
    def create_ui(self):
        """创建配置界面"""
        # 创建滚动区域
        canvas = tk.Canvas(self.frame)
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # MT5 终端选择
        self._create_mt5_terminal_section(scrollable_frame)
        
        # 自动检测 MT5 终端
        self.auto_detect_terminals()
        
        # 策略配置
        self._create_strategy_section(scrollable_frame)
        
        # MQTT 配置
        self._create_mqtt_section(scrollable_frame)
        
        # 账户上报
        self._create_reporter_section(scrollable_frame)
        
        # 通用配置
        self._create_common_section(scrollable_frame)
        
        # 按钮区域
        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        # 重新加载按钮
        ttk.Button(
            btn_frame,
            text=_("BTN_REFRESH"),
            command=self.reload_config,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        # 保存按钮
        ttk.Button(
            btn_frame,
            text=_("BTN_SAVE"),
            command=self.save_config,
            width=20
        ).pack(side=tk.RIGHT, padx=5)
    
    def auto_detect_terminals(self):
        """自动检测 MT5 终端（静默模式，不显示提示框）"""
        try:
            terminals = self.app.mt5_detector.detect_terminals()
            
            if not terminals:
                # 没有检测到终端，保持默认显示
                return
            
            # 格式化终端信息
            terminal_options = []
            self.terminals_data = terminals
            
            for term in terminals:
                display_text = f"{term['broker']} - 账号: {term['login']} | 服务器: {term['server']}"
                terminal_options.append(display_text)
            
            # 更新下拉框
            self.mt5_terminal_combo['values'] = terminal_options
            if terminal_options:
                # 尝试匹配已保存的路径
                saved_path = self.mt5_path_var.get()
                if saved_path:
                    for idx, term in enumerate(terminals):
                        if term['path'] == saved_path:
                            self.mt5_terminal_combo.current(idx)
                            self.on_terminal_selected(None)
                            return
                
                # 如果没有保存的路径，选择第一个
                self.mt5_terminal_combo.current(0)
                self.on_terminal_selected(None)
            
            # 绑定选择事件
            self.mt5_terminal_combo.bind('<<ComboboxSelected>>', self.on_terminal_selected)
            
        except Exception as e:
            print(f"自动检测 MT5 终端失败: {e}")
    
    def reload_config(self):
        """重新加载配置"""
        self.load_config_to_ui()
        messagebox.showinfo(_("MSG_INFO"), _("MSG_CONFIG_LOADED"))
        self.app.update_status(_("MSG_CONFIG_LOADED"))
    
    def _create_mt5_terminal_section(self, parent):
        """创建 MT5 终端选择区域"""
        mt5_terminal_frame = ttk.LabelFrame(parent, text=_("CONFIG_MT5_SETTINGS"), padding=10)
        mt5_terminal_frame.pack(fill=tk.X, padx=10, pady=5)

        # 终端列表框架
        terminal_list_frame = ttk.Frame(mt5_terminal_frame)
        terminal_list_frame.pack(fill=tk.X, pady=5)

        ttk.Label(terminal_list_frame, text=_("CONFIG_TERMINAL_PATH")).pack(side=tk.LEFT, padx=5)
        
        # MT5 终端下拉框
        self.mt5_terminal_combo = ttk.Combobox(
            terminal_list_frame, 
            textvariable=self.mt5_terminal_var,
            width=50,
            state="readonly"
        )
        self.mt5_terminal_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 刷新按钮
        ttk.Button(
            terminal_list_frame,
            text=_("BTN_REFRESH"),
            command=self.refresh_terminals,
            width=10
        ).pack(side=tk.LEFT, padx=5)

        # 显示终端详细信息
        self.terminal_info_label = ttk.Label(
            mt5_terminal_frame,
            text=_("BTN_DETECT_MT5"),
            foreground="gray",
            wraplength=600,
            justify=tk.LEFT
        )
        self.terminal_info_label.pack(anchor=tk.W, pady=5)
        
        # MT5 路径（手动输入）
        path_frame = ttk.Frame(mt5_terminal_frame)
        path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(path_frame, text=_("CONFIG_TERMINAL_PATH")).pack(side=tk.LEFT, padx=5)
        ttk.Entry(path_frame, textvariable=self.mt5_path_var, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            path_frame,
            text=_("BTN_BROWSE"),
            command=lambda: self.browse_folder(self.mt5_path_var)
        ).pack(side=tk.LEFT, padx=5)
    
    def _create_strategy_section(self, parent):
        """创建策略ID区域"""
        strategy_frame = ttk.LabelFrame(parent, text="策略配置", padding=10)
        strategy_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        ttk.Label(strategy_frame, text="策略ID (Strategy ID)").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(strategy_frame, textvariable=self.strategy_id_var, width=40).grid(row=row, column=1, padx=5)
        ttk.Label(strategy_frame, text="(用于统一订阅频道)", foreground="gray").grid(row=row, column=2, sticky=tk.W)
        row += 1
        
        info_text = "说明：\n" \
                   "• 所有 Slave 必须配置与 Master 相同的策略ID\n" \
                   "• 信号将发布到: trademind/signals/{strategy_id}/trade\n" \
                   "• 不同策略使用不同的 ID，互不干扰"
        ttk.Label(strategy_frame, text=info_text, foreground="blue", justify=tk.LEFT).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, pady=5
        )
    
    def _create_reporter_section(self, parent):
        """创建账户上报配置区域"""
        reporter_frame = ttk.LabelFrame(parent, text="账户上报配置", padding=10)
        reporter_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        ttk.Label(reporter_frame, text="Auth Proxy URL").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(reporter_frame, textvariable=self.reporter_proxy_var, width=40).grid(row=row, column=1, padx=5)
        ttk.Label(reporter_frame, text="(如: http://154.36.184.20:5000)", foreground="gray").grid(row=row, column=2, sticky=tk.W)
        row += 1

        ttk.Label(reporter_frame, text="上报间隔(秒)").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(reporter_frame, from_=10, to=300, increment=10, textvariable=self.reporter_interval_var, width=38).grid(row=row, column=1, padx=5)
        ttk.Label(reporter_frame, text="(默认 60 秒)", foreground="gray").grid(row=row, column=2, sticky=tk.W)
    
    def _create_common_section(self, parent):
        """创建通用配置区域"""
        common_frame = ttk.LabelFrame(parent, text="通用配置", padding=10)
        common_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        ttk.Label(common_frame, text="Magic Number").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(common_frame, from_=0, to=999999, textvariable=self.magic_number_var, width=38).grid(row=row, column=1, padx=5)
        ttk.Label(common_frame, text="(订单魔术码，用于识别)", foreground="gray").grid(row=row, column=2, sticky=tk.W)
        row += 1

        ttk.Label(common_frame, text="滑点点数").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(common_frame, from_=0, to=100, textvariable=self.slippage_points_var, width=38).grid(row=row, column=1, padx=5)
        ttk.Label(common_frame, text="(允许的价格偏差)", foreground="gray").grid(row=row, column=2, sticky=tk.W)
        row += 1

        ttk.Label(common_frame, text="订单注释前缀").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(common_frame, textvariable=self.comment_prefix_var, width=40).grid(row=row, column=1, padx=5)
        ttk.Label(common_frame, text="(如: TM_)", foreground="gray").grid(row=row, column=2, sticky=tk.W)
    
    def _create_signal_section(self, parent):
        """创建信号配置区域（已废弃，保留兼容）"""
        # 这个区域可以隐藏或删除
        pass
    
    def _create_mqtt_section(self, parent):
        """创建 MQTT 配置区域"""
        mqtt_frame = ttk.LabelFrame(parent, text=_("CONFIG_MQTT_SETTINGS"), padding=10)
        mqtt_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        ttk.Label(mqtt_frame, text=_("CONFIG_BROKER")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(mqtt_frame, textvariable=self.broker_var, width=40).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(mqtt_frame, text=_("CONFIG_PORT")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(mqtt_frame, from_=1, to=65535, textvariable=self.port_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(mqtt_frame, text=_("CONFIG_USERNAME")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(mqtt_frame, textvariable=self.mqtt_user_var, width=40).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(mqtt_frame, text=_("CONFIG_PASSWORD")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(mqtt_frame, textvariable=self.mqtt_pass_var, show="*", width=40).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(mqtt_frame, text=_("CONFIG_CLIENT_ID")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(mqtt_frame, textvariable=self.client_id_var, width=40).grid(row=row, column=1, padx=5)
    
    def refresh_terminals(self):
        """刷新 MT5 终端列表"""
        try:
            terminals = self.app.mt5_detector.detect_terminals()
            
            if not terminals:
                messagebox.showwarning(
                    _("MSG_WARNING"), 
                    "未检测到运行中的 MT5 终端\n\n"
                    "请确保：\n"
                    "1. MT5 终端正在运行\n"
                    "2. 终端已登录交易账号\n"
                    "3. 以管理员权限运行本程序（如果需要）"
                )
                return
            
            # 格式化终端信息
            terminal_options = []
            self.terminals_data = terminals
            
            for term in terminals:
                display_text = f"{term['broker']} - 账号: {term['login']} | 服务器: {term['server']}"
                terminal_options.append(display_text)
            
            # 更新下拉框
            self.mt5_terminal_combo['values'] = terminal_options
            if terminal_options:
                self.mt5_terminal_combo.current(0)
                self.on_terminal_selected(None)
            
            # 绑定选择事件
            self.mt5_terminal_combo.bind('<<ComboboxSelected>>', self.on_terminal_selected)
            
            messagebox.showinfo(_("MSG_SUCCESS"), f"检测到 {len(terminals)} 个 MT5 终端")
            
        except Exception as e:
            messagebox.showerror("错误", f"检测 MT5 终端失败:\n{e}")
            import traceback
            traceback.print_exc()
    
    def on_terminal_selected(self, event):
        """当用户选择终端时"""
        selection = self.mt5_terminal_combo.get()
        if selection and hasattr(self, 'terminals_data'):
            # 根据选择找到对应的终端路径
            idx = self.mt5_terminal_combo.current()
            if idx >= 0 and idx < len(self.terminals_data):
                terminal = self.terminals_data[idx]
                self.mt5_path_var.set(terminal['path'])
                self.terminal_info_label.config(
                    text=f"已选择: {terminal['broker']} | 账号: {terminal['login']} | 服务器: {terminal['server']}",
                    foreground="green"
                )
    
    def browse_folder(self, string_var):
        """浏览文件夹"""
        folder = filedialog.askdirectory()
        if folder:
            string_var.set(folder)
    
    def save_config(self):
        """保存配置"""
        config = {
            "strategy_id": self.strategy_id_var.get(),
            
            "mqtt": {
                "broker": self.broker_var.get(),
                "port": self.port_var.get(),
                "username": self.mqtt_user_var.get(),
                "password": self.mqtt_pass_var.get(),
                "client_id": self.client_id_var.get(),
                "topic_prefix": "trademind/signals",
                "qos": 1,
                "keepalive": 60
            },
            "mt5": {
                "terminal_path": self.mt5_path_var.get(),
                "auto_select": False
            },
            "account_reporter": {
                "proxy_url": self.reporter_proxy_var.get(),
                "interval": self.reporter_interval_var.get()
            },
            "common": {
                "magic_number": self.magic_number_var.get(),
                "slippage_points": self.slippage_points_var.get(),
                "comment_prefix": self.comment_prefix_var.get()
            },
            "logging": {
                "level": "INFO",
                "file": "logs/master.log"
            }
        }

        if self.app.config_manager.save_config("master_config", config):
            # 更新 app 中的配置
            self.app.master_config = config
            messagebox.showinfo(_("MSG_SUCCESS"), _("MSG_CONFIG_SAVED"))
            self.app.update_status(_("MSG_CONFIG_SAVED"))
        else:
            messagebox.showerror(_("MSG_ERROR"), f"{_('CONFIG_ERROR')}: {_('MSG_CONFIG_SAVE_FAILED')}")
