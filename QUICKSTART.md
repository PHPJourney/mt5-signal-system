# 快速开始指南

## 5分钟快速部署

### 步骤1: 安装MQTT Broker

**macOS:**
```bash
brew install mosquitto
brew services start mosquitto
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl start mosquitto
```

**Windows:**
下载并安装: https://mosquitto.org/download/

### 步骤2: 安装Python依赖

```bash
cd mt5_signal_system
pip install -r requirements.txt
```

### 步骤3: 测试MQTT连接

```bash
python test/test_mqtt.py
```

如果看到 "✓ 连接成功!" 说明MQTT正常工作。

### 步骤4: 配置系统

编辑 `config/slave_config.json`:

```json
{
    "trading": {
        "multiplier": 1.0,        // 改为想要的倍数
        "reverse_trading": false   // true为反向交易
    },
    "symbol_mapping": {
        // 根据实际经纪商调整
        "EURUSD": "EURUSD"
    }
}
```

### 步骤5: 启动服务

**终端1 - 启动主服务器:**
```bash
./start_master.sh
```

**终端2 - 启动从服务器:**
```bash
./start_slave.sh
```

### 步骤6: 验证工作

1. 在主服务器的MT5上手动开一个订单
2. 查看从服务器日志,应该看到订单被复制
3. 检查从服务器MT5是否有对应订单

## 常见场景配置

### 场景1: 半仓跟单

```json
{
    "trading": {
        "multiplier": 0.5,
        "max_lot_size": 5.0
    }
}
```

### 场景2: 反向对冲

```json
{
    "trading": {
        "multiplier": 1.0,
        "reverse_trading": true
    }
}
```

### 场景3: 不同经纪商品种映射

```json
{
    "symbol_mapping": {
        "XAUUSD": "GOLD",
        "BTCUSD": "BITCOIN",
        "US30": "DJI30",
        "NAS100": "NDX100"
    }
}
```

### 场景4: 严格风险控制

```json
{
    "risk_management": {
        "max_daily_loss_usd": 100,
        "max_spread_points": 20,
        "enable_spread_filter": true,
        "enable_risk_management": true
    },
    "trading": {
        "max_lot_size": 1.0
    }
}
```

## 故障排查

### 问题: 无法连接MQTT

**解决:**
```bash
# 检查Mosquitto是否运行
ps aux | grep mosquitto

# 测试端口
telnet localhost 1883

# 重启Mosquitto
sudo systemctl restart mosquitto
```

### 问题: MT5连接失败

**解决:**
- 确认在Windows系统运行
- 确认MT5已登录
- 检查是否有交易权限

### 问题: 品种映射失败

**解决:**
1. 查看 `logs/symbol_mapper.log`
2. 确认可用交易品种:
```python
import MetaTrader5 as mt5
mt5.initialize()
symbols = mt5.symbols_get()
for s in symbols:
    print(s.name)
```

### 问题: 订单未执行

**解决:**
1. 检查 `logs/slave.log` 错误信息
2. 确认账户余额充足
3. 检查点差是否过大
4. 确认风险管理未阻止交易

## 监控和维护

### 查看实时日志

```bash
# 主服务器
tail -f logs/master.log

# 从服务器
tail -f logs/slave.log

# MQTT通信
tail -f logs/mqtt_slave.log
```

### 检查风险状态

查看 `logs/risk_manager.log`:
```
Daily loss reset
Spread too high for EURUSD: 35.2 points (max: 30)
Trading disabled: Daily loss limit reached
```

### 备份配置

```bash
cp config/slave_config.json config/slave_config.json.backup
```

## 下一步

1. **阅读完整文档**: 查看 `README.md` 和 `ARCHITECTURE.md`
2. **模拟账户测试**: 先在demo账户充分测试
3. **调整参数**: 根据实际情况优化配置
4. **实盘部署**: 测试无误后切换到实盘

## 获取帮助

- 查看日志文件定位问题
- 阅读 `ARCHITECTURE.md` 了解系统设计
- 检查配置文件语法是否正确

---

**提示**: 建议先用模拟账户测试至少一周,确认系统稳定后再考虑实盘使用。
