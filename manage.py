#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综测计算助手 - 统一项目管理工具
整合所有子项目的管理功能

使用方法:
    python manage.py <命令> [选项]

可用命令:
    start            : 启动所有服务
    stop             : 停止所有服务
    status           : 查看服务状态
    db               : 数据库管理
    test             : 运行测试
    install          : 安装依赖
    clean            : 清理临时文件
"""

import argparse
import subprocess
import sys
import os
import signal
import time
from pathlib import Path
from typing import Optional

project_root = Path(__file__).parent
visual_model_dir = project_root / "visual_model"
rag_dir = project_root / "PaddleOCRRAG"
frontend_dir = project_root / "fronted" / "front"

visual_model_venv = visual_model_dir / "venv"
rag_conda_env = project_root / ".conda"


def get_visual_model_python():
    """获取Visual Model项目的Python解释器 (venv环境)"""
    python_exe = visual_model_venv / "python.exe"
    if python_exe.exists():
        return str(python_exe)
    return sys.executable


def get_rag_python():
    """获取RAG项目的Python解释器 (.conda环境)"""
    python_exe = rag_conda_env / "python.exe"
    if python_exe.exists():
        return str(python_exe)
    return sys.executable


def start_services(args):
    """启动所有服务"""
    print("=" * 60)
    print("🚀 启动所有服务")
    print("=" * 60)
    
    if sys.platform == "win32":
        subprocess.run(["start.bat"], cwd=project_root, shell=True)
    else:
        print("请使用以下命令启动服务:")
        print("  ./start.sh")
    
    print("\n服务启动中...")
    print("  - RAG后端: http://localhost:8010")
    print("  - Visual Model后端: http://localhost:8001")
    print("  - 前端: http://localhost:5173")


def stop_services(args):
    """停止所有服务"""
    print("=" * 60)
    print("🛑 停止所有服务")
    print("=" * 60)
    
    if sys.platform == "win32":
        subprocess.run(["stop.bat"], cwd=project_root, shell=True)
    else:
        print("请使用以下命令停止服务:")
        print("  ./stop.sh")
    
    print("\n服务已停止")


def check_status(args):
    """检查服务状态"""
    import requests
    
    print("=" * 60)
    print("📊 服务状态检查")
    print("=" * 60)
    
    services = [
        ("RAG后端", "http://localhost:8010/api/v1/system/health"),
        ("Visual Model后端", "http://localhost:8001/health"),
        ("前端", "http://localhost:5173")
    ]
    
    for name, url in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {name}: 运行中 ({url})")
            else:
                print(f"  ⚠️ {name}: 异常 (状态码: {response.status_code})")
        except requests.exceptions.RequestException:
            print(f"  ❌ {name}: 未运行 ({url})")


def db_management(args):
    """数据库管理"""
    db_script = visual_model_dir / "scripts" / "db_manager.py"
    
    if not db_script.exists():
        print(f"错误: {db_script} 不存在")
        return
    
    python_exe = get_visual_model_python()
    cmd = [python_exe, str(db_script)]
    
    if args.db_command:
        cmd.append(args.db_command)
    if args.verbose:
        cmd.append("--verbose")
    if args.yes:
        cmd.append("--yes")
    
    try:
        subprocess.run(cmd, cwd=visual_model_dir)
    except KeyboardInterrupt:
        print("\n操作已取消")


def run_tests(args):
    """运行测试"""
    print("=" * 60)
    print("🧪 运行测试")
    print("=" * 60)
    
    if args.target == "rag" or args.target == "all":
        print("\n测试 RAG 系统...")
        rag_python = get_rag_python()
        test_script = rag_dir / "test_api.py"
        if test_script.exists():
                subprocess.run([rag_python, str(test_script), "--quick"], cwd=rag_dir)
        else:
                print("  RAG测试脚本不存在")
    
    if args.target == "visual" or args.target == "all":
        print("\n测试 Visual Model...")
        visual_python = get_visual_model_python()
        subprocess.run([visual_python, "-m", "pytest", "tests/", "-v"], cwd=visual_model_dir)


def install_dependencies(args):
    """安装依赖"""
    print("=" * 60)
    print("📦 安装依赖")
    print("=" * 60)
    
    if args.target == "visual" or args.target == "all":
        print("\n安装 Visual Model 依赖 (venv环境)...")
        python_exe = get_visual_model_python()
        subprocess.run([python_exe, "-m", "pip", "install", "-r", "requirements.txt"], cwd=visual_model_dir)
    
    if args.target == "rag" or args.target == "all":
        print("\n安装 RAG 系统依赖 (.conda环境)...")
        python_exe = get_rag_python()
        subprocess.run([python_exe, "-m", "pip", "install", "-r", "requirements.txt"], cwd=rag_dir)
    
    if args.target == "frontend" or args.target == "all":
        print("\n安装前端依赖...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, shell=True)
    
    print("\n✅ 依赖安装完成")


def create_venv(args):
    """创建虚拟环境"""
    print("=" * 60)
    print("🔧 创建虚拟环境")
    print("=" * 60)
    
    if args.target == "visual" or args.target == "all":
        print("\n创建 Visual Model 虚拟环境 (venv)...")
        venv_path = visual_model_dir / "venv"
        if not venv_path.exists():
                subprocess.run(["conda", "create", "-p", str(venv_path), "python=3.12", "-y"])
                print(f"  ✅ 虚拟环境创建成功: {venv_path}")
        else:
            print(f"  虚拟环境已存在: {venv_path}")
    
    if args.target == "rag" or args.target == "all":
        print("\n创建 RAG 虚拟环境 (.conda)...")
        conda_path = rag_conda_env
        if not conda_path.exists():
                subprocess.run(["conda", "create", "-p", str(conda_path), "python=3.12", "-y"])
                print(f"  ✅ 虚拟环境创建成功: {conda_path}")
        else:
            print(f"  虚拟环境已存在: {conda_path}")
    
    print("\n✅ 虚拟环境创建完成")


def clean_temp_files(args):
    """清理临时文件"""
    print("=" * 60)
    print("🧹 清理临时文件")
    print("=" * 60)
    
    patterns_to_clean = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        "**/*.log",
        "**/.pytest_cache",
        "**/.mypy_cache",
        "**/node_modules/.cache"
    ]
    
    import shutil
    
    for pattern in patterns_to_clean:
        for path in project_root.glob(pattern):
            if path.is_dir():
                print(f"  删除目录: {path}")
                shutil.rmtree(path, ignore_errors=True)
            elif path.is_file():
                print(f"  删除文件: {path}")
                path.unlink(missing_ok=True)
    
    print("\n✅ 清理完成")


def show_help():
    """显示帮助信息"""
    print(__doc__)
    print("\n" + "=" * 60)
    print("命令详细说明")
    print("=" * 60)
    print("\n1. 服务管理")
    print("   python manage.py start              # 启动所有服务")
    print("   python manage.py stop               # 停止所有服务")
    print("   python manage.py status             # 查看服务状态")
    print("\n2. 数据库管理")
    print("   python manage.py db init            # 初始化数据库")
    print("   python manage.py db migrate         # 执行数据库迁移")
    print("   python manage.py db backup          # 备份数据库")
    print("   python manage.py db reset           # 重置数据库")
    print("\n3. 测试")
    print("   python manage.py test               # 运行所有测试")
    print("   python manage.py test --target rag  # 仅测试RAG系统")
    print("\n4. 依赖管理")
    print("   python manage.py install            # 安装所有依赖")
    print("   python manage.py install --target visual  # 仅安装Visual Model依赖")
    print("\n5. 虚拟环境")
    print("   python manage.py venv               # 创建所有虚拟环境")
    print("   python manage.py venv --target rag  # 仅创建RAG虚拟环境")
    print("\n6. 清理")
    print("   python manage.py clean              # 清理临时文件")
    print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='综测计算助手 - 统一项目管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    start_parser = subparsers.add_parser('start', help='启动所有服务')
    stop_parser = subparsers.add_parser('stop', help='停止所有服务')
    status_parser = subparsers.add_parser('status', help='查看服务状态')
    
    db_parser = subparsers.add_parser('db', help='数据库管理')
    db_parser.add_argument('db_command', nargs='?', 
                          choices=['init', 'check', 'migrate', 'backup', 'reset', 'sample', 'import'],
                          help='数据库操作命令')
    db_parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    db_parser.add_argument('--yes', '-y', action='store_true', help='自动确认')
    
    test_parser = subparsers.add_parser('test', help='运行测试')
    test_parser.add_argument('--target', '-t', choices=['all', 'rag', 'visual'], default='all',
                            help='测试目标')
    
    install_parser = subparsers.add_parser('install', help='安装依赖')
    install_parser.add_argument('--target', '-t', choices=['all', 'visual', 'rag', 'frontend'],
                               default='all', help='安装目标')
    
    venv_parser = subparsers.add_parser('venv', help='创建虚拟环境')
    venv_parser.add_argument('--target', '-t', choices=['all', 'visual', 'rag'],
                            default='all', help='创建目标')
    
    clean_parser = subparsers.add_parser('clean', help='清理临时文件')
    
    args = parser.parse_args()
    
    if not args.command:
        show_help()
        return
    
    try:
        if args.command == 'start':
            start_services(args)
        elif args.command == 'stop':
            stop_services(args)
        elif args.command == 'status':
            check_status(args)
        elif args.command == 'db':
            db_management(args)
        elif args.command == 'test':
            run_tests(args)
        elif args.command == 'install':
            install_dependencies(args)
        elif args.command == 'venv':
            create_venv(args)
        elif args.command == 'clean':
            clean_temp_files(args)
        else:
            show_help()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n[ERROR] 执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
