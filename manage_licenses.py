#!/usr/bin/env python3
"""
License Management Tool for MT5 Signal System
Generate, validate, and manage client licenses
"""

import sys
import os
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from master.auth_manager import LicenseManager


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def generate_license(args):
    """生成许可证"""
    manager = LicenseManager()

    client_name = args[0] if len(args) > 0 else input("客户名称: ")
    days_valid = int(args[1]) if len(args) > 1 else input("有效天数 (默认365): ") or 365
    max_conn = int(args[2]) if len(args) > 2 else input("最大连接数 (默认1): ") or 1

    license_key = manager.generate_license_key(
        client_name=client_name,
        days_valid=int(days_valid),
        max_connections=int(max_conn)
    )

    print_header("许可证生成成功!")
    print(f"客户名称: {client_name}")
    print(f"许可证密钥: {license_key}")
    print(f"有效天数: {days_valid} 天")
    print(f"最大连接: {max_conn}")

    expire_date = manager.get_license_info(license_key)["expire_date"]
    print(f"过期时间: {expire_date}")
    print("\n请将许可证密钥提供给客户。")


def list_licenses(args):
    """列出所有许可证"""
    manager = LicenseManager()
    licenses = manager.list_licenses()

    print_header("许可证列表")

    if not licenses:
        print("暂无许可证")
        return

    print(f"{'客户名称':<20} {'许可证密钥':<35} {'状态':<10} {'连接数':<10} {'过期时间'}")
    print("-" * 100)

    for lic in licenses:
        print(f"{lic['client_name']:<20} {lic['license_key']:<35} "
              f"{lic['status']:<10} {lic['connections']:<10} {lic['expire_date']}")

    print(f"\n总计: {len(licenses)} 个许可证")


def validate_license(args):
    """验证许可证"""
    manager = LicenseManager()

    license_key = args[0] if len(args) > 0 else input("请输入许可证密钥: ")
    result = manager.validate_license(license_key)

    print_header("许可证验证结果")

    if result["valid"]:
        print("✅ 许可证有效")
        print(f"客户名称: {result['data']['client_name']}")
        print(f"过期时间: {result['data']['expire_date']}")
        print(f"最大连接: {result['data']['max_connections']}")
        print(f"\n功能权限:")
        for feature, enabled in result['data']['features'].items():
            status = "✓" if enabled else "✗"
            print(f"  {status} {feature}")
    else:
        print(f"❌ 许可证无效")
        print(f"原因: {result['message']}")
        print(f"错误代码: {result.get('error_code', 'UNKNOWN')}")


def revoke_license(args):
    """吊销许可证"""
    manager = LicenseManager()

    license_key = args[0] if len(args) > 0 else input("请输入要吊销的许可证密钥: ")

    # 先验证是否存在
    info = manager.get_license_info(license_key)
    if not info:
        print(f"❌ 许可证不存在: {license_key}")
        return

    confirm = input(f"确认吊销许可证? (客户: {info['client_name']}) [y/N]: ")
    if confirm.lower() != 'y':
        print("已取消")
        return

    if manager.revoke_license(license_key):
        print(f"✅ 许可证已吊销: {license_key}")
    else:
        print(f"❌ 吊销失败")


def show_stats(args):
    """显示统计信息"""
    manager = LicenseManager()
    licenses = manager.list_licenses()

    print_header("许可证统计")

    total = len(licenses)
    active = sum(1 for l in licenses if l['status'] == 'active')
    expired = sum(1 for l in licenses if l['status'] == 'expired')
    revoked = sum(1 for l in licenses if l['status'] == 'revoked')

    print(f"总许可证数: {total}")
    print(f"活跃: {active}")
    print(f"已过期: {expired}")
    print(f"已吊销: {revoked}")
    print()

    # 连接统计
    total_connections = 0
    for lic_data in manager.licenses["clients"].values():
        total_connections += lic_data.get("current_connections", 0)

    print(f"当前总连接数: {total_connections}")


def export_licenses(args):
    """导出许可证"""
    manager = LicenseManager()
    output_file = args[0] if len(args) > 0 else "licenses_export.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(manager.licenses, f, indent=4, ensure_ascii=False)

    print(f"✅ 许可证已导出到: {output_file}")


def print_usage():
    """打印使用说明"""
    print_header("MT5 Signal System - License Manager")
    print("用法: python manage_licenses.py <命令> [参数]\n")
    print("可用命令:")
    print("  generate [名称] [天数] [连接数]  - 生成新许可证")
    print("  list                            - 列出所有许可证")
    print("  validate [密钥]                  - 验证许可证")
    print("  revoke [密钥]                    - 吊销许可证")
    print("  stats                           - 显示统计信息")
    print("  export [文件]                    - 导出许可证")
    print("\n示例:")
    print("  python manage_licenses.py generate \"客户A\" 365 1")
    print("  python manage_licenses.py list")
    print("  python manage_licenses.py validate ABC123...")
    print("  python manage_licenses.py revoke ABC123...")
    print()


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1].lower()
    args = sys.argv[2:]

    commands = {
        "generate": generate_license,
        "gen": generate_license,
        "list": list_licenses,
        "ls": list_licenses,
        "validate": validate_license,
        "val": validate_license,
        "revoke": revoke_license,
        "rev": revoke_license,
        "stats": show_stats,
        "export": export_licenses,
    }

    if command in commands:
        try:
            commands[command](args)
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"未知命令: {command}")
        print_usage()


if __name__ == "__main__":
    main()
