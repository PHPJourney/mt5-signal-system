# 如何打包Windows EXE (从macOS)

由于PyInstaller是平台特定的工具,在macOS上无法直接生成Windows EXE。以下是三种解决方案:

---

## 🚀 推荐方案: GitHub Actions (最简单)

### 优点
- ✅ 无需Windows电脑
- ✅ 全自动构建
- ✅ 每次提交自动打包
- ✅ 公开下载链接

### 步骤

**1. 将代码推送到GitHub**
```bash
cd mt5_signal_system
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/你的用户名/mt5-signal.git
git push -u origin main
```

**2. 触发自动构建**

方式A - 推送标签(推荐):
```bash
git tag v1.0.0
git push origin v1.0.0
```

方式B - 手动触发:
- 进入GitHub仓库页面
- 点击 "Actions" 标签
- 选择 "Build Windows EXE"
- 点击 "Run workflow"

**3. 下载构建结果**
- Actions页面查看构建进度
- 完成后点击Artifacts下载
- 或在Releases页面下载

**配置文件已提供:** `.github/workflows/build-windows.yml`

---

## 💻 方案二: 在Windows电脑上打包

### 步骤

**1. 传输项目到Windows**
- 使用U盘
- 网络共享
- Git克隆
- 云存储

**2. 安装Python for Windows**
- 下载: https://www.python.org/downloads/
- 安装时勾选 "Add Python to PATH"

**3. 运行打包脚本**
```cmd
cd mt5_signal_system
build_exe.bat
```

**4. 获取EXE文件**
```
输出目录: dist/MT5_Signal_System_Release/
```

**脚本已提供:** `build_exe.bat`

---

## 🐳 方案三: Docker交叉编译

### 前提条件
- Docker Desktop for Mac
- 或Windows上的Docker

### 步骤
```bash
cd mt5_signal_system
./build_with_docker.sh
```

**注意:** macOS版Docker不支持Windows容器,此方案需要在Windows上运行。

**脚本已提供:** `build_with_docker.sh`

---

## 📦 打包后的文件

```
MT5_Signal_System_Release/
├── Master_Server/           # 主服务器
│   └── MT5_Master_Server.exe
├── Slave_Server/            # 从服务器
│   └── MT5_Slave_Server.exe
├── config/                  # 配置文件
├── start_master.bat         # 启动脚本
├── start_slave.bat          # 启动脚本
└── 文档文件...
```

---

## ⚡ 快速对比

| 方案 | 难度 | 需要Windows | 自动化 | 推荐度 |
|------|------|------------|--------|--------|
| GitHub Actions | ⭐ | ❌ | ✅ | ⭐⭐⭐ |
| Windows电脑 | ⭐⭐ | ✅ | ❌ | ⭐⭐ |
| Docker | ⭐⭐⭐ | ✅ | ✅ | ⭐ |

---

## 🎯 推荐流程

**对于个人开发者:**
1. 使用GitHub Actions
2. 推送代码自动构建
3. 下载EXE分发

**对于团队:**
1. 配置CI/CD流水线
2. 自动测试和打包
3. 自动发布到内部服务器

**对于临时需求:**
1. 找一台Windows电脑
2. 运行 `build_exe.bat`
3. 复制EXE文件

---

## 📖 详细文档

查看 `BUILD_GUIDE.md` 了解:
- PyInstaller详细用法
- 优化EXE大小
- 添加应用图标
- 代码签名
- 制作安装程序

---

## ❓ 常见问题

**Q: 为什么不能用Wine?**
A: Wine环境下打包的EXE可能不稳定,不推荐用于生产环境。

**Q: EXE文件很大怎么办?**
A: 正常现象,包含Python解释器和依赖库,约50-100MB。

**Q: 能否生成单个EXE?**
A: 可以,使用 `--onefile` 参数,但启动较慢。

---

**建议:** 使用 **GitHub Actions** 方案,简单、可靠、自动化!
