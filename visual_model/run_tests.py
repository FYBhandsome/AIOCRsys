#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试运行脚本
运行所有测试并生成报告
"""
import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path


def run_tests(test_type: str = "all", verbose: bool = True):
    """运行测试
    
    Args:
        test_type: 测试类型 (all/unit/integration/api)
        verbose: 是否详细输出
    """
    print("=" * 60)
    print("综测计算助手 - 测试运行器")
    print("=" * 60)
    print(f"测试类型: {test_type}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    os.chdir(Path(__file__).parent)
    
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend(["--tb=short", "-ra"])
    
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "api":
        cmd.extend(["-m", "api"])
    elif test_type == "auth":
        cmd.extend(["-m", "auth"])
    elif test_type == "comprehensive":
        cmd.extend(["-m", "comprehensive"])
    elif test_type == "ai":
        cmd.extend(["-m", "ai"])
    
    cmd.append("--json-report")
    cmd.append("--json-report-file=test_report.json")
    
    cmd.append("tests/")
    
    print(f"执行命令: {' '.join(cmd)}")
    print("-" * 60)
    
    result = subprocess.run(cmd, capture_output=False)
    
    print("-" * 60)
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"退出码: {result.returncode}")
    print("=" * 60)
    
    return result.returncode


def generate_report():
    """生成测试报告"""
    report_file = Path(__file__).parent / "test_report.json"
    
    if not report_file.exists():
        print("未找到测试报告文件")
        return
    
    with open(report_file, "r", encoding="utf-8") as f:
        report = json.load(f)
    
    summary = report.get("summary", {})
    
    print("\n" + "=" * 60)
    print("测试报告摘要")
    print("=" * 60)
    print(f"总测试数: {summary.get('total', 0)}")
    print(f"通过: {summary.get('passed', 0)}")
    print(f"失败: {summary.get('failed', 0)}")
    print(f"跳过: {summary.get('skipped', 0)}")
    print(f"错误: {summary.get('error', 0)}")
    print(f"执行时间: {summary.get('duration', 0):.2f}秒")
    print("=" * 60)
    
    if summary.get("failed", 0) > 0:
        print("\n失败的测试:")
        for test in report.get("tests", []):
            if test.get("outcome") == "failed":
                print(f"  - {test.get('nodeid', 'unknown')}")
                if "call" in test and "crash" in test["call"]:
                    print(f"    错误: {test['call']['crash'].get('message', 'unknown')}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="综测计算助手测试运行器")
    parser.add_argument(
        "--type", "-t",
        choices=["all", "unit", "integration", "api", "auth", "comprehensive", "ai"],
        default="all",
        help="测试类型"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="安静模式，减少输出"
    )
    parser.add_argument(
        "--report", "-r",
        action="store_true",
        help="生成测试报告"
    )
    
    args = parser.parse_args()
    
    exit_code = run_tests(args.type, not args.quiet)
    
    if args.report:
        generate_report()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
