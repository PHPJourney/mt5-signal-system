#!/bin/bash
# Docker-based Cross-Compilation for Windows EXE
# 注意: macOS 版 Docker 不支持 Windows 容器
# 此脚本提供替代方案

set -e

echo "==============================================="
echo "  MT5 Signal System - Windows EXE Builder"
echo "==============================================="
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "[错误] Docker 未安装"
    exit 1
fi

echo "[✓] Docker 已安装: $(docker --version)"
echo ""

# 重要提示
echo "⚠️  重要提示:"
echo ""
echo "Docker for Mac 不支持 Windows 容器!"
echo "macOS 版 Docker Desktop 只能运行 Linux 容器"
echo ""
echo "以下是推荐的替代方案:"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "方案1: GitHub Actions (强烈推荐) ⭐⭐⭐"
echo "  ✓ 无需 Windows 电脑"
echo "  ✓ 自动在 Windows Server 2022 上构建"
echo "  ✓ 完全免费 (Public 仓库)"
echo "  ✓ 5-10分钟完成"
echo ""
echo "  使用方法:"
echo "    1. git push origin v1.0.0"
echo "    2. 等待自动构建"
echo "    3. 从 Actions 页面下载 EXE"
echo ""
echo "  详细文档: GITHUB_ACTIONS_SUMMARY.md"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "方案2: 在真实 Windows 电脑上打包 ⭐⭐"
echo "  ✓ 最简单直接"
echo "  ✓ 可以测试生成的 EXE"
echo "  ✓ 100% 兼容"
echo ""
echo "  使用方法:"
echo "    1. 将项目复制到 Windows 电脑"
echo "    2. 运行: build_exe.bat"
echo "    3. 获取 dist/ 目录下的 EXE"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "方案3: 使用远程 Windows 服务器 ⭐⭐"
echo "  ✓ 适合团队使用"
echo "  ✓ 可以自动化"
echo ""
echo "  选项:"
echo "    - Azure Windows VM"
echo "    - AWS EC2 Windows"
echo "    - 公司内部 Windows 服务器"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

read -p "是否查看 GitHub Actions 快速指南? (y/n): " CHOICE

if [ "$CHOICE" = "y" ]; then
    echo ""
    echo "==============================================="
    echo "  GitHub Actions 快速开始"
    echo "==============================================="
    echo ""
    
    # 检查是否有 GitHub Actions 配置
    if [ -f ".github/workflows/build-windows.yml" ]; then
        echo "[✓] GitHub Actions 配置文件已存在"
        echo ""
        echo "步骤:"
        echo ""
        echo "1. 初始化 Git 仓库 (如果还没有):"
        echo "   git init"
        echo "   git add ."
        echo "   git commit -m \"Initial commit\""
        echo ""
        echo "2. 创建 GitHub 仓库并关联:"
        echo "   git remote add origin https://github.com/你的用户名/仓库名.git"
        echo ""
        echo "3. 推送代码:"
        echo "   git push -u origin main"
        echo ""
        echo "4. 触发构建 (创建标签):"
        echo "   git tag v1.0.0"
        echo "   git push origin v1.0.0"
        echo ""
        echo "5. 等待 5-10 分钟，然后下载 EXE:"
        echo "   https://github.com/你的用户名/仓库名/actions"
        echo ""
        
        read -p "是否现在运行一键设置脚本? (y/n): " SETUP
        
        if [ "$SETUP" = "y" ]; then
            if [ -f "setup_github.sh" ]; then
                chmod +x setup_github.sh
                ./setup_github.sh
            else
                echo "[错误] setup_github.sh 不存在"
            fi
        fi
    else
        echo "[错误] GitHub Actions 配置文件不存在"
        echo "请确保 .github/workflows/build-windows.yml 存在"
    fi
fi

echo ""
echo "==============================================="
echo "  其他资源"
echo "==============================================="
echo ""
echo "详细文档:"
echo "  - GITHUB_ACTIONS_SUMMARY.md     (完整总结)"
echo "  - GITHUB_ACTIONS_GUIDE.md       (详细指南)"
echo "  - GITHUB_ACTIONS_QUICK_REF.md   (快速参考)"
echo "  - BUILD_GUIDE.md                (打包指南)"
echo "  - WINDOWS_COMPATIBILITY.md      (兼容性说明)"
echo ""
echo "Windows 打包脚本:"
echo "  - build_exe.bat                 (在 Windows 上运行)"
echo ""
echo "一键设置:"
echo "  - setup_github.sh               (macOS/Linux)"
echo ""
