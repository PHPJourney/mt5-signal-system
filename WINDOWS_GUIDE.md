# Windows 使用指南

## 快速开始 (3步部署)

### 方法1: 一键部署 (推荐)

双击运行 `deploy.bat`，按照提示完成部署。

### 方法2: 手动安装

#### 步骤1: 安装依赖
```bash
install.bat
```

#### 步骤2: 配置系统
```bash
config_panel.bat
```

#### 步骤3: 启动服务
- 主服务器: `start_master.bat`
- 从服务器: `start_slave.bat`

---

## 文件说明

### 批处理文件 (.bat)

| 文件名 | 功能 | 说明 |
|--------|------|------|
| `deploy.bat` | 一键部署 | 自动检查环境、安装依赖、引导配置 |
| `install.bat` | 安装依赖 | 安装Python包 (MetaTrader5, paho-mqtt) |
| `install_mosquitto.bat` | 安装MQTT | 下载并安装Mosquitto Broker |
| `config_panel.bat` | 配置面板 | 图形化配置界面 |
| `start_master.bat` | 启动主服务器 | 信号发送端 |
| `start_slave.bat` | 启动从服务器 | 信号接收和交易执行端 |

### 配置文件

| 文件 | 用途 |
|------|------|
| `config/master_config.json` | 主服务器配置 |
| `config/slave_config.json` | 从服务器配置 |

### Python脚本

| 文件 | 功能 |
|------|------|
| `config_panel.py` | 配置面板GUI |
| `build_windows.py` | Windows打包工具 |

---

## 详细使用步骤

### 1. 系统要求

**必需软件:**
- ✅ Windows 7/8/10/11 (64位)
- ✅ Python 3.7 或更高版本
- ✅ MetaTrader 5 终端
- ✅ Mosquitto MQTT Broker

**推荐配置:**
- CPU: 双核以上
- 内存: 4GB RAM
- 网络: 稳定的互联网连接

### 2. 安装Python

1. 访问 https://www.python.org/downloads/
2. 下载最新版本的Python 3.x
3. **重要**: 安装时勾选 "Add Python to PATH"
4. 点击 "Install Now"

验证安装:
```cmd
python --version
```

### 3. 安装MQTT Broker

**选项A: 使用安装脚本 (推荐)**
```cmd
install_mosquitto.bat
```

**选项B: 手动安装**
1. 访问 https://mosquitto.org/download/
2. 下载Windows版本
3. 安装时勾选 "Add to PATH"
4. 启动服务:
   ```cmd
   net start mosquitto
   ```

**选项C: 使用Docker**
```cmd
docker run -d -p 1883:1883 eclipse-mosquitto
```

### 4. 安装项目依赖

```cmd
install.bat
```

这会安装:
- MetaTrader5 (MT5接口)
- paho-mqtt (MQTT客户端)

### 5. 配置系统

运行配置面板:
```cmd
config_panel.bat
```

**配置主服务器:**
- MQTT Broker地址 (默认: localhost)
- MQTT端口 (默认: 1883)
- 检测间隔 (默认: 100ms)

**配置从服务器:**
- MQTT连接信息
- 跟单倍数 (例如: 1.0 = 相同手数, 0.5 = 半仓)
- 是否反向交易
- 风险管理参数
- 品种映射关系

**保存配置:**
点击 "保存所有配置" 按钮

### 6. 启动服务

**启动主服务器:**
```cmd
start_master.bat
```
或双击 `start_master.bat`

**启动从服务器:**
```cmd
start_slave.bat
```
或双击 `start_slave.bat`

**注意:** 每个服务器会在独立的窗口中运行

---

## 配置示例

### 场景1: 标准跟单 (1倍)

在配置面板的"从服务器配置"选项卡:
```
跟单倍数: 1.0
反向交易: ☐ (不勾选)
最大手数: 10.0
每日最大亏损: 1000
```

### 场景2: 半仓跟单

```
跟单倍数: 0.5
反向交易: ☐ (不勾选)
最大手数: 5.0
每日最大亏损: 500
```

### 场景3: 反向对冲

```
跟单倍数: 1.0
反向交易: ☑ (勾选)
最大手数: 10.0
每日最大亏损: 1000
```

### 场景4: 不同经纪商品种映射

在"品种映射"选项卡添加:
```
主服务器品种      从服务器品种
XAUUSD           GOLD
BTCUSD           BITCOIN
US30             DJI30
NAS100           NDX100
EURUSD           EURUSD.pro
```

---

## 常见问题

### Q1: 提示 "Python未安装"

**解决方法:**
1. 确认已安装Python 3.7+
2. 重新安装Python,确保勾选 "Add Python to PATH"
3. 重启电脑
4. 验证: 打开CMD输入 `python --version`

### Q2: 无法连接MQTT Broker

**错误信息:** "Connection refused" 或 "Connection timeout"

**解决方法:**
1. 检查Mosquitto是否运行:
   ```cmd
   net start | findstr mosquitto
   ```
2. 如果未运行,启动服务:
   ```cmd
   net start mosquitto
   ```
3. 检查防火墙是否阻止1883端口
4. 测试连接:
   ```cmd
   telnet localhost 1883
   ```

### Q3: MT5连接失败

**错误信息:** "MT5 initialization failed"

**解决方法:**
1. 确认MetaTrader 5已安装
2. 打开MT5终端并登录账户
3. 确认账户有交易权限
4. 检查是否在Windows系统上运行

### Q4: 品种映射失败

**日志显示:** "Cannot map symbol: XXX"

**解决方法:**
1. 打开配置面板
2. 进入"品种映射"选项卡
3. 添加正确的映射关系
4. 查看从服务器可用的品种列表:
   - 在MT5市场报价窗口查看所有品种
   - 或在配置面板中添加映射

### Q5: 订单未执行

**可能原因:**
1. 风险管理阻止 (点差过大/达到日亏损限制)
2. 账户余额不足
3. 手数超出限制
4. 品种不可用

**排查步骤:**
1. 查看 `logs/slave.log`
2. 查看 `logs/risk_manager.log`
3. 检查账户余额
4. 确认品种映射正确

### Q6: 如何停止服务器?

**方法1:** 在服务器窗口按 `Ctrl+C`

**方法2:** 直接关闭窗口

### Q7: 如何查看日志?

日志文件位于 `logs/` 目录:
- `master.log` - 主服务器日志
- `slave.log` - 从服务器日志
- `risk_manager.log` - 风险管理日志
- `symbol_mapper.log` - 品种映射日志

使用记事本或其他文本编辑器打开即可查看。

---

## 高级用法

### 多从服务器部署

可以为不同的从服务器创建独立配置:

1. 复制配置文件:
   ```cmd
   copy config\slave_config.json config\slave_config_2.json
   ```

2. 修改配置:
   - 更改 `client_id` (必须唯一)
   - 调整 `multiplier` (跟单倍数)

3. 启动第二个从服务器:
   ```cmd
   python slave\signal_receiver.py --config config\slave_config_2.json
   ```

### 自定义魔术数字

每个从服务器应使用不同的魔术数字以区分订单:

在配置文件中修改:
```json
"trading": {
    "magic_number": 999998  // 从服务器2
}
```

### 后台运行

使用VBScript实现后台运行:

创建 `run_master.vbs`:
```vbscript
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "start_master.bat" & Chr(34), 0
Set WshShell = Nothing
```

双击运行即可后台启动。

---

## 性能优化

### 降低延迟

1. 减小检测间隔 (主服务器配置):
   ```json
   "send_interval_ms": 50  // 从100ms改为50ms
   ```

2. 使用本地MQTT Broker
3. 关闭不必要的持仓/挂单同步

### 提高稳定性

1. 启用MQTT认证
2. 设置合理的风控参数
3. 定期重启服务清理状态
4. 监控系统资源使用

---

## 安全建议

1. **MQTT认证**: 生产环境务必设置用户名密码
2. **防火墙**: 限制MQTT端口访问
3. **专用账户**: 从服务器使用独立交易账户
4. **风险控制**: 始终启用风险管理
5. **定期备份**: 备份配置文件和日志

---

## 技术支持

### 获取帮助

1. 查看日志文件
2. 阅读 README.md
3. 查看 ARCHITECTURE.md 了解系统架构

### 报告问题

提供以下信息:
- 操作系统版本
- Python版本
- 错误日志内容
- 配置文件 (敏感信息脱敏)

---

## 更新日志

### v1.0.0 (2026-04-15)
- ✅ 初始版本发布
- ✅ 支持实时信号传输
- ✅ 支持灵活跟单倍数
- ✅ 支持反向交易
- ✅ 完整的市场映射
- ✅ 全面的风险管理
- ✅ 图形化配置面板
- ✅ Windows一键部署

---

**免责声明**: 本系统仅供学习和研究使用。外汇和差价合约交易存在高风险,可能导致资金损失。使用者需自行承担交易风险。建议先在模拟账户充分测试。
