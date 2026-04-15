#!/bin/bash
# GitHub Actions 一键设置脚本
# 自动初始化Git仓库并推送到GitHub

set -e

echo "=============================================="
echo "  GitHub Actions 一键设置"
echo "=============================================="
echo ""

# 检查Git
if ! command -v git &> /dev/null; then
    echo "[错误] Git未安装"
    echo "请先安装Git: https://git-scm.com/downloads"
    exit 1
fi

echo "[✓] Git已安装: $(git --version)"
echo ""

# 获取用户输入
read -p "请输入GitHub用户名: " GITHUB_USERNAME
read -p "请输入仓库名称 (默认: mt5-signal-system): " REPO_NAME
REPO_NAME=${REPO_NAME:-mt5-signal-system}

echo ""
echo "配置信息:"
echo "  GitHub用户名: $GITHUB_USERNAME"
echo "  仓库名称: $REPO_NAME"
echo ""

read -p "确认继续? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo "已取消"
    exit 0
fi

echo ""
echo "=============================================="
echo "  步骤1: 初始化Git仓库"
echo "=============================================="
echo ""

# 检查是否已是Git仓库
if [ -d ".git" ]; then
    echo "[提示] 已是Git仓库，跳过初始化"
else
    git init
    echo "[✓] Git仓库已初始化"
fi

echo ""
echo "=============================================="
echo "  步骤2: 添加文件"
echo "=============================================="
echo ""

git add .
echo "[✓] 文件已添加"

echo ""
echo "=============================================="
echo "  步骤3: 创建提交"
echo "=============================================="
echo ""

# 检查是否有变更
if git diff --staged --quiet; then
    echo "[提示] 没有变更需要提交"
else
    git commit -m "Initial commit: MT5 Signal System v1.0.0"
    echo "[✓] 提交已创建"
fi

echo ""
echo "=============================================="
echo "  步骤4: 关联远程仓库"
echo "=============================================="
echo ""

REMOTE_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"

# 检查是否已关联
if git remote | grep -q "origin"; then
    echo "[提示] 远程仓库已存在"
    read -p "是否重新设置? (y/n): " RESET
    if [ "$RESET" = "y" ]; then
        git remote remove origin
        git remote add origin $REMOTE_URL
        echo "[✓] 远程仓库已更新"
    fi
else
    git remote add origin $REMOTE_URL
    echo "[✓] 远程仓库已关联"
fi

echo ""
echo "=============================================="
echo "  步骤5: 推送到GitHub"
echo "=============================================="
echo ""

# 设置默认分支
git branch -M main

echo "即将推送到: $REMOTE_URL"
echo ""
echo "注意:"
echo "1. 首次推送需要GitHub用户名和密码"
echo "2. 密码使用Personal Access Token"
echo "3. 获取Token: https://github.com/settings/tokens"
echo ""

read -p "准备推送? (y/n): " PUSH_CONFIRM
if [ "$PUSH_CONFIRM" != "y" ]; then
    echo ""
    echo "手动推送命令:"
    echo "  git push -u origin main"
    exit 0
fi

echo ""
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "[✓] 推送成功!"
else
    echo ""
    echo "[错误] 推送失败"
    echo ""
    echo "可能的原因:"
    echo "1. 仓库不存在 - 请先在GitHub上创建仓库"
    echo "2. 认证失败 - 请使用Personal Access Token"
    echo "3. 网络问题 - 请检查网络连接"
    echo ""
    echo "手动推送命令:"
    echo "  git push -u origin main"
    exit 1
fi

echo ""
echo "=============================================="
echo "  步骤6: 触发自动构建"
echo "=============================================="
echo ""

read -p "是否创建标签触发构建? (y/n): " TAG_CONFIRM
if [ "$TAG_CONFIRM" = "y" ]; then
    read -p "版本号 (默认: v1.0.0): " VERSION
    VERSION=${VERSION:-v1.0.0}

    git tag $VERSION
    git push origin $VERSION

    echo ""
    echo "[✓] 标签已推送，自动构建已触发!"
    echo ""
    echo "查看构建进度:"
    echo "  https://github.com/${GITHUB_USERNAME}/${REPO_NAME}/actions"
fi

echo ""
echo "=============================================="
echo "  设置完成!"
echo "=============================================="
echo ""
echo "仓库地址:"
echo "  https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
echo ""
echo "Actions页面:"
echo "  https://github.com/${GITHUB_USERNAME}/${REPO_NAME}/actions"
echo ""
echo "下一步:"
echo "1. 访问Actions页面查看构建进度"
echo "2. 等待5-10分钟完成构建"
echo "3. 下载生成的Windows EXE文件"
echo ""
echo "详细说明请查看: GITHUB_ACTIONS_GUIDE.md"
echo ""
