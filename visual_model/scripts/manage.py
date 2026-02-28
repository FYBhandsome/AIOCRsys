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

project_root = Path(__file__).parent.parent
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(project_root))


def db_command(args):
    """数据库管理命令"""
    db_manager_script = scripts_dir / "db_manager.py"
    
    if not db_manager_script.exists():
        print(f"错误: {db_manager_script} 不存在")
        sys.exit(1)
    
    cmd = [sys.executable, str(db_manager_script)]
    
    if hasattr(args, 'db_subcommand') and args.db_subcommand:
        cmd.append(args.db_subcommand)
        if hasattr(args, 'verbose') and args.verbose:
            cmd.append('--verbose')
        if hasattr(args, 'yes') and args.yes:
            cmd.append('--yes')
        if hasattr(args, 'file') and args.file:
            cmd.extend(['--file', args.file])
    else:
        print("数据库管理工具需要指定子命令")
        print("可用子命令: init, check, migrate, backup, reset, sample, import")
        print("使用示例: python scripts/manage.py db init")
        sys.exit(1)
    
    try:
        result = subprocess.run(cmd, cwd=str(project_root))
        sys.exit(result.returncode)
    except Exception as e:
        print(f"执行数据库管理失败: {e}")
        sys.exit(1)


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
        sys.exit(1)


def show_help():
    """显示帮助信息"""
    print(__doc__)
    print("\n" + "=" * 60)
    print("命令详细说明")
    print("=" * 60)
    print("\n1. 数据库管理 (db)")
    print("   python scripts/manage.py db init              # 初始化数据库")
    print("   python scripts/manage.py db check             # 检查数据库表")
    print("   python scripts/manage.py db migrate           # 执行数据库迁移")
    print("   python scripts/manage.py db backup            # 备份数据库")
    print("   python scripts/manage.py db reset             # 重置数据库")
    print("   python scripts/manage.py db sample            # 创建示例数据")
    print("   python scripts/manage.py db import            # 导入综测数据")
    print("\n2. 模型下载 (download)")
    print("   python scripts/manage.py download             # 下载OCR模型")
    print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='统一项目管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    db_parser = subparsers.add_parser('db', help='数据库管理')
    db_parser.add_argument(
        'db_subcommand',
        nargs='?',
        choices=['init', 'check', 'migrate', 'migrate-users', 'migrate-academic', 
                 'migrate-config', 'backup', 'reset', 'sample', 'import'],
        help='数据库操作子命令'
    )
    db_parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    db_parser.add_argument('--yes', '-y', action='store_true', help='自动确认')
    db_parser.add_argument('--file', '-f', help='指定导入文件路径')
    
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
        sys.exit(1)


if __name__ == "__main__":
    main()
