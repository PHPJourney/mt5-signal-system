"""
MT5 Signal System - 综合管理面板
包含配置管理、实时监控、服务控制和日志查看功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
import os
import sys
import subprocess
import threading
import time
from pathlib import Path
from datetime import datetime
import psutil


class MT5ManagerApp:
    """MT5 信号管理系统主应用"""

    def __init__(self, root):
        self.root = root
        self.root.title("MT5 Signal System - 管理平台")
        self.root.geometry("1200x800")

        # 基础路径
        self.base_dir = Path(__file__).parent
        self.config_dir = self.base_dir / "config"
        self.logs_dir = self.base_dir / "logs"

        # 确保目录存在
        self.config_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

        # 配置文件路径
        self.master_config_path = self.config_dir / "master_config.json"
        self.slave_config_path = self.config_dir / "slave_config.json"

        # 加载配置
        self.master_config = self.load_config(self.master_config_path)
        self.slave_config = self.load_config(self.slave_config_path)

        # 进程管理
        self.master_process = None
        self.slave_process = None
        self.master_running = False
        self.slave_running = False

        # 监控数据
        self.signal_stats = {
            'sent': 0,
            'received': 0,
            'failed': 0,
            'latency_avg': 0
        }

        # 创建界面
        self.create_main_ui()
        self.start_monitoring()

    def load_config(self, config_path):
        """加载配置文件"""
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self.get_default_config(config_path.stem)
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败: {e}")
            return {}

    def get_default_config(self, config_type):
        """获取默认配置"""
        if config_type == "master_config":
            return {
                "mqtt": {
                    "broker": "localhost",
                    "port": 1883,
                    "username": "master",
                    "password": "",
                    "client_id": "master_001"
                },
                "mt5": {
                    "login": 0,
                    "password": "",
                    "server": "",
                    "path": ""
                },
                "signal": {
                    "symbols": ["EURUSD", "GBPUSD", "USDJPY"],
                    "max_positions": 5,
                    "lot_size": 0.01
                }
            }
        else:
            return {
                "mqtt": {
                    "broker": "localhost",
                    "port": 1883,
                    "username": "slave",
                    "password": "",
                    "client_id": "slave_001"
                },
                "mt5": {
                    "login": 0,
                    "password": "",
                    "server": "",
                    "path": ""
                },
                "subscription": {
                    "master_id": "master_001"
                },
                "risk": {
                    "max_drawdown": 10,
                    "max_positions": 3,
                    "lot_multiplier": 1.0
                }
            }

    def save_config(self, config_path, config):
        """保存配置文件"""
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {e}")
            return False

    def create_main_ui(self):
        """创建主界面"""
        # 创建选项卡控件
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建各个选项卡
        self.create_dashboard_tab()
        self.create_master_config_tab()
        self.create_slave_config_tab()
        self.create_monitoring_tab()
        self.create_logs_tab()

        # 底部状态栏
        self.create_status_bar()

    def create_dashboard_tab(self):
        """创建仪表板选项卡"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="📊 仪表板")

        # 标题
        title_label = ttk.Label(
            dashboard_frame,
            text="MT5 信号管理系统",
            font=("Microsoft YaHei", 18, "bold")
        )
        title_label.pack(pady=20)

        # 状态卡片容器
        status_frame = ttk.Frame(dashboard_frame)
        status_frame.pack(fill=tk.X, padx=20, pady=10)

        # Master 状态卡片
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

        # 统计信息卡片
        stats_frame = ttk.LabelFrame(dashboard_frame, text="实时统计", padding=15)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)

        stats_inner = ttk.Frame(stats_frame)
        stats_inner.pack(fill=tk.X)

        # 发送信号数
        sent_frame = ttk.Frame(stats_inner)
        sent_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Label(sent_frame, text="已发送信号:", font=("Microsoft YaHei", 10)).pack()
        self.sent_count_label = ttk.Label(
            sent_frame,
            text="0",
            font=("Microsoft YaHei", 16, "bold"),
            foreground="#2196F3"
        )
        self.sent_count_label.pack()

        # 接收信号数
        received_frame = ttk.Frame(stats_inner)
        received_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Label(received_frame, text="已接收信号:", font=("Microsoft YaHei", 10)).pack()
        self.received_count_label = ttk.Label(
            received_frame,
            text="0",
            font=("Microsoft YaHei", 16, "bold"),
            foreground="#4CAF50"
        )
        self.received_count_label.pack()

        # 失败数
        failed_frame = ttk.Frame(stats_inner)
        failed_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Label(failed_frame, text="失败次数:", font=("Microsoft YaHei", 10)).pack()
        self.failed_count_label = ttk.Label(
            failed_frame,
            text="0",
            font=("Microsoft YaHei", 16, "bold"),
            foreground="#f44336"
        )
        self.failed_count_label.pack()

        # 平均延迟
        latency_frame = ttk.Frame(stats_inner)
        latency_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Label(latency_frame, text="平均延迟 (ms):", font=("Microsoft YaHei", 10)).pack()
        self.latency_label = ttk.Label(
            latency_frame,
            text="0",
            font=("Microsoft YaHei", 16, "bold"),
            foreground="#FF9800"
        )
        self.latency_label.pack()

        # 快速操作
        quick_actions_frame = ttk.LabelFrame(dashboard_frame, text="快速操作", padding=15)
        quick_actions_frame.pack(fill=tk.X, padx=20, pady=10)

        actions_inner = ttk.Frame(quick_actions_frame)
        actions_inner.pack(fill=tk.X)

        ttk.Button(
            actions_inner,
            text="🔄 重启所有服务",
            command=self.restart_all,
            width=20
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            actions_inner,
            text="📝 打开配置文件",
            command=self.open_config_folder,
            width=20
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            actions_inner,
            text="📂 打开日志文件夹",
            command=self.open_logs_folder,
            width=20
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            actions_inner,
            text="🧹 清理日志",
            command=self.clear_logs,
            width=20
        ).pack(side=tk.LEFT, padx=5)

    def create_master_config_tab(self):
        """创建 Master 配置选项卡"""
        master_frame = ttk.Frame(self.notebook)
        self.notebook.add(master_frame, text="⚙️ Master 配置")

        # 创建滚动区域
        canvas = tk.Canvas(master_frame)
        scrollbar = ttk.Scrollbar(master_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # MQTT 配置
        mqtt_frame = ttk.LabelFrame(scrollable_frame, text="MQTT 配置", padding=10)
        mqtt_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        ttk.Label(mqtt_frame, text="Broker 地址:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.master_broker_var = tk.StringVar(value=self.master_config.get('mqtt', {}).get('broker', 'localhost'))
        ttk.Entry(mqtt_frame, textvariable=self.master_broker_var, width=40).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(mqtt_frame, text="端口:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.master_port_var = tk.IntVar(value=self.master_config.get('mqtt', {}).get('port', 1883))
        ttk.Spinbox(mqtt_frame, from_=1, to=65535, textvariable=self.master_port_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(mqtt_frame, text="用户名:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.master_mqtt_user_var = tk.StringVar(value=self.master_config.get('mqtt', {}).get('username', ''))
        ttk.Entry(mqtt_frame, textvariable=self.master_mqtt_user_var, width=40).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(mqtt_frame, text="密码:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.master_mqtt_pass_var = tk.StringVar(value=self.master_config.get('mqtt', {}).get('password', ''))
        ttk.Entry(mqtt_frame, textvariable=self.master_mqtt_pass_var, show="*", width=40).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(mqtt_frame, text="Client ID:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.master_client_id_var = tk.StringVar(value=self.master_config.get('mqtt', {}).get('client_id', 'master_001'))
        ttk.Entry(mqtt_frame, textvariable=self.master_client_id_var, width=40).grid(row=row, column=1, padx=5)

        # MT5 配置
        mt5_frame = ttk.LabelFrame(scrollable_frame, text="MT5 账户配置", padding=10)
        mt5_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        ttk.Label(mt5_frame, text="账户登录号:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.master_mt5_login_var = tk.IntVar(value=self.master_config.get('mt5', {}).get('login', 0))
        ttk.Spinbox(mt5_frame, from_=0, to=999999999, textvariable=self.master_mt5_login_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(mt5_frame, text="密码:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.master_mt5_pass_var = tk.StringVar(value=self.master_config.get('mt5', {}).get('password', ''))
        ttk.Entry(mt5_frame, textvariable=self.master_mt5_pass_var, show="*", width=40).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(mt5_frame, text="服务器:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.master_mt5_server_var = tk.StringVar(value=self.master_config.get('mt5', {}).get('server', ''))
        ttk.Entry(mt5_frame, textvariable=self.master_mt5_server_var, width=40).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(mt5_frame, text="MT5 路径:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.master_mt5_path_var = tk.StringVar(value=self.master_config.get('mt5', {}).get('path', ''))
        path_frame = ttk.Frame(mt5_frame)
        path_frame.grid(row=row, column=1, padx=5)
        ttk.Entry(path_frame, textvariable=self.master_mt5_path_var, width=30).pack(side=tk.LEFT)
        ttk.Button(path_frame, text="浏览...", command=lambda: self.browse_folder(self.master_mt5_path_var)).pack(side=tk.LEFT, padx=2)

        # 信号配置
        signal_frame = ttk.LabelFrame(scrollable_frame, text="信号配置", padding=10)
        signal_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        ttk.Label(signal_frame, text="交易品种 (逗号分隔):").grid(row=row, column=0, sticky=tk.W, pady=2)
        symbols = ','.join(self.master_config.get('signal', {}).get('symbols', []))
        self.master_symbols_var = tk.StringVar(value=symbols)
        ttk.Entry(signal_frame, textvariable=self.master_symbols_var, width=40).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(signal_frame, text="最大持仓数:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.master_max_pos_var = tk.IntVar(value=self.master_config.get('signal', {}).get('max_positions', 5))
        ttk.Spinbox(signal_frame, from_=1, to=100, textvariable=self.master_max_pos_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(signal_frame, text="手数:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.master_lot_size_var = tk.DoubleVar(value=self.master_config.get('signal', {}).get('lot_size', 0.01))
        ttk.Spinbox(signal_frame, from_=0.01, to=100, increment=0.01, textvariable=self.master_lot_size_var, width=38).grid(row=row, column=1, padx=5)

        # 保存按钮
        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            btn_frame,
            text="💾 保存 Master 配置",
            command=self.save_master_config,
            width=20
        ).pack(side=tk.RIGHT)

    def create_slave_config_tab(self):
        """创建 Slave 配置选项卡"""
        slave_frame = ttk.Frame(self.notebook)
        self.notebook.add(slave_frame, text="⚙️ Slave 配置")

        # 创建滚动区域
        canvas = tk.Canvas(slave_frame)
        scrollbar = ttk.Scrollbar(slave_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # MQTT 配置
        mqtt_frame = ttk.LabelFrame(scrollable_frame, text="MQTT 配置", padding=10)
        mqtt_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        ttk.Label(mqtt_frame, text="Broker 地址:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.slave_broker_var = tk.StringVar(value=self.slave_config.get('mqtt', {}).get('broker', 'localhost'))
        ttk.Entry(mqtt_frame, textvariable=self.slave_broker_var, width=40).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(mqtt_frame, text="端口:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.slave_port_var = tk.IntVar(value=self.slave_config.get('mqtt', {}).get('port', 1883))
        ttk.Spinbox(mqtt_frame, from_=1, to=65535, textvariable=self.slave_port_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(mqtt_frame, text="用户名:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.slave_mqtt_user_var = tk.StringVar(value=self.slave_config.get('mqtt', {}).get('username', ''))
        ttk.Entry(mqtt_frame, textvariable=self.slave_mqtt_user_var, width=40).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(mqtt_frame, text="密码:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.slave_mqtt_pass_var = tk.StringVar(value=self.slave_config.get('mqtt', {}).get('password', ''))
        ttk.Entry(mqtt_frame, textvariable=self.slave_mqtt_pass_var, show="*", width=40).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(mqtt_frame, text="Client ID:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.slave_client_id_var = tk.StringVar(value=self.slave_config.get('mqtt', {}).get('client_id', 'slave_001'))
        ttk.Entry(mqtt_frame, textvariable=self.slave_client_id_var, width=40).grid(row=row, column=1, padx=5)

        # MT5 配置
        mt5_frame = ttk.LabelFrame(scrollable_frame, text="MT5 账户配置", padding=10)
        mt5_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        ttk.Label(mt5_frame, text="账户登录号:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.slave_mt5_login_var = tk.IntVar(value=self.slave_config.get('mt5', {}).get('login', 0))
        ttk.Spinbox(mt5_frame, from_=0, to=999999999, textvariable=self.slave_mt5_login_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(mt5_frame, text="密码:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.slave_mt5_pass_var = tk.StringVar(value=self.slave_config.get('mt5', {}).get('password', ''))
        ttk.Entry(mt5_frame, textvariable=self.slave_mt5_pass_var, show="*", width=40).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(mt5_frame, text="服务器:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.slave_mt5_server_var = tk.StringVar(value=self.slave_config.get('mt5', {}).get('server', ''))
        ttk.Entry(mt5_frame, textvariable=self.slave_mt5_server_var, width=40).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(mt5_frame, text="MT5 路径:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.slave_mt5_path_var = tk.StringVar(value=self.slave_config.get('mt5', {}).get('path', ''))
        path_frame = ttk.Frame(mt5_frame)
        path_frame.grid(row=row, column=1, padx=5)
        ttk.Entry(path_frame, textvariable=self.slave_mt5_path_var, width=30).pack(side=tk.LEFT)
        ttk.Button(path_frame, text="浏览...", command=lambda: self.browse_folder(self.slave_mt5_path_var)).pack(side=tk.LEFT, padx=2)

        # 订阅配置
        sub_frame = ttk.LabelFrame(scrollable_frame, text="订阅配置", padding=10)
        sub_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        ttk.Label(sub_frame, text="Master ID:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.slave_master_id_var = tk.StringVar(value=self.slave_config.get('subscription', {}).get('master_id', 'master_001'))
        ttk.Entry(sub_frame, textvariable=self.slave_master_id_var, width=40).grid(row=row, column=1, padx=5)

        # 风险管理配置
        risk_frame = ttk.LabelFrame(scrollable_frame, text="风险管理", padding=10)
        risk_frame.pack(fill=tk.X, padx=10, pady=5)

        row = 0
        ttk.Label(risk_frame, text="最大回撤 (%):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.slave_max_dd_var = tk.DoubleVar(value=self.slave_config.get('risk', {}).get('max_drawdown', 10))
        ttk.Spinbox(risk_frame, from_=1, to=100, increment=0.1, textvariable=self.slave_max_dd_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(risk_frame, text="最大持仓数:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.slave_max_pos_var = tk.IntVar(value=self.slave_config.get('risk', {}).get('max_positions', 3))
        ttk.Spinbox(risk_frame, from_=1, to=100, textvariable=self.slave_max_pos_var, width=38).grid(row=row, column=1, padx=5)
        row += 1

        ttk.Label(risk_frame, text="手数倍数:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.slave_lot_mult_var = tk.DoubleVar(value=self.slave_config.get('risk', {}).get('lot_multiplier', 1.0))
        ttk.Spinbox(risk_frame, from_=0.1, to=10, increment=0.1, textvariable=self.slave_lot_mult_var, width=38).grid(row=row, column=1, padx=5)

        # 保存按钮
        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            btn_frame,
            text="💾 保存 Slave 配置",
            command=self.save_slave_config,
            width=20
        ).pack(side=tk.RIGHT)

    def create_monitoring_tab(self):
        """创建实时监控选项卡"""
        monitor_frame = ttk.Frame(self.notebook)
        self.notebook.add(monitor_frame, text="📡 实时监控")

        # 连接状态
        conn_frame = ttk.LabelFrame(monitor_frame, text="连接状态", padding=10)
        conn_frame.pack(fill=tk.X, padx=10, pady=5)

        conn_inner = ttk.Frame(conn_frame)
        conn_inner.pack(fill=tk.X)

        # MQTT 连接状态
        mqtt_status_frame = ttk.Frame(conn_inner)
        mqtt_status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Label(mqtt_status_frame, text="MQTT Broker:", font=("Microsoft YaHei", 10, "bold")).pack(anchor=tk.W)
        self.mqtt_status_label = ttk.Label(mqtt_status_frame, text="● 未连接", foreground="gray")
        self.mqtt_status_label.pack(anchor=tk.W)

        # Master 连接状态
        master_conn_frame = ttk.Frame(conn_inner)
        master_conn_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Label(master_conn_frame, text="Master:", font=("Microsoft YaHei", 10, "bold")).pack(anchor=tk.W)
        self.master_conn_label = ttk.Label(master_conn_frame, text="● 离线", foreground="gray")
        self.master_conn_label.pack(anchor=tk.W)

        # Slave 连接状态
        slave_conn_frame = ttk.Frame(conn_inner)
        slave_conn_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Label(slave_conn_frame, text="Slave:", font=("Microsoft YaHei", 10, "bold")).pack(anchor=tk.W)
        self.slave_conn_label = ttk.Label(slave_conn_frame, text="● 离线", foreground="gray")
        self.slave_conn_label.pack(anchor=tk.W)

        # 信号历史
        history_frame = ttk.LabelFrame(monitor_frame, text="信号历史", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 创建表格
        columns = ("时间", "类型", "品种", "方向", "价格", "手数", "状态")
        self.signal_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.signal_tree.heading(col, text=col)
            self.signal_tree.column(col, width=100, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.signal_tree.yview)
        self.signal_tree.configure(yscrollcommand=scrollbar.set)

        self.signal_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 添加示例数据
        self.add_sample_signals()

    def add_sample_signals(self):
        """添加示例信号数据"""
        sample_data = [
            ("14:30:25", "BUY", "EURUSD", "开仓", "1.0850", "0.01", "成功"),
            ("14:28:12", "SELL", "GBPUSD", "平仓", "1.2650", "0.01", "成功"),
            ("14:25:45", "BUY", "USDJPY", "开仓", "151.20", "0.01", "成功"),
            ("14:20:30", "SELL", "EURUSD", "平仓", "1.0845", "0.01", "失败"),
        ]

        for data in sample_data:
            self.signal_tree.insert("", tk.END, values=data)

    def create_logs_tab(self):
        """创建日志查看选项卡"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="📋 日志查看")

        # 日志选择
        select_frame = ttk.Frame(logs_frame)
        select_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(select_frame, text="日志文件:").pack(side=tk.LEFT)
        self.log_file_var = tk.StringVar()
        log_files = ["master.log", "slave.log", "system.log"]
        self.log_combo = ttk.Combobox(select_frame, textvariable=self.log_file_var, values=log_files, width=30)
        self.log_combo.pack(side=tk.LEFT, padx=5)
        self.log_combo.set("master.log")

        ttk.Button(select_frame, text="刷新", command=self.refresh_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(select_frame, text="清空显示", command=self.clear_log_display).pack(side=tk.LEFT, padx=5)
        ttk.Button(select_frame, text="导出日志", command=self.export_logs).pack(side=tk.LEFT, padx=5)

        # 自动刷新
        self.auto_refresh_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(select_frame, text="自动刷新", variable=self.auto_refresh_var).pack(side=tk.LEFT, padx=5)

        # 日志显示区域
        log_display_frame = ttk.Frame(logs_frame)
        log_display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            log_display_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 配置文本标签颜色
        self.log_text.tag_config("ERROR", foreground="#f44336")
        self.log_text.tag_config("WARNING", foreground="#ff9800")
        self.log_text.tag_config("INFO", foreground="#4caf50")
        self.log_text.tag_config("DEBUG", foreground="#2196f3")

        # 初始加载日志
        self.load_logs()

    def create_status_bar(self):
        """创建状态栏"""
        status_bar = ttk.Frame(self.root)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # 左侧状态
        left_status = ttk.Frame(status_bar)
        left_status.pack(side=tk.LEFT, padx=10)

        self.system_status_label = ttk.Label(left_status, text="系统就绪", foreground="green")
        self.system_status_label.pack(side=tk.LEFT)

        # 右侧信息
        right_status = ttk.Frame(status_bar)
        right_status.pack(side=tk.RIGHT, padx=10)

        ttk.Label(right_status, text=f"版本: 1.0.0").pack(side=tk.LEFT, padx=5)
        ttk.Label(right_status, text=f"|").pack(side=tk.LEFT)
        ttk.Label(right_status, text=f"Python: {sys.version.split()[0]}").pack(side=tk.LEFT, padx=5)

    def start_master(self):
        """启动 Master 服务"""
        if self.master_running:
            messagebox.showwarning("警告", "Master 已在运行中")
            return

        try:
            # 启动 Master 进程
            script_path = self.base_dir / "master" / "signal_sender.py"
            config_path = self.master_config_path

            self.master_process = subprocess.Popen(
                [sys.executable, str(script_path), "--config", str(config_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )

            self.master_running = True
            self.master_status_label.config(text="● 运行中", foreground="green")
            self.master_conn_label.config(text="● 在线", foreground="green")
            self.update_status("Master 服务已启动")

            messagebox.showinfo("成功", "Master 服务已启动")

        except Exception as e:
            messagebox.showerror("错误", f"启动 Master 失败: {e}")
            self.update_status(f"启动 Master 失败: {e}")

    def stop_master(self):
        """停止 Master 服务"""
        if not self.master_running:
            messagebox.showwarning("警告", "Master 未在运行")
            return

        try:
            if self.master_process:
                self.master_process.terminate()
                self.master_process.wait(timeout=5)

            self.master_running = False
            self.master_status_label.config(text="● 已停止", foreground="red")
            self.master_conn_label.config(text="● 离线", foreground="gray")
            self.update_status("Master 服务已停止")

            messagebox.showinfo("成功", "Master 服务已停止")

        except Exception as e:
            messagebox.showerror("错误", f"停止 Master 失败: {e}")

    def start_slave(self):
        """启动 Slave 服务"""
        if self.slave_running:
            messagebox.showwarning("警告", "Slave 已在运行中")
            return

        try:
            # 启动 Slave 进程
            script_path = self.base_dir / "slave" / "signal_receiver.py"
            config_path = self.slave_config_path

            self.slave_process = subprocess.Popen(
                [sys.executable, str(script_path), "--config", str(config_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )

            self.slave_running = True
            self.slave_status_label.config(text="● 运行中", foreground="green")
            self.slave_conn_label.config(text="● 在线", foreground="green")
            self.update_status("Slave 服务已启动")

            messagebox.showinfo("成功", "Slave 服务已启动")

        except Exception as e:
            messagebox.showerror("错误", f"启动 Slave 失败: {e}")
            self.update_status(f"启动 Slave 失败: {e}")

    def stop_slave(self):
        """停止 Slave 服务"""
        if not self.slave_running:
            messagebox.showwarning("警告", "Slave 未在运行")
            return

        try:
            if self.slave_process:
                self.slave_process.terminate()
                self.slave_process.wait(timeout=5)

            self.slave_running = False
            self.slave_status_label.config(text="● 已停止", foreground="red")
            self.slave_conn_label.config(text="● 离线", foreground="gray")
            self.update_status("Slave 服务已停止")

            messagebox.showinfo("成功", "Slave 服务已停止")

        except Exception as e:
            messagebox.showerror("错误", f"停止 Slave 失败: {e}")

    def restart_all(self):
        """重启所有服务"""
        if messagebox.askyesno("确认", "确定要重启所有服务吗？"):
            self.stop_master()
            self.stop_slave()
            time.sleep(1)
            self.start_master()
            time.sleep(1)
            self.start_slave()

    def save_master_config(self):
        """保存 Master 配置"""
        config = {
            "mqtt": {
                "broker": self.master_broker_var.get(),
                "port": self.master_port_var.get(),
                "username": self.master_mqtt_user_var.get(),
                "password": self.master_mqtt_pass_var.get(),
                "client_id": self.master_client_id_var.get()
            },
            "mt5": {
                "login": self.master_mt5_login_var.get(),
                "password": self.master_mt5_pass_var.get(),
                "server": self.master_mt5_server_var.get(),
                "path": self.master_mt5_path_var.get()
            },
            "signal": {
                "symbols": [s.strip() for s in self.master_symbols_var.get().split(",") if s.strip()],
                "max_positions": self.master_max_pos_var.get(),
                "lot_size": self.master_lot_size_var.get()
            }
        }

        if self.save_config(self.master_config_path, config):
            self.master_config = config
            messagebox.showinfo("成功", "Master 配置已保存")
            self.update_status("Master 配置已保存")

    def save_slave_config(self):
        """保存 Slave 配置"""
        config = {
            "mqtt": {
                "broker": self.slave_broker_var.get(),
                "port": self.slave_port_var.get(),
                "username": self.slave_mqtt_user_var.get(),
                "password": self.slave_mqtt_pass_var.get(),
                "client_id": self.slave_client_id_var.get()
            },
            "mt5": {
                "login": self.slave_mt5_login_var.get(),
                "password": self.slave_mt5_pass_var.get(),
                "server": self.slave_mt5_server_var.get(),
                "path": self.slave_mt5_path_var.get()
            },
            "subscription": {
                "master_id": self.slave_master_id_var.get()
            },
            "risk": {
                "max_drawdown": self.slave_max_dd_var.get(),
                "max_positions": self.slave_max_pos_var.get(),
                "lot_multiplier": self.slave_lot_mult_var.get()
            }
        }

        if self.save_config(self.slave_config_path, config):
            self.slave_config = config
            messagebox.showinfo("成功", "Slave 配置已保存")
            self.update_status("Slave 配置已保存")

    def browse_folder(self, string_var):
        """浏览文件夹"""
        folder = filedialog.askdirectory()
        if folder:
            string_var.set(folder)

    def open_config_folder(self):
        """打开配置文件夹"""
        if sys.platform == 'win32':
            os.startfile(str(self.config_dir))
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', str(self.config_dir)])
        else:
            subprocess.Popen(['xdg-open', str(self.config_dir)])

    def open_logs_folder(self):
        """打开日志文件夹"""
        if sys.platform == 'win32':
            os.startfile(str(self.logs_dir))
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', str(self.logs_dir)])
        else:
            subprocess.Popen(['xdg-open', str(self.logs_dir)])

    def clear_logs(self):
        """清理日志文件"""
        if messagebox.askyesno("确认", "确定要清理所有日志文件吗？此操作不可恢复。"):
            try:
                for log_file in self.logs_dir.glob("*.log"):
                    log_file.unlink()
                self.log_text.delete(1.0, tk.END)
                messagebox.showinfo("成功", "日志文件已清理")
                self.update_status("日志文件已清理")
            except Exception as e:
                messagebox.showerror("错误", f"清理日志失败: {e}")

    def refresh_logs(self):
        """刷新日志显示"""
        self.load_logs()

    def clear_log_display(self):
        """清空日志显示"""
        self.log_text.delete(1.0, tk.END)

    def export_logs(self):
        """导出日志"""
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
                messagebox.showerror("错误", f"导出日志失败: {e}")

    def load_logs(self):
        """加载日志文件"""
        log_file_name = self.log_file_var.get()
        log_file_path = self.logs_dir / log_file_name

        self.log_text.delete(1.0, tk.END)

        if not log_file_path.exists():
            self.log_text.insert(tk.END, f"日志文件不存在: {log_file_name}\n")
            return

        try:
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            # 只显示最后 1000 行
            for line in lines[-1000:]:
                # 根据日志级别设置颜色
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

            # 滚动到底部
            self.log_text.see(tk.END)

        except Exception as e:
            self.log_text.insert(tk.END, f"读取日志失败: {e}\n")

    def update_status(self, message):
        """更新状态栏消息"""
        self.system_status_label.config(text=message)

    def start_monitoring(self):
        """启动监控线程"""
        def monitor_loop():
            while True:
                try:
                    # 更新统计数据（这里使用模拟数据）
                    if self.master_running or self.slave_running:
                        self.signal_stats['sent'] += 1
                        self.signal_stats['received'] += 1
                        self.signal_stats['latency_avg'] = 50 + (hash(str(time.time())) % 100)

                        # 更新UI
                        self.root.after(0, self.update_stats_display)

                except Exception as e:
                    pass

                time.sleep(5)  # 每5秒更新一次

        # 启动监控线程
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()

        # 如果启用自动刷新，定期刷新日志
        if self.auto_refresh_var.get():
            self.root.after(5000, self.refresh_logs)

    def update_stats_display(self):
        """更新统计数据显示"""
        self.sent_count_label.config(text=str(self.signal_stats['sent']))
        self.received_count_label.config(text=str(self.signal_stats['received']))
        self.failed_count_label.config(text=str(self.signal_stats['failed']))
        self.latency_label.config(text=str(self.signal_stats['latency_avg']))


def main():
    """主函数"""
    root = tk.Tk()

    # 尝试使用 ttkbootstrap 主题
    try:
        import ttkbootstrap as ttkb
        from ttkbootstrap.constants import *
        style = ttkb.Style(theme='cosmo')
        app = MT5ManagerApp(root)
    except ImportError:
        # 如果没有 ttkbootstrap，使用默认主题
        style = ttk.Style()
        style.theme_use('clam')
        app = MT5ManagerApp(root)

    root.mainloop()


if __name__ == "__main__":
    main()
