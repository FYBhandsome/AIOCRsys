#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综测计算助手 - 服务启动脚本 v5.0
=====================================

功能描述:
    一键启动所有后端服务和前端应用，支持端口冲突自动处理、多进程并发启动。

特性:
    1. 多进程并发启动 - 显著提升启动速度
    2. 端口冲突自动处理 - 自动检测并切换到备用端口
    3. 完善的健康检查 - 确保服务正常启动
    4. 详细的日志记录 - 便于问题排查
    5. 优雅的关闭机制 - 确保服务正确停止

使用方法:
    直接运行: python start.py
    或通过批处理: start.bat

参数说明:
    无需参数，所有配置在脚本内部定义

作者: 综测计算助手开发团队
版本: 5.0
更新日期: 2026-03-01
"""

import os
import sys
import time
import signal
import socket
import subprocess
import threading
import warnings
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("[错误] 请安装 requests 库: pip install requests")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
    from rich.table import Table
    from rich.live import Live
    from rich.text import Text
    from rich.style import Style
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("[提示] 安装 rich 库可获得更好的显示效果: pip install rich")


# ============================================================================
# 全局配置
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.resolve()
VISUAL_MODEL_DIR = PROJECT_ROOT / "visual_model"
RAG_DIR = PROJECT_ROOT / "PaddleOCRRAG"
FRONTEND_DIR = PROJECT_ROOT / "fronted" / "front"
LOG_DIR = PROJECT_ROOT / "logs" / "startup"

VENV_PYTHON = VISUAL_MODEL_DIR / "venv" / "python.exe"
CONDA_PYTHON = PROJECT_ROOT / ".conda" / "python.exe"

MAX_PORT_RETRIES = 5
PORT_RETRY_INTERVAL = 2
HEALTH_CHECK_TIMEOUT = 60
HEALTH_CHECK_INTERVAL = 1

TEST_ACCOUNTS = [
    {"role": "管理员", "username": "dev_admin", "password": "dev123456", "description": "拥有所有权限"},
    {"role": "教师", "username": "dev_teacher", "password": "dev123456", "description": "可管理学生和成绩"},
    {"role": "学生", "username": "dev_student", "password": "dev123456", "description": "可查看个人信息和成绩"},
]

TEST_DATA_INFO = {
    "测试数据库": "data/database.db (SQLite)",
    "测试证书图片": "visual_model/testphoto/",
    "测试Excel文件": "visual_model/data/",
    "规则文档": "PaddleOCRRAG/data/rules/",
}


# ============================================================================
# 服务配置
# ============================================================================

SERVICES_CONFIG = {
    "visual_model": {
        "name": "Visual Model 后端",
        "default_port": 8001,
        "fallback_ports": [8002, 8003, 8004, 8005, 8006],
        "cwd": VISUAL_MODEL_DIR,
        "python": VENV_PYTHON,
        "script_template": "main.py",
        "enabled": True,
        "priority": 1,
        "description": "主后端API服务，提供OCR识别、用户认证、数据管理等功能",
        "health_path": "/api/v1/health",
        "api_prefix": "/api",
        "proxy_prefix": "/api",
    },
    "rag": {
        "name": "RAG 服务",
        "default_port": 8000,
        "fallback_ports": [8010, 8011, 8012, 8013, 8014],
        "cwd": RAG_DIR,
        "python": CONDA_PYTHON,
        "script_template": "-m uvicorn app.main:app --host 127.0.0.1 --port {port}",
        "enabled": True,
        "priority": 2,
        "description": "RAG智能问答服务，提供文档检索和AI对话功能",
        "health_path": "/health",
        "api_prefix": "",
        "proxy_prefix": "/rag-api",
    },
    "frontend": {
        "name": "前端应用",
        "default_port": 5173,
        "fallback_ports": [5174, 5175, 5176, 5177, 5178],
        "cwd": FRONTEND_DIR,
        "python": None,
        "script_template": None,
        "cmd_template": ["npm", "run", "dev", "--", "--port", "{port}"],
        "enabled": True,
        "priority": 3,
        "description": "Vue.js前端应用，提供用户界面",
        "health_path": "/",
        "api_prefix": None,
        "proxy_prefix": None,
    }
}


# ============================================================================
# 全局状态
# ============================================================================

processes: Dict[str, subprocess.Popen] = {}
shutdown_event = threading.Event()
service_ports: Dict[str, int] = {}
service_urls: Dict[str, Dict[str, str]] = {}


# ============================================================================
# 数据类定义
# ============================================================================

@dataclass
class PortChangeRecord:
    """端口变更记录"""
    service_id: str
    service_name: str
    original_port: int
    new_port: int
    change_time: str
    reason: str


@dataclass
class ServiceStatus:
    """服务状态"""
    service_id: str
    name: str
    port: int
    status: str
    url: str
    health_url: str
    process: Optional[subprocess.Popen] = None
    start_time: Optional[datetime] = None
    port_changed: bool = False


# ============================================================================
# 日志管理器
# ============================================================================

class ServiceLogger:
    """
    服务日志记录器
    
    功能:
        - 记录启动过程日志
        - 记录各服务输出
        - 线程安全
    
    属性:
        log_dir: 日志目录
        main_log: 主日志文件路径
    """
    
    def __init__(self, log_dir: Path):
        """
        初始化日志记录器
        
        Args:
            log_dir: 日志存储目录
        """
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.main_log = self.log_dir / "startup.log"
        self._lock = threading.Lock()
        
        self._init_main_log()
    
    def _init_main_log(self):
        """初始化主日志文件"""
        with open(self.main_log, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*70}\n")
            f.write(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"脚本版本: v5.0\n")
            f.write(f"{'='*70}\n")
    
    def log(self, service: str, level: str, message: str):
        """
        记录日志
        
        Args:
            service: 服务标识
            level: 日志级别 (INFO, WARN, ERROR, DEBUG)
            message: 日志消息
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] [{service:^15}] [{level:^5}] {message}\n"
        
        with self._lock:
            with open(self.main_log, 'a', encoding='utf-8') as f:
                f.write(log_line)
    
    def log_service_output(self, service: str, output: str):
        """
        记录服务输出
        
        Args:
            service: 服务标识
            output: 输出内容
        """
        log_file = self.log_dir / f"{service}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(output)
            if not output.endswith('\n'):
                f.write('\n')


# ============================================================================
# 端口管理器
# ============================================================================

class PortManager:
    """
    端口管理器
    
    功能:
        - 检测端口可用性
        - 自动查找可用端口
        - 记录端口变更
    
    属性:
        port_changes: 端口变更记录列表
    """
    
    def __init__(self, logger: ServiceLogger):
        """
        初始化端口管理器
        
        Args:
            logger: 日志记录器实例
        """
        self.logger = logger
        self.port_changes: List[PortChangeRecord] = []
        self._lock = threading.Lock()
    
    def is_port_available(self, port: int, host: str = '127.0.0.1') -> bool:
        """
        检查端口是否可用
        
        Args:
            port: 端口号
            host: 主机地址
            
        Returns:
            bool: 端口是否可用
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.settimeout(1)
                s.bind((host, port))
                return True
        except (OSError, socket.timeout):
            return False
    
    def find_available_port(self, service_id: str, default_port: int, 
                           fallback_ports: List[int]) -> Tuple[Optional[int], bool]:
        """
        查找可用端口
        
        Args:
            service_id: 服务标识
            default_port: 默认端口
            fallback_ports: 备用端口列表
            
        Returns:
            Tuple[Optional[int], bool]: (可用端口, 是否切换)
        """
        if self.is_port_available(default_port):
            return default_port, False
        
        self.logger.log(service_id, "WARN", 
                       f"默认端口 {default_port} 已被占用，尝试备用端口...")
        
        for fallback_port in fallback_ports:
            if self.is_port_available(fallback_port):
                self.logger.log(service_id, "INFO", 
                               f"找到可用备用端口: {fallback_port}")
                return fallback_port, True
        
        self.logger.log(service_id, "ERROR", 
                       f"所有备用端口均不可用: {fallback_ports}")
        return None, True
    
    def record_port_change(self, service_id: str, service_name: str,
                          original_port: int, new_port: int, reason: str = "端口冲突"):
        """
        记录端口变更
        
        Args:
            service_id: 服务标识
            service_name: 服务名称
            original_port: 原端口
            new_port: 新端口
            reason: 变更原因
        """
        record = PortChangeRecord(
            service_id=service_id,
            service_name=service_name,
            original_port=original_port,
            new_port=new_port,
            change_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            reason=reason
        )
        
        with self._lock:
            self.port_changes.append(record)
        
        self.logger.log("PORT_MANAGER", "INFO",
                       f"端口变更: {service_name} {original_port} -> {new_port}")
    
    def get_port_change_summary(self) -> str:
        """
        获取端口变更摘要
        
        Returns:
            str: 变更摘要文本
        """
        if not self.port_changes:
            return ""
        
        lines = ["端口变更记录:"]
        for change in self.port_changes:
            lines.append(f"  - {change.service_name}: "
                        f"{change.original_port} -> {change.new_port} "
                        f"[{change.change_time}]")
        return '\n'.join(lines)


# ============================================================================
# 健康检查器
# ============================================================================

class HealthChecker:
    """
    服务健康检查器
    
    功能:
        - 检查服务是否正常运行
        - 支持重试机制
    """
    
    def __init__(self, logger: ServiceLogger):
        """
        初始化健康检查器
        
        Args:
            logger: 日志记录器实例
        """
        self.logger = logger
        self._session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """创建带重试机制的请求会话"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def check_health(self, service_id: str, port: int, health_path: str,
                    timeout: int = HEALTH_CHECK_TIMEOUT) -> bool:
        """
        检查服务健康状态
        
        Args:
            service_id: 服务标识
            port: 服务端口
            health_path: 健康检查路径
            timeout: 超时时间(秒)
            
        Returns:
            bool: 服务是否健康
        """
        health_url = f"http://localhost:{port}{health_path}"
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self._session.get(health_url, timeout=3)
                if response.status_code in [200, 304]:
                    self.logger.log(service_id, "INFO", 
                                   f"健康检查通过: {health_url}")
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(HEALTH_CHECK_INTERVAL)
        
        self.logger.log(service_id, "WARN", 
                       f"健康检查超时 ({timeout}秒): {health_url}")
        return False


# ============================================================================
# 服务启动器
# ============================================================================

class ServiceLauncher:
    """
    服务启动器
    
    功能:
        - 构建启动命令
        - 启动服务进程
        - 管理进程输出
    """
    
    def __init__(self, logger: ServiceLogger):
        """
        初始化服务启动器
        
        Args:
            logger: 日志记录器实例
        """
        self.logger = logger
    
    def build_command(self, service_id: str, config: dict, port: int) -> Tuple[Optional[List[str]], Path, bool]:
        """
        构建服务启动命令
        
        Args:
            service_id: 服务标识
            config: 服务配置
            port: 服务端口
            
        Returns:
            Tuple[Optional[List[str]], Path, bool]: (命令列表, 工作目录, 是否使用shell)
        """
        cwd = config['cwd']
        
        if service_id == 'frontend':
            if sys.platform == 'win32':
                cmd = f'npm run dev -- --port {port}'
                return cmd, cwd, True
            else:
                cmd = ["npm", "run", "dev", "--", "--port", str(port)]
                return cmd, cwd, False
        
        if config.get('python') and config.get('script_template'):
            script = config['script_template']
            if '{port}' in script:
                script = script.format(port=port)
            
            import shlex
            if script.startswith('-m'):
                cmd = [str(config['python'])] + shlex.split(script)
            else:
                cmd = [str(config['python'])] + shlex.split(script)
            
            return cmd, cwd, False
        
        return None, cwd, False
    
    def start_service(self, service_id: str, config: dict, port: int, dev_mode: bool = False) -> Optional[subprocess.Popen]:
        """
        启动服务
        
        Args:
            service_id: 服务标识
            config: 服务配置
            port: 服务端口
            dev_mode: 是否为开发模式
            
        Returns:
            Optional[subprocess.Popen]: 进程对象或None
        """
        cmd, cwd, use_shell = self.build_command(service_id, config, port)
        
        if not cmd:
            self.logger.log(service_id, "ERROR", "无法构建启动命令")
            return None
        
        if isinstance(cmd, list):
            cmd_str = ' '.join(cmd)
        else:
            cmd_str = cmd
        self.logger.log(service_id, "INFO", f"启动命令: {cmd_str}")
        self.logger.log(service_id, "INFO", f"工作目录: {cwd}")
        self.logger.log(service_id, "INFO", f"使用端口: {port}")
        
        try:
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            env['PYTHONIOENCODING'] = 'utf-8'
            
            if dev_mode:
                env['DEV_MODE'] = 'true'
                env['DISABLE_AUTH'] = 'true'
            
            env['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
            
            process = subprocess.Popen(
                cmd,
                cwd=str(cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                shell=use_shell,
                env=env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            
            stdout_thread = threading.Thread(
                target=self._read_output,
                args=(service_id, process, process.stdout, "STDOUT"),
                daemon=True
            )
            stdout_thread.start()
            
            stderr_thread = threading.Thread(
                target=self._read_output,
                args=(service_id, process, process.stderr, "STDERR"),
                daemon=True
            )
            stderr_thread.start()
            
            return process
        
        except Exception as e:
            self.logger.log(service_id, "ERROR", f"启动失败: {str(e)}")
            return None
    
    def _read_output(self, service_id: str, process: subprocess.Popen, pipe, pipe_name: str):
        """
        读取进程输出
        
        Args:
            service_id: 服务标识
            process: 进程对象
            pipe: 输出管道 (stdout 或 stderr)
            pipe_name: 管道名称
        """
        service_name = SERVICES_CONFIG.get(service_id, {}).get('name', service_id)
        prefix = f"[{service_name}]"
        
        while not shutdown_event.is_set():
            try:
                line = pipe.readline()
                if line:
                    line = line.rstrip('\n\r')
                    if line.strip():
                        self.logger.log_service_output(service_id, line + '\n')
                        print(f"{prefix} {line}")
                        sys.stdout.flush()
                elif process.poll() is not None:
                    break
            except Exception as e:
                break


# ============================================================================
# 主启动器
# ============================================================================

class StartupManager:
    """
    启动管理器
    
    功能:
        - 协调所有服务的启动
        - 管理端口冲突
        - 执行健康检查
        - 显示启动状态
    """
    
    def __init__(self, dev_mode: bool = False, no_frontend: bool = False, no_rag: bool = False):
        """初始化启动管理器
        
        Args:
            dev_mode: 开发模式，禁用认证
            no_frontend: 不启动前端
            no_rag: 不启动RAG服务
        """
        self.dev_mode = dev_mode
        self.no_frontend = no_frontend
        self.no_rag = no_rag
        
        if self.no_frontend:
            SERVICES_CONFIG['frontend']['enabled'] = False
        if self.no_rag:
            SERVICES_CONFIG['rag']['enabled'] = False
        
        self.logger = ServiceLogger(LOG_DIR)
        self.port_manager = PortManager(self.logger)
        self.health_checker = HealthChecker(self.logger)
        self.launcher = ServiceLauncher(self.logger)
        self.console = Console() if RICH_AVAILABLE else None
        self.service_statuses: Dict[str, ServiceStatus] = {}
    
    def print_banner(self):
        """打印启动横幅"""
        banner = """
    ╔════════════════════════════════════════════════════════════╗
    ║          综测计算助手 - 服务启动脚本 v5.0                  ║
    ║     多进程并发启动 | 端口冲突自动处理 | 智能健康检查        ║
    ╚════════════════════════════════════════════════════════════╝
    """
        if RICH_AVAILABLE and self.console:
            self.console.print(Panel(banner, style="bold blue"))
        else:
            print(banner)
        
        if self.dev_mode:
            dev_banner = """
    ╔════════════════════════════════════════════════════════════╗
    ║  ⚠️  开发测试模式已启用 - 认证已禁用  ⚠️                   ║
    ║  请勿在生产环境中使用此模式！                              ║
    ╚════════════════════════════════════════════════════════════╝
    """
            if RICH_AVAILABLE and self.console:
                self.console.print(Panel(dev_banner, style="bold yellow on red"))
            else:
                print(dev_banner)
        
        if self.no_frontend:
            print("\n  [提示] 前端服务已禁用 (--no-frontend)")
        if self.no_rag:
            print("  [提示] RAG服务已禁用 (--no-rag)")
    
    def check_environment(self) -> bool:
        """
        检查运行环境
        
        Returns:
            bool: 环境检查是否通过
        """
        print("\n[1/5] 检查运行环境...")
        
        all_ok = True
        
        if VENV_PYTHON.exists():
            print(f"  ✓ Visual Model 虚拟环境: {VENV_PYTHON}")
            self.logger.log("SYSTEM", "INFO", f"Visual Model 虚拟环境检查通过")
        else:
            print(f"  ✗ Visual Model 虚拟环境不存在: {VENV_PYTHON}")
            self.logger.log("SYSTEM", "ERROR", f"Visual Model 虚拟环境不存在")
            all_ok = False
        
        if CONDA_PYTHON.exists():
            print(f"  ✓ RAG Conda 环境: {CONDA_PYTHON}")
            self.logger.log("SYSTEM", "INFO", f"RAG Conda 环境检查通过")
        else:
            print(f"  ⚠ RAG Conda 环境不存在，将跳过 RAG 服务")
            self.logger.log("SYSTEM", "WARN", f"RAG Conda 环境不存在，跳过 RAG 服务")
            SERVICES_CONFIG['rag']['enabled'] = False
        
        if (FRONTEND_DIR / "node_modules").exists():
            print(f"  ✓ 前端依赖已安装")
            self.logger.log("SYSTEM", "INFO", "前端依赖检查通过")
        else:
            print(f"  ⚠ 前端依赖未安装，启动时将自动安装")
            self.logger.log("SYSTEM", "WARN", "前端依赖未安装")
        
        if not all_ok:
            print("\n[错误] 必需的运行环境不满足！")
            print("请先运行: python manage.py venv")
            return False
        
        return True
    
    def start_service(self, service_id: str, config: dict) -> Optional[ServiceStatus]:
        """
        启动单个服务
        
        Args:
            service_id: 服务标识
            config: 服务配置
            
        Returns:
            Optional[ServiceStatus]: 服务状态或None
        """
        if not config.get('enabled', True):
            return None
        
        service_name = config['name']
        default_port = config['default_port']
        fallback_ports = config.get('fallback_ports', [])
        health_path = config.get('health_path', '/health')
        
        port, port_changed = self.port_manager.find_available_port(
            service_id, default_port, fallback_ports
        )
        
        if port is None:
            self._print_port_error(service_name, default_port, fallback_ports)
            return None
        
        if port_changed:
            self.port_manager.record_port_change(
                service_id, service_name, default_port, port
            )
        
        process = self.launcher.start_service(service_id, config, port, self.dev_mode)
        
        if process is None:
            return None
        
        health_ok = self.health_checker.check_health(
            service_id, port, health_path
        )
        
        status = ServiceStatus(
            service_id=service_id,
            name=service_name,
            port=port,
            status="运行中" if health_ok else "启动中",
            url=f"http://localhost:{port}",
            health_url=f"http://localhost:{port}{health_path}",
            process=process,
            start_time=datetime.now(),
            port_changed=port_changed
        )
        
        return status
    
    def _print_port_error(self, service_name: str, default_port: int, fallback_ports: List[int]):
        """打印端口错误信息"""
        error_msg = f"""
[错误] {service_name} 无法找到可用端口！
  - 默认端口: {default_port} (已被占用)
  - 备用端口: {fallback_ports} (均已被占用)

解决方案:
  1. 检查并关闭占用端口的程序:
     Windows: netstat -ano | findstr ":{default_port}"
     然后使用: taskkill /F /PID <进程ID>
  2. 或手动修改配置使用其他端口
"""
        if RICH_AVAILABLE and self.console:
            self.console.print(Panel(error_msg, title=f"[red]{service_name} 启动失败[/red]", style="red"))
        else:
            print(error_msg)
    
    def start_all_services(self) -> Dict[str, ServiceStatus]:
        """
        并发启动所有服务
        
        Returns:
            Dict[str, ServiceStatus]: 服务状态字典
        """
        print("\n[2/5] 并发启动服务...")
        
        enabled_services = [
            (sid, cfg) for sid, cfg in SERVICES_CONFIG.items() 
            if cfg.get('enabled', True)
        ]
        
        sorted_services = sorted(enabled_services, key=lambda x: x[1]['priority'])
        
        results = {}
        
        if RICH_AVAILABLE and self.console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                console=self.console
            ) as progress:
                task = progress.add_task("[cyan]启动服务中...", total=len(sorted_services))
                
                with ThreadPoolExecutor(max_workers=3) as executor:
                    future_to_service = {
                        executor.submit(self.start_service, sid, cfg): (sid, cfg)
                        for sid, cfg in sorted_services
                    }
                    
                    for future in as_completed(future_to_service):
                        sid, cfg = future_to_service[future]
                        try:
                            status = future.result()
                            if status:
                                results[sid] = status
                                processes[sid] = status.process
                                service_ports[sid] = status.port
                                
                                port_info = f"(端口 {status.port})"
                                if status.port_changed:
                                    port_info = f"(端口 {status.port} - 已切换)"
                                
                                self.console.print(f"  [green]✓[/green] {cfg['name']} 启动成功 {port_info}")
                            else:
                                self.console.print(f"  [red]✗[/red] {cfg['name']} 启动失败")
                        except Exception as e:
                            self.console.print(f"  [red]✗[/red] {cfg['name']} 启动异常: {e}")
                        
                        progress.advance(task)
        else:
            with ThreadPoolExecutor(max_workers=3) as executor:
                future_to_service = {
                    executor.submit(self.start_service, sid, cfg): (sid, cfg)
                    for sid, cfg in sorted_services
                }
                
                for future in as_completed(future_to_service):
                    sid, cfg = future_to_service[future]
                    try:
                        status = future.result()
                        if status:
                            results[sid] = status
                            processes[sid] = status.process
                            service_ports[sid] = status.port
                            print(f"  ✓ {cfg['name']} 启动成功 (端口 {status.port})")
                        else:
                            print(f"  ✗ {cfg['name']} 启动失败")
                    except Exception as e:
                        print(f"  ✗ {cfg['name']} 启动异常: {e}")
        
        return results
    
    def print_service_status(self, statuses: Dict[str, ServiceStatus]):
        """
        打印服务状态
        
        Args:
            statuses: 服务状态字典
        """
        print("\n[3/5] 服务状态汇总...")
        
        if RICH_AVAILABLE and self.console:
            table = Table(title="服务状态", show_header=True, header_style="bold cyan")
            table.add_column("服务名称", style="cyan", width=20)
            table.add_column("端口", style="yellow", width=12)
            table.add_column("状态", style="green", width=10)
            table.add_column("访问地址", style="blue", width=30)
            
            for sid, status in statuses.items():
                port_str = str(status.port)
                if status.port_changed:
                    port_str += " (已切换)"
                
                status_text = "运行中" if status.process and status.process.poll() is None else "已停止"
                status_style = "green" if status_text == "运行中" else "red"
                
                table.add_row(
                    status.name,
                    port_str,
                    f"[{status_style}]{status_text}[/{status_style}]",
                    status.url
                )
            
            self.console.print(table)
            
            if self.port_manager.port_changes:
                self.console.print(f"\n[yellow]{self.port_manager.get_port_change_summary()}[/yellow]")
        else:
            print("\n" + "="*70)
            print("服务状态")
            print("="*70)
            for sid, status in statuses.items():
                port_str = str(status.port)
                if status.port_changed:
                    port_str += " (已切换)"
                print(f"  {status.name}: 端口 {port_str}")
                print(f"    访问地址: {status.url}")
            
            if self.port_manager.port_changes:
                print(f"\n{self.port_manager.get_port_change_summary()}")
    
    def print_test_resources(self):
        """打印测试资源信息"""
        print("\n[4/5] 测试资源...")
        
        if RICH_AVAILABLE and self.console:
            accounts_table = Table(title="测试账号", show_header=True, header_style="bold magenta")
            accounts_table.add_column("角色", style="cyan", width=10)
            accounts_table.add_column("用户名", style="yellow", width=15)
            accounts_table.add_column("密码", style="green", width=15)
            accounts_table.add_column("权限说明", style="white", width=25)
            
            for acc in TEST_ACCOUNTS:
                accounts_table.add_row(
                    acc["role"],
                    acc["username"],
                    acc["password"],
                    acc["description"]
                )
            
            self.console.print(accounts_table)
            
            data_table = Table(title="测试数据", show_header=True, header_style="bold magenta")
            data_table.add_column("数据类型", style="cyan", width=15)
            data_table.add_column("位置", style="yellow", width=40)
            
            for data_type, location in TEST_DATA_INFO.items():
                data_table.add_row(data_type, location)
            
            self.console.print(data_table)
        else:
            print("\n测试账号:")
            for acc in TEST_ACCOUNTS:
                print(f"  - {acc['role']}: {acc['username']} / {acc['password']}")
            
            print("\n测试数据:")
            for data_type, location in TEST_DATA_INFO.items():
                print(f"  - {data_type}: {location}")
    
    def print_proxy_info(self, statuses: Dict[str, ServiceStatus]):
        """
        打印代理配置信息
        
        Args:
            statuses: 服务状态字典
        """
        print("\n[5/5] 前端代理配置...")
        
        if RICH_AVAILABLE and self.console:
            proxy_table = Table(title="前端代理配置 (vite.config.js)", show_header=True)
            proxy_table.add_column("代理路径", style="cyan", width=15)
            proxy_table.add_column("目标地址", style="yellow", width=25)
            proxy_table.add_column("状态", style="green", width=15)
            
            for sid, status in statuses.items():
                config = SERVICES_CONFIG.get(sid, {})
                proxy_prefix = config.get('proxy_prefix')
                
                if proxy_prefix:
                    target = f"http://localhost:{status.port}"
                    match = "✓ 匹配" if status.port == config.get('default_port') else "⚠ 需更新"
                    proxy_table.add_row(proxy_prefix, target, match)
            
            self.console.print(proxy_table)
            
            port_changes = [s for s in statuses.values() if s.port_changed]
            if port_changes:
                self.console.print("\n[yellow]⚠ 检测到端口变更，前端代理配置可能需要更新！[/yellow]")
                self.console.print("[yellow]  请检查 vite.config.js 中的代理目标地址[/yellow]")
        else:
            print("\n前端代理配置:")
            for sid, status in statuses.items():
                config = SERVICES_CONFIG.get(sid, {})
                proxy_prefix = config.get('proxy_prefix')
                
                if proxy_prefix:
                    target = f"http://localhost:{status.port}"
                    print(f"  {proxy_prefix} -> {target}")
            
            port_changes = [s for s in statuses.values() if s.port_changed]
            if port_changes:
                print("\n⚠ 检测到端口变更，前端代理配置可能需要更新！")
    
    def monitor_logs(self):
        """等待服务运行"""
        print("\n服务已启动，日志实时显示中 (按 Ctrl+C 停止所有服务)...")
        print("="*70)
        
        while not shutdown_event.is_set():
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break
    
    def stop_all_services(self):
        """停止所有服务"""
        print("\n正在停止所有服务...")
        self.logger.log("SYSTEM", "INFO", "开始停止所有服务")
        
        for sid, process in processes.items():
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                    print(f"  ✓ {SERVICES_CONFIG[sid]['name']} 已停止")
                    self.logger.log(sid, "INFO", "服务已停止")
                except subprocess.TimeoutExpired:
                    process.kill()
                    print(f"  ✓ {SERVICES_CONFIG[sid]['name']} 已强制停止")
                    self.logger.log(sid, "WARN", "服务被强制停止")
                except Exception as e:
                    print(f"  ✗ 停止 {SERVICES_CONFIG[sid]['name']} 时出错: {e}")
                    self.logger.log(sid, "ERROR", f"停止服务时出错: {e}")
    
    def run(self):
        """运行启动流程"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.print_banner()
        
        self.logger.log("SYSTEM", "INFO", "服务启动脚本开始执行 (v5.0)")
        
        if not self.check_environment():
            sys.exit(1)
        
        statuses = self.start_all_services()
        
        if not statuses:
            print("\n[错误] 没有服务启动成功！")
            self.logger.log("SYSTEM", "ERROR", "没有服务启动成功")
            sys.exit(1)
        
        self.print_service_status(statuses)
        self.print_test_resources()
        self.print_proxy_info(statuses)
        
        print(f"\n日志文件位置: {LOG_DIR}")
        print("\n按 Ctrl+C 停止所有服务并退出")
        print("="*70)
        
        self.logger.log("SYSTEM", "INFO", f"所有服务启动完成，共 {len(statuses)} 个服务")
        
        try:
            self.monitor_logs()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_all_services()
            print("\n所有服务已停止，再见！")
            self.logger.log("SYSTEM", "INFO", "服务启动脚本执行结束")
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        shutdown_event.set()
        print("\n\n收到退出信号，正在停止服务...")
        self.stop_all_services()
        sys.exit(0)


# ============================================================================
# 主入口
# ============================================================================

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='综测计算助手 - 服务启动脚本 v5.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  python start.py                  # 正常启动所有服务
  python start.py --dev            # 开发测试模式（禁用认证）
  python start.py --no-frontend    # 不启动前端
  python start.py --no-rag         # 不启动RAG服务
  python start.py --dev --no-rag   # 开发模式且不启动RAG
        '''
    )
    parser.add_argument(
        '--dev',
        action='store_true',
        help='开发测试模式（禁用认证，设置 DEV_MODE=true 和 DISABLE_AUTH=true）'
    )
    parser.add_argument(
        '--no-frontend',
        action='store_true',
        help='不启动前端服务'
    )
    parser.add_argument(
        '--no-rag',
        action='store_true',
        help='不启动RAG服务'
    )
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    manager = StartupManager(
        dev_mode=args.dev,
        no_frontend=args.no_frontend,
        no_rag=args.no_rag
    )
    manager.run()


if __name__ == "__main__":
    main()
