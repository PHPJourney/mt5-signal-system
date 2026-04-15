# ui/monitoring.py
"""监控模块"""
import tkinter as tk
from tkinter import ttk


class MonitoringTab:
    """实时监控选项卡"""
    
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="📡 实时监控")
        
        self.create_ui()
    
    def create_ui(self):
        """创建监控界面"""
        # 连接状态
        conn_frame = ttk.LabelFrame(self.frame, text="连接状态", padding=10)
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
        if self.app.install_config.get('enable_master', True):
            master_conn_frame = ttk.Frame(conn_inner)
            master_conn_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            ttk.Label(master_conn_frame, text="Master:", font=("Microsoft YaHei", 10, "bold")).pack(anchor=tk.W)
            self.master_conn_label = ttk.Label(master_conn_frame, text="● 离线", foreground="gray")
            self.master_conn_label.pack(anchor=tk.W)

        # Slave 连接状态
        if self.app.install_config.get('enable_slave', True):
            slave_conn_frame = ttk.Frame(conn_inner)
            slave_conn_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            ttk.Label(slave_conn_frame, text="Slave:", font=("Microsoft YaHei", 10, "bold")).pack(anchor=tk.W)
            self.slave_conn_label = ttk.Label(slave_conn_frame, text="● 离线", foreground="gray")
            self.slave_conn_label.pack(anchor=tk.W)

        # 信号历史
        history_frame = ttk.LabelFrame(self.frame, text="信号历史", padding=10)
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

        # 加载信号历史
        self.load_signal_history()
    
    def load_signal_history(self):
        """从日志文件加载信号历史"""
        # TODO: 实现从日志文件读取真实数据
        pass
