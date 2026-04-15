# MT5 信号跟单系统 - 架构说明

## 项目结构

```
mt5_signal_system/
├── config/                      # 配置文件目录
│   ├── master_config.json      # 主服务器配置
│   └── slave_config.json       # 从服务器配置
├── common/                      # 通用模块
│   ├── __init__.py
│   ├── models.py               # 数据模型定义
│   ├── utils.py                # 工具函数
│   └── mqtt_client.py          # MQTT客户端封装
├── master/                      # 主服务器模块
│   ├── __init__.py
│   └── signal_sender.py        # 信号发送器
├── slave/                       # 从服务器模块
│   ├── __init__.py
│   ├── signal_receiver.py      # 信号接收器
│   ├── symbol_mapper.py        # 品种映射器
│   └── risk_manager.py         # 风险管理器
├── test/                        # 测试工具
│   ├── __init__.py
│   └── test_mqtt.py            # MQTT连接测试
├── logs/                        # 日志目录(自动生成)
├── requirements.txt             # Python依赖
├── start_master.sh             # 主服务器启动脚本
├── start_slave.sh              # 从服务器启动脚本
├── README.md                    # 使用说明
└── ARCHITECTURE.md             # 架构说明
```

## 核心组件说明

### 1. 数据模型 (common/models.py)

定义了系统中使用的所有数据结构:

- **SignalType**: 信号类型枚举 (新订单、平仓、修改等)
- **OrderType**: 订单类型枚举 (买入、卖出等)
- **PositionInfo**: 持仓信息数据类
- **OrderInfo**: 挂单信息数据类
- **TradingSignal**: 交易信号数据类
- **SignalMessage**: 完整信号消息包装类
- **RiskStatus**: 风险管理状态类

### 2. MQTT通信 (common/mqtt_client.py)

封装了MQTT客户端功能:

**主要功能:**
- 自动重连机制
- 连接状态管理
- 消息发布/订阅
- 回调函数支持
- 日志记录

**QoS级别:**
- QoS 0: 最多一次 (快速但可能丢失)
- QoS 1: 至少一次 (推荐,确保送达)
- QoS 2: 恰好一次 (最可靠但较慢)

### 3. 主服务器 (master/signal_sender.py)

负责监控MT5账户并广播信号:

**工作流程:**
1. 初始化MT5连接
2. 连接到MQTT Broker
3. 定期检测持仓变化
4. 识别新开仓/平仓/修改操作
5. 打包成信号消息并通过MQTT发送

**关键特性:**
- 智能信号检测 (避免重复发送)
- 可配置的发送频率
- 完整的持仓和挂单同步

### 4. 从服务器 (slave/signal_receiver.py)

接收信号并执行交易:

**工作流程:**
1. 初始化MT5连接
2. 订阅MQTT信号主题
3. 接收并解析信号消息
4. 通过品种映射器转换交易品种
5. 通过风险管理器检查是否允许交易
6. 计算实际手数 (应用倍数)
7. 执行交易 (支持反向)
8. 记录订单对应关系

**关键特性:**
- 异步信号处理
- 完整的错误处理
- 订单跟踪 (master ticket <-> slave ticket)

### 5. 品种映射器 (slave/symbol_mapper.py)

处理不同经纪商的品种名称差异:

**映射策略:**
1. 显式映射 (配置文件定义)
2. 直接使用原名称
3. 常见变体自动匹配 (XAUUSD->GOLD等)

**功能:**
- 动态刷新可用品种列表
- 点差检查
- 品种信息查询

### 6. 风险管理器 (slave/risk_manager.py)

多层风险控制:

**控制项:**
1. **每日亏损限制**: 达到限额后自动停止交易
2. **点差过滤**: 点差过大时不执行交易
3. **手数限制**: 
   - 最小/最大手数约束
   - 按步长标准化
   - 应用跟单倍数

**风险监控:**
- 实时跟踪当日盈亏
- 自动日结重置
- 交易状态管理

## 数据流图

```
主服务器                          MQTT Broker                      从服务器
    |                                  |                                |
    |  1. 检测持仓变化                  |                                |
    |----- 监控MT5 --------------------|                                |
    |                                  |                                |
    |  2. 生成信号                     |                                |
    |----- SignalMessage ------------->|                                |
    |     (JSON格式)                   |                                |
    |                                  |  3. 转发信号                   |
    |                                  |------------------------------>|
    |                                  |                                | 4. 解析信号
    |                                  |                                | 5. 映射品种
    |                                  |                                | 6. 风险检查
    |                                  |                                | 7. 计算手数
    |                                  |                                | 8. 执行交易
    |                                  |                                |----- 下单到MT5
    |                                  |                                |
```

## 消息格式

### 信号消息 (SignalMessage)

```json
{
    "signal_type": "NEW_ORDER",
    "master_id": "master_server",
    "timestamp": 1234567890.123,
    "signals": [
        {
            "signal_type": "NEW_ORDER",
            "symbol": "EURUSD",
            "order_type": "BUY",
            "volume": 1.0,
            "price": 1.1000,
            "sl": 1.0950,
            "tp": 1.1100,
            "ticket": 123456,
            "magic": 0,
            "comment": "",
            "timestamp": 1234567890.123
        }
    ],
    "positions": [...],
    "orders": [...]
}
```

## 配置最佳实践

### 保守型配置
```json
{
    "trading": {
        "multiplier": 0.5,
        "max_lot_size": 1.0
    },
    "risk_management": {
        "max_daily_loss_usd": 200,
        "max_spread_points": 30
    }
}
```

### 激进型配置
```json
{
    "trading": {
        "multiplier": 2.0,
        "max_lot_size": 10.0
    },
    "risk_management": {
        "max_daily_loss_usd": 1000,
        "max_spread_points": 100
    }
}
```

### 反向交易配置
```json
{
    "trading": {
        "multiplier": 1.0,
        "reverse_trading": true
    }
}
```

## 部署方案

### 方案1: 单机部署 (测试用)
- 主服务器和从服务器在同一台机器
- 使用本地Mosquitto broker
- 适合开发和测试

### 方案2: 局域网部署
- 主服务器在交易电脑
- 从服务器在其他电脑/VPS
- Mosquitto在内网服务器
- 低延迟,适合实盘

### 方案3: 互联网部署
- 使用公网MQTT broker (如CloudMQTT)
- 配置SSL/TLS加密
- 设置强密码认证
- 适合远程跟单

## 性能优化建议

1. **调整检测间隔**: `send_interval_ms` 根据网络情况调整
2. **使用QoS 1**: 平衡可靠性和性能
3. **减少不必要的数据**: 关闭 `include_positions` 如果不需要
4. **合理设置滑点**: 避免频繁重试
5. **监控日志**: 及时发现和解决问题

## 故障恢复

### 断线重连
- MQTT客户端自动重连
- 重新订阅主题
- 无需手动干预

### 订单同步
- 重启后会重新同步所有持仓
- 通过ticket跟踪避免重复下单
- 建议定期重启以清理状态

## 安全注意事项

1. **MQTT认证**: 生产环境必须启用
2. **防火墙**: 限制MQTT端口访问
3. **魔术数字**: 使用唯一值标识跟单订单
4. **权限隔离**: 从服务器使用独立账户
5. **备份配置**: 定期备份配置文件

## 扩展开发

### 添加新的信号类型
1. 在 `SignalType` 枚举中添加
2. 在主服务器中实现检测逻辑
3. 在从服务器中实现执行逻辑

### 添加新的风险控制
1. 在 `RiskManager` 中添加检查方法
2. 在配置文件中添加参数
3. 在 `_process_signal` 中调用检查

### 自定义品种映射
编辑 `slave_config.json` 中的 `symbol_mapping` 部分

---

**版本**: 1.0.0
**更新日期**: 2026-04-15
