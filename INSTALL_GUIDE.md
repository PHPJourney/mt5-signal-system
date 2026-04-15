# MT5 Signal System - 安装指南

## 📦 快速开始（无需安装 Python！）

### 方法一：使用一键启动器（推荐）

1. 解压下载的文件到任意目录
2. 双击 **`setup_and_start.bat`**
3. 选择要启动的服务

系统会自动检测 Python 环境，如果未安装会自动下载安装。

### 方法二：使用增强版管理面板

1. 双击 **`start_manager.bat`**
2. 在 UI 界面中配置 Master/Slave 参数
3. 点击"启动"按钮

### 方法三：单独启动服务

- 双击 **`start_master.bat`** 启动主服务器
- 双击 **`start_slave.bat`** 启动从服务器

---

## 🐍 Python 环境说明

### 内置 Python 运行时（便携版）

本系统**内置了 Python 3.11 便携版**，无需单独安装 Python！

- Python 运行时位于 `python_runtime/` 目录
- 启动脚本会自动检测并使用内置 Python
- 如果内置 Python 不存在，会尝试使用系统 Python
- 如果系统 Python 也不存在，可以运行 `install_python.bat` 自动安装

### 手动安装 Python

如果需要使用系统 Python：

1. 访问：https://www.python.org/downloads/
2. 下载 Python 3.8 或更高版本
3. 安装时**务必勾选 "Add Python to PATH"**
4. 安装完成后重启命令提示符

### 自动安装脚本

双击 **`install_python.bat`** 可以：
- 自动下载 Python 3.11 嵌入式版本
- 自动配置 pip 包管理器
- 自动安装所有必需的依赖包

---

## 📋 依赖包列表

系统运行需要以下 Python 包：

```
paho-mqtt    # MQTT 通信
numpy        # 数据处理
psutil       # 系统监控
MetaTrader5  # MT5 交易接口（可选，仅交易时需要）
```

这些依赖包会自动安装，无需手动操作。

---

## ⚙️ 配置说明

### 使用管理面板配置（推荐）

1. 双击 `start_manager.bat` 打开管理面板
2. 切换到"Master 配置"或"Slave 配置"选项卡
3. 填写各项参数后点击"保存"

### 手动编辑配置文件

配置文件位于 `config/` 目录：

- **`config/master_config.json`** - 主服务器配置
- **`config/slave_config.json`** - 从服务器配置

---

## 📂 目录结构

```
MT5_Signal_System/
├── python_runtime/          # 内置 Python 运行时（自动创建）
├── config/                  # 配置文件目录
│   ├── master_config.json   # 主服务器配置
│   └── slave_config.json    # 从服务器配置
├── logs/                    # 日志文件目录
├── master/                  # 主服务器代码
├── slave/                   # 从服务器代码
├── common/                  # 公共模块
├── setup_and_start.bat      # 一键启动器（推荐）
├── start_manager.bat        # 启动增强版管理面板
├── start_master.bat         # 启动主服务器
├── start_slave.bat          # 启动从服务器
├── install_python.bat       # Python 安装脚本
└── mt5_manager_enhanced.py  # 增强版管理面板
```

---

## 🚀 使用流程

### 首次使用

1. **双击 `setup_and_start.bat`** 启动一键启动器
2. 如果提示 Python 未安装，选择"自动安装"
3. 等待依赖包安装完成
4. 选择"启动管理面板"进行配置
5. 配置完成后，启动 Master 和 Slave 服务

### 日常使用

- 直接双击 `setup_and_start.bat` 选择服务启动
- 或使用 `start_manager.bat` 打开管理面板

---

## ❓ 常见问题

### Q: 提示 "Python 未安装" 怎么办？

A: 双击 `install_python.bat` 自动安装 Python，或从 https://www.python.org/downloads/ 手动安装。

### Q: 依赖包安装失败怎么办？

A: 
1. 检查网络连接
2. 尝试使用国内镜像：`python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple paho-mqtt numpy psutil`
3. MetaTrader5 安装失败不影响信号功能，只影响实际交易

### Q: 如何在后台运行服务？

A: 使用 Windows 任务计划程序创建定时任务，或使用 NSSM (Non-Sucking Service Manager) 将脚本注册为 Windows 服务。

### Q: 日志文件在哪里？

A: 日志文件位于 `logs/` 目录，也可以通过管理面板的"日志查看"选项卡查看。

---

## 📞 技术支持

如遇问题，请检查：
1. `logs/` 目录下的日志文件
2. 管理面板的状态栏信息
3. 确保防火墙允许 MQTT 端口通信
