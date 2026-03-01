#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试报告生成器
生成详细的测试报告，包括覆盖率、发现的问题及修复情况
"""
import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path


class TestReportGenerator:
    """测试报告生成器"""
    
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.report = {
            "generated_at": datetime.now().isoformat(),
            "project": "综测计算助手",
            "summary": {},
            "categories": {},
            "issues": [],
            "recommendations": []
        }
    
    def run_tests(self):
        """运行测试并收集结果"""
        print("=" * 60)
        print("综测计算助手 - 测试报告生成器")
        print("=" * 60)
        print(f"项目目录: {self.project_dir}")
        print(f"生成时间: {self.report['generated_at']}")
        print("-" * 60)
        
        os.chdir(self.project_dir)
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/", "-v", "--tb=no",
            "--ignore=tests/test_e2e.py",
            "--ignore=tests/test_auth_api_new.py",
            "--ignore=tests/test_comprehensive_score_api_new.py",
            "--ignore=tests/test_ai_api_new.py",
            "--ignore=tests/test_integration_new.py",
            "--ignore=tests/test_rag_api_new.py",
            "-q"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return result
    
    def parse_test_results(self, output: str) -> dict:
        """解析测试结果"""
        lines = output.split('\n')
        
        passed = 0
        failed = 0
        errors = 0
        skipped = 0
        
        for line in lines:
            if 'passed' in line:
                parts = line.split()
                for part in parts:
                    if 'passed' in part:
                        try:
                            passed = int(part.replace('passed', ''))
                        except:
                            pass
                    if 'failed' in part:
                        try:
                            failed = int(part.replace('failed', ''))
                        except:
                            pass
                    if 'error' in part:
                        try:
                            errors = int(part.replace('error', ''))
                        except:
                            pass
                    if 'skipped' in part:
                        try:
                            skipped = int(part.replace('skipped', ''))
                        except:
                            pass
        
        return {
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "total": passed + failed + errors + skipped
        }
    
    def categorize_tests(self):
        """分类测试"""
        categories = {
            "认证模块": {
                "files": ["test_auth_api.py"],
                "description": "用户登录、注册、密码重置等功能测试"
            },
            "学生模块": {
                "files": ["test_student_api.py"],
                "description": "学生证书上传、成绩查询等功能测试"
            },
            "教师模块": {
                "files": ["test_teacher_api.py"],
                "description": "教师班级管理、成绩上传等功能测试"
            },
            "管理员模块": {
                "files": ["test_admin_api.py"],
                "description": "管理员系统配置、用户管理等功能测试"
            },
            "AI助手模块": {
                "files": ["test_ai_api.py"],
                "description": "AI对话、建议问题等功能测试"
            },
            "综测计算模块": {
                "files": ["test_comprehensive_score_api.py", "test_comprehensive_flow.py"],
                "description": "综测成绩计算、配置管理等功能测试"
            },
            "证书模块": {
                "files": ["test_certificate_api.py"],
                "description": "证书上传、OCR识别、审核等功能测试"
            },
            "文件管理模块": {
                "files": ["test_file_api.py"],
                "description": "文件上传、下载、删除等功能测试"
            },
            "API工具模块": {
                "files": ["test_api_utils.py"],
                "description": "API工具函数、参数验证等功能测试"
            },
            "中间件模块": {
                "files": ["test_middleware_api.py"],
                "description": "中间件功能测试"
            }
        }
        
        return categories
    
    def identify_issues(self, failed_tests: list):
        """识别问题"""
        issues = []
        
        issue_patterns = {
            "认证失败": {
                "pattern": ["login", "auth", "token", "password"],
                "severity": "高",
                "suggestion": "检查测试用户数据是否已初始化，确认认证中间件配置正确"
            },
            "权限问题": {
                "pattern": ["permission", "401", "403", "unauthorized", "forbidden"],
                "severity": "高",
                "suggestion": "检查权限控制逻辑，确认角色权限配置正确"
            },
            "文件操作失败": {
                "pattern": ["upload", "download", "file", "delete"],
                "severity": "中",
                "suggestion": "检查文件存储路径权限，确认文件操作API端点正确"
            },
            "参数验证失败": {
                "pattern": ["validation", "invalid", "empty", "missing"],
                "severity": "中",
                "suggestion": "检查参数验证逻辑，确认必填字段和格式要求"
            },
            "数据库操作失败": {
                "pattern": ["database", "not found", "does not exist"],
                "severity": "高",
                "suggestion": "检查数据库连接，确认测试数据已正确初始化"
            }
        }
        
        for test in failed_tests:
            for issue_type, info in issue_patterns.items():
                if any(p in test.lower() for p in info["pattern"]):
                    issues.append({
                        "test": test,
                        "type": issue_type,
                        "severity": info["severity"],
                        "suggestion": info["suggestion"]
                    })
                    break
        
        return issues
    
    def generate_recommendations(self, summary: dict, issues: list):
        """生成改进建议"""
        recommendations = []
        
        pass_rate = summary["passed"] / summary["total"] * 100 if summary["total"] > 0 else 0
        
        if pass_rate < 80:
            recommendations.append({
                "priority": "高",
                "title": "提高测试通过率",
                "description": f"当前测试通过率为 {pass_rate:.1f}%，建议优先修复失败的测试用例"
            })
        
        if summary["failed"] > 10:
            recommendations.append({
                "priority": "高",
                "title": "修复失败测试",
                "description": f"有 {summary['failed']} 个测试失败，建议按模块逐一排查和修复"
            })
        
        auth_issues = [i for i in issues if i["type"] == "认证失败"]
        if auth_issues:
            recommendations.append({
                "priority": "高",
                "title": "解决认证问题",
                "description": "发现认证相关的测试失败，建议先初始化测试用户数据"
            })
        
        file_issues = [i for i in issues if i["type"] == "文件操作失败"]
        if file_issues:
            recommendations.append({
                "priority": "中",
                "title": "完善文件操作",
                "description": "发现文件操作相关的测试失败，建议检查文件存储和权限配置"
            })
        
        recommendations.append({
            "priority": "中",
            "title": "增加测试覆盖率",
            "description": "建议增加边界条件测试和异常场景测试"
        })
        
        recommendations.append({
            "priority": "低",
            "title": "持续集成",
            "description": "建议配置CI/CD流水线，实现自动化测试"
        })
        
        return recommendations
    
    def generate_report(self):
        """生成完整报告"""
        result = self.run_tests()
        summary = self.parse_test_results(result.stdout + result.stderr)
        categories = self.categorize_tests()
        
        failed_tests = []
        for line in (result.stdout + result.stderr).split('\n'):
            if 'FAILED' in line:
                test_name = line.split('::')[-1].split()[0] if '::' in line else line
                failed_tests.append(test_name)
        
        issues = self.identify_issues(failed_tests)
        recommendations = self.generate_recommendations(summary, issues)
        
        self.report["summary"] = summary
        self.report["categories"] = categories
        self.report["issues"] = issues
        self.report["recommendations"] = recommendations
        
        return self.report
    
    def print_report(self):
        """打印报告"""
        report = self.generate_report()
        
        print("\n" + "=" * 60)
        print("测试报告摘要")
        print("=" * 60)
        
        summary = report["summary"]
        total = summary["total"]
        passed = summary["passed"]
        failed = summary["failed"]
        
        pass_rate = passed / total * 100 if total > 0 else 0
        
        print(f"总测试数: {total}")
        print(f"通过: {passed} ({pass_rate:.1f}%)")
        print(f"失败: {failed}")
        print(f"跳过: {summary['skipped']}")
        print(f"错误: {summary['errors']}")
        
        print("\n" + "-" * 60)
        print("测试模块分类:")
        print("-" * 60)
        
        for category, info in report["categories"].items():
            print(f"  {category}: {info['description']}")
        
        if report["issues"]:
            print("\n" + "-" * 60)
            print("发现的问题:")
            print("-" * 60)
            
            for i, issue in enumerate(report["issues"][:10], 1):
                print(f"  {i}. [{issue['severity']}] {issue['test']}")
                print(f"     类型: {issue['type']}")
                print(f"     建议: {issue['suggestion']}")
        
        print("\n" + "-" * 60)
        print("改进建议:")
        print("-" * 60)
        
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"  {i}. [{rec['priority']}] {rec['title']}")
            print(f"     {rec['description']}")
        
        print("\n" + "=" * 60)
        print("报告生成完成")
        print("=" * 60)
        
        return report


def main():
    """主函数"""
    project_dir = Path(__file__).parent.parent
    generator = TestReportGenerator(str(project_dir))
    report = generator.print_report()
    
    report_file = project_dir / "test_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n详细报告已保存到: {report_file}")


if __name__ == "__main__":
    main()
