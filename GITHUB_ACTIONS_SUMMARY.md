# GitHub Actions 完整使用指南

## 🎯 概述

GitHub Actions 让你可以**无需Windows电脑**就能自动打包Windows EXE文件！

---

## ✨ 优势

- ✅ **零成本** - Public仓库完全免费
- ✅ **全自动** - 推送代码自动构建
- ✅ **可靠** - GitHub官方提供的Windows环境
- ✅ **简单** - 只需推送代码即可
- ✅ **快速** - 5-10分钟完成构建

---

## 🚀 超简单3步

### 方法1: 一键脚本 (推荐) ⭐⭐⭐

```bash
cd mt5_signal_system
./setup_github.sh
```

按照提示操作即可！

---

### 方法2: 手动操作

#### Step 1: 创建GitHub仓库
访问: https://github.com/new
- 仓库名: `mt5-signal-system`
- 公开或私有均可
- 点击 "Create repository"

#### Step 2: 推送代码
```bash
cd mt5_signal_system

git init
git add .
git commit -m "Initial commit"

git remote add origin https://github.com/你的用户名/mt5-signal-system.git
git branch -M main
git push -u origin main
```

#### Step 3: 触发构建
```bash
git tag v1.0.0
git push origin v1.0.0
```

**完成！** 等待5-10分钟，EXE就打包好了！

---

## 📦 下载EXE文件

### 方式1: 从Actions下载

1. 访问: `https://github.com/你的用户名/mt5-signal-system/actions`
2. 点击完成的构建任务
3. 滚动到底部 "Artifacts"
4. 点击 **"MT5-Signal-System-Windows"** 下载
5. 解压ZIP文件

### 方式2: 从Releases下载

如果使用标签触发：
1. 仓库首页右侧 "Releases"
2. 点击最新版本
3. 下载Assets中的文件

---

## 🔐 首次推送认证

### 问题: 密码是什么？

GitHub不再支持账户密码，需要使用 **Personal Access Token**。

### 获取Token步骤:

1. 访问: https://github.com/settings/tokens
2. 点击 **"Generate new token (classic)"**
3. 填写Note (例如: "MT5 Project")
4. 勾选权限: **`repo`** (全选)
5. 滚动到底部，点击 **"Generate token"**
6. **复制Token** (只显示一次！)

### 使用Token:

```bash
git push -u origin main
```
- 用户名: 你的GitHub用户名
- 密码: **粘贴刚才复制的Token**

---

## 📊 构建流程

```
推送代码/标签
    ↓
GitHub检测到变更
    ↓
自动启动Windows虚拟机
    ↓
安装Python和依赖
    ↓
运行PyInstaller打包
    ↓
生成EXE文件
    ↓
上传到Artifacts
    ↓
完成！(5-10分钟)
```

---

## ⚙️ 配置文件说明

配置文件位置: `.github/workflows/build-windows.yml`

这个文件告诉GitHub Actions:
- 什么时候触发构建
- 使用什么环境 (Windows)
- 执行什么命令
- 生成什么文件

**你不需要修改它，直接使用即可！**

---

## 💡 常用场景

### 场景1: 发布新版本

```bash
# 修改代码...
git add .
git commit -m "Update feature"

# 创建新标签
git tag v1.1.0
git push origin v1.1.0

# 自动触发构建，生成新版EXE
```

### 场景2: 修复Bug后重新打包

```bash
# 修复bug
git add .
git commit -m "Fix bug"

# 删除旧标签
git tag -d v1.0.0
git push origin --delete v1.0.0

# 重新创建标签
git tag v1.0.0
git push origin v1.0.0
```

### 场景3: 手动触发构建

1. 进入仓库的 **Actions** 页面
2. 左侧选择 **"Build Windows EXE"**
3. 右侧点击 **"Run workflow"**
4. 选择分支，点击绿色按钮

---

## 🔍 查看构建状态

### 状态图标

- 🟡 **黄色圆圈** = 正在构建
- 🟢 **绿色对勾** = 构建成功
- 🔴 **红色叉号** = 构建失败
- ⚪ **灰色圆圈** = 已取消

### 查看详细日志

1. 点击构建任务
2. 展开各个步骤
3. 查看每一步的输出
4. 找到错误信息 (如果失败)

---

## ❌ 常见问题解决

### 问题1: 推送时认证失败

**错误:**
```
remote: Support for password authentication was removed
```

**解决:**
使用 Personal Access Token (见上方说明)

---

### 问题2: Actions没有触发

**检查清单:**
- [ ] `.github/workflows/build-windows.yml` 文件存在
- [ ] 文件语法正确 (YAML格式)
- [ ] 推送到了正确的分支
- [ ] Actions没有被禁用

**调试:**
```bash
# 检查文件是否存在
ls -la .github/workflows/

# 查看远程仓库
git remote -v

# 查看当前分支
git branch

# 重新推送
git push origin main
```

---

### 问题3: 构建失败

**步骤:**
1. 进入Actions页面
2. 点击失败的构建
3. 展开出错的步骤
4. 查看错误信息

**常见错误:**

**错误A: ModuleNotFoundError**
```
解决: 检查requirements.txt包含所有依赖
```

**错误B: File not found**
```
解决: 确认文件路径正确，使用正斜杠 /
```

**错误C: Permission denied**
```
解决: 检查GITHUB_TOKEN权限
```

---

### 问题4: 下载链接过期

**说明:** Artifacts保留90天

**解决:**
```bash
# 删除旧标签
git tag -d v1.0.0
git push origin --delete v1.0.0

# 重新创建
git tag v1.0.0
git push origin v1.0.0
```

---

### 问题5: 构建太慢

**正常时长:**
- 首次: 5-10分钟
- 后续: 3-5分钟 (有缓存)

**如果超过15分钟:**
- 检查网络
- 查看是否有死循环
- 联系GitHub支持

---

## 💰 费用和限制

### Public仓库 (公开)
- ✅ **完全免费**
- ✅ **无限构建次数**
- ✅ **无限存储空间**

### Private仓库 (私有)
- ✅ **每月2,000分钟**
- ✅ **500MB存储**
- 💰 超出部分收费

**对于本项目:**
- 每次构建约5-10分钟
- 每月可构建200-400次
- **完全够用！**

---

## 🎯 最佳实践

### 1. 使用语义化版本

```bash
v1.0.0  # 主版本.次版本.修订版本
v1.0.1  # Bug修复
v1.1.0  # 新功能
v2.0.0  # 重大更新
```

### 2. 编写清晰的提交信息

```bash
git commit -m "Add reverse trading feature"
git commit -m "Fix spread calculation bug"
git commit -m "Update risk management parameters"
```

### 3. 定期清理旧标签

```bash
# 查看本地标签
git tag

# 删除不需要的标签
git tag -d v0.1.0
git push origin --delete v0.1.0
```

### 4. 添加构建徽章

在README.md中添加:

```markdown
![Build Status](https://github.com/用户名/仓库名/actions/workflows/build-windows.yml/badge.svg)
```

显示实时构建状态！

---

## 📚 相关文档

- `GITHUB_ACTIONS_GUIDE.md` - 详细使用指南
- `GITHUB_ACTIONS_QUICK_REF.md` - 快速参考卡片
- `BUILD_GUIDE.md` - EXE打包完整指南
- `.github/workflows/build-windows.yml` - Actions配置文件

---

## 🔗 重要链接

| 用途 | 链接 |
|------|------|
| 创建仓库 | https://github.com/new |
| 获取Token | https://github.com/settings/tokens |
| Actions页面 | https://github.com/用户名/仓库名/actions |
| 官方文档 | https://docs.github.com/actions |
| Marketplace | https://github.com/marketplace?type=actions |

---

## ✨ 总结

**GitHub Actions让打包EXE变得超级简单:**

```
只需3步:
1. 推送代码到GitHub
2. 等待自动构建 (5-10分钟)
3. 下载生成的EXE文件

无需:
❌ Windows电脑
❌ 安装PyInstaller
❌ 配置环境
❌ 手动打包

全部自动化！🎉
```

---

**开始使用吧！** 🚀

如有问题，查看:
- `GITHUB_ACTIONS_GUIDE.md` (详细指南)
- `GITHUB_ACTIONS_QUICK_REF.md` (快速参考)
