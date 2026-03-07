#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能基准测试框架

测试关键API端点的性能指标：
- API响应时间
- 内存使用情况
- CPU使用率
- 生成基准测试报告
"""

import asyncio
import json
import os
import sys
import time
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings


@dataclass
class MetricResult:
    """单个指标结果"""
    name: str
    value: float
    unit: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class APIBenchmarkResult:
    """API基准测试结果"""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    response_size_bytes: int
    success: bool
    error_message: Optional[str] = None
    memory_before_mb: float = 0.0
    memory_after_mb: float = 0.0
    memory_delta_mb: float = 0.0
    cpu_percent_before: float = 0.0
    cpu_percent_after: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ResourceSnapshot:
    """资源快照"""
    timestamp: str
    memory_rss_mb: float
    memory_vms_mb: float
    memory_percent: float
    cpu_percent: float
    available_memory_mb: float


@dataclass
class BenchmarkReport:
    """基准测试报告"""
    test_name: str
    start_time: str
    end_time: str
    duration_seconds: float
    api_results: List[Dict[str, Any]]
    resource_summary: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    recommendations: List[str]
    environment: Dict[str, Any]


class ResourceMonitor:
    """资源监控器"""
    
    def __init__(self):
        self._process = None
        if PSUTIL_AVAILABLE:
            self._process = psutil.Process(os.getpid())
    
    def get_snapshot(self) -> ResourceSnapshot:
        """获取当前资源快照"""
        snapshot = ResourceSnapshot(
            timestamp=datetime.now().isoformat(),
            memory_rss_mb=0.0,
            memory_vms_mb=0.0,
            memory_percent=0.0,
            cpu_percent=0.0,
            available_memory_mb=0.0
        )
        
        if PSUTIL_AVAILABLE and self._process:
            try:
                memory_info = self._process.memory_info()
                snapshot.memory_rss_mb = memory_info.rss / (1024 * 1024)
                snapshot.memory_vms_mb = memory_info.vms / (1024 * 1024)
                snapshot.memory_percent = self._process.memory_percent()
                snapshot.cpu_percent = self._process.cpu_percent(interval=0.1)
                
                virtual_memory = psutil.virtual_memory()
                snapshot.available_memory_mb = virtual_memory.available / (1024 * 1024)
            except Exception:
                pass
        
        return snapshot
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        info = {
            "psutil_available": PSUTIL_AVAILABLE,
            "platform": sys.platform,
        }
        
        if PSUTIL_AVAILABLE:
            try:
                cpu_count = psutil.cpu_count()
                cpu_freq = psutil.cpu_freq()
                virtual_mem = psutil.virtual_memory()
                
                info.update({
                    "cpu_count": cpu_count,
                    "cpu_freq_mhz": cpu_freq.current if cpu_freq else None,
                    "total_memory_gb": round(virtual_mem.total / (1024**3), 2),
                    "available_memory_gb": round(virtual_mem.available / (1024**3), 2),
                    "memory_percent": round(virtual_mem.percent, 2)
                })
            except Exception:
                pass
        
        return info


class PerformanceBenchmark:
    """性能基准测试"""
    
    def __init__(
        self,
        base_url: str = None,
        timeout: float = 30.0,
        iterations: int = 3
    ):
        self.base_url = base_url or f"http://127.0.0.1:{settings.PORT}"
        self.timeout = timeout
        self.iterations = iterations
        self.resource_monitor = ResourceMonitor()
        self.results: List[APIBenchmarkResult] = []
        self._token: Optional[str] = None
        self._test_user = {
            "username": "benchmark_test_user",
            "password": "benchmark_test_pass123"
        }
    
    async def _make_request(
        self,
        client: httpx.AsyncClient,
        method: str,
        endpoint: str,
        **kwargs
    ) -> APIBenchmarkResult:
        """执行HTTP请求并测量性能"""
        url = f"{self.base_url}{endpoint}"
        
        memory_before = self.resource_monitor.get_snapshot()
        cpu_before = memory_before.cpu_percent
        
        start_time = time.perf_counter()
        status_code = 0
        response_size = 0
        success = False
        error_message = None
        
        try:
            if method.upper() == "GET":
                response = await client.get(url, **kwargs)
            elif method.upper() == "POST":
                response = await client.post(url, **kwargs)
            elif method.upper() == "PUT":
                response = await client.put(url, **kwargs)
            elif method.upper() == "DELETE":
                response = await client.delete(url, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            status_code = response.status_code
            response_size = len(response.content)
            success = 200 <= status_code < 300
            
            if not success:
                try:
                    error_data = response.json()
                    error_message = error_data.get("detail", str(error_data))
                except Exception:
                    error_message = response.text[:200] if response.text else "Unknown error"
                    
        except httpx.TimeoutException:
            status_code = 0
            error_message = "Request timeout"
        except httpx.ConnectError:
            status_code = 0
            error_message = "Connection failed - server may not be running"
        except Exception as e:
            status_code = 0
            error_message = str(e)
        
        end_time = time.perf_counter()
        response_time_ms = (end_time - start_time) * 1000
        
        memory_after = self.resource_monitor.get_snapshot()
        cpu_after = memory_after.cpu_percent
        
        return APIBenchmarkResult(
            endpoint=endpoint,
            method=method.upper(),
            status_code=status_code,
            response_time_ms=round(response_time_ms, 2),
            response_size_bytes=response_size,
            success=success,
            error_message=error_message,
            memory_before_mb=round(memory_before.memory_rss_mb, 2),
            memory_after_mb=round(memory_after.memory_rss_mb, 2),
            memory_delta_mb=round(memory_after.memory_rss_mb - memory_before.memory_rss_mb, 2),
            cpu_percent_before=round(cpu_before, 2),
            cpu_percent_after=round(cpu_after, 2)
        )
    
    async def test_login(self, client: httpx.AsyncClient) -> APIBenchmarkResult:
        """测试登录API"""
        result = await self._make_request(
            client,
            "POST",
            "/api/v1/auth/login",
            json={
                "username": self._test_user["username"],
                "password": self._test_user["password"]
            }
        )
        
        if result.success:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/auth/login",
                    json=self._test_user
                )
                data = response.json()
                self._token = data.get("access_token")
            except Exception:
                pass
        
        return result
    
    async def test_score_summary(self, client: httpx.AsyncClient) -> APIBenchmarkResult:
        """测试成绩摘要API"""
        headers = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        
        return await self._make_request(
            client,
            "GET",
            "/api/v1/student/scores/summary",
            headers=headers
        )
    
    async def test_certificate_upload(self, client: httpx.AsyncClient) -> APIBenchmarkResult:
        """测试证书上传API"""
        headers = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        
        test_image_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        
        return await self._make_request(
            client,
            "POST",
            "/api/v1/certificate/upload",
            headers=headers,
            data={"student_id": "test_student"},
            files={"files": ("test.png", test_image_content, "image/png")}
        )
    
    async def test_comprehensive_score_calculate(self, client: httpx.AsyncClient) -> APIBenchmarkResult:
        """测试综测计算API"""
        headers = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        
        return await self._make_request(
            client,
            "POST",
            "/api/v1/comprehensive-score/calculate/student/test_student?academic_year=2024-2025&semester=1",
            headers=headers
        )
    
    async def run_benchmark(self) -> BenchmarkReport:
        """运行完整基准测试"""
        start_time = datetime.now()
        print(f"\n{'='*60}")
        print(f"性能基准测试开始")
        print(f"{'='*60}")
        print(f"测试时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目标服务: {self.base_url}")
        print(f"迭代次数: {self.iterations}")
        print(f"{'='*60}\n")
        
        all_results: List[APIBenchmarkResult] = []
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            test_methods = [
                ("登录认证", self.test_login),
                ("成绩摘要", self.test_score_summary),
                ("证书上传", self.test_certificate_upload),
                ("综测计算", self.test_comprehensive_score_calculate)
            ]
            
            for test_name, test_method in test_methods:
                print(f"\n测试: {test_name}")
                print("-" * 40)
                
                iteration_results = []
                
                for i in range(self.iterations):
                    print(f"  迭代 {i+1}/{self.iterations}...", end=" ")
                    result = await test_method(client)
                    iteration_results.append(result)
                    
                    status = "✓" if result.success else "✗"
                    print(f"{status} {result.response_time_ms:.2f}ms (状态码: {result.status_code})")
                    
                    await asyncio.sleep(0.5)
                
                avg_time = sum(r.response_time_ms for r in iteration_results) / len(iteration_results)
                success_rate = sum(1 for r in iteration_results if r.success) / len(iteration_results) * 100
                
                print(f"  平均响应时间: {avg_time:.2f}ms")
                print(f"  成功率: {success_rate:.0f}%")
                
                all_results.extend(iteration_results)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        report = self._generate_report(
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            results=all_results
        )
        
        return report
    
    def _generate_report(
        self,
        start_time: datetime,
        end_time: datetime,
        duration: float,
        results: List[APIBenchmarkResult]
    ) -> BenchmarkReport:
        """生成基准测试报告"""
        api_results = []
        
        endpoints = {}
        for r in results:
            key = f"{r.method} {r.endpoint}"
            if key not in endpoints:
                endpoints[key] = []
            endpoints[key].append(r)
        
        for endpoint, endpoint_results in endpoints.items():
            times = [r.response_time_ms for r in endpoint_results]
            successes = [r for r in endpoint_results if r.success]
            
            api_results.append({
                "endpoint": endpoint,
                "iterations": len(endpoint_results),
                "success_count": len(successes),
                "success_rate": round(len(successes) / len(endpoint_results) * 100, 2),
                "response_time": {
                    "min_ms": round(min(times), 2),
                    "max_ms": round(max(times), 2),
                    "avg_ms": round(sum(times) / len(times), 2),
                    "p50_ms": round(sorted(times)[len(times) // 2], 2),
                    "p95_ms": round(sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else times[0], 2)
                },
                "memory": {
                    "avg_delta_mb": round(sum(r.memory_delta_mb for r in endpoint_results) / len(endpoint_results), 2),
                    "max_delta_mb": round(max(r.memory_delta_mb for r in endpoint_results), 2)
                },
                "cpu": {
                    "avg_percent": round(sum(r.cpu_percent_after for r in endpoint_results) / len(endpoint_results), 2),
                    "max_percent": round(max(r.cpu_percent_after for r in endpoint_results), 2)
                }
            })
        
        resource_summary = {
            "psutil_available": PSUTIL_AVAILABLE,
            "total_requests": len(results),
            "successful_requests": sum(1 for r in results if r.success),
            "failed_requests": sum(1 for r in results if not r.success)
        }
        
        if PSUTIL_AVAILABLE and results:
            resource_summary["memory"] = {
                "avg_before_mb": round(sum(r.memory_before_mb for r in results) / len(results), 2),
                "avg_after_mb": round(sum(r.memory_after_mb for r in results) / len(results), 2),
                "total_delta_mb": round(results[-1].memory_after_mb - results[0].memory_before_mb, 2)
            }
            resource_summary["cpu"] = {
                "avg_percent": round(sum(r.cpu_percent_after for r in results) / len(results), 2),
                "max_percent": round(max(r.cpu_percent_after for r in results), 2)
            }
        
        performance_metrics = {
            "total_test_duration_seconds": round(duration, 2),
            "requests_per_second": round(len(results) / duration, 2) if duration > 0 else 0,
            "avg_response_time_ms": round(sum(r.response_time_ms for r in results) / len(results), 2) if results else 0,
            "overall_success_rate": round(sum(1 for r in results if r.success) / len(results) * 100, 2) if results else 0
        }
        
        recommendations = self._generate_recommendations(api_results, results)
        
        environment = {
            "base_url": self.base_url,
            "iterations": self.iterations,
            "timeout_seconds": self.timeout,
            "system": self.resource_monitor.get_system_info()
        }
        
        return BenchmarkReport(
            test_name="API Performance Benchmark",
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration_seconds=round(duration, 2),
            api_results=api_results,
            resource_summary=resource_summary,
            performance_metrics=performance_metrics,
            recommendations=recommendations,
            environment=environment
        )
    
    def _generate_recommendations(
        self,
        api_results: List[Dict[str, Any]],
        results: List[APIBenchmarkResult]
    ) -> List[str]:
        """生成性能优化建议"""
        recommendations = []
        
        for api in api_results:
            endpoint = api["endpoint"]
            avg_time = api["response_time"]["avg_ms"]
            success_rate = api["success_rate"]
            
            if success_rate < 100:
                recommendations.append(
                    f"[{endpoint}] 成功率为 {success_rate}%，建议检查错误处理和异常情况"
                )
            
            if avg_time > 1000:
                recommendations.append(
                    f"[{endpoint}] 平均响应时间 {avg_time:.0f}ms 超过1秒，建议优化数据库查询或添加缓存"
                )
            elif avg_time > 500:
                recommendations.append(
                    f"[{endpoint}] 平均响应时间 {avg_time:.0f}ms 较高，可考虑优化处理逻辑"
                )
            
            if api["memory"]["max_delta_mb"] > 50:
                recommendations.append(
                    f"[{endpoint}] 内存增量最大 {api['memory']['max_delta_mb']:.0f}MB，建议检查内存泄漏"
                )
            
            if api["cpu"]["max_percent"] > 80:
                recommendations.append(
                    f"[{endpoint}] CPU使用率峰值 {api['cpu']['max_percent']:.0f}%，建议优化计算密集型操作"
                )
        
        failed_endpoints = [r for r in results if not r.success]
        if failed_endpoints:
            connection_errors = [r for r in failed_endpoints if "Connection" in (r.error_message or "")]
            if connection_errors:
                recommendations.append(
                    "存在连接错误，请确保服务器正在运行且端口正确"
                )
        
        if not recommendations:
            recommendations.append("所有API端点性能表现良好，暂无优化建议")
        
        return recommendations
    
    def save_report(self, report: BenchmarkReport, output_path: str = None) -> str:
        """保存报告到JSON文件"""
        if output_path is None:
            output_dir = Path(__file__).parent.parent / "reports"
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"benchmark_report_{timestamp}.json"
        
        report_dict = asdict(report)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)
        
        return str(output_path)
    
    def print_summary(self, report: BenchmarkReport):
        """打印测试摘要"""
        print(f"\n{'='*60}")
        print("基准测试报告摘要")
        print(f"{'='*60}")
        print(f"测试名称: {report.test_name}")
        print(f"开始时间: {report.start_time}")
        print(f"结束时间: {report.end_time}")
        print(f"总耗时: {report.duration_seconds}秒")
        print(f"\n性能指标:")
        print(f"  - 总请求数: {report.resource_summary['total_requests']}")
        print(f"  - 成功请求: {report.resource_summary['successful_requests']}")
        print(f"  - 失败请求: {report.resource_summary['failed_requests']}")
        print(f"  - 平均响应时间: {report.performance_metrics['avg_response_time_ms']}ms")
        print(f"  - 整体成功率: {report.performance_metrics['overall_success_rate']}%")
        print(f"  - 每秒请求数: {report.performance_metrics['requests_per_second']}")
        
        print(f"\nAPI端点结果:")
        for api in report.api_results:
            print(f"\n  {api['endpoint']}:")
            print(f"    成功率: {api['success_rate']}%")
            print(f"    响应时间: min={api['response_time']['min_ms']}ms, "
                  f"avg={api['response_time']['avg_ms']}ms, "
                  f"max={api['response_time']['max_ms']}ms")
            print(f"    内存增量: avg={api['memory']['avg_delta_mb']}MB")
            print(f"    CPU使用: avg={api['cpu']['avg_percent']}%")
        
        print(f"\n优化建议:")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"  {i}. {rec}")
        
        print(f"\n{'='*60}")


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="API性能基准测试")
    parser.add_argument("--url", type=str, default=None, help="API服务地址")
    parser.add_argument("--iterations", type=int, default=3, help="每个端点测试迭代次数")
    parser.add_argument("--timeout", type=float, default=30.0, help="请求超时时间(秒)")
    parser.add_argument("--output", type=str, default=None, help="报告输出路径")
    
    args = parser.parse_args()
    
    benchmark = PerformanceBenchmark(
        base_url=args.url,
        timeout=args.timeout,
        iterations=args.iterations
    )
    
    try:
        report = await benchmark.run_benchmark()
        
        output_path = benchmark.save_report(report, args.output)
        benchmark.print_summary(report)
        
        print(f"\n报告已保存至: {output_path}")
        
        return 0 if report.performance_metrics["overall_success_rate"] > 0 else 1
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return 130
    except Exception as e:
        print(f"\n测试执行失败: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
