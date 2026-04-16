# TradeMind MT5 - 打包指南

本指南介绍如何将 Master 和 Slave 分开打包，生成独立的安装包。

## 📦 打包方式

### 方式一：使用一键打包脚本（推荐）

#### Windows 用户
```bash
# 双击运行或在命令行执行
build_all.bat
```

#### macOS/Linux 用户
```bash
python build_all.py
```

### 方式二：分别打包

#### 仅打包 Master
```bash
# Windows
build_master.bat

# macOS/Linux
python build_master.py
```

#### 仅打包 Slave
```bash
# Windows
build_slave.bat

# macOS/Linux
python build_slave.py
```

## 🎯 打包选项

运行打包脚本后，可以选择以下三种打包方式：

### 1. 仅创建便携版（推荐）
- ✅ 无需编译
- ✅ 跨平台兼容
- ✅ 文件体积小
- ❌ 需要安装 Python 环境

**适用场景：** 开发测试、快速部署、有 Python 环境的服务器

### 2. 创建 PyInstaller 可执行文件
- ✅ 独立可执行文件
- ✅ 无需 Python 环境
- ❌ 文件体积大（约 50-100MB）
- ❌ 仅 Windows 可用

**适用场景：** 最终用户分发、无 Python 环境的生产环境

### 3. 完整打包（+ NSIS 安装程序）
- ✅ 包含所有选项
- ✅ 标准 Windows 安装体验
- ❌ 需要额外安装 NSIS

**适用场景：** 正式产品发布、企业级部署

## 📁 生成的文件结构

```
dist/
├── MT5_Master_Portable/          # Master 便携版
│   ├── start_master.bat          # 启动脚本
│   ├── config/
│   │   └── master_config.json    # 配置文件
│   ├── common/                   # 公共模块
│   ├── master/                   # Master 代码
│   ├── requirements.txt          # Python 依赖
│   └── 使用说明.txt
│
├── MT5_Slave_Portable/           # Slave 便携版
│   ├── start_slave.bat           # 启动脚本
│   ├── config/
│   │   └── slave_config.json     # 配置文件
│   ├── common/                   # 公共模块
│   ├── slave/                    # Slave 代码
│   ├── requirements.txt          # Python 依赖
│   └── 使用说明.txt
│
├── MT5_Master_Server_Installer.exe  # Master 安装程序（需编译 NSIS）
├── MT5_Slave_Server_Installer.exe   # Slave 安装程序（需编译 NSIS）
└── 发布说明.txt
```

## 🔧 编译 NSIS 安装程序

如果选择了选项 3，需要安装 NSIS 来编译安装程序：

### 1. 下载 NSIS
访问 https://nsis.sourceforge.io/Download 下载并安装

### 2. 编译安装程序
```bash
# 编译 Master 安装程序
makensis build/master_installer.nsi

# 编译 Slave 安装程序
makensis build/slave_installer.nsi
```

## 🚀 使用便携版

### Master Server
```bash
# 1. 进入目录
cd dist/MT5_Master_Portable

# 2. 安装依赖
pip install -r requirements.txt

# 3. 编辑配置
notepad config/master_config.json

# 4. 启动服务
start_master.bat
```

### Slave Server
```bash
# 1. 进入目录
cd dist/MT5_Slave_Portable

# 2. 安装依赖
pip install -r requirements.txt

# 3. 编辑配置
notepad config/slave_config.json

# 4. 启动服务
start_slave.bat
```

## ⚙️ 配置说明

### Master 配置 (config/master_config.json)
```json
{
  "mqtt": {
    "broker": "localhost",
    "port": 1883,
    "username": "master",
    "password": "your_password"
  },
  "mt5": {
    "login": 12345678,
    "password": "your_password",
    "server": "YourBroker-Server"
  }
}
```

### Slave 配置 (config/slave_config.json)
```json
{
  "mqtt": {
    "broker": "localhost",
    "port": 1883,
    "username": "slave",
    "password": "your_password"
  },
  "mt5": {
    "login": 87654321,
    "password": "your_password",
    "server": "YourBroker-Server"
  },
  "subscription": {
    "master_id": "master_001"
  }
}
```

## 📝 注意事项

1. **Master 和 Slave 可以部署在不同机器上**
   - 确保它们都能访问同一个 MQTT Broker

2. **首次运行前必须配置**
   - 修改配置文件中的 MQTT 和 MT5 账户信息
   - 确保 MT5 终端已安装并可登录

3. **防火墙设置**
   - 开放 MQTT 端口（默认 1883）
   - 允许 Python 或生成的 exe 通过防火墙

4. **日志查看**
   - 运行时日志保存在 `logs/` 目录
   - 遇到问题先查看日志文件

## 🐛 常见问题

### Q: PyInstaller 构建失败
A: 确保安装了最新版本的 PyInstaller：
```bash
pip install --upgrade pyinstaller
```

### Q: 生成的 exe 无法运行
A: 检查是否缺少依赖库，尝试重新构建：
```bash
python -m PyInstaller --clean build/master.spec
```

### Q: NSIS 编译报错
A: 确保 NSIS 已正确安装并添加到系统 PATH

### Q: 便携版启动失败
A: 确认已安装 Python 3.8+ 和所有依赖：
```bash
pip install -r requirements.txt
```

## 📞 技术支持

如遇问题请查看：
- README.md - 项目总览
- QUICKSTART.md - 快速开始
- ARCHITECTURE.md - 架构说明
- logs/*.log - 运行日志
