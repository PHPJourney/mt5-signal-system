# ui/monitoring.py
"""监控模块"""
import tkinter as tk
from tkinter import ttk
from common.i18n import _


class MonitoringTab:
    """实时监控选项卡"""
    
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text=_("TAB_MONITORING"))
        
        # 读取配置中的 enabled 状态
        master_config = app.config_manager.load_config("master_config")
        slave_config = app.config_manager.load_config("slave_config")
        self.enable_master = master_config.get('enabled', True)
        self.enable_slave = slave_config.get('enabled', True)
        
        self.create_ui()
    
    def create_ui(self):
        """创建监控界面"""
        # 连接状态
        conn_frame = ttk.LabelFrame(self.frame, text=_("MONITORING_CONNECTION_STATUS"), padding=10)
        conn_frame.pack(fill=tk.X, padx=10, pady=5)

        conn_inner = ttk.Frame(conn_frame)
        conn_inner.pack(fill=tk.X)

        # MQTT 连接状态
        mqtt_status_frame = ttk.Frame(conn_inner)
        mqtt_status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Label(mqtt_status_frame, text="MQTT Broker:", font=("Microsoft YaHei", 10, "bold")).pack(anchor=tk.W)
        self.mqtt_status_label = ttk.Label(mqtt_status_frame, text=_("MONITORING_DISCONNECTED"), foreground="gray")
        self.mqtt_status_label.pack(anchor=tk.W)

        # Master 连接状态
        if self.enable_master:
            master_conn_frame = ttk.Frame(conn_inner)
            master_conn_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            ttk.Label(master_conn_frame, text="Master:", font=("Microsoft YaHei", 10, "bold")).pack(anchor=tk.W)
            self.master_conn_label = ttk.Label(master_conn_frame, text=_("MONITORING_OFFLINE"), foreground="gray")
            self.master_conn_label.pack(anchor=tk.W)

        # Slave 连接状态
        if self.enable_slave:
            slave_conn_frame = ttk.Frame(conn_inner)
            slave_conn_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            ttk.Label(slave_conn_frame, text="Slave:", font=("Microsoft YaHei", 10, "bold")).pack(anchor=tk.W)
            self.slave_conn_label = ttk.Label(slave_conn_frame, text=_("MONITORING_OFFLINE"), foreground="gray")
            self.slave_conn_label.pack(anchor=tk.W)

        # 信号历史
        history_frame = ttk.LabelFrame(self.frame, text=_("MONITORING_SIGNAL_HISTORY"), padding=10)
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
    
    def refresh_status(self):
        """刷新连接状态（从心跳文件和日志文件读取）"""
        try:
            import time
            
            # 检查 Master 连接状态
            if hasattr(self, 'master_conn_label'):
                master_heartbeat = self.app.base_dir / 'logs' / 'master.heartbeat'
                master_log = self.app.base_dir / 'logs' / 'master.log'
                
                status_text = _("MONITORING_OFFLINE")
                status_color = "gray"
                
                # 优先检查心跳文件
                if master_heartbeat.exists():
                    try:
                        with open(master_heartbeat, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            if lines:
                                last_heartbeat_time = float(lines[0].strip())
                                current_time = time.time()
                                
                                if current_time - last_heartbeat_time < 60:
                                    # 解析心跳信息
                                    info = {}
                                    for line in lines[1:]:
                                        if '=' in line:
                                            key, value = line.strip().split('=', 1)
                                            info[key] = value
                                    
                                    uptime = int(info.get('uptime', 0))
                                    hours = uptime // 3600
                                    minutes = (uptime % 3600) // 60
                                    
                                    if info.get('mqtt_connected') == 'True':
                                        status_text = f"已连接 (运行 {hours}h{minutes}m)"
                                        status_color = "green"
                                    else:
                                        status_text = f"MT5连接 (MQTT断开)"
                                        status_color = "orange"
                                else:
                                    status_text = "心跳超时 (可能已停止)"
                                    status_color = "red"
                    except Exception:
                        pass
                
                # 如果心跳文件不存在，回退到日志检查
                if status_text == _("MONITORING_OFFLINE") and master_log.exists():
                    try:
                        with open(master_log, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            recent_lines = lines[-50:] if len(lines) > 50 else lines
                            content = ''.join(recent_lines)
                            
                            if 'Connected to MQTT broker' in content:
                                if 'Shutting down' not in content or content.rfind('Connected') > content.rfind('Shutting down'):
                                    status_text = "已连接"
                                    status_color = "green"
                    except Exception:
                        pass
                
                self.master_conn_label.config(text=status_text, foreground=status_color)
            
            # 检查 Slave 连接状态
            if hasattr(self, 'slave_conn_label'):
                slave_heartbeat = self.app.base_dir / 'logs' / 'slave.heartbeat'
                slave_log = self.app.base_dir / 'logs' / 'slave.log'
                
                status_text = _("MONITORING_OFFLINE")
                status_color = "gray"
                
                # 优先检查心跳文件
                if slave_heartbeat.exists():
                    try:
                        with open(slave_heartbeat, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            if lines:
                                last_heartbeat_time = float(lines[0].strip())
                                current_time = time.time()
                                
                                if current_time - last_heartbeat_time < 60:
                                    # 解析心跳信息
                                    info = {}
                                    for line in lines[1:]:
                                        if '=' in line:
                                            key, value = line.strip().split('=', 1)
                                            info[key] = value
                                    
                                    uptime = int(info.get('uptime', 0))
                                    hours = uptime // 3600
                                    minutes = (uptime % 3600) // 60
                                    
                                    if info.get('mqtt_connected') == 'True':
                                        status_text = f"已连接 (运行 {hours}h{minutes}m)"
                                        status_color = "green"
                                    else:
                                        status_text = f"MT5连接 (MQTT断开)"
                                        status_color = "orange"
                                else:
                                    status_text = "心跳超时 (可能已停止)"
                                    status_color = "red"
                    except Exception:
                        pass
                
                # 如果心跳文件不存在，回退到日志检查
                if status_text == _("MONITORING_OFFLINE") and slave_log.exists():
                    try:
                        with open(slave_log, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            recent_lines = lines[-50:] if len(lines) > 50 else lines
                            content = ''.join(recent_lines)
                            
                            if 'Connected to MQTT broker' in content:
                                if 'Shutting down' not in content or content.rfind('Connected') > content.rfind('Shutting down'):
                                    status_text = "已连接"
                                    status_color = "green"
                    except Exception:
                        pass
                
                self.slave_conn_label.config(text=status_text, foreground=status_color)
            
            # 更新 MQTT Broker 状态（基于主从进程状态综合判断）
            if hasattr(self, 'mqtt_status_label'):
                master_online = hasattr(self, 'master_conn_label') and self.master_conn_label.cget('foreground') == 'green'
                slave_online = hasattr(self, 'slave_conn_label') and self.slave_conn_label.cget('foreground') == 'green'
                
                if master_online and slave_online:
                    mqtt_status = "Broker 正常 (Master+Slave 在线)"
                    mqtt_color = "green"
                elif master_online or slave_online:
                    mqtt_status = "Broker 正常 (部分在线)"
                    mqtt_color = "orange"
                else:
                    # 检查是否有最近的心跳文件
                    has_recent_heartbeat = False
                    for hb_file in ['master.heartbeat', 'slave.heartbeat']:
                        hb_path = self.app.base_dir / 'logs' / hb_file
                        if hb_path.exists():
                            try:
                                with open(hb_path, 'r', encoding='utf-8') as f:
                                    lines = f.readlines()
                                    if lines:
                                        last_time = float(lines[0].strip())
                                        if time.time() - last_time < 120:  # 2分钟内
                                            has_recent_heartbeat = True
                                            break
                            except:
                                pass
                    
                    if has_recent_heartbeat:
                        mqtt_status = "Broker 可能正常 (心跳存在但进程未响应)"
                        mqtt_color = "orange"
                    else:
                        mqtt_status = "Broker 离线或无活动"
                        mqtt_color = "red"
                
                self.mqtt_status_label.config(text=mqtt_status, foreground=mqtt_color)
                            
        except Exception as e:
            print(f"[ERROR] 刷新状态失败: {e}")
            import traceback
            traceback.print_exc()
