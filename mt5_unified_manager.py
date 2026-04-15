"""
MT5 Signal System - Management Panel

Supports three running modes:
- 'master': Master Server management panel only
- 'slave': Slave Server management panel only  
- 'unified': Full unified management panel (default)

Usage:
    python mt5_unified_manager.py              # Unified mode
    python mt5_unified_manager.py --mode master  # Master mode
    python mt5_unified_manager.py --mode slave   # Slave mode
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
import os
import sys
import threading
import time
import queue
import io
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import psutil
except ImportError:
    psutil = None


class StreamToQueue(io.StringIO):
    """Redirect stdout/stderr to a queue for GUI display"""
    def __init__(self, queue_obj):
        super().__init__()
        self.queue = queue_obj

    def write(self, text):
        if text.strip():
            self.queue.put(('log', text.rstrip()))

    def flush(self):
        pass


class UnifiedMT5Manager:
    """Unified MT5 Signal System Management Panel"""

    def __init__(self, root, mode='unified'):
        self.root = root
        self.mode = mode  # 'master', 'slave', or 'unified'
        
        # Set title based on mode
        mode_titles = {
            'master': "MT5 Signal System - Master 管理面板 v2.0",
            'slave': "MT5 Signal System - Slave 管理面板 v2.0",
            'unified': "MT5 Signal System - 统一管理平台 v2.0"
        }
        self.root.title(mode_titles.get(mode, mode_titles['unified']))
        self.root.geometry("1300x850")
        self.root.minsize(1100, 700)

        # 基础路径
        self.base_dir = Path(__file__).parent
        self.config_dir = self.base_dir / "config"
        self.logs_dir = self.base_dir / "logs"
        self.config_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

        # 配置文件
        self.master_config_path = self.config_dir / "master_config.json"
        self.slave_config_path = self.config_dir / "slave_config.json"

        # 加载配置
        self.master_config = self._load_json(self.master_config_path, self._default_master_config())
        self.slave_config = self._load_json(self.slave_config_path, self._default_slave_config())

        # 服务状态
        self.master_thread = None
        self.master_running = False
        self.master_output = queue.Queue()

        self.slave_thread = None
        self.slave_running = False
        self.slave_output = queue.Queue()

        # License 管理
        self.license_manager = None
        self.license_list = []

        # 监控数据
        self.monitor_data = {
            'master_signals_sent': 0,
            'slave_signals_received': 0,
            'slave_trades_executed': 0,
            'errors': 0,
        }

        # 构建界面
        self._build_ui()

        # 启动日志刷新定时器
        self._refresh_logs_timer()

    def _load_json(self, path, default):
        """Load JSON file or return default"""
        try:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return default.copy() if isinstance(default, dict) else default

    def _save_json(self, path, data):
        """Save data to JSON file"""
        try:
            path.parent.mkdir(exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")
            return False

    def _default_master_config(self):
        return {
            "mqtt": {
                "broker": "localhost",
                "port": 1883,
                "username": "",
                "password": "",
                "client_id": "master_001",
                "topic_prefix": "mt5/signal"
            },
            "signal": {
                "send_interval_ms": 100,
                "include_positions": True,
                "include_orders": True
            },
            "logging": {
                "level": "INFO",
                "file": "logs/master.log",
                "max_size_mb": 10,
                "backup_count": 5
            }
        }

    def _default_slave_config(self):
        return {
            "mqtt": {
                "broker": "localhost",
                "port": 1883,
                "username": "",
                "password": "",
                "client_id": "slave_001",
                "topic_prefix": "mt5/signal"
            },
            "trading": {
                "multiplier": 1.0,
                "reverse_trading": False,
                "max_lot_size": 10.0,
                "min_lot_size": 0.01,
                "lot_step": 0.01,
                "slippage_points": 30,
                "magic_number": 999999
            },
            "risk_management": {
                "max_daily_loss_usd": 1000.0,
                "max_spread_points": 50,
                "enable_spread_filter": True,
                "enable_risk_management": True
            },
            "symbol_mapping": {
                "EURUSD": "EURUSD",
                "GBPUSD": "GBPUSD",
                "XAUUSD": "GOLD"
            },
            "logging": {
                "level": "INFO",
                "file": "logs/slave.log",
                "max_size_mb": 10,
                "backup_count": 5
            }
        }

    def _build_ui(self):
        """Build the entire UI based on mode"""
        # === Top Menu Bar ===
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="打开配置目录", command=self._open_config_dir)
        file_menu.add_command(label="打开日志目录", command=self._open_logs_dir)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._on_closing)

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="检查依赖", command=self._check_dependencies)
        tools_menu.add_command(label="清理日志", command=self._clear_all_logs)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self._show_about)

        # === Notebook (Tabs) ===
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Dashboard (always shown)
        self.tab_dashboard = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dashboard, text="  📊 控制面板  ")
        self._build_dashboard()

        # Mode-specific tabs
        if self.mode in ('master', 'unified'):
            # Master Config tab
            self.tab_master_config = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_master_config, text="  ⚙️ Master 配置  ")
            self._build_master_config()

        if self.mode in ('slave', 'unified'):
            # Slave Config tab
            self.tab_slave_config = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_slave_config, text="  ⚙️ Slave 配置  ")
            self._build_slave_config()

        if self.mode == 'unified':
            # License Management (only in unified mode)
            self.tab_license = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_license, text="  🔑 授权管理  ")
            self._build_license_tab()

            # Monitoring (only in unified mode)
            self.tab_monitoring = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_monitoring, text="  📡 实时监控  ")
            self._build_monitoring_tab()

        # Logs tab (always shown)
        self.tab_logs = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_logs, text="  📋 日志查看  ")
        self._build_logs_tab()

        # === Status Bar ===
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_left = ttk.Label(self.status_bar, text="就绪", foreground="green")
        self.status_left.pack(side=tk.LEFT, padx=10, pady=3)

        mode_labels = {
            'master': "Master 模式",
            'slave': "Slave 模式",
            'unified': "统一管理模式"
        }
        self.status_right = ttk.Label(self.status_bar, text=f"MT5 Signal System v2.0 - {mode_labels.get(self.mode, '')}")
        self.status_right.pack(side=tk.RIGHT, padx=10)

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _build_dashboard(self):
        """Build the Dashboard tab - main control center"""
        # Title based on mode
        title_frame = ttk.Frame(self.tab_dashboard)
        title_frame.pack(fill=tk.X, padx=20, pady=10)

        mode_titles = {
            'master': "MT5 信号系统 - Master 管理面板",
            'slave': "MT5 信号系统 - Slave 管理面板",
            'unified': "MT5 信号系统 - 统一管理平台"
        }
        ttk.Label(
            title_frame,
            text=mode_titles.get(self.mode, mode_titles['unified']),
            font=("Microsoft YaHei", 18, "bold")
        ).pack(side=tk.LEFT)

        # Service Cards Container
        cards_frame = ttk.Frame(self.tab_dashboard)
        cards_frame.pack(fill=tk.X, padx=20, pady=10)

        if self.mode in ('master', 'unified'):
            # === Master Server Card ===
            master_card = ttk.LabelFrame(cards_frame, text="🔴 Master Server (主服务器)", padding=15)
            master_card.pack(side=tk.LEFT if self.mode == 'unified' else tk.TOP, 
                           fill=tk.BOTH, expand=True, padx=10)

            # Status
            self.master_status_var = tk.StringVar(value="● 已停止")
            master_status_lbl = ttk.Label(
                master_card,
                textvariable=self.master_status_var,
                font=("Microsoft YaHei", 12, "bold"),
                foreground="red"
            )
            master_status_lbl.pack(pady=5)

            # Info
            self.master_info_var = tk.StringVar(value="未运行")
            ttk.Label(master_card, textvariable=self.master_info_var, foreground="gray").pack(pady=2)

            # Control buttons
            master_btn_frame = ttk.Frame(master_card)
            master_btn_frame.pack(pady=10)

            self.master_start_btn = ttk.Button(
                master_btn_frame,
                text="▶ 启动 Master",
                command=self._start_master_service,
                width=15
            )
            self.master_start_btn.pack(side=tk.LEFT, padx=5)

            self.master_stop_btn = ttk.Button(
                master_btn_frame,
                text="⏹ 停止 Master",
                command=self._stop_master_service,
                state=tk.DISABLED,
                width=15
            )
            self.master_stop_btn.pack(side=tk.LEFT, padx=5)

        if self.mode in ('slave', 'unified'):
            # === Slave Server Card ===
            slave_card = ttk.LabelFrame(cards_frame, text="🔵 Slave Server (从服务器)", padding=15)
            slave_card.pack(side=tk.LEFT if self.mode == 'unified' else tk.TOP,
                          fill=tk.BOTH, expand=True, padx=10)

            self.slave_status_var = tk.StringVar(value="● 已停止")
            slave_status_lbl = ttk.Label(
                slave_card,
                textvariable=self.slave_status_var,
                font=("Microsoft YaHei", 12, "bold"),
                foreground="red"
            )
            slave_status_lbl.pack(pady=5)

            self.slave_info_var = tk.StringVar(value="未运行")
            ttk.Label(slave_card, textvariable=self.slave_info_var, foreground="gray").pack(pady=2)

            slave_btn_frame = ttk.Frame(slave_card)
            slave_btn_frame.pack(pady=10)

            self.slave_start_btn = ttk.Button(
                slave_btn_frame,
                text="▶ 启动 Slave",
                command=self._start_slave_service,
                width=15
            )
            self.slave_start_btn.pack(side=tk.LEFT, padx=5)

            self.slave_stop_btn = ttk.Button(
                slave_btn_frame,
                text="⏹ 停止 Slave",
                command=self._stop_slave_service,
                state=tk.DISABLED,
                width=15
            )
            self.slave_stop_btn.pack(side=tk.LEFT, padx=5)

        # === Quick Actions ===
        quick_frame = ttk.LabelFrame(self.tab_dashboard, text="⚡ 快速操作", padding=15)
        quick_frame.pack(fill=tk.X, padx=20, pady=10)

        quick_inner = ttk.Frame(quick_frame)
        quick_inner.pack(fill=tk.X)

        # Mode-specific restart button
        if self.mode == 'unified':
            ttk.Button(quick_inner, text="🔄 重启全部", command=self._restart_all, width=15).pack(side=tk.LEFT, padx=5)
        elif self.mode == 'master':
            ttk.Button(quick_inner, text="🔄 重启 Master", command=self._restart_master, width=15).pack(side=tk.LEFT, padx=5)
        elif self.mode == 'slave':
            ttk.Button(quick_inner, text="🔄 重启 Slave", command=self._restart_slave, width=15).pack(side=tk.LEFT, padx=5)

        ttk.Button(quick_inner, text="📁 配置目录", command=self._open_config_dir, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_inner, text="📁 日志目录", command=self._open_logs_dir, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_inner, text="🧹 清理日志", command=self._clear_all_logs, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_inner, text="🔍 检查依赖", command=self._check_dependencies, width=15).pack(side=tk.LEFT, padx=5)

        # === System Info ===
        info_frame = ttk.LabelFrame(self.tab_dashboard, text="ℹ️ 系统信息", padding=15)
        info_frame.pack(fill=tk.X, padx=20, pady=10)

        info_inner = ttk.Frame(info_frame)
        info_inner.pack(fill=tk.X)

        ttk.Label(info_inner, text=f"Python: {sys.version.split()[0]}", width=25, anchor=tk.W).grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_inner, text=f"平台: {sys.platform}", width=25, anchor=tk.W).grid(row=0, column=1, sticky=tk.W, pady=2)
        ttk.Label(info_inner, text=f"工作目录: {self.base_dir}", anchor=tk.W).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)

        # Dependency status
        self.dep_status_var = tk.StringVar(value="正在检查依赖...")
        ttk.Label(info_inner, textvariable=self.dep_status_var, foreground="blue", anchor=tk.W).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)

        # Check deps in background
        self.root.after(500, self._check_dependencies)

    def _build_master_config(self):
        """Build Master configuration tab"""
        canvas = tk.Canvas(self.tab_master_config)
        scrollbar = ttk.Scrollbar(self.tab_master_config, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # MQTT Config
        mqtt_frame = ttk.LabelFrame(scroll_frame, text="MQTT 配置", padding=10)
        mqtt_frame.pack(fill=tk.X, padx=10, pady=5)

        self.mc = {}  # master config vars

        row = 0
        for label, key, default in [
            ("Broker 地址", "broker", "localhost"),
            ("端口", "port", 1883),
            ("用户名", "username", ""),
            ("密码", "password", ""),
            ("Client ID", "client_id", "master_001"),
            ("Topic 前缀", "topic_prefix", "mt5/signal"),
        ]:
            ttk.Label(mqtt_frame, text=label + ":").grid(row=row, column=0, sticky=tk.W, pady=3)
            if key == "port":
                var = tk.IntVar(value=self.master_config.get('mqtt', {}).get(key, default))
            else:
                var = tk.StringVar(value=self.master_config.get('mqtt', {}).get(key, default))
            self.mc[f"mqtt_{key}"] = var
            if key == "password":
                ttk.Entry(mqtt_frame, textvariable=var, width=40, show="*").grid(row=row, column=1, padx=5)
            else:
                ttk.Entry(mqtt_frame, textvariable=var, width=40).grid(row=row, column=1, padx=5)
            row += 1

        # Signal Config
        signal_frame = ttk.LabelFrame(scroll_frame, text="信号配置", padding=10)
        signal_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        ttk.Label(signal_frame, text="发送间隔 (毫秒):").grid(row=row, column=0, sticky=tk.W, pady=3)
        self.mc["signal_interval"] = tk.IntVar(value=self.master_config.get('signal', {}).get('send_interval_ms', 100))
        ttk.Spinbox(signal_frame, from_=50, to=5000, increment=50, textvariable=self.mc["signal_interval"], width=38).grid(row=row, column=1, padx=5)
        row += 1

        self.mc["signal_positions"] = tk.BooleanVar(value=self.master_config.get('signal', {}).get('include_positions', True))
        ttk.Checkbutton(signal_frame, text="包含持仓信息", variable=self.mc["signal_positions"]).grid(row=row, column=0, columnspan=2, sticky=tk.W)
        row += 1

        self.mc["signal_orders"] = tk.BooleanVar(value=self.master_config.get('signal', {}).get('include_orders', True))
        ttk.Checkbutton(signal_frame, text="包含挂单信息", variable=self.mc["signal_orders"]).grid(row=row, column=0, columnspan=2, sticky=tk.W)
        row += 1

        # Logging Config
        log_frame = ttk.LabelFrame(scroll_frame, text="日志配置", padding=10)
        log_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        ttk.Label(log_frame, text="日志级别:").grid(row=row, column=0, sticky=tk.W, pady=3)
        self.mc["log_level"] = tk.StringVar(value=self.master_config.get('logging', {}).get('level', 'INFO'))
        ttk.Combobox(log_frame, textvariable=self.mc["log_level"], values=["DEBUG", "INFO", "WARNING", "ERROR"], width=38, state="readonly").grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(log_frame, text="日志文件:").grid(row=row, column=0, sticky=tk.W, pady=3)
        self.mc["log_file"] = tk.StringVar(value=self.master_config.get('logging', {}).get('file', 'logs/master.log'))
        ttk.Entry(log_frame, textvariable=self.mc["log_file"], width=40).grid(row=row, column=1, padx=5)

        # Save button
        btn_frame = ttk.Frame(scroll_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=15)
        ttk.Button(btn_frame, text="💾 保存 Master 配置", command=self._save_master_config, width=20).pack(side=tk.RIGHT)

    def _build_slave_config(self):
        """Build Slave configuration tab"""
        canvas = tk.Canvas(self.tab_slave_config)
        scrollbar = ttk.Scrollbar(self.tab_slave_config, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.sc = {}  # slave config vars

        # MQTT Config
        mqtt_frame = ttk.LabelFrame(scroll_frame, text="MQTT 配置", padding=10)
        mqtt_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        for label, key, default in [
            ("Broker 地址", "broker", "localhost"),
            ("端口", "port", 1883),
            ("用户名", "username", ""),
            ("密码", "password", ""),
            ("Client ID", "client_id", "slave_001"),
            ("Topic 前缀", "topic_prefix", "mt5/signal"),
        ]:
            ttk.Label(mqtt_frame, text=label + ":").grid(row=row, column=0, sticky=tk.W, pady=3)
            if key == "port":
                var = tk.IntVar(value=self.slave_config.get('mqtt', {}).get(key, default))
            else:
                var = tk.StringVar(value=self.slave_config.get('mqtt', {}).get(key, default))
            self.sc[f"mqtt_{key}"] = var
            if key == "password":
                ttk.Entry(mqtt_frame, textvariable=var, width=40, show="*").grid(row=row, column=1, padx=5)
            else:
                ttk.Entry(mqtt_frame, textvariable=var, width=40).grid(row=row, column=1, padx=5)
            row += 1

        # Trading Config
        trade_frame = ttk.LabelFrame(scroll_frame, text="交易配置", padding=10)
        trade_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        ttk.Label(trade_frame, text="跟单倍数:").grid(row=row, column=0, sticky=tk.W, pady=3)
        self.sc["trade_multiplier"] = tk.DoubleVar(value=self.slave_config.get('trading', {}).get('multiplier', 1.0))
        ttk.Spinbox(trade_frame, from_=0.1, to=10, increment=0.1, textvariable=self.sc["trade_multiplier"], width=38).grid(row=row, column=1, padx=5)
        ttk.Label(trade_frame, text="(1.0=全仓, 0.5=半仓, 2.0=双倍)", foreground="gray").grid(row=row, column=2, padx=5)
        row += 1

        self.sc["trade_reverse"] = tk.BooleanVar(value=self.slave_config.get('trading', {}).get('reverse_trading', False))
        ttk.Checkbutton(trade_frame, text="反向交易 (BUY↔SELL)", variable=self.sc["trade_reverse"]).grid(row=row, column=0, columnspan=2, sticky=tk.W)
        row += 1

        ttk.Label(trade_frame, text="最大手数:").grid(row=row, column=0, sticky=tk.W, pady=3)
        self.sc["trade_max_lot"] = tk.DoubleVar(value=self.slave_config.get('trading', {}).get('max_lot_size', 10.0))
        ttk.Spinbox(trade_frame, from_=0.01, to=100, increment=0.01, textvariable=self.sc["trade_max_lot"], width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(trade_frame, text="最小手数:").grid(row=row, column=0, sticky=tk.W, pady=3)
        self.sc["trade_min_lot"] = tk.DoubleVar(value=self.slave_config.get('trading', {}).get('min_lot_size', 0.01))
        ttk.Spinbox(trade_frame, from_=0.01, to=1, increment=0.01, textvariable=self.sc["trade_min_lot"], width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(trade_frame, text="滑点 (点数):").grid(row=row, column=0, sticky=tk.W, pady=3)
        self.sc["trade_slippage"] = tk.IntVar(value=self.slave_config.get('trading', {}).get('slippage_points', 30))
        ttk.Spinbox(trade_frame, from_=0, to=500, textvariable=self.sc["trade_slippage"], width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(trade_frame, text="Magic Number:").grid(row=row, column=0, sticky=tk.W, pady=3)
        self.sc["trade_magic"] = tk.IntVar(value=self.slave_config.get('trading', {}).get('magic_number', 999999))
        ttk.Spinbox(trade_frame, from_=0, to=9999999, textvariable=self.sc["trade_magic"], width=38).grid(row=row, column=1, padx=5)

        # Risk Management
        risk_frame = ttk.LabelFrame(scroll_frame, text="风险管理", padding=10)
        risk_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        self.sc["risk_enabled"] = tk.BooleanVar(value=self.slave_config.get('risk_management', {}).get('enable_risk_management', True))
        ttk.Checkbutton(risk_frame, text="启用风险管理", variable=self.sc["risk_enabled"]).grid(row=row, column=0, columnspan=2, sticky=tk.W)
        row += 1

        ttk.Label(risk_frame, text="每日最大亏损 (USD):").grid(row=row, column=0, sticky=tk.W, pady=3)
        self.sc["risk_max_loss"] = tk.DoubleVar(value=self.slave_config.get('risk_management', {}).get('max_daily_loss_usd', 1000.0))
        ttk.Spinbox(risk_frame, from_=100, to=100000, increment=100, textvariable=self.sc["risk_max_loss"], width=38).grid(row=row, column=1, padx=5)
        row += 1

        self.sc["risk_spread_filter"] = tk.BooleanVar(value=self.slave_config.get('risk_management', {}).get('enable_spread_filter', True))
        ttk.Checkbutton(risk_frame, text="启用点差过滤", variable=self.sc["risk_spread_filter"]).grid(row=row, column=0, columnspan=2, sticky=tk.W)
        row += 1

        ttk.Label(risk_frame, text="最大点差 (点数):").grid(row=row, column=0, sticky=tk.W, pady=3)
        self.sc["risk_max_spread"] = tk.IntVar(value=self.slave_config.get('risk_management', {}).get('max_spread_points', 50))
        ttk.Spinbox(risk_frame, from_=1, to=500, textvariable=self.sc["risk_max_spread"], width=38).grid(row=row, column=1, padx=5)

        # Symbol Mapping
        map_frame = ttk.LabelFrame(scroll_frame, text="品种映射", padding=10)
        map_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(map_frame, text="格式: 主服务器品种=从服务器品种 (每行一个)").pack(anchor=tk.W)

        self.sc["symbol_mapping_text"] = tk.Text(map_frame, height=6, width=50)
        self.sc["symbol_mapping_text"].pack(fill=tk.X, pady=5)

        # Load existing mappings
        mappings = self.slave_config.get('symbol_mapping', {})
        mapping_lines = [f"{k}={v}" for k, v in mappings.items()]
        self.sc["symbol_mapping_text"].insert(tk.END, "\n".join(mapping_lines))

        # Logging
        log_frame = ttk.LabelFrame(scroll_frame, text="日志配置", padding=10)
        log_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        ttk.Label(log_frame, text="日志级别:").grid(row=row, column=0, sticky=tk.W, pady=3)
        self.sc["log_level"] = tk.StringVar(value=self.slave_config.get('logging', {}).get('level', 'INFO'))
        ttk.Combobox(log_frame, textvariable=self.sc["log_level"], values=["DEBUG", "INFO", "WARNING", "ERROR"], width=38, state="readonly").grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(log_frame, text="日志文件:").grid(row=row, column=0, sticky=tk.W, pady=3)
        self.sc["log_file"] = tk.StringVar(value=self.slave_config.get('logging', {}).get('file', 'logs/slave.log'))
        ttk.Entry(log_frame, textvariable=self.sc["log_file"], width=40).grid(row=row, column=1, padx=5)

        # Save button
        btn_frame = ttk.Frame(scroll_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=15)
        ttk.Button(btn_frame, text="💾 保存 Slave 配置", command=self._save_slave_config, width=20).pack(side=tk.RIGHT)

    def _build_license_tab(self):
        """Build License Management tab"""
        # Header
        header_frame = ttk.Frame(self.tab_license)
        header_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(
            header_frame,
            text="🔑 授权许可证管理",
            font=("Microsoft YaHei", 14, "bold")
        ).pack(side=tk.LEFT)

        # Init license manager
        try:
            from master.auth_manager import LicenseManager
            self.license_manager = LicenseManager()
            self._refresh_license_list()
        except ImportError:
            ttk.Label(header_frame, text="(授权管理模块未找到)", foreground="orange").pack(side=tk.LEFT, padx=10)

        # License list
        list_frame = ttk.LabelFrame(self.tab_license, text="许可证列表", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ('client', 'key', 'status', 'connections', 'max_conn', 'expire')
        self.license_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)

        self.license_tree.heading('client', text='客户名称')
        self.license_tree.heading('key', text='许可证密钥')
        self.license_tree.heading('status', text='状态')
        self.license_tree.heading('connections', text='当前连接')
        self.license_tree.heading('max_conn', text='最大连接')
        self.license_tree.heading('expire', text='过期时间')

        self.license_tree.column('client', width=120)
        self.license_tree.column('key', width=250)
        self.license_tree.column('status', width=80)
        self.license_tree.column('connections', width=80)
        self.license_tree.column('max_conn', width=80)
        self.license_tree.column('expire', width=150)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.license_tree.yview)
        self.license_tree.configure(yscrollcommand=scrollbar.set)
        self.license_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Action buttons
        action_frame = ttk.Frame(self.tab_license)
        action_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(action_frame, text="➕ 生成许可证", command=self._generate_license_dialog, width=18).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="🔄 刷新列表", command=self._refresh_license_list, width=15).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="🔍 验证许可证", command=self._validate_license_dialog, width=15).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="🚫 吊销许可证", command=self._revoke_license, width=15).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="📊 统计信息", command=self._show_license_stats, width=15).pack(side=tk.LEFT, padx=3)

    def _build_monitoring_tab(self):
        """Build real-time monitoring tab"""
        # Stats cards
        stats_frame = ttk.Frame(self.tab_monitoring)
        stats_frame.pack(fill=tk.X, padx=10, pady=10)

        card_configs = [
            ("Master 信号发送", "master_signals_sent", "#2196F3"),
            ("Slave 信号接收", "slave_signals_received", "#4CAF50"),
            ("Slave 交易执行", "slave_trades_executed", "#FF9800"),
            ("错误次数", "errors", "#f44336"),
        ]

        self.stat_labels = {}
        for title, key, color in card_configs:
            card = ttk.LabelFrame(stats_frame, text=title, padding=10)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            lbl = ttk.Label(
                card,
                text="0",
                font=("Microsoft YaHei", 20, "bold"),
                foreground=color
            )
            lbl.pack(pady=5)
            self.stat_labels[key] = lbl

        # Service status
        status_frame = ttk.LabelFrame(self.tab_monitoring, text="服务状态", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.mon_master_status = ttk.Label(status_frame, text="Master: ● 离线", font=("Consolas", 11))
        self.mon_master_status.pack(side=tk.LEFT, padx=20)

        self.mon_slave_status = ttk.Label(status_frame, text="Slave: ● 离线", font=("Consolas", 11))
        self.mon_slave_status.pack(side=tk.LEFT, padx=20)

        # Live output area
        output_frame = ttk.LabelFrame(self.tab_monitoring, text="实时输出", padding=5)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.live_output = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            state=tk.DISABLED
        )
        self.live_output.pack(fill=tk.BOTH, expand=True)

        # Start monitoring loop
        self._start_monitoring_loop()

    def _build_logs_tab(self):
        """Build logs tab"""
        # Log selector
        select_frame = ttk.Frame(self.tab_logs)
        select_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(select_frame, text="日志文件:").pack(side=tk.LEFT)
        self.log_file_var = tk.StringVar(value="master.log")
        log_files = ["master.log", "slave.log"]
        self.log_combo = ttk.Combobox(select_frame, textvariable=self.log_file_var, values=log_files, width=20)
        self.log_combo.pack(side=tk.LEFT, padx=5)

        ttk.Button(select_frame, text="🔄 刷新", command=self._load_log_file).pack(side=tk.LEFT, padx=3)
        ttk.Button(select_frame, text="🧹 清空", command=lambda: self.log_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=3)
        ttk.Button(select_frame, text="📤 导出", command=self._export_logs).pack(side=tk.LEFT, padx=3)

        self.auto_refresh_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(select_frame, text="自动刷新", variable=self.auto_refresh_var).pack(side=tk.LEFT, padx=10)

        # Log display
        log_display_frame = ttk.Frame(self.tab_logs)
        log_display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            log_display_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.log_text.tag_config("ERROR", foreground="#f44336")
        self.log_text.tag_config("WARNING", foreground="#ff9800")
        self.log_text.tag_config("INFO", foreground="#4caf50")
        self.log_text.tag_config("DEBUG", foreground="#2196f3")

        self._load_log_file()

    # === Service Control Methods ===

    def _start_master_service(self):
        """Start Master service as a background thread"""
        if self.master_running:
            messagebox.showwarning("警告", "Master 已在运行中")
            return

        # Save config first
        self._save_master_config(silent=True)

        self.master_running = True
        self.master_output = queue.Queue()

        def run_master():
            """Run Master in a thread with redirected output"""
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = StreamToQueue(self.master_output)
            sys.stderr = StreamToQueue(self.master_output)

            try:
                from master.signal_sender import MasterSignalSender
                config_file = str(self.master_config_path)
                sender = MasterSignalSender(config_file)
                sender.run()
            except Exception as e:
                self.master_output.put(('log', f"[Master ERROR] {e}"))
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                self.master_output.put(('done', ''))

        self.master_thread = threading.Thread(target=run_master, daemon=True)
        self.master_thread.start()

        # Update UI
        self.master_status_var.set("● 运行中")
        self.master_start_btn.config(state=tk.DISABLED)
        self.master_stop_btn.config(state=tk.NORMAL)
        self._set_status("Master 服务已启动", "green")

        # Start reading output
        self._read_master_output()

    def _stop_master_service(self):
        """Stop Master service"""
        if not self.master_running:
            return

        self.master_running = False
        self.master_output.put(('log', "[Master] 正在停止服务..."))

        # For a graceful stop, we would need to signal the master thread
        # For now, we just mark it as stopped
        self.master_status_var.set("● 已停止")
        self.master_start_btn.config(state=tk.NORMAL)
        self.master_stop_btn.config(state=tk.DISABLED)
        self._set_status("Master 服务已停止", "red")

    def _read_master_output(self):
        """Read output from Master queue and display in live output"""
        if not self.master_running:
            return

        try:
            while not self.master_output.empty():
                msg_type, text = self.master_output.get_nowait()
                if msg_type == 'log':
                    self._append_live_output(f"[Master] {text}\n")
                elif msg_type == 'done':
                    self.master_running = False
                    self.master_status_var.set("● 已停止")
                    self.master_start_btn.config(state=tk.NORMAL)
                    self.master_stop_btn.config(state=tk.DISABLED)
                    return
        except queue.Empty:
            pass

        self.root.after(200, self._read_master_output)

    def _start_slave_service(self):
        """Start Slave service as a background thread"""
        if self.slave_running:
            messagebox.showwarning("警告", "Slave 已在运行中")
            return

        self._save_slave_config(silent=True)

        self.slave_running = True
        self.slave_output = queue.Queue()

        def run_slave():
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = StreamToQueue(self.slave_output)
            sys.stderr = StreamToQueue(self.slave_output)

            try:
                from slave.signal_receiver import SlaveSignalReceiver
                config_file = str(self.slave_config_path)
                receiver = SlaveSignalReceiver(config_file)
                receiver.run()
            except Exception as e:
                self.slave_output.put(('log', f"[Slave ERROR] {e}"))
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                self.slave_output.put(('done', ''))

        self.slave_thread = threading.Thread(target=run_slave, daemon=True)
        self.slave_thread.start()

        self.slave_status_var.set("● 运行中")
        self.slave_start_btn.config(state=tk.DISABLED)
        self.slave_stop_btn.config(state=tk.NORMAL)
        self._set_status("Slave 服务已启动", "green")

        self._read_slave_output()

    def _stop_slave_service(self):
        """Stop Slave service"""
        if not self.slave_running:
            return

        self.slave_running = False
        self.slave_output.put(('log', "[Slave] 正在停止服务..."))

        self.slave_status_var.set("● 已停止")
        self.slave_start_btn.config(state=tk.NORMAL)
        self.slave_stop_btn.config(state=tk.DISABLED)
        self._set_status("Slave 服务已停止", "red")

    def _read_slave_output(self):
        """Read output from Slave queue"""
        if not self.slave_running:
            return

        try:
            while not self.slave_output.empty():
                msg_type, text = self.slave_output.get_nowait()
                if msg_type == 'log':
                    self._append_live_output(f"[Slave] {text}\n")
                elif msg_type == 'done':
                    self.slave_running = False
                    self.slave_status_var.set("● 已停止")
                    self.slave_start_btn.config(state=tk.NORMAL)
                    self.slave_stop_btn.config(state=tk.DISABLED)
                    return
        except queue.Empty:
            pass

        self.root.after(200, self._read_slave_output)

    def _restart_all(self):
        """Restart all services"""
        if self.master_running or self.slave_running:
            if not messagebox.askyesno("确认", "确定要重启所有服务吗？"):
                return
            self._stop_master_service()
            self._stop_slave_service()
            self.root.after(1000, self._restart_all_start)
        else:
            self._restart_all_start()

    def _restart_all_start(self):
        self._start_master_service()
        self.root.after(1000, self._start_slave_service)

    def _restart_master(self):
        """Restart Master service only"""
        if self.mode not in ('master', 'unified'):
            return
        if self.master_running:
            if not messagebox.askyesno("确认", "确定要重启 Master 服务吗？"):
                return
            self._stop_master_service()
        self.root.after(500, self._start_master_service)

    def _restart_slave(self):
        """Restart Slave service only"""
        if self.mode not in ('slave', 'unified'):
            return
        if self.slave_running:
            if not messagebox.askyesno("确认", "确定要重启 Slave 服务吗？"):
                return
            self._stop_slave_service()
        self.root.after(500, self._start_slave_service)

    # === Config Save Methods ===

    def _save_master_config(self, silent=False):
        """Save master configuration"""
        config = {
            "mqtt": {
                "broker": self.mc["mqtt_broker"].get(),
                "port": self.mc["mqtt_port"].get(),
                "username": self.mc["mqtt_username"].get(),
                "password": self.mc["mqtt_password"].get(),
                "client_id": self.mc["mqtt_client_id"].get(),
                "topic_prefix": self.mc["mqtt_topic_prefix"].get(),
            },
            "signal": {
                "send_interval_ms": self.mc["signal_interval"].get(),
                "include_positions": self.mc["signal_positions"].get(),
                "include_orders": self.mc["signal_orders"].get(),
            },
            "logging": {
                "level": self.mc["log_level"].get(),
                "file": self.mc["log_file"].get(),
                "max_size_mb": 10,
                "backup_count": 5
            }
        }

        if self._save_json(self.master_config_path, config):
            self.master_config = config
            if not silent:
                messagebox.showinfo("成功", "Master 配置已保存")
            self._set_status("Master 配置已保存", "green")

    def _save_slave_config(self, silent=False):
        """Save slave configuration"""
        # Parse symbol mappings
        mapping_text = self.sc["symbol_mapping_text"].get(1.0, tk.END).strip()
        symbol_mapping = {}
        for line in mapping_text.split('\n'):
            line = line.strip()
            if '=' in line:
                k, v = line.split('=', 1)
                symbol_mapping[k.strip()] = v.strip()

        config = {
            "mqtt": {
                "broker": self.sc["mqtt_broker"].get(),
                "port": self.sc["mqtt_port"].get(),
                "username": self.sc["mqtt_username"].get(),
                "password": self.sc["mqtt_password"].get(),
                "client_id": self.sc["mqtt_client_id"].get(),
                "topic_prefix": self.sc["mqtt_topic_prefix"].get(),
            },
            "trading": {
                "multiplier": self.sc["trade_multiplier"].get(),
                "reverse_trading": self.sc["trade_reverse"].get(),
                "max_lot_size": self.sc["trade_max_lot"].get(),
                "min_lot_size": self.sc["trade_min_lot"].get(),
                "lot_step": 0.01,
                "slippage_points": self.sc["trade_slippage"].get(),
                "magic_number": self.sc["trade_magic"].get(),
            },
            "risk_management": {
                "enable_risk_management": self.sc["risk_enabled"].get(),
                "max_daily_loss_usd": self.sc["risk_max_loss"].get(),
                "enable_spread_filter": self.sc["risk_spread_filter"].get(),
                "max_spread_points": self.sc["risk_max_spread"].get(),
            },
            "symbol_mapping": symbol_mapping,
            "logging": {
                "level": self.sc["log_level"].get(),
                "file": self.sc["log_file"].get(),
                "max_size_mb": 10,
                "backup_count": 5
            }
        }

        if self._save_json(self.slave_config_path, config):
            self.slave_config = config
            if not silent:
                messagebox.showinfo("成功", "Slave 配置已保存")
            self._set_status("Slave 配置已保存", "green")

    # === License Management Methods ===

    def _refresh_license_list(self):
        """Refresh the license list in the tree"""
        if not self.license_manager:
            return

        # Clear existing
        for item in self.license_tree.get_children():
            self.license_tree.delete(item)

        try:
            licenses = self.license_manager.list_licenses()
            for lic in licenses:
                self.license_tree.insert('', tk.END, values=(
                    lic.get('client_name', ''),
                    lic.get('license_key', '')[:30] + '...',
                    lic.get('status', 'unknown'),
                    lic.get('connections', 0),
                    lic.get('max_connections', 1),
                    lic.get('expire_date', '')
                ))
        except Exception as e:
            self._append_live_output(f"[License] 刷新失败: {e}\n")

    def _generate_license_dialog(self):
        """Show dialog to generate a new license"""
        if not self.license_manager:
            messagebox.showerror("错误", "授权管理模块未加载")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("生成许可证")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="客户名称:").pack(pady=5)
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var, width=40).pack(pady=3)

        ttk.Label(dialog, text="有效天数:").pack(pady=5)
        days_var = tk.StringVar(value="365")
        ttk.Entry(dialog, textvariable=days_var, width=40).pack(pady=3)

        ttk.Label(dialog, text="最大连接数:").pack(pady=5)
        conn_var = tk.StringVar(value="1")
        ttk.Entry(dialog, textvariable=conn_var, width=40).pack(pady=3)

        result_label = ttk.Label(dialog, text="", wraplength=380, foreground="blue")
        result_label.pack(pady=10)

        def do_generate():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("警告", "请输入客户名称")
                return
            try:
                days = int(days_var.get())
                max_conn = int(conn_var.get())
                key = self.license_manager.generate_license_key(name, days, max_conn)
                result_label.config(text=f"✓ 许可证已生成!\n密钥: {key}")
                self._refresh_license_list()
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字")

        ttk.Button(dialog, text="生成", command=do_generate).pack(pady=10)
        ttk.Button(dialog, text="关闭", command=dialog.destroy).pack()

    def _validate_license_dialog(self):
        """Show dialog to validate a license"""
        if not self.license_manager:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("验证许可证")
        dialog.geometry("450x300")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="许可证密钥:").pack(pady=5)
        key_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=key_var, width=55).pack(pady=3)

        result_text = scrolledtext.ScrolledText(dialog, height=8, width=55)
        result_text.pack(pady=10)

        def do_validate():
            key = key_var.get().strip()
            if not key:
                return
            result = self.license_manager.validate_license(key)
            result_text.delete(1.0, tk.END)
            if result.get('valid'):
                result_text.insert(tk.END, "✅ 许可证有效\n\n")
                for k, v in result.get('data', {}).items():
                    result_text.insert(tk.END, f"{k}: {v}\n")
            else:
                result_text.insert(tk.END, f"❌ 许可证无效\n原因: {result.get('message', 'Unknown')}\n")

        ttk.Button(dialog, text="验证", command=do_validate).pack(pady=5)
        ttk.Button(dialog, text="关闭", command=dialog.destroy).pack()

    def _revoke_license(self):
        """Revoke selected license"""
        if not self.license_manager:
            return

        selected = self.license_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要吊销的许可证")
            return

        if not messagebox.askyesno("确认", "确定要吊销选中的许可证吗？"):
            return

        # Get the license key from the selected row
        item = self.license_tree.item(selected[0])
        key_prefix = item['values'][1]

        # Find matching license
        try:
            licenses = self.license_manager.list_licenses()
            for lic in licenses:
                if lic.get('license_key', '').startswith(key_prefix[:10]):
                    if self.license_manager.revoke_license(lic['license_key']):
                        messagebox.showinfo("成功", f"许可证已吊销")
                        self._refresh_license_list()
                    else:
                        messagebox.showerror("错误", "吊销失败")
                    return
        except Exception as e:
            messagebox.showerror("错误", f"吊销失败: {e}")

    def _show_license_stats(self):
        """Show license statistics"""
        if not self.license_manager:
            return

        try:
            licenses = self.license_manager.list_licenses()
            total = len(licenses)
            active = sum(1 for l in licenses if l.get('status') == 'active')
            expired = sum(1 for l in licenses if l.get('status') == 'expired')
            revoked = sum(1 for l in licenses if l.get('status') == 'revoked')

            msg = (f"总许可证数: {total}\n"
                   f"活跃: {active}\n"
                   f"已过期: {expired}\n"
                   f"已吊销: {revoked}")
            messagebox.showinfo("许可证统计", msg)
        except Exception as e:
            messagebox.showerror("错误", f"获取统计失败: {e}")

    # === Monitoring Methods ===

    def _start_monitoring_loop(self):
        """Start the monitoring loop"""
        def loop():
            # Update service status
            master_text = "Master: ● 运行中" if self.master_running else "Master: ● 离线"
            master_color = "green" if self.master_running else "gray"
            self.mon_master_status.config(text=master_text, foreground=master_color)

            slave_text = "Slave: ● 运行中" if self.slave_running else "Slave: ● 离线"
            slave_color = "green" if self.slave_running else "gray"
            self.mon_slave_status.config(text=slave_text, foreground=slave_color)

            # Update stat labels (simulated for now)
            if self.master_running:
                self.monitor_data['master_signals_sent'] += 1
            if self.slave_running:
                self.monitor_data['slave_signals_received'] += 1

            for key, lbl in self.stat_labels.items():
                lbl.config(text=str(self.monitor_data.get(key, 0)))

            self.root.after(2000, loop)

        self.root.after(2000, loop)

    def _append_live_output(self, text):
        """Append text to live output area"""
        self.live_output.config(state=tk.NORMAL)
        self.live_output.insert(tk.END, text)
        self.live_output.see(tk.END)
        self.live_output.config(state=tk.DISABLED)

    # === Log Methods ===

    def _load_log_file(self):
        """Load and display a log file"""
        log_name = self.log_file_var.get()
        log_path = self.logs_dir / log_name

        self.log_text.delete(1.0, tk.END)

        if not log_path.exists():
            self.log_text.insert(tk.END, f"日志文件不存在: {log_name}\n")
            return

        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            for line in lines[-2000:]:
                if "ERROR" in line:
                    self.log_text.insert(tk.END, line, "ERROR")
                elif "WARNING" in line:
                    self.log_text.insert(tk.END, line, "WARNING")
                elif "INFO" in line:
                    self.log_text.insert(tk.END, line, "INFO")
                elif "DEBUG" in line:
                    self.log_text.insert(tk.END, line, "DEBUG")
                else:
                    self.log_text.insert(tk.END, line)

            self.log_text.see(tk.END)
        except Exception as e:
            self.log_text.insert(tk.END, f"读取日志失败: {e}\n")

    def _refresh_logs_timer(self):
        """Auto-refresh logs periodically"""
        if self.auto_refresh_var.get() and (self.master_running or self.slave_running):
            self._load_log_file()
        self.root.after(5000, self._refresh_logs_timer)

    def _export_logs(self):
        """Export current log view to file"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("成功", f"日志已导出到: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")

    # === Utility Methods ===

    def _set_status(self, message, color="black"):
        self.status_left.config(text=message, foreground=color)

    def _open_config_dir(self):
        self._open_dir(self.config_dir)

    def _open_logs_dir(self):
        self._open_dir(self.logs_dir)

    def _open_dir(self, path):
        import subprocess
        path = str(path)
        if sys.platform == 'win32':
            os.startfile(path)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', path])
        else:
            subprocess.Popen(['xdg-open', path])

    def _clear_all_logs(self):
        if messagebox.askyesno("确认", "确定要清理所有日志文件吗？"):
            try:
                for f in self.logs_dir.glob("*.log"):
                    f.unlink()
                self.log_text.delete(1.0, tk.END)
                messagebox.showinfo("成功", "日志已清理")
            except Exception as e:
                messagebox.showerror("错误", f"清理失败: {e}")

    def _check_dependencies(self):
        """Check if required Python packages are installed"""
        required = {
            'paho.mqtt': 'paho-mqtt',
            'numpy': 'numpy',
            'psutil': 'psutil',
        }
        missing = []
        for module, package in required.items():
            try:
                __import__(module.replace('.', '_') if '.' in module and module.count('.') == 1 else module.split('.')[0])
            except ImportError:
                missing.append(package)

        if missing:
            self.dep_status_var.set(f"缺少依赖: {', '.join(missing)}")
            self.dep_status_var.set(self.dep_status_var.get())  # force update

            if messagebox.askyesno("缺少依赖", f"缺少以下依赖:\n{', '.join(missing)}\n\n是否现在安装？"):
                self._install_deps(missing)
        else:
            self.dep_status_var.set("✓ 所有依赖已就绪")

    def _install_deps(self, packages):
        """Install missing dependencies"""
        import subprocess
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install'] + packages,
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                self.dep_status_var.set("✓ 依赖安装完成")
                messagebox.showinfo("成功", "依赖包安装完成")
            else:
                self.dep_status_var.set("✗ 依赖安装失败")
                messagebox.showerror("错误", f"安装失败:\n{result.stderr}")
        except Exception as e:
            self.dep_status_var.set("✗ 安装出错")
            messagebox.showerror("错误", f"安装出错: {e}")

    def _show_about(self):
        messagebox.showinfo(
            "关于",
            "MT5 Signal System - 统一管理平台 v2.0\n\n"
            "一个集成的 MT5 信号跟单管理系统\n"
            "• Master/Slave 服务统一管理\n"
            "• 可视化配置编辑\n"
            "• 授权许可证管理\n"
            "• 实时监控和日志查看\n\n"
            "© 2026 All Rights Reserved"
        )

    def _on_closing(self):
        """Handle window close event"""
        if self.master_running or self.slave_running:
            if messagebox.askyesno("确认", "服务正在运行，确定要退出吗？\n服务将自动停止。"):
                self._stop_master_service()
                self._stop_slave_service()
                self.root.after(500, self.root.destroy)
        else:
            self.root.destroy()


def main():
    """Main entry point with mode support"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='MT5 Signal System Management Panel')
    parser.add_argument('--mode', choices=['master', 'slave', 'unified'],
                       default='unified', help='Running mode (default: unified)')
    args = parser.parse_args()

    root = tk.Tk()

    # Try ttkbootstrap for better theming
    try:
        import ttkbootstrap as ttkb
        style = ttkb.Style(theme='cosmo')
    except ImportError:
        style = ttk.Style()
        style.theme_use('clam')

    app = UnifiedMT5Manager(root, mode=args.mode)
    root.mainloop()


if __name__ == "__main__":
    main()