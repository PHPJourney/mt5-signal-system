"""
Configuration Panel for TradeMind MT5
GUI-based configuration management tool
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import sys
from pathlib import Path


class ConfigPanel:
    """配置面板主窗口"""

    def __init__(self, root):
        self.root = root
        self.root.title("TradeMind MT5 - Configuration Panel")
        self.root.geometry("900x700")

        # 配置文件路径
        self.base_dir = Path(__file__).parent
        self.master_config_path = self.base_dir / "config" / "master_config.json"
        self.slave_config_path = self.base_dir / "config" / "slave_config.json"

        # 加载配置
        self.master_config = self.load_config(self.master_config_path)
        self.slave_config = self.load_config(self.slave_config_path)

        # 创建界面
        self.create_widgets()

    def load_config(self, config_path):
        """加载配置文件"""
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                messagebox.showwarning("警告", f"配置文件不存在: {config_path}")
                return {}
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败: {e}")
            return {}

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

    def create_widgets(self):
        """创建界面组件"""
        # 创建选项卡
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 主服务器配置选项卡
        master_frame = ttk.Frame(notebook)
        notebook.add(master_frame, text="主服务器配置")
        self.create_master_config(master_frame)

        # 从服务器配置选项卡
        slave_frame = ttk.Frame(notebook)
        notebook.add(slave_frame, text="从服务器配置")
        self.create_slave_config(slave_frame)

        # 品种映射配置选项卡
        mapping_frame = ttk.Frame(notebook)
        notebook.add(mapping_frame, text="品种映射")
        self.create_symbol_mapping(mapping_frame)

        # 底部按钮
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        save_btn = ttk.Button(button_frame, text="保存所有配置", command=self.save_all_configs)
        save_btn.pack(side=tk.RIGHT, padx=5)

        reset_btn = ttk.Button(button_frame, text="重置为默认", command=self.reset_to_default)
        reset_btn.pack(side=tk.RIGHT, padx=5)

        test_btn = ttk.Button(button_frame, text="测试MQTT连接", command=self.test_mqtt)
        test_btn.pack(side=tk.RIGHT, padx=5)

    def create_master_config(self, parent):
        """创建主服务器配置界面"""
        # MQTT配置
        mqtt_frame = ttk.LabelFrame(parent, text="MQTT 配置", padding=10)
        mqtt_frame.pack(fill=tk.X, padx=5, pady=5)

        row = 0
        ttk.Label(mqtt_frame, text="Broker地址:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.master_broker_var = tk.StringVar(value=self.master_config.get('mqtt', {}).get('broker', 'localhost'))
        ttk.Entry(mqtt_frame, textvariable=self.master_broker_var, width=40).grid(row=row, column=1, padx=5, pady=2)
        row += 1

        ttk.Label(mqtt_frame, text="端口:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.master_port_var = tk.StringVar(value=str(self.master_config.get('mqtt', {}).get('port', 1883)))
        ttk.Entry(mqtt_frame, textvariable=self.master_port_var, width=40).grid(row=row, column=1, padx=5, pady=2)
        row += 1

        ttk.Label(mqtt_frame, text="用户名:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.master_username_var = tk.StringVar(value=self.master_config.get('mqtt', {}).get('username', ''))
        ttk.Entry(mqtt_frame, textvariable=self.master_username_var, width=40).grid(row=row, column=1, padx=5, pady=2)
        row += 1

        ttk.Label(mqtt_frame, text="密码:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.master_password_var = tk.StringVar(value=self.master_config.get('mqtt', {}).get('password', ''))
        ttk.Entry(mqtt_frame, textvariable=self.master_password_var, width=40, show="*").grid(row=row, column=1, padx=5, pady=2)
        row += 1

        ttk.Label(mqtt_frame, text="客户端ID:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.master_client_id_var = tk.StringVar(value=self.master_config.get('mqtt', {}).get('client_id', 'master_server'))
        ttk.Entry(mqtt_frame, textvariable=self.master_client_id_var, width=40).grid(row=row, column=1, padx=5, pady=2)

        # 信号配置
        signal_frame = ttk.LabelFrame(parent, text="信号配置", padding=10)
        signal_frame.pack(fill=tk.X, padx=5, pady=5)

        row = 0
        ttk.Label(signal_frame, text="检测间隔(毫秒):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.master_interval_var = tk.StringVar(value=str(self.master_config.get('signal', {}).get('send_interval_ms', 100)))
        ttk.Entry(signal_frame, textvariable=self.master_interval_var, width=40).grid(row=row, column=1, padx=5, pady=2)
        row += 1

        self.master_include_pos_var = tk.BooleanVar(value=self.master_config.get('signal', {}).get('include_positions', True))
        ttk.Checkbutton(signal_frame, text="包含持仓信息", variable=self.master_include_pos_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        row += 1

        self.master_include_orders_var = tk.BooleanVar(value=self.master_config.get('signal', {}).get('include_orders', True))
        ttk.Checkbutton(signal_frame, text="包含挂单信息", variable=self.master_include_orders_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)

    def create_slave_config(self, parent):
        """创建从服务器配置界面"""
        # 创建可滚动框架
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # MQTT配置
        mqtt_frame = ttk.LabelFrame(scrollable_frame, text="MQTT 配置", padding=10)
        mqtt_frame.pack(fill=tk.X, padx=5, pady=5)

        row = 0
        ttk.Label(mqtt_frame, text="Broker地址:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.slave_broker_var = tk.StringVar(value=self.slave_config.get('mqtt', {}).get('broker', 'localhost'))
        ttk.Entry(mqtt_frame, textvariable=self.slave_broker_var, width=40).grid(row=row, column=1, padx=5, pady=2)
        row += 1

        ttk.Label(mqtt_frame, text="端口:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.slave_port_var = tk.StringVar(value=str(self.slave_config.get('mqtt', {}).get('port', 1883)))
        ttk.Entry(mqtt_frame, textvariable=self.slave_port_var, width=40).grid(row=row, column=1, padx=5, pady=2)
        row += 1

        ttk.Label(mqtt_frame, text="客户端ID:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.slave_client_id_var = tk.StringVar(value=self.slave_config.get('mqtt', {}).get('client_id', 'slave_server_001'))
        ttk.Entry(mqtt_frame, textvariable=self.slave_client_id_var, width=40).grid(row=row, column=1, padx=5, pady=2)

        # 交易配置
        trading_frame = ttk.LabelFrame(scrollable_frame, text="交易配置", padding=10)
        trading_frame.pack(fill=tk.X, padx=5, pady=5)

        row = 0
        ttk.Label(trading_frame, text="跟单倍数:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.slave_multiplier_var = tk.StringVar(value=str(self.slave_config.get('trading', {}).get('multiplier', 1.0)))
        ttk.Entry(trading_frame, textvariable=self.slave_multiplier_var, width=40).grid(row=row, column=1, padx=5, pady=2)
        ttk.Label(trading_frame, text="(例如: 0.5=半仓, 1.0=全仓, 2.0=双倍)", foreground="gray").grid(row=row, column=2, padx=5, pady=2)
        row += 1

        self.slave_reverse_var = tk.BooleanVar(value=self.slave_config.get('trading', {}).get('reverse_trading', False))
        ttk.Checkbutton(trading_frame, text="反向交易 (买入变卖出,卖出变买入)", variable=self.slave_reverse_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        row += 1

        ttk.Label(trading_frame, text="最大手数:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.slave_max_lot_var = tk.StringVar(value=str(self.slave_config.get('trading', {}).get('max_lot_size', 10.0)))
        ttk.Entry(trading_frame, textvariable=self.slave_max_lot_var, width=40).grid(row=row, column=1, padx=5, pady=2)
        row += 1

        ttk.Label(trading_frame, text="最小手数:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.slave_min_lot_var = tk.StringVar(value=str(self.slave_config.get('trading', {}).get('min_lot_size', 0.01)))
        ttk.Entry(trading_frame, textvariable=self.slave_min_lot_var, width=40).grid(row=row, column=1, padx=5, pady=2)
        row += 1

        ttk.Label(trading_frame, text="滑点(点数):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.slave_slippage_var = tk.StringVar(value=str(self.slave_config.get('trading', {}).get('slippage_points', 30)))
        ttk.Entry(trading_frame, textvariable=self.slave_slippage_var, width=40).grid(row=row, column=1, padx=5, pady=2)

        # 风险管理配置
        risk_frame = ttk.LabelFrame(scrollable_frame, text="风险管理", padding=10)
        risk_frame.pack(fill=tk.X, padx=5, pady=5)

        row = 0
        self.slave_enable_risk_var = tk.BooleanVar(value=self.slave_config.get('risk_management', {}).get('enable_risk_management', True))
        ttk.Checkbutton(risk_frame, text="启用风险管理", variable=self.slave_enable_risk_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        row += 1

        ttk.Label(risk_frame, text="每日最大亏损(USD):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.slave_max_loss_var = tk.StringVar(value=str(self.slave_config.get('risk_management', {}).get('max_daily_loss_usd', 1000.0)))
        ttk.Entry(risk_frame, textvariable=self.slave_max_loss_var, width=40).grid(row=row, column=1, padx=5, pady=2)
        row += 1

        self.slave_enable_spread_var = tk.BooleanVar(value=self.slave_config.get('risk_management', {}).get('enable_spread_filter', True))
        ttk.Checkbutton(risk_frame, text="启用点差过滤", variable=self.slave_enable_spread_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        row += 1

        ttk.Label(risk_frame, text="最大点差(点数):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.slave_max_spread_var = tk.StringVar(value=str(self.slave_config.get('risk_management', {}).get('max_spread_points', 50)))
        ttk.Entry(risk_frame, textvariable=self.slave_max_spread_var, width=40).grid(row=row, column=1, padx=5, pady=2)

    def create_symbol_mapping(self, parent):
        """创建品种映射配置界面"""
        # 说明
        info_label = ttk.Label(
            parent,
            text="配置主服务器和从服务器之间的交易品种映射关系\n例如: XAUUSD (主) -> GOLD (从)",
            foreground="blue"
        )
        info_label.pack(pady=10)

        # 映射列表框架
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 树形视图
        columns = ('master', 'slave')
        self.mapping_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        self.mapping_tree.heading('master', text='主服务器品种')
        self.mapping_tree.heading('slave', text='从服务器品种')
        self.mapping_tree.column('master', width=200)
        self.mapping_tree.column('slave', width=200)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.mapping_tree.yview)
        self.mapping_tree.configure(yscrollcommand=scrollbar.set)

        self.mapping_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 加载现有映射
        self.load_symbol_mappings()

        # 按钮框架
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        add_btn = ttk.Button(btn_frame, text="添加映射", command=self.add_mapping)
        add_btn.pack(side=tk.LEFT, padx=5)

        edit_btn = ttk.Button(btn_frame, text="编辑映射", command=self.edit_mapping)
        edit_btn.pack(side=tk.LEFT, padx=5)

        delete_btn = ttk.Button(btn_frame, text="删除映射", command=self.delete_mapping)
        delete_btn.pack(side=tk.LEFT, padx=5)

    def load_symbol_mappings(self):
        """加载品种映射到树形视图"""
        # 清空现有项
        for item in self.mapping_tree.get_children():
            self.mapping_tree.delete(item)

        # 添加映射
        mappings = self.slave_config.get('symbol_mapping', {})
        for master, slave in mappings.items():
            self.mapping_tree.insert('', tk.END, values=(master, slave))

    def add_mapping(self):
        """添加新的品种映射"""
        dialog = MappingDialog(self.root, "添加品种映射")
        if dialog.result:
            master, slave = dialog.result
            # 检查是否已存在
            for item in self.mapping_tree.get_children():
                if self.mapping_tree.item(item)['values'][0] == master:
                    messagebox.showwarning("警告", f"映射已存在: {master}")
                    return

            self.mapping_tree.insert('', tk.END, values=(master, slave))

    def edit_mapping(self):
        """编辑品种映射"""
        selected = self.mapping_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要编辑的映射")
            return

        item = self.mapping_tree.item(selected[0])
        current_master, current_slave = item['values']

        dialog = MappingDialog(self.root, "编辑品种映射", current_master, current_slave)
        if dialog.result:
            master, slave = dialog.result
            self.mapping_tree.item(selected[0], values=(master, slave))

    def delete_mapping(self):
        """删除品种映射"""
        selected = self.mapping_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要删除的映射")
            return

        if messagebox.askyesno("确认", "确定要删除选中的映射吗?"):
            self.mapping_tree.delete(selected[0])

    def save_all_configs(self):
        """保存所有配置"""
        try:
            # 保存主服务器配置
            self.master_config['mqtt'] = {
                'broker': self.master_broker_var.get(),
                'port': int(self.master_port_var.get()),
                'username': self.master_username_var.get(),
                'password': self.master_password_var.get(),
                'topic_prefix': 'mt5/signal',
                'client_id': self.master_client_id_var.get()
            }
            self.master_config['signal'] = {
                'send_interval_ms': int(self.master_interval_var.get()),
                'include_positions': self.master_include_pos_var.get(),
                'include_orders': self.master_include_orders_var.get()
            }

            # 保存从服务器配置
            self.slave_config['mqtt'] = {
                'broker': self.slave_broker_var.get(),
                'port': int(self.slave_port_var.get()),
                'username': '',
                'password': '',
                'topic_prefix': 'mt5/signal',
                'client_id': self.slave_client_id_var.get()
            }
            self.slave_config['trading'] = {
                'multiplier': float(self.slave_multiplier_var.get()),
                'reverse_trading': self.slave_reverse_var.get(),
                'max_lot_size': float(self.slave_max_lot_var.get()),
                'min_lot_size': float(self.slave_min_lot_var.get()),
                'lot_step': 0.01,
                'slippage_points': int(self.slave_slippage_var.get()),
                'magic_number': 999999
            }
            self.slave_config['risk_management'] = {
                'max_daily_loss_usd': float(self.slave_max_loss_var.get()),
                'max_spread_points': int(self.slave_max_spread_var.get()),
                'enable_spread_filter': self.slave_enable_spread_var.get(),
                'enable_risk_management': self.slave_enable_risk_var.get()
            }

            # 保存品种映射
            symbol_mapping = {}
            for item in self.mapping_tree.get_children():
                values = self.mapping_tree.item(item)['values']
                symbol_mapping[values[0]] = values[1]
            self.slave_config['symbol_mapping'] = symbol_mapping

            # 写入文件
            if self.save_config(self.master_config_path, self.master_config):
                print(f"✓ 主服务器配置已保存: {self.master_config_path}")

            if self.save_config(self.slave_config_path, self.slave_config):
                print(f"✓ 从服务器配置已保存: {self.slave_config_path}")

            messagebox.showinfo("成功", "配置已保存!")

        except ValueError as e:
            messagebox.showerror("错误", f"输入值无效: {e}")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {e}")

    def reset_to_default(self):
        """重置为默认配置"""
        if messagebox.askyesno("确认", "确定要重置为默认配置吗?\n当前配置将丢失!"):
            # 重新加载默认配置
            self.master_config = self.load_config(self.master_config_path)
            self.slave_config = self.load_config(self.slave_config_path)

            # 刷新界面
            self.create_widgets()
            messagebox.showinfo("成功", "已重置为默认配置")

    def test_mqtt(self):
        """测试MQTT连接"""
        try:
            import paho.mqtt.client as mqtt
            import time

            broker = self.slave_broker_var.get()
            port = int(self.slave_port_var.get())

            messagebox.showinfo("测试中", f"正在测试连接到 {broker}:{port}...")

            # 创建测试客户端
            client = mqtt.Client()
            connected = False

            def on_connect(client, userdata, flags, rc):
                nonlocal connected
                if rc == 0:
                    connected = True
                    client.disconnect()

            client.on_connect = on_connect

            try:
                client.connect(broker, port, 5)
                client.loop_start()

                # 等待连接
                timeout = 5
                start_time = time.time()
                while not connected and time.time() - start_time < timeout:
                    time.sleep(0.1)

                client.loop_stop()

                if connected:
                    messagebox.showinfo("成功", f"✓ MQTT连接成功!\n{broker}:{port}")
                else:
                    messagebox.showerror("失败", f"✗ MQTT连接超时\n{broker}:{port}")

            except Exception as e:
                messagebox.showerror("失败", f"✗ MQTT连接失败\n{e}")

        except ImportError:
            messagebox.showwarning("警告", "paho-mqtt未安装，无法测试连接")


class MappingDialog:
    """品种映射对话框"""

    def __init__(self, parent, title, master="", slave=""):
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 居中显示
        self.dialog.update_idletasks()
        x = (parent.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (parent.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

        # 输入框
        frame = ttk.Frame(self.dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="主服务器品种:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.master_var = tk.StringVar(value=master)
        ttk.Entry(frame, textvariable=self.master_var, width=30).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="从服务器品种:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.slave_var = tk.StringVar(value=slave)
        ttk.Entry(frame, textvariable=self.slave_var, width=30).grid(row=1, column=1, padx=5, pady=5)

        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Button(btn_frame, text="确定", command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.cancel).pack(side=tk.LEFT, padx=5)

        # 绑定Enter键
        self.dialog.bind('<Return>', lambda e: self.ok())
        self.dialog.bind('<Escape>', lambda e: self.cancel())

        self.dialog.wait_window()

    def ok(self):
        master = self.master_var.get().strip()
        slave = self.slave_var.get().strip()

        if not master or not slave:
            messagebox.showwarning("警告", "请填写所有字段")
            return

        self.result = (master, slave)
        self.dialog.destroy()

    def cancel(self):
        self.dialog.destroy()


def main():
    """主函数"""
    root = tk.Tk()

    # 设置样式
    style = ttk.Style()
    style.theme_use('clam')

    app = ConfigPanel(root)
    root.mainloop()


if __name__ == "__main__":
    main()
