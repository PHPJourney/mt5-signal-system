# GitHub Actions 错误修复指南

## ❌ 遇到的错误

```
This request has been automatically failed because it uses a deprecated version of `actions/upload-artifact: v3`.
```

## ✅ 已修复

我已经更新了 `.github/workflows/build-windows.yml` 文件，将所有 actions 升级到最新版本：

**修改内容:**
- `actions/checkout@v3` → `actions/checkout@v4`
- `actions/setup-python@v4` → `actions/setup-python@v5`
- `actions/upload-artifact@v3` → `actions/upload-artifact@v4`

---

## 🚀 如何应用修复

### 方法1: 在本地 Git 仓库提交 (推荐)

```bash
cd /Users/mac/Downloads/cndnsidc/mt5_signal_system

# 添加修改的文件
git add .github/workflows/build-windows.yml

# 提交
git commit -m "Fix: Upgrade GitHub Actions to latest versions"

# 推送 (会触发新的构建)
git push origin main
```

### 方法2: 直接在 GitHub 上编辑

1. 访问你的 GitHub 仓库
2. 进入 `.github/workflows/build-windows.yml`
3. 点击 "Edit this file"
4. 修改以下行：

**第17行:**
```yaml
# 从
uses: actions/checkout@v3
# 改为
uses: actions/checkout@v4
```

**第20行:**
```yaml
# 从
uses: actions/setup-python@v4
# 改为
uses: actions/setup-python@v5
```

**第104行:**
```yaml
# 从
uses: actions/upload-artifact@v3
# 改为
uses: actions/upload-artifact@v4
```

5. 点击 "Commit changes"
6. 会自动触发新的构建

---

## 📊 验证修复

推送后，访问：
```
https://github.com/你的用户名/仓库名/actions
```

应该看到：
- 🟢 新的构建任务自动启动
- ✅ 使用最新的 actions v4/v5
- ✅ 不再出现 deprecated 警告

---

## 🔍 当前配置

修复后的配置已经是正确的，文件位于：
```
mt5_signal_system/.github/workflows/build-windows.yml
```

**关键部分:**
```yaml
- name: Checkout code
  uses: actions/checkout@v4          # ✅ 已更新

- name: Set up Python
  uses: actions/setup-python@v5      # ✅ 已更新
  with:
    python-version: '3.11'

- name: Upload artifacts
  uses: actions/upload-artifact@v4   # ✅ 已更新
  with:
    name: MT5-Signal-System-Windows
    path: dist/MT5_Signal_System_Release/
    retention-days: 90
```

---

## ⚡ 快速修复命令

复制粘贴执行：

```bash
cd mt5_signal_system
git add .
git commit -m "Fix GitHub Actions versions"
git push
```

然后等待 5-10 分钟，新的构建会自动完成！

---

## 📝 总结

- ✅ 问题已识别：actions 版本过旧
- ✅ 代码已修复：升级到 v4/v5
- ⏳ 待操作：提交并推送到 GitHub
- 🎯 结果：构建将成功完成

**只需提交修改，GitHub Actions 就会自动重新构建！**
