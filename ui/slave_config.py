"""Slave 配置模块 - 增强版"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from common.i18n import _


class SlaveConfigTab:
    """Slave 配置选项卡 - 增强版"""
    
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text=_("TAB_SLAVE_CONFIG"))
        
        # 创建变量
        self._create_variables()
        
        # 加载配置到 UI
        self.load_config_to_ui()
        
        self.create_ui()
    
    def _create_variables(self):
        """创建 Tk 变量"""
        # MT5 终端
        self.mt5_terminal_var = tk.StringVar()
        self.mt5_path_var = tk.StringVar()
        
        # MQTT 配置
        self.broker_var = tk.StringVar()
        self.port_var = tk.IntVar()
        self.mqtt_user_var = tk.StringVar()
        self.mqtt_pass_var = tk.StringVar()
        self.client_id_var = tk.StringVar()
        
        # 订阅配置
        self.master_id_var = tk.StringVar()
        
        # 常用设置
        self.follow_mode_var = tk.StringVar(value="both")
        self.enable_alerts_var = tk.BooleanVar(value=True)
        self.allow_auto_trading_var = tk.BooleanVar(value=True)
        
        # 风险管理
        self.max_dd_percent_var = tk.DoubleVar()
        self.max_dd_usd_var = tk.DoubleVar()
        self.max_profit_percent_var = tk.DoubleVar()
        self.max_profit_usd_var = tk.DoubleVar()
        self.session_loss_var = tk.DoubleVar()
        self.cooldown_var = tk.IntVar()
        self.max_positions_var = tk.IntVar()
        self.max_total_lots_var = tk.DoubleVar()
        
        # 手数配置
        self.lot_mode_var = tk.StringVar(value="multiplier")
        self.lot_multiplier_var = tk.DoubleVar()
        self.fixed_lot_var = tk.DoubleVar()
        self.balance_ratio_var = tk.DoubleVar()
        self.usd_per_lot_var = tk.DoubleVar()
        self.incremental_base_var = tk.DoubleVar()
        self.incremental_step_var = tk.DoubleVar()
        self.min_lot_var = tk.DoubleVar()
        self.max_lot_var = tk.DoubleVar()
        self.skip_lot_less_var = tk.DoubleVar()
        self.skip_lot_greater_var = tk.DoubleVar()
        
        # 过滤配置
        self.follow_buy_var = tk.BooleanVar(value=True)
        self.follow_sell_var = tk.BooleanVar(value=True)
        self.follow_market_var = tk.BooleanVar(value=True)
        self.follow_pending_var = tk.BooleanVar(value=False)
        self.max_order_age_var = tk.DoubleVar()
        self.follow_close_var = tk.BooleanVar(value=True)
        self.whitelist_symbols_var = tk.StringVar()
        self.blacklist_symbols_var = tk.StringVar()
        
        # 追踪止损
        self.trailing_enabled_var = tk.BooleanVar(value=False)
        self.trailing_profit_var = tk.IntVar()
        self.trailing_trail_var = tk.IntVar()
    
    def load_config_to_ui(self):
        """从配置文件加载到 UI"""
        self.config = self.app.config_manager.load_config("slave_config")
        self.app.slave_config = self.config
        
        # MT5 终端
        self.mt5_path_var.set(self.config.get('mt5', {}).get('terminal_path', ''))
        
        # MQTT 配置
        mqtt_config = self.config.get('mqtt', {})
        self.broker_var.set(mqtt_config.get('broker', 'localhost'))
        self.port_var.set(mqtt_config.get('port', 1883))
        self.mqtt_user_var.set(mqtt_config.get('username', ''))
        self.mqtt_pass_var.set(mqtt_config.get('password', ''))
        self.client_id_var.set(mqtt_config.get('client_id', 'slave_001'))
        
        # 订阅配置
        self.master_id_var.set(self.config.get('subscription', {}).get('master_id', 'master_001'))
        
        # 常用设置
        common_config = self.config.get('common', {})
        self.follow_mode_var.set(common_config.get('follow_mode', 'both'))
        self.enable_alerts_var.set(common_config.get('enable_alerts', True))
        
        security_config = self.config.get('security', {})
        self.allow_auto_trading_var.set(security_config.get('allow_auto_trading', True))
        
        # 风险管理
        risk_config = self.config.get('risk', {})
        self.max_dd_percent_var.set(risk_config.get('max_drawdown_percent', 10.0))
        self.max_dd_usd_var.set(risk_config.get('max_drawdown_usd', 1000.0))
        self.max_profit_percent_var.set(risk_config.get('max_profit_percent', 20.0))
        self.max_profit_usd_var.set(risk_config.get('max_profit_usd', 2000.0))
        self.session_loss_var.set(risk_config.get('session_loss_usd', 0.0))
        self.cooldown_var.set(risk_config.get('cooldown_minutes', 0))
        self.max_positions_var.set(risk_config.get('max_positions', 3))
        self.max_total_lots_var.set(risk_config.get('max_total_lots', 10.0))
        
        # 手数配置
        self.lot_mode_var.set(risk_config.get('lot_mode', 'multiplier'))
        self.lot_multiplier_var.set(risk_config.get('lot_multiplier', 1.0))
        self.fixed_lot_var.set(risk_config.get('fixed_lot', 0.1))
        self.balance_ratio_var.set(risk_config.get('balance_ratio', 1.0))
        self.usd_per_lot_var.set(risk_config.get('usd_per_lot', 1000.0))
        self.incremental_base_var.set(risk_config.get('incremental_base', 0.01))
        self.incremental_step_var.set(risk_config.get('incremental_step', 0.01))
        self.min_lot_var.set(risk_config.get('min_lot', 0.01))
        self.max_lot_var.set(risk_config.get('max_lot', 888.8))
        self.skip_lot_less_var.set(risk_config.get('skip_lot_less_than', 0.01))
        self.skip_lot_greater_var.set(risk_config.get('skip_lot_greater_than', 888.8))
        
        # 过滤配置
        filter_config = self.config.get('filter', {})
        self.follow_buy_var.set(filter_config.get('follow_buy', True))
        self.follow_sell_var.set(filter_config.get('follow_sell', True))
        self.follow_market_var.set(filter_config.get('follow_market_orders', True))
        self.follow_pending_var.set(filter_config.get('follow_pending_orders', False))
        self.max_order_age_var.set(filter_config.get('max_order_age_minutes', 0.0))
        self.follow_close_var.set(filter_config.get('follow_close', True))
        self.whitelist_symbols_var.set(','.join(filter_config.get('whitelist_symbols', [])))
        self.blacklist_symbols_var.set(','.join(filter_config.get('blacklist_symbols', [])))
        
        # 追踪止损
        trailing_config = self.config.get('trailing_stop', {})
        self.trailing_enabled_var.set(trailing_config.get('enabled', False))
        self.trailing_profit_var.set(trailing_config.get('profit_points', 0))
        self.trailing_trail_var.set(trailing_config.get('trail_points', 0))
        
        print("✓ Slave 配置已加载到 UI")
    
    def create_ui(self):
        """创建配置界面"""
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

        self._create_common_section(scrollable_frame)
        self._create_security_section(scrollable_frame)
        self._create_mt5_terminal_section(scrollable_frame)
        self._create_mqtt_section(scrollable_frame)
        self._create_subscription_section(scrollable_frame)
        self._create_risk_section(scrollable_frame)
        self._create_lot_section(scrollable_frame)
        self._create_filter_section(scrollable_frame)
        self._create_trailing_section(scrollable_frame)
        
        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            btn_frame,
            text=_("BTN_REFRESH"),
            command=self.reload_config,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text=_("BTN_SAVE"),
            command=self.save_config,
            width=20
        ).pack(side=tk.RIGHT, padx=5)
    
    def _create_common_section(self, parent):
        """创建常用设置区域"""
        common_frame = ttk.LabelFrame(parent, text=_("CONFIG_COMMON_SETTINGS"), padding=10)
        common_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        ttk.Label(common_frame, text=_("CONFIG_FOLLOW_MODE")).grid(row=row, column=0, sticky=tk.W, pady=2)
        mode_combo = ttk.Combobox(common_frame, textvariable=self.follow_mode_var, 
                                 values=["both", "long_only", "short_only"], width=38, state="readonly")
        mode_combo.grid(row=row, column=1, padx=5)
        ttk.Label(common_frame, text="(both=多空都跟, long_only=只跟多, short_only=只跟空)").grid(row=row, column=2, sticky=tk.W)
        row += 1

        ttk.Checkbutton(common_frame, text=_("CONFIG_ENABLE_ALERTS"), variable=self.enable_alerts_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        row += 1

    def _create_security_section(self, parent):
        """创建安全性设置区域"""
        security_frame = ttk.LabelFrame(parent, text=_("CONFIG_SECURITY_SETTINGS"), padding=10)
        security_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Checkbutton(security_frame, text=_("CONFIG_ALLOW_AUTO_TRADING"), variable=self.allow_auto_trading_var).pack(anchor=tk.W, pady=2)

    def _create_mt5_terminal_section(self, parent):
        """创建 MT5 终端选择区域"""
        mt5_terminal_frame = ttk.LabelFrame(parent, text=_("CONFIG_MT5_SETTINGS"), padding=10)
        mt5_terminal_frame.pack(fill=tk.X, padx=10, pady=5)

        # 终端下拉框
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
    
    def _create_subscription_section(self, parent):
        """创建订阅配置区域"""
        sub_frame = ttk.LabelFrame(parent, text=_("CONFIG_SUBSCRIPTION_SETTINGS"), padding=10)
        sub_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        ttk.Label(sub_frame, text=_("CONFIG_MASTER_ID")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(sub_frame, textvariable=self.master_id_var, width=40).grid(row=row, column=1, padx=5)
    
    def _create_risk_section(self, parent):
        """创建风险管理区域"""
        risk_frame = ttk.LabelFrame(parent, text=_("CONFIG_RISK_SETTINGS"), padding=10)
        risk_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        ttk.Label(risk_frame, text=_("CONFIG_MAX_DRAWDOWN_PERCENT")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(risk_frame, from_=1, to=100, increment=0.1, textvariable=self.max_dd_percent_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(risk_frame, text=_("CONFIG_MAX_DRAWDOWN_USD")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(risk_frame, from_=0, to=100000, increment=100, textvariable=self.max_dd_usd_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(risk_frame, text=_("CONFIG_MAX_PROFIT_PERCENT")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(risk_frame, from_=0, to=100, increment=0.1, textvariable=self.max_profit_percent_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(risk_frame, text=_("CONFIG_MAX_PROFIT_USD")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(risk_frame, from_=0, to=100000, increment=100, textvariable=self.max_profit_usd_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(risk_frame, text=_("CONFIG_SESSION_LOSS_USD")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(risk_frame, from_=0, to=100000, increment=100, textvariable=self.session_loss_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(risk_frame, text=_("CONFIG_COOLDOWN_MINUTES")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(risk_frame, from_=0, to=1440, textvariable=self.cooldown_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(risk_frame, text=_("CONFIG_MAX_POSITIONS")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(risk_frame, from_=0, to=100, textvariable=self.max_positions_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(risk_frame, text=_("CONFIG_MAX_TOTAL_LOTS")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(risk_frame, from_=0, to=1000, increment=0.1, textvariable=self.max_total_lots_var, width=38).grid(row=row, column=1, padx=5)
    
    def _create_lot_section(self, parent):
        """创建手数配置区域"""
        lot_frame = ttk.LabelFrame(parent, text=_("CONFIG_LOT_SETTINGS"), padding=10)
        lot_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        ttk.Label(lot_frame, text=_("CONFIG_LOT_MODE")).grid(row=row, column=0, sticky=tk.W, pady=2)
        mode_combo = ttk.Combobox(lot_frame, textvariable=self.lot_mode_var, 
                                 values=["multiplier", "balance_ratio", "fixed", "fixed_per_usd", "incremental"], 
                                 width=38, state="readonly")
        mode_combo.grid(row=row, column=1, padx=5)
        ttk.Label(lot_frame, text="(multiplier=倍数, balance_ratio=余额倍率, fixed=固定, fixed_per_usd=余额大小, incremental=递增)").grid(row=row, column=2, sticky=tk.W, columnspan=2)
        row += 1

        ttk.Label(lot_frame, text=_("CONFIG_LOT_MULTIPLIER")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(lot_frame, from_=0.1, to=10, increment=0.1, textvariable=self.lot_multiplier_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(lot_frame, text=_("CONFIG_FIXED_LOT")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(lot_frame, from_=0.01, to=100, increment=0.01, textvariable=self.fixed_lot_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(lot_frame, text=_("CONFIG_BALANCE_RATIO")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(lot_frame, from_=0.1, to=10, increment=0.1, textvariable=self.balance_ratio_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(lot_frame, text=_("CONFIG_USD_PER_LOT")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(lot_frame, from_=100, to=100000, increment=100, textvariable=self.usd_per_lot_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(lot_frame, text=_("CONFIG_INCREMENTAL_BASE")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(lot_frame, from_=0.01, to=10, increment=0.01, textvariable=self.incremental_base_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(lot_frame, text=_("CONFIG_INCREMENTAL_STEP")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(lot_frame, from_=0.01, to=10, increment=0.01, textvariable=self.incremental_step_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(lot_frame, text=_("CONFIG_MIN_LOT")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(lot_frame, from_=0.01, to=100, increment=0.01, textvariable=self.min_lot_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(lot_frame, text=_("CONFIG_MAX_LOT")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(lot_frame, from_=0.01, to=1000, increment=0.01, textvariable=self.max_lot_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(lot_frame, text=_("CONFIG_SKIP_LOT_LESS")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(lot_frame, from_=0, to=100, increment=0.01, textvariable=self.skip_lot_less_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(lot_frame, text=_("CONFIG_SKIP_LOT_GREATER")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(lot_frame, from_=0, to=1000, increment=0.01, textvariable=self.skip_lot_greater_var, width=38).grid(row=row, column=1, padx=5)
    
    def _create_filter_section(self, parent):
        """创建过滤配置区域"""
        filter_frame = ttk.LabelFrame(parent, text=_("CONFIG_FILTER_SETTINGS"), padding=10)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        ttk.Checkbutton(filter_frame, text=_("CONFIG_FOLLOW_BUY"), variable=self.follow_buy_var).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(filter_frame, text=_("CONFIG_FOLLOW_SELL"), variable=self.follow_sell_var).grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1

        ttk.Checkbutton(filter_frame, text=_("CONFIG_FOLLOW_MARKET"), variable=self.follow_market_var).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(filter_frame, text=_("CONFIG_FOLLOW_PENDING"), variable=self.follow_pending_var).grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1

        ttk.Checkbutton(filter_frame, text=_("CONFIG_FOLLOW_CLOSE"), variable=self.follow_close_var).grid(row=row, column=0, sticky=tk.W, pady=2)
        row += 1

        ttk.Label(filter_frame, text=_("CONFIG_MAX_ORDER_AGE")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(filter_frame, from_=0, to=1440, increment=0.1, textvariable=self.max_order_age_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(filter_frame, text=_("CONFIG_WHITELIST_SYMBOLS")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(filter_frame, textvariable=self.whitelist_symbols_var, width=40).grid(row=row, column=1, padx=5)
        ttk.Label(filter_frame, text="(逗号分隔，如: EURUSD,GBPUSD)").grid(row=row, column=2, sticky=tk.W)
        row += 1

        ttk.Label(filter_frame, text=_("CONFIG_BLACKLIST_SYMBOLS")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(filter_frame, textvariable=self.blacklist_symbols_var, width=40).grid(row=row, column=1, padx=5)
        ttk.Label(filter_frame, text="(逗号分隔)").grid(row=row, column=2, sticky=tk.W)
    
    def _create_trailing_section(self, parent):
        """创建追踪止损区域"""
        trailing_frame = ttk.LabelFrame(parent, text=_("CONFIG_TRAILING_STOP"), padding=10)
        trailing_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        ttk.Checkbutton(trailing_frame, text=_("CONFIG_TRAILING_ENABLED"), variable=self.trailing_enabled_var).grid(row=row, column=0, sticky=tk.W, pady=2)
        row += 1

        ttk.Label(trailing_frame, text=_("CONFIG_TRAILING_PROFIT")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(trailing_frame, from_=0, to=10000, textvariable=self.trailing_profit_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(trailing_frame, text=_("CONFIG_TRAILING_TRAIL")).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(trailing_frame, from_=0, to=10000, textvariable=self.trailing_trail_var, width=38).grid(row=row, column=1, padx=5)
    
    def reload_config(self):
        """重新加载配置"""
        self.load_config_to_ui()
        messagebox.showinfo(_("MSG_INFO"), _("MSG_CONFIG_LOADED"))
        self.app.update_status(_("MSG_CONFIG_LOADED"))
    
    def browse_folder(self, string_var):
        """浏览文件夹"""
        folder = filedialog.askdirectory()
        if folder:
            string_var.set(folder)
    
    def save_config(self):
        """保存配置"""
        # 解析符号列表
        whitelist = [s.strip() for s in self.whitelist_symbols_var.get().split(',') if s.strip()]
        blacklist = [s.strip() for s in self.blacklist_symbols_var.get().split(',') if s.strip()]
        
        config = {
            "enabled": True,
            "common": {
                "follow_mode": self.follow_mode_var.get(),
                "enable_alerts": self.enable_alerts_var.get(),
                "stop_alert_on_price": False
            },
            "security": {
                "allow_auto_trading": self.allow_auto_trading_var.get(),
                "allow_dll_import": False
            },
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
            "subscription": {
                "master_id": self.master_id_var.get()
            },
            "risk": {
                "max_drawdown_percent": self.max_dd_percent_var.get(),
                "max_drawdown_usd": self.max_dd_usd_var.get(),
                "max_profit_percent": self.max_profit_percent_var.get(),
                "max_profit_usd": self.max_profit_usd_var.get(),
                "session_loss_usd": self.session_loss_var.get(),
                "session_profit_usd": 0.0,
                "cooldown_minutes": self.cooldown_var.get(),
                "max_positions": self.max_positions_var.get(),
                "max_total_lots": self.max_total_lots_var.get(),
                "lot_mode": self.lot_mode_var.get(),
                "lot_multiplier": self.lot_multiplier_var.get(),
                "fixed_lot": self.fixed_lot_var.get(),
                "balance_ratio": self.balance_ratio_var.get(),
                "usd_per_lot": self.usd_per_lot_var.get(),
                "incremental_base": self.incremental_base_var.get(),
                "incremental_step": self.incremental_step_var.get(),
                "min_lot": self.min_lot_var.get(),
                "max_lot": self.max_lot_var.get(),
                "skip_lot_less_than": self.skip_lot_less_var.get(),
                "skip_lot_greater_than": self.skip_lot_greater_var.get()
            },
            "filter": {
                "follow_buy": self.follow_buy_var.get(),
                "follow_sell": self.follow_sell_var.get(),
                "follow_market_orders": self.follow_market_var.get(),
                "follow_pending_orders": self.follow_pending_var.get(),
                "follow_old_orders": False,
                "max_order_age_minutes": self.max_order_age_var.get(),
                "allow_duplicate_follow": False,
                "follow_close": self.follow_close_var.get(),
                "follow_sl_tp": False,
                "require_profit_points": 0,
                "require_loss_points": 0,
                "max_price_deviation_points": 0,
                "allowed_magics": [],
                "required_comments": [],
                "allowed_hours_start": "00:00:00",
                "allowed_hours_end": "23:59:59",
                "whitelist_symbols": whitelist,
                "blacklist_symbols": blacklist
            },
            "trailing_stop": {
                "enabled": self.trailing_enabled_var.get(),
                "profit_points": self.trailing_profit_var.get(),
                "trail_points": self.trailing_trail_var.get()
            },
            "symbol_mapping": self.config.get('symbol_mapping', {}),
            "logging": {
                "level": "INFO",
                "file": "logs/slave.log"
            }
        }

        if self.app.config_manager.save_config("slave_config", config):
            self.app.slave_config = config
            messagebox.showinfo(_("MSG_SUCCESS"), _("MSG_CONFIG_SAVED"))
            self.app.update_status(_("MSG_CONFIG_SAVED"))
        else:
            messagebox.showerror(_("MSG_ERROR"), f"{_('CONFIG_ERROR')}: {_('MSG_CONFIG_SAVE_FAILED')}")
    
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
            # 显示: 券商 - 账号: xxx | 服务器: xxx
            display_text = f"{term['broker']} - 账号: {term['login']} | 服务器: {term['server']}"
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
            # 根据选择找到对应的终端路径
            idx = self.mt5_terminal_combo.current()
            if idx >= 0 and idx < len(self.terminals_data):
                terminal = self.terminals_data[idx]
                self.mt5_path_var.set(terminal['path'])
                self.terminal_info_label.config(
                    text=f"已选择: {terminal['broker']} | 账号: {terminal['login']} | 服务器: {terminal['server']}",
                    foreground="green"
                )
