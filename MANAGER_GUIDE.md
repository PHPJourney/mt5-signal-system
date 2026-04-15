# MT5 Signal System - 管理面板使用指南

## 📋 概述

MT5 Manager 是一个综合性的桌面图形界面管理工具，用于配置、监控和管理 MT5 信号系统的 Master 和 Slave 服务。

## ✨ 主要功能

### 1. 📊 仪表板 (Dashboard)
- **服务状态总览**：实时显示 Master 和 Slave 的运行状态
- **一键控制**：启动/停止 Master 和 Slave 服务
- **实时统计**：
  - 已发送信号数
  - 已接收信号数
  - 失败次数
  - 平均延迟（毫秒）
- **快速操作**：
  - 重启所有服务
  - 打开配置文件目录
  - 打开日志文件目录
  - 清理日志文件

### 2. ⚙️ Master 配置
可视化编辑 Master 服务器配置：

**MQTT 配置**
- Broker 地址
- 端口号
- 用户名/密码
- Client ID

**MT5 账户配置**
- 账户登录号
- 密码
- 服务器名称
- MT5 终端路径

**信号配置**
- 交易品种列表
- 最大持仓数
- 默认手数

### 3. ⚙️ Slave 配置
可视化编辑 Slave 服务器配置：

**MQTT 配置**
- Broker 地址
- 端口号
- 用户名/密码
- Client ID

**MT5 账户配置**
- 账户登录号
- 密码
- 服务器名称
- MT5 终端路径

**订阅配置**
- Master ID（要订阅的 Master）

**风险管理**
- 最大回撤百分比
- 最大持仓数
- 手数倍数

### 4. 📡 实时监控
- **连接状态监控**：
  - MQTT Broker 连接状态
  - Master 在线状态
  - Slave 在线状态
- **信号历史表格**：
  - 时间戳
  - 信号类型（BUY/SELL）
  - 交易品种
  - 方向（开仓/平仓）
  - 价格
  - 手数
  - 执行状态

### 5. 📋 日志查看
- **多日志文件切换**：master.log / slave.log / system.log
- **彩色日志显示**：
  - 🔴 ERROR - 红色
  - 🟠 WARNING - 橙色
  - 🟢 INFO - 绿色
  - 🔵 DEBUG - 蓝色
- **功能按钮**：
  - 刷新：重新加载日志
  - 清空显示：清除当前显示
  - 导出日志：保存为文本文件
  - 自动刷新：定时更新日志内容

## 🚀 快速开始

### Windows 用户

1. **双击运行**
   ```
   双击 start_manager.bat
   ```

2. **或命令行运行**
   ```bash
   python mt5_manager.py
   ```

### macOS/Linux 用户

```bash
# 赋予执行权限
chmod +x start_manager.sh

# 运行
./start_manager.sh

# 或直接使用 Python
python3 mt5_manager.py
```

## 📦 依赖安装

管理面板会自动检查并安装必要的依赖：

```bash
# 手动安装依赖
pip install psutil

# 可选：安装美化主题
pip install ttkbootstrap
```

## 💡 使用技巧

### 1. 配置管理
- 修改配置后点击"保存"按钮
- 配置会立即写入 JSON 文件
- 重启服务后新配置生效

### 2. 服务控制
- 启动服务前确保配置文件正确
- 停止服务会优雅地终止进程
- 重启所有服务会按顺序停止再启动

### 3. 日志查看
- 启用"自动刷新"可实时查看新日志
- 使用颜色标签快速识别日志级别
- 定期导出重要日志作为备份

### 4. 实时监控
- 统计数据每 5 秒自动更新
- 信号历史表格显示最近的交易信号
- 连接状态实时反映服务健康状况

## ⚠️ 注意事项

1. **首次使用**
   - 确保已正确配置 MQTT Broker
   - 确保 MT5 终端已安装
   - 测试 MQTT 连接是否正常

2. **服务启动失败**
   - 检查配置文件是否正确
   - 查看日志文件了解错误详情
   - 确认端口未被占用

3. **配置保存**
   - 修改配置后务必点击"保存"
   - 建议定期备份配置文件
   - 敏感信息（密码）注意保护

4. **性能优化**
   - 日志文件过大会影响性能
   - 定期清理旧日志文件
   - 关闭不需要的自动刷新

## 🐛 常见问题

### Q: 界面显示异常或样式不正确
A: 安装 ttkbootstrap 获得更好的视觉效果
```bash
pip install ttkbootstrap
```

### Q: 无法启动 Master/Slave 服务
A: 检查以下几点：
- 配置文件中的路径是否正确
- MT5 终端是否已安装
- MQTT Broker 是否正在运行
- 端口是否被占用

### Q: 日志文件为空
A: 
- 确认服务已启动并运行
- 检查日志目录权限
- 查看控制台输出是否有错误

### Q: 统计数据不更新
A:
- 确认至少有一个服务在运行
- 检查网络连接
- 重启管理面板

## 🎨 主题定制

如果使用 ttkbootstrap，可以切换不同主题：

```python
# 在 mt5_manager.py 中修改主题
style = ttkb.Style(theme='cosmo')  # 可选主题: litera, journal, darkly, cyborg 等
```

可用主题列表：
- cosmo（默认）
- flatly
- journal
- litera
- darkly
- cyborg
- solar
- minty
- lumen
- sandstone
- yeti
- pulse

## 📞 技术支持

如遇问题请查看：
- README.md - 项目总览
- QUICKSTART.md - 快速开始
- ARCHITECTURE.md - 架构说明
- logs/*.log - 运行日志

## 📝 更新日志

### v1.0.0 (2026-04-15)
- ✨ 初始版本发布
- ✅ 完整的配置管理界面
- ✅ 实时服务监控
- ✅ 一键启停控制
- ✅ 彩色日志查看器
- ✅ 实时统计仪表板
