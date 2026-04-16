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
        
        # MQTT
        self.broker_var = tk.StringVar()
        self.port_var = tk.IntVar()
        self.mqtt_user_var = tk.StringVar()
        self.mqtt_pass_var = tk.StringVar()
        self.client_id_var = tk.StringVar()
        
        # 信号
        self.symbols_var = tk.StringVar()
        self.max_pos_var = tk.IntVar()
        self.lot_size_var = tk.DoubleVar()
    
    def load_config_to_ui(self):
        """从配置文件加载到 UI"""
        # 重新读取配置
        self.config = self.app.config_manager.load_config("master_config")
        self.app.master_config = self.config  # 同步到 app
        
        # 更新变量值
        self.mt5_path_var.set(self.config.get('mt5', {}).get('terminal_path', ''))
        
        self.broker_var.set(self.config.get('mqtt', {}).get('broker', 'localhost'))
        self.port_var.set(self.config.get('mqtt', {}).get('port', 1883))
        self.mqtt_user_var.set(self.config.get('mqtt', {}).get('username', ''))
        self.mqtt_pass_var.set(self.config.get('mqtt', {}).get('password', ''))
        self.client_id_var.set(self.config.get('mqtt', {}).get('client_id', 'master_001'))
        
        symbols = ','.join(self.config.get('signal', {}).get('symbols', []))
        self.symbols_var.set(symbols)
        self.max_pos_var.set(self.config.get('signal', {}).get('max_positions', 5))
        self.lot_size_var.set(self.config.get('signal', {}).get('lot_size', 0.01))
        
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
        
        # MQTT 配置
        self._create_mqtt_section(scrollable_frame)
        
        # 信号配置
        self._create_signal_section(scrollable_frame)
        
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
    
    def _create_signal_section(self, parent):
        """创建信号配置区域"""
        signal_frame = ttk.LabelFrame(parent, text=_("CONFIG_SIGNAL_SETTINGS"), padding=10)
        signal_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        ttk.Label(signal_frame, text=_("CONFIG_SYMBOLS")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(signal_frame, textvariable=self.symbols_var, width=40).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(signal_frame, text=_("CONFIG_MAX_POSITIONS")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(signal_frame, from_=1, to=100, textvariable=self.max_pos_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(signal_frame, text=_("CONFIG_LOT_SIZE")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(signal_frame, from_=0.01, to=100, increment=0.01, textvariable=self.lot_size_var, width=38).grid(row=row, column=1, padx=5)
    
    def refresh_terminals(self):
        """刷新 MT5 终端列表"""
        terminals = self.app.mt5_detector.detect_terminals()
        
        if not terminals:
            messagebox.showwarning(_("MSG_WARNING"), _("NO_MT5_DETECTED"))
            return
        
        # 格式化终端信息
        terminal_options = []
        self.terminals_data = terminals  # 保存原始数据
        
        for term in terminals:
            display_text = f"{term['broker']} - 账号: {term['login']} ({term['path']})"
            terminal_options.append(display_text)
        
        # 更新下拉框
        self.mt5_terminal_combo['values'] = terminal_options
        if terminal_options:
            self.mt5_terminal_combo.current(0)
            self.on_terminal_selected(None)
        
        # 绑定选择事件
        self.mt5_terminal_combo.bind('<<ComboboxSelected>>', self.on_terminal_selected)
        
        messagebox.showinfo(_("MSG_SUCCESS"), f"{_('BTN_DETECT_MT5')}: {len(terminals)}")
    
    def on_terminal_selected(self, event):
        """当用户选择终端时"""
        selection = self.mt5_terminal_combo.get()
        if selection and hasattr(self, 'terminals_data'):
            import re
            path_match = re.search(r'\((.+)\)$', selection)
            if path_match:
                path = path_match.group(1)
                self.mt5_path_var.set(path)
                self.terminal_info_label.config(
                    text=f"{_('STATUS_RUNNING')}: {selection}",
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
            "mqtt": {
                "broker": self.broker_var.get(),
                "port": self.port_var.get(),
                "username": self.mqtt_user_var.get(),
                "password": self.mqtt_pass_var.get(),
                "client_id": self.client_id_var.get()
            },
            "mt5": {
                "terminal_path": self.mt5_path_var.get(),
                "auto_select": False
            },
            "signal": {
                "symbols": [s.strip() for s in self.symbols_var.get().split(",") if s.strip()],
                "max_positions": self.max_pos_var.get(),
                "lot_size": self.lot_size_var.get()
            }
        }

        if self.app.config_manager.save_config("master_config", config):
            # 更新 app 中的配置
            self.app.master_config = config
            messagebox.showinfo(_("MSG_SUCCESS"), _("MSG_CONFIG_SAVED"))
            self.app.update_status(_("MSG_CONFIG_SAVED"))
        else:
            messagebox.showerror(_("MSG_ERROR"), f"{_('CONFIG_ERROR')}: {_('MSG_CONFIG_SAVE_FAILED')}")