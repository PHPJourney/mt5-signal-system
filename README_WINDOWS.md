# MT5 Signal System - Windows版

> 完整的MT5信号跟单系统,支持实时复制交易信号

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com)
[![Python](https://img.shields.io/badge/python-3.7+-green.svg)](https://www.python.org)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

---

## 🎯 核心功能

✅ **实时信号传输** - 基于MQTT协议,毫秒级延迟
✅ **灵活跟单倍数** - 0.1x到任意倍数自由设置
✅ **反向交易** - 一键开启反向跟单
✅ **市场映射** - 支持不同经纪商品种名称映射
✅ **风险管理** - 日亏损限制、点差过滤、手数控制
✅ **图形配置** - 友好的GUI配置面板
✅ **一键部署** - Windows批处理脚本自动安装

---

## 🚀 快速开始 (3步)

### 步骤1: 一键部署
```
双击运行: deploy.bat
```
自动完成环境检查、依赖安装、配置引导

### 步骤2: 配置系统
```
双击运行: config_panel.bat
```
在图形界面中设置:
- 跟单倍数
- 反向交易开关
- 品种映射
- 风险参数

### 步骤3: 启动服务
```
双击: start_master.bat  (主服务器)
双击: start_slave.bat   (从服务器)
```

---

## 📋 系统要求

### 必需软件
- ✅ Windows 7/8/10/11 (64位)
- ✅ Python 3.7+ ([下载](https://www.python.org/downloads/))
- ✅ MetaTrader 5 终端
- ✅ Mosquitto MQTT Broker

### 推荐配置
- CPU: 双核 2.0GHz+
- 内存: 4GB RAM
- 网络: 稳定互联网连接

---

## 📦 文件说明

### 🎮 启动脚本
| 文件 | 功能 |
|------|------|
| `deploy.bat` | ⭐ 一键部署 (推荐从这里开始) |
| `install.bat` | 安装Python依赖 |
| `install_mosquitto.bat` | 安装MQTT Broker |
| `config_panel.bat` | 打开配置面板 |
| `start_master.bat` | 启动主服务器 |
| `start_slave.bat` | 启动从服务器 |
| `verify_install.bat` | 验证安装完整性 |

### ⚙️ 配置文件
- `config/master_config.json` - 主服务器配置
- `config/slave_config.json` - 从服务器配置

### 📚 文档
- `WINDOWS_GUIDE.md` - 📘 详细使用指南
- `QUICKSTART.md` - 🚀 快速开始
- `ARCHITECTURE.md` - 🏗️ 技术架构
- `CHEATSHEET.md` - 📝 快速参考
- `PROJECT_SUMMARY.md` - 📊 项目总览

---

## 🎨 配置面板预览

运行 `config_panel.bat` 打开图形化配置界面:

**主要功能:**
- 🖥️ 主服务器配置 (MQTT、检测间隔)
- 📊 从服务器配置 (倍数、反向、风控)
- 🔄 品种映射管理 (添加/编辑/删除)
- 🔌 MQTT连接测试
- 💾 一键保存配置

---

## 💡 常用配置场景

### 场景1: 标准跟单 (1倍)
```json
{
    "multiplier": 1.0,
    "reverse_trading": false,
    "max_daily_loss_usd": 1000
}
```

### 场景2: 半仓跟单
```json
{
    "multiplier": 0.5,
    "max_lot_size": 5.0
}
```

### 场景3: 反向对冲
```json
{
    "multiplier": 1.0,
    "reverse_trading": true
}
```

### 场景4: 品种映射
```json
{
    "symbol_mapping": {
        "XAUUSD": "GOLD",
        "BTCUSD": "BITCOIN",
        "US30": "DJI30"
    }
}
```

---

## 🔧 故障排除

### 问题1: Python未找到
**解决:** 重新安装Python,勾选"Add Python to PATH"

### 问题2: MQTT连接失败
**解决:**
```cmd
net start mosquitto
```

### 问题3: MT5初始化失败
**解决:** 先登录MT5终端

### 问题4: 品种映射失败
**解决:** 在配置面板添加正确的映射关系

### 查看详细日志
```
logs/master.log      - 主服务器日志
logs/slave.log       - 从服务器日志
logs/risk_manager.log - 风险管理日志
```

---

## 🛡️ 安全建议

1. ⚠️ **先在模拟账户测试** - 至少测试1-2周
2. 🔐 **启用MQTT认证** - 生产环境设置用户名密码
3. 📊 **启用风险管理** - 设置合理的日亏损限制
4. 📝 **监控日志** - 定期检查logs目录
5. 💾 **备份配置** - 定期备份config文件

---

## 📖 学习路径

**新手用户:**
1. 阅读 `WINDOWS_GUIDE.md`
2. 运行 `deploy.bat`
3. 使用 `config_panel.bat` 配置
4. 查看 `CHEATSHEET.md` 快速参考

**进阶用户:**
1. 阅读 `ARCHITECTURE.md` 了解架构
2. 查看源代码理解实现
3. 根据需要定制功能

---

## 🎓 视频教程 (即将推出)

- [ ] 安装和配置教程
- [ ] 配置面板使用指南
- [ ] 故障排除指南
- [ ] 高级功能演示

---

## 🤝 贡献

欢迎提交Issue和Pull Request!

---

## 📄 许可证

MIT License

**免责声明:**
> 外汇和差价合约交易存在高风险,可能导致资金损失。
> 本系统仅供学习和研究使用,不构成投资建议。
> 使用者需自行承担所有交易风险。

---

## 📞 技术支持

- 📧 Email: support@example.com
- 💬 Issues: [GitHub Issues](https://github.com/yourrepo/issues)
- 📚 Docs: 查看docs/目录下的完整文档

---

## 🌟 特性对比

| 功能 | 免费版 | 专业版 |
|------|--------|--------|
| 实时信号传输 | ✅ | ✅ |
| 跟单倍数 | ✅ | ✅ |
| 反向交易 | ✅ | ✅ |
| 品种映射 | ✅ | ✅ |
| 风险管理 | ✅ | ✅ |
| 配置面板 | ✅ | ✅ |
| 多从服务器 | ✅ | ✅ |
| 技术支持 | 社区 | 优先 |
| 定制开发 | ❌ | ✅ |

---

## 📈 更新日志

### v1.0.0 (2026-04-15)
🎉 首次发布
- ✅ 完整的信号跟单系统
- ✅ 图形化配置面板
- ✅ Windows一键部署
- ✅ 全面的风险管理
- ✅ 详细的文档

---

**Made with ❤️ for MT5 Traders**

[⭐ Star this project](https://github.com/yourrepo) | [📖 Read Docs](WINDOWS_GUIDE.md) | [🚀 Get Started](deploy.bat)
