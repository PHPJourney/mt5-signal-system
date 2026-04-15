# 独立 MQTT Broker 授权方案

## 🎯 问题场景

当你使用**独立部署的 MQTT Broker** (如 Mosquitto) 时，如何实现信号转发的授权控制？

---

## 🏗️ 解决方案架构

### 方案对比

| 方案 | 安全性 | 复杂度 | 适用场景 |
|------|--------|--------|---------|
| **应用层认证+加密** | ⭐⭐⭐⭐⭐ | 中等 | ✅ 推荐 |
| Mosquitto ACL | ⭐⭐⭐⭐ | 简单 | 内网环境 |
| VPN + ACL | ⭐⭐⭐⭐⭐ | 复杂 | 高安全要求 |

---

## ✨ 推荐方案: 应用层认证 + 信号加密

### 架构图

```
┌─────────────────────────────────────────────────────┐
│              Master Server                          │
│                                                     │
│  ┌──────────────┐    ┌──────────────────────────┐  │
│  │ Signal Sender│───▶│   MQTT Auth Bridge       │  │
│  │              │    │   - License验证           │  │
│  └──────────────┘    │   - 信号加密              │  │
│                      │   - 会话管理              │  │
│                      └──────────┬───────────────┘  │
└─────────────────────────────────┼──────────────────┘
                                  │
                        发布加密信号到主题
                        mt5/signals/{license_prefix}
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │   Independent MQTT      │
                    │   Broker (Mosquitto)    │
                    │   - 用户认证            │
                    │   - ACL访问控制         │
                    │   - SSL/TLS (可选)      │
                    └───────────┬─────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
        ┌──────────────┐ ┌──────────┐ ┌──────────┐
        │ Slave Server │ │ Slave    │ │ Slave    │
        │ #1           │ │ Server #2│ │ Server #3│
        │              │ │          │ │          │
        │ Auth Client  │ │Auth Client│ │Auth Client│
        │ - License认证│ │- License │ │- License │
        │ - 信号解密   │ │ 认证     │ │ 认证     │
        └──────────────┘ └──────────┘ └──────────┘
```

---

## 🔧 实现步骤

### 步骤1: 配置 Mosquitto Broker

#### 1.1 安装 Mosquitto

```bash
# Ubuntu/Debian
sudo apt-get install mosquitto mosquitto-clients

# macOS
brew install mosquitto

# Docker
docker run -d -p 1883:1883 eclipse-mosquitto
```

#### 1.2 生成ACL配置

```bash
cd mt5_signal_system

# 使用工具生成ACL配置
python -c "
from master.auth_manager import LicenseManager
from master.mqtt_auth_bridge import MosquittoACLGenerator

manager = LicenseManager()
generator = MosquittoACLGenerator(manager)

# 生成ACL文件
generator.generate_acl_config('config/mosquitto_acl.conf')
generator.generate_password_file('config/mosquitto_passwd')
generator.generate_mosquitto_conf('config/mosquitto.conf')
"
```

#### 1.3 设置Mosquitto密码

```bash
# 为每个License创建用户
mosquitto_passwd -b config/mosquitto_passwd A1B2C3D4 A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6
mosquitto_passwd -b config/mosquitto_passwd B2C3D4E5 B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7

# 复制配置文件到Mosquitto目录
sudo cp config/mosquitto.conf /etc/mosquitto/mosquitto.conf
sudo cp config/mosquitto_acl.conf /etc/mosquitto/mosquitto_acl.conf
sudo cp config/mosquitto_passwd /etc/mosquitto/mosquitto_passwd

# 重启Mosquitto
sudo systemctl restart mosquitto
```

#### 1.4 Mosquitto 配置示例

`/etc/mosquitto/mosquitto.conf`:

```conf
# 监听端口
listener 1883

# 禁用匿名访问
allow_anonymous false

# 密码文件
password_file /etc/mosquitto/mosquitto_passwd

# ACL文件
acl_file /etc/mosquitto/mosquitto_acl.conf

# SSL/TLS (生产环境推荐)
# listener 8883
# cafile /etc/mosquitto/ca_certificates/ca.crt
# certfile /etc/mosquitto/certs/server.crt
# keyfile /etc/mosquitto/certs/server.key

# 日志
log_type all
log_dest file /var/log/mosquitto/mosquitto.log

# 持久化
persistence true
persistence_location /var/lib/mosquitto/
```

`/etc/mosquitto/mosquitto_acl.conf`:

```conf
# 客户A (License: A1B2C3D4...)
user A1B2C3D4
topic read mt5/signals/A1B2C3D4
topic write mt5/heartbeat/A1B2C3D4

# 客户B (License: B2C3D4E5...)
user B2C3D4E5
topic read mt5/signals/B2C3D4E5
topic write mt5/heartbeat/B2C3D4E5
```

---

### 步骤2: 主服务器配置

#### 2.1 初始化 Auth Bridge

```python
from master.auth_manager import LicenseManager
from master.mqtt_auth_bridge import MQTTAuthBridge

# 创建License管理器
license_manager = LicenseManager()

# 创建Auth Bridge
bridge = MQTTAuthBridge(
    broker_host="your-mosquitto-server.com",
    broker_port=1883,
    license_manager=license_manager
)

# 启动
bridge.start()
```

#### 2.2 发布信号

```python
# 方式1: 广播给所有活跃License
signal_data = {
    "type": "NEW_ORDER",
    "symbol": "EURUSD",
    "order_type": "BUY",
    "volume": 1.0,
    ...
}

stats = bridge.broadcast_signal(signal_data)
print(f"Broadcast stats: {stats}")
# Output: {'total': 5, 'success': 5, 'failed': 0}

# 方式2: 发送给特定License
bridge.publish_signal(signal_data, "A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6")
```

---

### 步骤3: 从服务器配置

#### 3.1 使用认证客户端

```python
from slave.authenticated_client import AuthenticatedMQTTClient

# 创建认证客户端
client = AuthenticatedMQTTClient(
    broker_host="your-mosquitto-server.com",
    broker_port=1883,
    client_id="slave_server_001",
    license_key="A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6"  # 你的License
)

# 设置消息回调
def on_signal_received(signal_data):
    print(f"Received signal: {signal_data}")
    # 执行交易逻辑
    execute_trade(signal_data)

client.set_message_callback(on_signal_received)

# 连接
client.connect()

# 保持运行
import time
try:
    while True:
        client.send_heartbeat()  # 每30秒发送心跳
        time.sleep(30)
except KeyboardInterrupt:
    client.disconnect()
```

#### 3.2 配置文件

`config/slave_config.json`:

```json
{
    "mqtt": {
        "broker": "your-mosquitto-server.com",
        "port": 1883,
        "client_id": "slave_server_001",
        "license_key": "A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6"
    },
    ...
}
```

---

## 🔒 安全机制详解

### 1. 双层认证

```
第一层: Mosquitto 用户认证
  - 用户名: License前8位
  - 密码: 完整License密钥
  
第二层: 应用层License验证
  - 验证License有效性
  - 检查过期时间
  - 检查连接数限制
  - 记录IP地址
```

### 2. 信号加密

```python
# 加密过程
原始信号 → JSON序列化 → XOR加密(License密钥) → Base64编码 → 发布

# 解密过程
接收数据 → Base64解码 → XOR解密(License密钥) → JSON反序列化 → 原始信号
```

**加密强度:**
- 当前: XOR加密 (适合内网)
- 生产环境: 建议升级为 AES-256

### 3. 主题隔离

```
每个License有独立的主题:
- mt5/signals/A1B2C3D4  (客户A专属)
- mt5/signals/B2C3D4E5  (客户B专属)

ACL规则确保:
- 客户A只能订阅 mt5/signals/A1B2C3D4
- 客户B只能订阅 mt5/signals/B2C3D4E5
- 无法跨用户访问
```

### 4. IP绑定和追踪

```json
{
    "license_key": "A1B2C3D4...",
    "ip_addresses": ["192.168.1.100", "10.0.0.50"],
    "last_used": "2026-04-15T12:00:00"
}
```

---

## 📊 授权流程

### 完整流程图

```
从服务器启动
    ↓
连接到Mosquitto Broker
    ↓
Mosquitto认证 (用户名/密码)
    ├─ 失败: 拒绝连接
    └─ 成功: 继续
    ↓
发送应用层认证请求
    ↓
Master Auth Bridge验证
    ├─ 检查License是否存在
    ├─ 检查是否过期
    ├─ 检查连接数
    ├─ 检查黑名单
    └─ 生成会话密钥
    ↓
认证成功
    ↓
订阅专属主题: mt5/signals/{license_prefix}
    ↓
接收加密信号
    ↓
本地解密
    ↓
执行交易
    ↓
定期发送心跳
```

---

## 🛠️ 管理命令

### 生成和管理 License

```bash
# 生成新License
python manage_licenses.py generate "客户A" 365 1

# 查看所有License
python manage_licenses.py list

# 生成Mosquitto配置
python -c "
from master.auth_manager import LicenseManager
from master.mqtt_auth_bridge import MosquittoACLGenerator

manager = LicenseManager()
gen = MosquittoACLGenerator(manager)
gen.generate_acl_config()
gen.generate_password_file()
"

# 查看活跃会话
python -c "
from master.mqtt_auth_bridge import MQTTAuthBridge
bridge = MQTTAuthBridge('localhost')
sessions = bridge.get_active_sessions()
for s in sessions:
    print(s)
"
```

---

## 🔍 监控和日志

### 日志文件

```
logs/
├── license.log          # License验证日志
├── mqtt_bridge.log      # Auth Bridge日志
├── auth_client.log      # 从服务器客户端日志
└── mosquitto.log        # Mosquitto Broker日志
```

### 实时监控

```bash
# 查看License使用情况
tail -f logs/license.log

# 查看认证日志
tail -f logs/mqtt_bridge.log

# 查看Mosquitto日志
tail -f /var/log/mosquitto/mosquitto.log

# 查看活跃连接
mosquitto_sub -h localhost -t '$SYS/broker/clients/active' -v
```

---

## 💡 高级配置

### 1. 启用SSL/TLS

```bash
# 生成证书
openssl req -new -x509 -days 365 -nodes \
  -out mosquitto.crt -keyout mosquitto.key

# 配置Mosquitto
cat >> /etc/mosquitto/mosquitto.conf << EOF
listener 8883
cafile /etc/mosquitto/ca_certificates/ca.crt
certfile /etc/mosquitto/certs/server.crt
keyfile /etc/mosquitto/certs/server.key
require_certificate false
EOF

# 从服务器配置
{
    "mqtt": {
        "broker": "your-server.com",
        "port": 8883,
        "use_ssl": true,
        ...
    }
}
```

### 2. WebSocket支持

```conf
# Mosquitto配置
listener 9001
protocol websockets
```

### 3. 集群部署

```
多个Mosquitto Broker + Load Balancer
    ↓
HAProxy / Nginx 负载均衡
    ↓
Master Auth Bridge (多实例)
    ↓
共享License数据库 (Redis/MySQL)
```

---

## ❌ 常见问题

### Q1: 如果Mosquitto宕机怎么办?

**A:** 
- 主服务器会检测到断开
- 自动重连机制
- 从服务器也会自动重连
- 建议部署多个Mosquitto实例

### Q2: 信号加密会影响性能吗?

**A:**
- XOR加密非常快 (<1ms)
- 如果使用AES，约5-10ms
- 对交易延迟影响可忽略

### Q3: 如何防止License泄露?

**A:**
1. IP地址绑定
2. 连接数限制
3. 定期轮换密钥
4. 监控异常使用
5. 发现泄露立即吊销

### Q4: 可以动态添加/删除用户吗?

**A:**
可以！修改配置后重启Mosquitto:
```bash
# 添加新用户
mosquitto_passwd -b /etc/mosquitto/mosquitto_passwd NEWUSER NEWPASS

# 更新ACL
echo "user NEWUSER" >> /etc/mosquitto/mosquitto_acl.conf
echo "topic read mt5/signals/NEWUSER" >> /etc/mosquitto/mosquitto_acl.conf

# 重启
sudo systemctl restart mosquitto
```

---

## 📈 性能优化

### 1. QoS选择

```python
# 信号传输: QoS 1 (至少一次)
client.publish(topic, data, qos=1)

# 心跳: QoS 0 (最多一次)
client.publish(topic, data, qos=0)
```

### 2. 消息压缩

```python
import gzip
import base64

# 压缩
compressed = gzip.compress(json_str.encode())
encoded = base64.b64encode(compressed).decode()

# 解压
decoded = base64.b64decode(encoded)
decompressed = gzip.decompress(decoded).decode()
```

### 3. 批量发送

```python
# 累积多个信号后批量发送
signals_batch = []
for signal in signals:
    signals_batch.append(signal)
    if len(signals_batch) >= 10:
        bridge.broadcast_signal({"batch": signals_batch})
        signals_batch = []
```

---

## ✨ 总结

### 优势

✅ **完全自主控制** - 独立MQTT Broker  
✅ **双层安全** - Mosquitto ACL + 应用层认证  
✅ **信号加密** - 防止窃听  
✅ **灵活授权** - License管理系统  
✅ **可扩展** - 支持集群部署  

### 快速开始

```bash
# 1. 安装Mosquitto
brew install mosquitto

# 2. 生成License
python manage_licenses.py generate "客户A" 365 1

# 3. 生成Mosquitto配置
python -c "..."

# 4. 启动Mosquitto
brew services start mosquitto

# 5. 启动主服务器
./start_master.sh

# 6. 配置并启动从服务器
./start_slave.sh
```

**现在你可以在独立MQTT Broker上实现完整的授权控制了！** 🎉
