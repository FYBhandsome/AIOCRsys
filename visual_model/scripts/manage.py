#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一项目管理工具
整合所有管理脚本功能

使用方法:
    python scripts/manage.py <命令> [选项]

可用命令:
    db               : 数据库管理（备份、恢复、初始化、迁移等）
    download         : 下载OCR模型
"""

import argparse
import sys
import os
import subprocess
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(project_root))


# ============================================================================
# 数据库管理模块（调用db_manager.py）
# ============================================================================

def db_command(args):
    """数据库管理命令"""
    db_manager_script = scripts_dir / "db_manager.py"
    
    if not db_manager_script.exists():
        print(f"错误: {db_manager_script} 不存在")
        sys.exit(1)
    
    # 构建命令
    cmd = [sys.executable, str(db_manager_script)]
    
    # 如果提供了子命令，传递给它
    if hasattr(args, 'db_subcommand') and args.db_subcommand:
        cmd.append(args.db_subcommand)
        # 传递其他参数
        if hasattr(args, 'verbose') and args.verbose:
            cmd.append('--verbose')
        if hasattr(args, 'yes') and args.yes:
            cmd.append('--yes')
    else:
        # 如果没有提供子命令，显示帮助
        print("数据库管理工具需要指定子命令")
        print("可用子命令: init, check, migrate, backup, reset, sample")
        print("使用示例: python scripts/manage.py db init")
        sys.exit(1)
    
    # 执行脚本
    try:
        result = subprocess.run(cmd, cwd=str(project_root))
        sys.exit(result.returncode)
    except Exception as e:
        print(f"执行数据库管理失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# ============================================================================
# 模型下载模块（调用download_models.py）
# ============================================================================

def download_command(args):
    """模型下载命令"""
    download_script = scripts_dir / "download_models.py"
    
    if not download_script.exists():
        print(f"错误: {download_script} 不存在")
        sys.exit(1)
    
    try:
        result = subprocess.run(
            [sys.executable, str(download_script)],
            cwd=str(project_root)
        )
        sys.exit(result.returncode)
    except Exception as e:
        print(f"执行模型下载失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# ============================================================================
# 主函数
# ============================================================================

def show_help():
    """显示帮助信息"""
    print(__doc__)
    print("\n" + "=" * 60)
    print("命令详细说明")
    print("=" * 60)
    print("\n1. 数据库管理 (db)")
    print("   python scripts/manage.py db init")
    print("   python scripts/manage.py db backup")
    print("   python scripts/manage.py db check")
    print("   python scripts/manage.py db migrate")
    print("   python scripts/manage.py db reset")
    print("   python scripts/manage.py db sample")
    print("\n2. 模型下载 (download)")
    print("   python scripts/manage.py download")
    print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='统一项目管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.d_subparsers(dest='command', help='可用命令')
    
    # 数据库管理命令
    db_parser = subparsers.add_parser('db', help='数据库管理')
    db_parser.add_argument(
        'db_subcommand',
        nargs='?',
        choices=['init', 'check', 'migrate', 'migrate-users', 'migrate-academic', 
                 'migrate-config', 'backup', 'reset', 'sample'],
        help='数据库操作子命令'
    )
    db_parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    db_parser.add_argument('--yes', '-y', action='store_true', help='自动确认')
    
    # 模型下载命令
    download_parser = subparsers.add_parser('download', help='下载OCR模型')
    
    args = parser.parse_args()
    
    if not args.command:
        show_help()
        return
    
    try:
        if args.command == 'db':
            db_command(args)
        elif args.command == 'download':
            download_command(args)
        else:
            print(f"未知命令: {args.command}")
            show_help()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
