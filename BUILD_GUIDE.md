# Windows EXE 打包指南

本文档说明如何在 macOS 上为 Windows 平台打包可执行文件。

---

## 🎯 三种打包方案

### 方案1: 在Windows系统上打包 (推荐) ⭐⭐⭐

最简单、最可靠的方案。

**步骤:**

1. **将项目复制到Windows电脑**
   ```
   使用U盘、网络共享或Git克隆
   ```

2. **安装Python for Windows**
   - 下载: https://www.python.org/downloads/
   - 安装时勾选 "Add Python to PATH"

3. **运行打包脚本**
   ```cmd
   cd mt5_signal_system
   build_exe.bat
   ```

4. **获取EXE文件**
   ```
   输出目录: dist/MT5_Signal_System_Release/
   ```

**优点:**
- ✅ 最简单,无需额外配置
- ✅ 100%兼容Windows
- ✅ 可以测试生成的EXE

---

### 方案2: 使用GitHub Actions自动构建 (推荐) ⭐⭐⭐

无需Windows电脑,自动在云端构建。

**步骤:**

1. **将代码推送到GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/mt5-signal.git
   git push -u origin main
   ```

2. **触发构建**
   - 方式A: 推送新标签
     ```bash
     git tag v1.0.0
     git push origin v1.0.0
     ```
   - 方式B: 手动触发
     - 进入GitHub仓库
     - Actions → Build Windows EXE → Run workflow

3. **下载构建结果**
   - Actions页面查看构建状态
   - 完成后下载Artifacts
   - 或直接在Release页面下载

**优点:**
- ✅ 无需Windows电脑
- ✅ 自动化,每次提交自动构建
- ✅ 可公开下载

**配置文件:** `.github/workflows/build-windows.yml` (已提供)

---

### 方案3: 使用Docker交叉编译 ⭐⭐

在macOS上使用Windows容器构建。

**前提条件:**
- 安装Docker Desktop for Mac
- Docker需要启用Windows容器支持

**步骤:**

```bash
cd mt5_signal_system
./build_with_docker.sh
```

**注意:**
- Docker for Mac默认不支持Windows容器
- 需要在Windows机器上运行Docker
- 或使用云上的Windows Docker服务

---

## 📦 打包后的文件结构

```
MT5_Signal_System_Release/
├── Master_Server/           # 主服务器程序
│   ├── MT5_Master_Server.exe
│   ├── python311.dll
│   └── ... (其他依赖文件)
├── Slave_Server/            # 从服务器程序
│   ├── MT5_Slave_Server.exe
│   ├── python311.dll
│   └── ... (其他依赖文件)
├── config/                  # 配置文件
│   ├── master_config.json
│   └── slave_config.json
├── start_master.bat         # 启动主服务器
├── start_slave.bat          # 启动从服务器
├── README.md                # 使用说明
├── WINDOWS_GUIDE.md         # 详细指南
├── QUICKSTART.md            # 快速开始
└── CHEATSHEET.md            # 快速参考
```

---

## 🔧 手动打包步骤 (Windows)

如果你想了解详细过程:

### 1. 安装PyInstaller

```cmd
pip install pyinstaller
```

### 2. 打包主服务器

```cmd
pyinstaller --name="MT5_Master_Server" ^
    --onedir ^
    --console ^
    --add-data "config;config" ^
    --hidden-import=paho.mqtt.client ^
    --hidden-import=MetaTrader5 ^
    --hidden-import=common ^
    --hidden-import=common.models ^
    --hidden-import=common.utils ^
    --hidden-import=common.mqtt_client ^
    master\signal_sender.py
```

### 3. 打包从服务器

```cmd
pyinstaller --name="MT5_Slave_Server" ^
    --onedir ^
    --console ^
    --add-data "config;config" ^
    --hidden-import=paho.mqtt.client ^
    --hidden-import=MetaTrader5 ^
    --hidden-import=common ^
    --hidden-import=common.models ^
    --hidden-import=common.utils ^
    --hidden-import=common.mqtt_client ^
    --hidden-import=slave ^
    --hidden-import=slave.symbol_mapper ^
    --hidden-import=slave.risk_manager ^
    slave\signal_receiver.py
```

### 4. 创建发布包

```cmd
mkdir dist\MT5_Signal_System_Release
xcopy /E /I dist\MT5_Master_Server dist\MT5_Signal_System_Release\Master_Server
xcopy /E /I dist\MT5_Slave_Server dist\MT5_Signal_System_Release\Slave_Server
xcopy /E /I config dist\MT5_Signal_System_Release\config
```

---

## ⚙️ PyInstaller参数说明

| 参数 | 说明 |
|------|------|
| `--name` | 可执行文件名称 |
| `--onedir` | 生成文件夹模式(推荐) |
| `--onefile` | 生成单个exe文件 |
| `--console` | 显示控制台窗口 |
| `--windowed` | 隐藏控制台(GUI程序) |
| `--icon` | 设置图标文件(.ico) |
| `--add-data` | 添加数据文件 |
| `--hidden-import` | 添加隐藏的导入 |

---

## 🎨 添加应用图标 (可选)

1. **准备图标文件**
   - 创建或下载 `.ico` 格式图标
   - 推荐尺寸: 256x256

2. **修改打包命令**
   ```cmd
   pyinstaller --icon=myicon.ico ...
   ```

3. **在线转换工具**
   - https://convertio.co/png-ico/
   - https://www.icoconverter.com/

---

## 📊 优化EXE文件大小

### 方法1: 使用UPX压缩

```cmd
pip install pyinstaller[encryption]
pyinstaller --upx-dir=path/to/upx ...
```

### 方法2: 排除不必要的模块

```cmd
pyinstaller --exclude-module=tkinter ^
    --exclude-module=test ^
    ...
```

### 方法3: 使用--onefile模式

```cmd
pyinstaller --onefile ...
```

**注意:** onefile模式启动较慢,但便于分发

---

## 🧪 测试生成的EXE

### 在Windows上测试

1. **复制到其他Windows电脑**
2. **运行EXE文件**
   ```cmd
   cd Master_Server
   MT5_Master_Server.exe --help
   ```
3. **检查依赖**
   - 确认所有DLL文件存在
   - 确认config目录正确

### 常见问题

**问题1: 缺少DLL文件**
```
解决: 确保复制了整个输出文件夹
```

**问题2: 找不到配置文件**
```
解决: 检查config目录是否在正确位置
```

**问题3: MetaTrader5模块错误**
```
说明: MT5模块只在有MT5终端的Windows上工作
      这是正常的,EXE本身没问题
```

---

## 📤 分发EXE文件

### 方法1: ZIP压缩包

```cmd
# Windows
powershell Compress-Archive -Path dist\MT5_Signal_System_Release -DestinationPath MT5_Signal_System_v1.0.zip

# macOS/Linux
zip -r MT5_Signal_System_v1.0.zip dist/MT5_Signal_System_Release/
```

### 方法2: 制作安装程序

使用工具:
- **NSIS** (免费): https://nsis.sourceforge.io/
- **Inno Setup** (免费): https://jrsoftware.org/isinfo.php
- **Advanced Installer** (付费): https://www.advancedinstaller.com/

### 方法3: 上传到发布平台

- GitHub Releases
- SourceForge
- 公司内网服务器

---

## 🔐 代码签名 (可选)

如果需要正式分发,建议进行代码签名:

1. **购买代码签名证书**
   - DigiCert
   - Sectigo
   - GlobalSign

2. **签名EXE**
   ```cmd
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com MT5_Master_Server.exe
   ```

---

## 📝 版本管理

### 添加版本信息

创建 `version_info.txt`:

```
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Your Company'),
        StringStruct(u'FileDescription', u'TradeMind MT5'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'MT5_Master_Server'),
        StringStruct(u'LegalCopyright', u'© 2026 Your Company'),
        StringStruct(u'OriginalFilename', u'MT5_Master_Server.exe'),
        StringStruct(u'ProductName', u'TradeMind MT5'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
```

使用:
```cmd
pyinstaller --version-file=version_info.txt ...
```

---

## 🎯 推荐流程

### 开发阶段
1. 在Windows开发机上测试
2. 使用 `build_exe.bat` 快速构建
3. 本地测试EXE功能

### 发布阶段
1. 推送到GitHub
2. 创建tag触发自动构建
3. 从Actions下载构建结果
4. 测试后发布到Release

### 持续集成
1. 每次push自动构建
2. 自动生成版本号
3. 自动上传Artifacts

---

## ❓ 常见问题

### Q1: 为什么不在macOS上直接打包?

**A:** PyInstaller是平台特定的工具:
- macOS上的PyInstaller只能生成macOS可执行文件
- Windows上的PyInstaller只能生成Windows可执行文件
- 需要使用对应平台的工具

### Q2: Wine能用来打包吗?

**A:** 理论上可以,但不推荐:
- Wine环境配置复杂
- 可能出现兼容性问题
- 生成的EXE可能不稳定
- 建议使用真实Windows环境或GitHub Actions

### Q3: 能否生成单个EXE文件?

**A:** 可以,使用 `--onefile` 参数:
```cmd
pyinstaller --onefile master\signal_sender.py
```
**缺点:**
- 启动速度慢(需要解压)
- 文件体积更大
- 调试困难

### Q4: EXE文件太大怎么办?

**A:** 正常现象:
- Python解释器约20MB
- 加上依赖库总共50-100MB
- 使用UPX压缩可减少30-50%

---

## 📞 获取帮助

1. **查看PyInstaller文档**: https://pyinstaller.org/
2. **检查构建日志**: 查看详细错误信息
3. **搜索Issue**: GitHub上可能有类似问题
4. **询问社区**: Stack Overflow, Reddit等

---

## 🔗 相关资源

- [PyInstaller官方文档](https://pyinstaller.org/en/stable/)
- [GitHub Actions文档](https://docs.github.com/en/actions)
- [NSIS安装制作工具](https://nsis.sourceforge.io/)
- [Inno Setup安装制作工具](https://jrsoftware.org/isinfo.php)

---

**提示:** 对于大多数用户,推荐使用 **GitHub Actions** 方案,无需Windows电脑即可自动构建!
