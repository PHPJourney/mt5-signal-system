    def refresh_status(self):
        """刷新连接状态（从心跳文件和日志文件读取）"""
        try:
            # 检查 Master 连接状态
            if hasattr(self, 'master_conn_label'):
                master_heartbeat = self.app.base_dir / 'logs' / 'master.heartbeat'
                master_log = self.app.base_dir / 'logs' / 'master.log'
                
                status_text = _("MONITORING_OFFLINE")
                status_color = "gray"
                
                # 优先检查心跳文件
                if master_heartbeat.exists():
                    try:
                        import time
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
                        import time
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
                            
        except Exception as e:
            pass