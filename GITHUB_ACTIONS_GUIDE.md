# GitHub Actions 打包指南

## 📦 工作流概览

本项目包含 4 个 GitHub Actions 工作流，用于自动化编译和打包 TradeMind MT5。

### 1. build-master.yml - Master Server 打包
**触发条件：**
- 推送标签（v*）
- master/main 分支推送（仅当 master/ 或 common/ 目录变更时）
- 手动触发

**生成产物：**
- Windows: `MT5-Master-Server-vX.X.X-Windows.zip`
- Linux: `MT5-Master-Server-vX.X.X-Linux.tar.gz`

### 2. build-slave.yml - Slave Server 打包
**触发条件：**
- 推送标签（v*）
- master/main 分支推送（仅当 slave/ 或 common/ 目录变更时）
- 手动触发

**生成产物：**
- Windows: `MT5-Slave-Server-vX.X.X-Windows.zip`
- Linux: `MT5-Slave-Server-vX.X.X-Linux.tar.gz`

### 3. build-manager.yml - Management Panel 打包
**触发条件：**
- 推送标签（v*）
- master/main 分支推送（仅当 mt5_manager.py 或 config_panel.py 变更时）
- 手动触发

**生成产物：**
- Windows: `MT5-Manager-vX.X.X-Windows.zip`
- Linux: `MT5-Manager-vX.X.X-Linux.tar.gz`

### 4. release-all.yml - 综合发布
**触发条件：**
- 推送标签（v*）
- 手动触发

**功能：**
- 并行构建所有组件
- 创建统一的 Release
- 上传所有打包文件

---

## 🚀 使用方法

### 方法一：通过标签自动发布（推荐）

```bash
# 1. 提交代码更改
git add .
git commit -m "Update version"

# 2. 创建标签
git tag v1.0.0

# 3. 推送标签（触发自动构建）
git push origin v1.0.0
```

GitHub Actions 会自动：
1. 在 Windows 和 Linux 上构建所有组件
2. 生成独立的安装包
3. 创建 GitHub Release
4. 上传所有打包文件

### 方法二：手动触发

1. 进入项目的 **Actions** 标签页
2. 选择要运行的工作流：
   - Build Master Server
   - Build Slave Server
   - Build Management Panel
   - Release All Components
3. 点击 **Run workflow**
4. 选择分支（通常是 main/master）
5. 点击 **Run workflow** 按钮

### 方法三：PR/MR 测试

当创建 Pull Request 时，相关的工作流会自动运行以验证构建是否成功。

---

## 📋 前置要求

1. **GitHub 账号** - 免费注册: https://github.com/join
2. **Git 已安装** - 检查: `git --version`
3. **项目代码** - TradeMind MT5

---

## 🚀 快速开始 (5步完成)

### 步骤1: 创建 GitHub 仓库

1. 访问 https://github.com/new
2. 填写仓库名称: `mt5-signal-system`
3. 选择 Public 或 Private
4. **不要**勾选 "Initialize with README"
5. 点击 "Create repository"

---

### 步骤2: 初始化本地 Git 仓库

```bash
cd /Users/mac/Downloads/cndnsidc/mt5_signal_system

# 初始化 Git
git init

# 添加所有文件
git add .

# 创建初始提交
git commit -m "Initial commit: TradeMind MT5 v1.0.0"
```

---

### 步骤3: 关联远程仓库

```bash
# 替换为你的GitHub用户名和仓库名
git remote add origin https://github.com/YOUR_USERNAME/mt5-signal-system.git

# 验证远程仓库
git remote -v
```

---

### 步骤4: 推送代码到 GitHub

```bash
# 推送到 main 分支
git branch -M main
git push -u origin main
```

**输入你的 GitHub 用户名和密码**
- 用户名: 你的GitHub用户名
- 密码: Personal Access Token (不是账户密码)

**如何创建 Personal Access Token:**
1. 访问: https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 勾选权限: `repo` (全部)
4. 生成并复制 token
5. 用 token 作为密码

---

### 步骤5: 触发自动构建

#### 方法A: 推送标签 (推荐) ⭐⭐⭐

```bash
# 创建版本标签
git tag v1.0.0

# 推送标签 (触发构建)
git push origin v1.0.0
```

#### 方法B: 手动触发

1. 进入 GitHub 仓库页面
2. 点击 **"Actions"** 标签
3. 左侧选择 **"Build Windows EXE"**
4. 右侧点击 **"Run workflow"**
5. 选择分支: `main`
6. 点击绿色按钮 **"Run workflow"**

---

## 📊 查看构建进度

1. **进入 Actions 页面**
   ```
   https://github.com/YOUR_USERNAME/mt5-signal-system/actions
   ```

2. **查看构建状态**
   - 🟡 黄色 = 正在构建
   - 🟢 绿色 = 构建成功
   - 🔴 红色 = 构建失败

3. **查看详细日志**
   - 点击构建任务
   - 展开各个步骤
   - 查看输出日志

---

## 📦 下载构建结果

### 方法1: 从 Artifacts 下载

1. 构建成功后，进入 Actions 页面
2. 点击完成的构建任务
3. 滚动到底部 "Artifacts" 部分
4. 点击 **"MT5-Signal-System-Windows"** 下载
5. 解压 ZIP 文件

**下载的文件:**
```
MT5-Signal-System-Windows.zip
├── Master_Server/
│   └── MT5_Master_Server.exe
├── Slave_Server/
│   └── MT5_Slave_Server.exe
├── config/
├── start_master.bat
├── start_slave.bat
└── 文档文件...
```

### 方法2: 从 Releases 下载 (使用标签时)

1. 推送标签后，进入仓库首页
2. 右侧 "Releases" 部分
3. 点击最新版本
4. 下载 Assets 中的文件

---

## ⚙️ 自定义配置

### 修改触发条件

编辑 `.github/workflows/build-windows.yml`:

**只在推送标签时构建:**
```yaml
on:
  push:
    tags:
      - 'v*'  # 只响应 v1.0.0, v1.0.1 等标签
```

**每次推送都构建:**
```yaml
on:
  push:
    branches: [ main ]  # main分支每次push都构建
```

**定时构建 (每天凌晨):**
```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # 每天UTC 00:00
```

---

### 修改 Python 版本

```yaml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.10'  # 改为 3.9, 3.10, 3.11 等
```

---

### 添加更多构建步骤

**例如：运行测试**
```yaml
- name: Run tests
  run: |
    python -m pytest tests/
```

**例如：代码质量检查**
```yaml
- name: Lint code
  run: |
    pip install flake8
    flake8 .
```

---

## 🔧 常见问题

### Q1: 推送时认证失败

**错误信息:**
```
remote: Support for password authentication was removed
```

**解决方法:**
使用 Personal Access Token 代替密码:
1. https://github.com/settings/tokens
2. 生成新 token (勾选 `repo` 权限)
3. 用 token 作为密码

或者使用 SSH:
```bash
git remote set-url origin git@github.com:YOUR_USERNAME/mt5-signal-system.git
```

---

### Q2: Actions 没有触发

**检查:**
1. 确认 `.github/workflows/build-windows.yml` 存在
2. 检查 YAML 语法是否正确
3. 查看 Actions 页面是否有禁用
4. 确认推送到了正确的分支

**调试:**
```bash
# 查看远程仓库
git remote -v

# 查看当前分支
git branch

# 重新推送
git push origin main
```

---

### Q3: 构建失败

**查看日志:**
1. 进入 Actions 页面
2. 点击失败的构建
3. 展开出错的步骤
4. 查看错误信息

**常见错误:**

**错误1: Python模块找不到**
```
解决: 检查 requirements.txt 是否包含所有依赖
```

**错误2: 文件路径错误**
```
解决: 确认文件路径使用正斜杠 / 而不是反斜杠 \
```

**错误3: 权限不足**
```
解决: 检查 GITHUB_TOKEN 权限设置
```

---

### Q4: 下载链接过期

**说明:**
- Artifacts 保留 90 天
- 过期的需要重新构建

**解决:**
1. 删除旧标签
2. 重新创建标签
3. 重新推送触发构建

```bash
git tag -d v1.0.0
git tag v1.0.0
git push origin v1.0.0 --force
```

---

### Q5: 构建太慢

**正常情况:**
- 首次构建: 5-10 分钟
- 后续构建: 3-5 分钟 (有缓存)

**优化:**
```yaml
# 启用依赖缓存
- name: Cache pip packages
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

---

## 💡 高级用法

### 多版本同时构建

```yaml
strategy:
  matrix:
    python-version: ['3.9', '3.10', '3.11']

- name: Set up Python ${{ matrix.python-version }}
  uses: actions/setup-python@v4
  with:
    python-version: ${{ matrix.python-version }}
```

---

### 自动上传到 Release

```yaml
- name: Create Release
  if: startsWith(github.ref, 'refs/tags/')
  uses: softprops/action-gh-release@v1
  with:
    files: dist/MT5_Signal_System_Release/**
    body: |
      ## Changes
      - Auto-built Windows EXE
      - Python ${{ matrix.python-version }}
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

### 发送通知

**构建完成后发送邮件:**
```yaml
- name: Send email notification
  if: always()
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    username: ${{ secrets.EMAIL_USERNAME }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    subject: Build ${{ job.status }}
    to: your-email@example.com
    from: GitHub Actions
    body: Build completed with status ${{ job.status }}
```

---

## 📈 监控和统计

### 查看使用量

1. 进入仓库 Settings
2. 左侧 "Actions" → "General"
3. 查看 "Actions usage"

**免费额度:**
- Public 仓库: 无限
- Private 仓库: 2,000 分钟/月

---

### 构建历史

```
https://github.com/YOUR_USERNAME/mt5-signal-system/actions
```

可以看到:
- 所有构建记录
- 构建时长
- 成功/失败状态
- 触发原因

---

## 🎯 最佳实践

### 1. 使用标签管理版本

```bash
# 语义化版本
git tag v1.0.0    # 主版本.次版本.修订版本
git tag v1.1.0
git tag v1.1.1

# 推送标签
git push origin --tags
```

---

### 2. 保护主分支

1. Settings → Branches
2. Add rule: `main`
3. 勾选:
   - Require pull request reviews
   - Require status checks to pass
   - Include administrators

---

### 3. 定期清理 Artifacts

```yaml
# 添加清理步骤
- name: Delete old artifacts
  uses: c-hive/gha-remove-artifacts@v1
  with:
    age: '7 days'
    skip-tags: true
```

---

### 4. 添加构建徽章

在 README.md 中添加:

```markdown
![Build Status](https://github.com/YOUR_USERNAME/mt5-signal-system/actions/workflows/build-windows.yml/badge.svg)
```

显示实时构建状态！

---

## 🔗 相关资源

- [GitHub Actions 官方文档](https://docs.github.com/en/actions)
- [Actions Marketplace](https://github.com/marketplace?type=actions)
- [YAML 语法参考](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [上下文和表达式](https://docs.github.com/en/actions/learn-github-actions/contexts)

---

## 📞 获取帮助

1. **查看构建日志** - 最直接的调试方式
2. **搜索 Issues** - https://github.community/c/code-to-cloud/github-actions/
3. **阅读文档** - 官方文档非常详细
4. **询问社区** - Stack Overflow 标记 `github-actions`

---

## ✨ 总结

**GitHub Actions 优势:**
- ✅ 无需 Windows 电脑
- ✅ 完全自动化
- ✅ 免费使用 (Public 仓库)
- ✅ 可靠稳定
- ✅ 易于配置

**使用流程:**
```
推送代码 → 自动触发 → 云端构建 → 下载EXE
```

**只需3步:**
1. 推送代码到 GitHub
2. 等待自动构建 (5-10分钟)
3. 下载生成的 EXE 文件

---

**现在就开始使用吧！** 🚀
