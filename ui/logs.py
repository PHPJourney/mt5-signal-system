# ui/logs.py
"""日志模块"""
import tkinter as tk
from tkinter import ttk, scrolledtext
from pathlib import Path


class LogsTab:
    """日志查看选项卡"""
    
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="📋 日志")
        
        self.create_ui()
    
    def create_ui(self):
        """创建日志界面"""
        # 日志选择
        log_select_frame = ttk.Frame(self.frame)
        log_select_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(log_select_frame, text="日志文件:").pack(side=tk.LEFT, padx=5)
        
        self.log_file_var = tk.StringVar(value="master.log")
        log_files = ["master.log", "slave.log"]
        ttk.Combobox(
            log_select_frame,
            textvariable=self.log_file_var,
            values=log_files,
            state="readonly",
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            log_select_frame,
            text="🔄 刷新",
            command=self.refresh_logs
        ).pack(side=tk.LEFT, padx=5)

        # 日志内容
        log_frame = ttk.LabelFrame(self.frame, text="日志内容", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 加载日志
        self.load_logs()
    
    def load_logs(self):
        """加载日志文件"""
        log_file = self.app.base_dir / "logs" / self.log_file_var.get()
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.log_text.insert(tk.END, content)
            except Exception as e:
                self.log_text.insert(tk.END, f"读取日志失败: {e}")
        else:
            self.log_text.insert(tk.END, "日志文件不存在")
        
        self.log_text.config(state=tk.DISABLED)
    
    def refresh_logs(self):
        """刷新日志"""
        self.load_logs()
