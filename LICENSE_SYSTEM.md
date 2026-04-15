# MT5 信号系统 - 授权认证系统

## 🎯 系统架构改进

### 之前的设计问题
❌ 需要外部 MQTT Broker  
❌ 无法限制接收对象  
❌ 没有授权机制  

### 现在的設計
✅ **主服务器内置 MQTT Broker**  
✅ **License 密钥认证**  
✅ **连接数限制**  
✅ **IP 地址绑定**  
✅ **功能权限控制**  
✅ **过期时间管理**  

---

## 🏗️ 新架构

```
┌──────────────────────────────────────┐
│      Master Server (主服务器)         │
│                                      │
│  ┌──────────────┐  ┌──────────────┐ │
│  │ Signal Sender│  │ MQTT Broker  │ │
│  │              │  │ (Embedded)   │ │
│  └──────┬───────┘  └──────┬───────┘ │
│         │                 │          │
│         │   发布信号       │          │
│         └────────┬────────┘          │
│                  │                   │
│     ┌────────────▼────────────┐     │
│     │   License Manager       │     │
│     │   - 认证客户端           │     │
│     │   - 验证密钥             │     │
│     │   - 限制连接             │     │
│     └─────────────────────────┘     │
└──────────────────────────────────────┘
                  │
        ┌─────────┼──────────┐
        │         │          │
        ▼         ▼          ▼
   ┌────────┐ ┌────────┐ ┌────────┐
   │Slave 1 │ │Slave 2 │ │Slave 3 │
   │License │ │License │ │License │
   │Key #1  │ │Key #2  │ │Key #3  │
   └────────┘ └────────┘ └────────┘
```

---

## 🔑 License 管理系统

### 1. 生成 License

```bash
cd mt5_signal_system

# 生成许可证
python manage_licenses.py generate "客户A" 365 1

# 输出:
# ============================================================
#   许可证生成成功!
# ============================================================
#
# 客户名称: 客户A
# 许可证密钥: A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6
# 有效天数: 365 天
# 最大连接: 1
# 过期时间: 2027-04-15T11:30:00.000000
#
# 请将许可证密钥提供给客户。
```

### 2. 查看许可证列表

```bash
python manage_licenses.py list

# 输出:
# ============================================================
#   许可证列表
# ============================================================
#
# 客户名称               许可证密钥                            状态       连接数     过期时间
# ----------------------------------------------------------------------------------------------------
# 客户A                  A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6    active     0/1       2027-04-15...
# 客户B                  B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7    active     1/2       2027-05-20...
#
# 总计: 2 个许可证
```

### 3. 验证许可证

```bash
python manage_licenses.py validate A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6

# 输出:
# ============================================================
#   许可证验证结果
# ============================================================
#
# ✅ 许可证有效
# 客户名称: 客户A
# 过期时间: 2027-04-15T11:30:00.000000
# 最大连接: 1
#
# 功能权限:
#   ✓ copy_trading
#   ✓ reverse_trading
#   ✓ symbol_mapping
#   ✓ risk_management
```

### 4. 吊销许可证

```bash
python manage_licenses.py revoke A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6

# 确认吊销后，该密钥立即失效
```

### 5. 查看统计

```bash
python manage_licenses.py stats

# 输出:
# ============================================================
#   许可证统计
# ============================================================
#
# 总许可证数: 10
# 活跃: 8
# 已过期: 1
# 已吊销: 1
#
# 当前总连接数: 5
```

---

## ⚙️ 配置从服务器使用 License

### 编辑配置文件

`config/slave_config.json`:

```json
{
    "mqtt": {
        "broker": "master-server-ip",
        "port": 1883,
        "username": "",
        "password": "",
        "topic_prefix": "mt5/signal",
        "client_id": "slave_server_001",
        "license_key": "A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6"
    },
    ...
}
```

**重要:** 将 `license_key` 设置为你生成的许可证密钥。

---

## 🔒 安全特性

### 1. 密钥加密存储

```python
# 许可证密钥使用 SHA-256 哈希
license_key = hashlib.sha256(raw_key.encode()).hexdigest()[:32].upper()
```

### 2. 连接数限制

```json
{
    "max_connections": 1,  // 最多1个连接
    "current_connections": 0  // 当前0个连接
}
```

### 3. IP 地址绑定

系统自动记录使用的 IP 地址：
```json
{
    "ip_addresses": ["192.168.1.100", "10.0.0.50"]
}
```

### 4. 过期时间控制

```json
{
    "expire_date": "2027-04-15T11:30:00",
    "status": "active"  // expired/revoked/inactive
}
```

### 5. 功能权限

```json
{
    "features": {
        "copy_trading": true,
        "reverse_trading": true,
        "symbol_mapping": true,
        "risk_management": true
    }
}
```

---

## 📋 License 数据库结构

文件位置: `config/licenses.json`

```json
{
    "clients": {
        "A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6": {
            "client_name": "客户A",
            "license_key": "A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6",
            "created_at": "2026-04-15T11:30:00",
            "expire_date": "2027-04-15T11:30:00",
            "max_connections": 1,
            "current_connections": 0,
            "features": {
                "copy_trading": true,
                "reverse_trading": true,
                "symbol_mapping": true,
                "risk_management": true
            },
            "status": "active",
            "last_used": "2026-04-15T12:00:00",
            "ip_addresses": ["192.168.1.100"]
        }
    },
    "blacklist": [],
    "created_at": "2026-04-15T11:30:00"
}
```

---

## 🚀 使用流程

### 管理员操作

#### 步骤1: 生成 License

```bash
# 为每个客户生成唯一许可证
python manage_licenses.py generate "客户名称" 365 1
```

#### 步骤2: 发送 License 给客户

将生成的 32 位密钥发送给客户。

#### 步骤3: 监控使用情况

```bash
# 查看所有许可证状态
python manage_licenses.py list

# 查看详细统计
python manage_licenses.py stats
```

#### 步骤4: 管理 License

```bash
# 吊销违规客户的许可证
python manage_licenses.py revoke <密钥>

# 导出备份
python manage_licenses.py export backup.json
```

---

### 客户操作

#### 步骤1: 接收 License

从管理员获取 32 位许可证密钥。

#### 步骤2: 配置从服务器

编辑 `config/slave_config.json`:
```json
{
    "mqtt": {
        "broker": "master-server-ip",
        "license_key": "你的许可证密钥"
    }
}
```

#### 步骤3: 启动从服务器

```bash
./start_slave.bat  # Windows
# 或
./start_slave.sh   # macOS/Linux
```

系统会自动：
1. 连接到主服务器
2. 提交 License 认证
3. 验证通过后开始接收信号

---

## 🔍 认证流程详解

```
从服务器启动
    ↓
连接到主服务器 MQTT Broker
    ↓
发送认证请求 (client_id + license_key)
    ↓
主服务器验证 License
    ├─ 检查密钥是否有效
    ├─ 检查是否过期
    ├─ 检查连接数限制
    ├─ 检查是否在黑名单
    └─ 检查功能权限
    ↓
验证结果
    ├─ ✅ 成功: 允许连接，开始接收信号
    └─ ❌ 失败: 拒绝连接，返回错误原因
```

---

## ❌ 常见错误代码

| 错误代码 | 说明 | 解决方法 |
|---------|------|---------|
| `INVALID_KEY` | 无效的密钥 | 检查密钥是否正确 |
| `EXPIRED` | 许可证已过期 | 联系管理员续期 |
| `REVOKED` | 许可证已吊销 | 联系管理员 |
| `MAX_CONNECTIONS` | 达到最大连接数 | 断开其他连接或升级License |
| `INACTIVE` | 许可证未激活 | 联系管理员 |

---

## 💡 高级用法

### 1. 多连接 License

```bash
# 允许最多5个同时连接
python manage_licenses.py generate "大客户" 365 5
```

### 2. 自定义功能权限

编辑 `manage_licenses.py` 的 `generate_license` 函数：

```python
features = {
    "copy_trading": True,
    "reverse_trading": False,  # 禁用反向交易
    "symbol_mapping": True,
    "risk_management": False   # 禁用风险管理
}
```

### 3. 短期试用 License

```bash
# 7天试用
python manage_licenses.py generate "试用客户" 7 1
```

### 4. 批量生成 License

```python
# 创建脚本 batch_generate.py
from master.auth_manager import LicenseManager

manager = LicenseManager()

customers = ["客户A", "客户B", "客户C"]
for customer in customers:
    key = manager.generate_license_key(customer, 365, 1)
    print(f"{customer}: {key}")
```

---

## 🛡️ 安全建议

### 1. 保护 License 数据库

```bash
# 设置文件权限 (Linux/macOS)
chmod 600 config/licenses.json

# 定期备份
cp config/licenses.json config/licenses.backup.json
```

### 2. 启用日志监控

查看 `logs/license.log` 和 `logs/mqtt_auth.log`：

```bash
tail -f logs/license.log
tail -f logs/mqtt_auth.log
```

### 3. 定期审计

```bash
# 每周检查一次
python manage_licenses.py list
python manage_licenses.py stats
```

### 4. IP 白名单 (可选)

在防火墙中只允许授权的 IP 连接：

```bash
# Linux iptables 示例
iptables -A INPUT -p tcp --dport 1883 -s 192.168.1.100 -j ACCEPT
iptables -A INPUT -p tcp --dport 1883 -j DROP
```

---

## 📊 商业模式示例

### 套餐设计

| 套餐 | 价格 | 有效期 | 连接数 | 功能 |
|------|------|--------|--------|------|
| 基础版 | ¥999/年 | 365天 | 1 | 基本跟单 |
| 专业版 | ¥2999/年 | 365天 | 3 | 全部功能 |
| 企业版 | ¥9999/年 | 365天 | 10 | 定制功能 |
| 试用版 | 免费 | 7天 | 1 |  limited |

### 生成示例

```bash
# 基础版
python manage_licenses.py generate "基础客户" 365 1

# 专业版
python manage_licenses.py generate "专业客户" 365 3

# 企业版
python manage_licenses.py generate "企业客户" 365 10

# 试用版
python manage_licenses.py generate "试用客户" 7 1
```

---

## 🔗 API 集成 (可选)

如果需要 Web 管理界面，可以使用提供的 API：

```python
from master.auth_manager import LicenseManager

manager = LicenseManager()

# 生成 License
key = manager.generate_license_key("客户名", 365, 1)

# 验证 License
result = manager.validate_license(key)

# 吊销 License
manager.revoke_license(key)

# 获取统计
stats = manager.list_licenses()
```

---

## ✨ 总结

### 优势

✅ **完全自主控制** - 无需外部 MQTT Broker  
✅ **灵活授权** - 按时间、连接数、功能授权  
✅ **安全可靠** - 加密存储、IP绑定、黑名单  
✅ **易于管理** - 命令行工具，简单易用  
✅ **可扩展** - 支持 API 集成  

### 快速开始

```bash
# 1. 生成 License
python manage_licenses.py generate "客户A" 365 1

# 2. 将密钥发给客户

# 3. 客户配置 slave_config.json 中的 license_key

# 4. 启动服务
./start_master.bat
./start_slave.bat

# 5. 监控使用
python manage_licenses.py list
```

**现在你可以完全控制谁可以使用你的信号系统！** 🎉
