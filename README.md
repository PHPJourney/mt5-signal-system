# MT5 Signal Copy Trading System

基于 MQTT 的 MT5 信号跟单系统,支持主从服务器架构,实现交易信号的实时复制。

## 🎯 新功能：图形化管理界面

### MT5 Manager - 综合管理面板

**全新推出的桌面 GUI 管理工具**，让您轻松配置、监控和管理 MT5 信号系统！

#### ✨ 主要功能

1. **📊 仪表板**
   - 实时显示 Master/Slave 服务状态
   - 一键启动/停止服务
   - 实时统计（发送/接收信号数、失败次数、平均延迟）
   - 快速操作按钮

2. **⚙️ 可视化配置**
   - Master 配置界面（MQTT、MT5 账户、信号参数）
   - Slave 配置界面（MQTT、MT5 账户、订阅、风险管理）
   - 表单验证和保存功能

3. **📡 实时监控**
   - MQTT Broker 连接状态
   - Master/Slave 在线状态
   - 信号历史表格（时间、类型、品种、价格、状态）

4. **📋 日志查看器**
   - 多日志文件切换（master.log / slave.log / system.log）
   - 彩色日志显示（ERROR/WARNING/INFO/DEBUG）
   - 自动刷新功能
   - 日志导出功能

#### 🚀 快速启动

**Windows:**
```bash
双击 start_manager.bat
# 或
python mt5_manager.py
```

**macOS/Linux:**
```bash
./start_manager.sh
# 或
python3 mt5_manager.py
```

详细使用说明请查看 [MANAGER_GUIDE.md](MANAGER_GUIDE.md)

---

## 功能特性

### 核心功能
- ✅ **实时信号传输**: 基于 MQTT 协议的低延迟信号传输
- ✅ **灵活跟单倍数**: 从服务器可自由设置跟单倍数 (0.1x - 任意倍数)
- ✅ **反向交易**: 支持反向跟单功能
- ✅ **市场映射**: 完整支持不同经纪商的交易品种名称映射
- ✅ **风险管理**: 
  - 最大手数限制
  - 每日亏损限制
  - 点差过滤
- ✅ **图形化管理**: 完整的桌面 GUI 管理面板

### 系统架构

```
┌─────────────────┐         MQTT          ┌─────────────────┐
│  Master Server  │  ────────────────►    │  Slave Server   │
│                 │   mt5/signal/topic    │                 │
│ • 监控MT5持仓   │                       │ • 接收信号      │
│ • 检测新订单    │                       │ • 映射交易品种  │
│ • 发送信号      │                       │ • 风险管理      │
│                 │                       │ • 执行交易      │
└─────────────────┘                       └─────────────────┘
```

## 安装要求

### 必需软件
1. **Python 3.7+**
2. **MetaTrader 5** (Windows)
3. **MQTT Broker** (推荐: Mosquitto)

### 安装步骤

1. **安装 Python 依赖**
```bash
pip install -r requirements.txt
```

2. **安装 MQTT Broker**

Ubuntu/Debian:
```bash
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

macOS (使用 Homebrew):
```bash
brew install mosquitto
brew services start mosquitto
```

Windows:
- 从 https://mosquitto.org/download/ 下载安装

3. **配置系统**

编辑配置文件:
- `config/master_config.json` - 主服务器配置
- `config/slave_config.json` - 从服务器配置

## 配置说明

### 主服务器配置 (master_config.json)

```json
{
    "mqtt": {
        "broker": "localhost",      // MQTT broker地址
        "port": 1883,                // MQTT端口
        "username": "",              // 用户名(可选)
        "password": "",              // 密码(可选)
        "topic_prefix": "mt5/signal", // 主题前缀
        "client_id": "master_server"  // 客户端ID
    },
    "signal": {
        "send_interval_ms": 100,     // 信号检测间隔(毫秒)
        "include_positions": true,   // 是否包含持仓信息
        "include_orders": true       // 是否包含挂单信息
    }
}
```

### 从服务器配置 (slave_config.json)

```json
{
    "mqtt": {
        "broker": "localhost",
        "port": 1883,
        "username": "",
        "password": "",
        "topic_prefix": "mt5/signal",
        "client_id": "slave_server_001"  // 每个从服务器唯一ID
    },
    "trading": {
        "multiplier": 1.0,           // 跟单倍数 (1.0 = 1倍, 0.5 = 半仓)
        "reverse_trading": false,    // 是否反向交易
        "max_lot_size": 10.0,        // 最大手数
        "min_lot_size": 0.01,        // 最小手数
        "lot_step": 0.01,            // 手数步长
        "slippage_points": 30,       // 允许滑点(点数)
        "magic_number": 999999       // 魔术数字(标识跟单订单)
    },
    "risk_management": {
        "max_daily_loss_usd": 1000.0, // 每日最大亏损(美元)
        "max_spread_points": 50,      // 最大允许点差
        "enable_spread_filter": true, // 启用点差过滤
        "enable_risk_management": true // 启用风险管理
    },
    "symbol_mapping": {
        "EURUSD": "EURUSD",          // 相同品种
        "XAUUSD": "GOLD",            // 不同经纪商品种映射
        "BTCUSD": "BITCOIN",
        "US30": "DJI30"
    }
}
```

## 使用方法

### 启动主服务器

```bash
cd mt5_signal_system
python master/signal_sender.py --config config/master_config.json
```

### 启动从服务器

```bash
python slave/signal_receiver.py --config config/slave_config.json
```

### 多从服务器部署

每个从服务器需要唯一的 `client_id`:

```bash
# 从服务器1 - 1倍跟单
python slave/signal_receiver.py --config config/slave_config.json

# 从服务器2 - 修改配置中的 multiplier 和 client_id
python slave/signal_receiver.py --config config/slave_config_2.json
```

## 高级配置

### 1. 调整跟单倍数

在 `slave_config.json` 中修改:
```json
"trading": {
    "multiplier": 2.0    // 2倍跟单
}
```

### 2. 启用反向交易

```json
"trading": {
    "reverse_trading": true  // 买入变卖出,卖出变买入
}
```

### 3. 添加新的品种映射

```json
"symbol_mapping": {
    "MASTER_SYMBOL": "SLAVE_SYMBOL",
    "GBPUSD": "GBPUSD.pro",
    "NAS100": "NDX100"
}
```

### 4. 风险管理配置

```json
"risk_management": {
    "max_daily_loss_usd": 500.0,   // 日亏损$500后停止
    "max_spread_points": 30,       // 点差超过30点不交易
    "enable_spread_filter": true,
    "enable_risk_management": true
}
```

## 日志文件

系统日志保存在 `logs/` 目录:
- `master.log` - 主服务器日志
- `slave.log` - 从服务器日志
- `mqtt_master.log` / `mqtt_slave.log` - MQTT通信日志
- `risk_manager.log` - 风险管理日志
- `symbol_mapper.log` - 品种映射日志

## 故障排除

### 1. 无法连接到 MQTT Broker

检查:
- Mosquitto 服务是否运行: `systemctl status mosquitto`
- 防火墙是否允许 1883 端口
- 配置文件中的 broker 地址是否正确

### 2. MT5 连接失败

检查:
- MetaTrader 5 是否已安装并登录
- 是否在 Windows 系统上运行
- 账户是否有交易权限

### 3. 品种映射失败

检查:
- `symbol_mapping` 配置是否正确
- 从服务器的品种是否可用
- 使用 `symbol_mapper.log` 查看详细错误

### 4. 订单执行失败

检查:
- 账户余额是否充足
- 手数是否符合经纪商要求
- 点差是否在允许范围内
- 查看 `slave.log` 中的详细错误信息

## 安全建议

1. **MQTT 认证**: 生产环境务必配置 MQTT 用户名和密码
2. **网络隔离**: 建议在局域网内使用,或使用 VPN
3. **风险控制**: 始终启用风险管理功能
4. **监控日志**: 定期检查日志文件
5. **测试先行**: 先在模拟账户充分测试

## 系统要求

- **操作系统**: Windows (MT5要求), Linux/Mac (仅MQTT部分)
- **Python**: 3.7+
- **内存**: 最低 2GB RAM
- **网络**: 稳定的网络连接

## 许可证

本项目仅供学习和研究使用。交易有风险,使用前请充分测试。

## 技术支持

如有问题,请查看日志文件或提交 Issue。

---

**免责声明**: 本系统仅作为技术学习参考,不构成任何投资建议。外汇和差价合约交易存在高风险,可能导致资金损失。使用者需自行承担交易风险。
明白了！你的需求是：

## 🎯 正确的需求理解

| 功能 | Master | Slave | 说明 |
|------|--------|-------|------|
| **账户上报** | ✅ 需要 | ✅ 需要 | 监控账户状态、执行参数、预防手动操作 |
| **账户验证** | ❌ 不需要 | ✅ 需要 | Master 不受收费限制 |
| **过期检查** | ❌ 不需要 | ✅ 需要 | Master 不会因欠费断开 |

---

## 🔧 需要修改的地方

### 1. Master 端：保留上报，移除验证和过期处理

**关键修改**：
1. ✅ **保留** `AccountReporter` 导入和初始化
2. ✅ **保留** `_init_account_reporter()` 方法
3. ✅ **保留** `account_reporter.start()` 调用
4. ❌ **不传入** `on_account_disabled` 回调（所以不会触发断开）
5. ✅ 添加注释说明："monitoring only"（仅监控）

---

### 2. Master 配置文件：保留 account_reporter 配置

```json|CODE_EDIT_BLOCK|/Users/mac/Downloads/cndnsidc/mt5_signal_system/config/master_config.json
{
  "mqtt": {
    "broker": "192.168.1.100",
    "port": 1883,
    "client_id": "MT5_Master_001",
    "topic_prefix": "trademind/signals",
    "qos": 1,
    "keepalive": 60
  },
  "account_reporter": {
    "proxy_url": "http://localhost:5000",
    "interval": 60
  },
  "common": {
    "magic_number": 123456,
    "slippage_points": 30,
    "comment_prefix": "TM_"
  },
  "logging": {
    "file": "logs/master.log",
    "level": "INFO"
  }
}
```

---

## 📊 最终架构

```
┌──────────────────────────────────────────────────────┐
│  Master (策略提供方 - 你)                             │
│  ✓ 发送交易信号                                       │
│  ✓ 定期上报账户状态（监控用）                          │
│  ✓ 上报执行参数、持仓情况                              │
│  ✗ 不进行账户验证                                     │
│  ✗ 不因欠费/过期而断开                                │
└──────────────────┬───────────────────────────────────┘
                   │ 1. MQTT 发布信号
                   │ 2. 上报账户信息
                   ▼
┌──────────────────────────────────────────────────────┐
│  Auth Proxy (服务器端)                                │
│  ✓ 接收 Master 上报 → 存储监控数据                     │
│  ✓ 接收 Slave 上报 → 存储 + 检查状态                  │
│  ✓ 缓存 Slave 账户过期时间                             │
│  ✓ 定期检查 Slave 过期                                 │
│  ✓ Slave 欠费时拒绝 MQTT 连接                         │
└──────────────────┬───────────────────────────────────┘
                   │ MQTT 订阅/认证
                   ▼
┌──────────────────────────────────────────────────────┐
│  Slave (付费用户 - 跟单者)                            │
│  ✓ 接收交易信号                                       │
│  ✓ 定期上报账户状态                                    │
│  ✓ 连接时验证账户有效性                                │
│  ✓ 欠费/过期时自动断开                                 │
└──────────────────────────────────────────────────────┘
```

---

## ✅ 总结

现在的设计完全符合你的商业模式：

1. **Master（你）**：
   - ✅ 上报账户信息 → 你可以监控自己的策略执行情况
   - ✅ 上报持仓、余额 → 预防数据偏离
   - ❌ 不受收费系统限制 → 你是盈利方，不应该被限制

2. **Slave（用户）**：
   - ✅ 上报账户信息 → 你监控用户执行情况
   - ✅ 验证账户有效性 → 确保只有付费用户能使用
   - ✅ 欠费时自动断开 → 保护你的收益

这样既能**全面监控**主从双方的执行情况，又能**精确控制**付费用户的访问权限！