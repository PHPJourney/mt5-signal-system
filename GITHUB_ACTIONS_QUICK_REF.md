# GitHub Actions 快速参考卡片

## 🚀 3步快速使用

### 1️⃣ 一键设置 (macOS/Linux)
```bash
cd mt5_signal_system
./setup_github.sh
```

### 2️⃣ 触发构建
```bash
git tag v1.0.0
git push origin v1.0.0
```

### 3️⃣ 下载EXE
访问: https://github.com/你的用户名/仓库名/actions

---

## 📝 手动设置步骤

### Step 1: 创建GitHub仓库
```
https://github.com/new
仓库名: mt5-signal-system
```

### Step 2: 初始化Git
```bash
cd mt5_signal_system
git init
git add .
git commit -m "Initial commit"
```

### Step 3: 关联远程仓库
```bash
git remote add origin https://github.com/用户名/mt5-signal-system.git
git branch -M main
git push -u origin main
```

### Step 4: 触发构建
```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## 🔑 Personal Access Token

**获取Token:**
1. https://github.com/settings/tokens
2. Generate new token (classic)
3. 勾选权限: `repo`
4. 生成并复制

**使用Token:**
```
用户名: 你的GitHub用户名
密码: 粘贴Token
```

---

## 📊 查看构建

**Actions页面:**
```
https://github.com/用户名/仓库名/actions
```

**状态说明:**
- 🟡 黄色 = 构建中
- 🟢 绿色 = 成功
- 🔴 红色 = 失败

---

## 📦 下载文件

**方法1: Artifacts**
1. 进入Actions页面
2. 点击完成的构建
3. 点击 "MT5-Signal-System-Windows"
4. 解压ZIP文件

**方法2: Releases** (使用标签时)
1. 仓库首页右侧
2. 点击最新版本
3. 下载Assets

---

## ⚙️ 常用命令

**查看远程仓库:**
```bash
git remote -v
```

**查看分支:**
```bash
git branch
```

**创建新标签:**
```bash
git tag v1.0.1
git push origin v1.0.1
```

**删除标签:**
```bash
git tag -d v1.0.0
git push origin --delete v1.0.0
```

**重新推送:**
```bash
git push origin main --force
```

---

## ❌ 常见问题速查

| 问题 | 解决 |
|------|------|
| 认证失败 | 使用Personal Access Token |
| Actions未触发 | 检查.yml文件是否存在 |
| 构建失败 | 查看Actions日志 |
| 下载链接过期 | 重新推送标签 |
| 推送被拒绝 | 先在GitHub创建仓库 |

---

## 🔗 重要链接

- **创建仓库**: https://github.com/new
- **获取Token**: https://github.com/settings/tokens
- **Actions文档**: https://docs.github.com/actions
- **本项目配置**: `.github/workflows/build-windows.yml`

---

## 💡 提示

✅ Public仓库免费使用  
✅ 每月2000分钟构建时长  
✅ Artifacts保留90天  
✅ 支持手动触发  

---

**详细指南**: 查看 `GITHUB_ACTIONS_GUIDE.md`
