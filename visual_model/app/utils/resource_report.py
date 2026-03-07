#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源报告生成器

生成资源消耗的可视化报告，支持JSON和HTML格式。
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from app.core.logger import logger
from app.core.resource_monitor import get_resource_monitor


class ResourceReportGenerator:
    """资源报告生成器
    
    功能:
    - 生成资源消耗报告
    - 支持JSON/HTML格式
    - 包含图表可视化
    - 导出测试报告
    """
    
    def __init__(self):
        """初始化报告生成器"""
        self.monitor = get_resource_monitor()
    
    def generate_json_report(self, 
                            include_history: bool = True,
                            include_alerts: bool = True) -> Dict[str, Any]:
        """生成JSON格式报告
        
        Args:
            include_history: 是否包含历史记录
            include_alerts: 是否包含告警记录
            
        Returns:
            报告数据字典
        """
        report = {
            "report_type": "resource_usage",
            "generated_at": datetime.now().isoformat(),
            "summary": self.monitor.get_summary(),
            "current_status": self.monitor.get_current_status()
        }
        
        if include_history:
            report["history"] = self.monitor.get_history(limit=500)
        
        if include_alerts:
            report["alerts"] = self.monitor.get_alerts(limit=100)
        
        return report
    
    def generate_html_report(self,
                            include_charts: bool = True,
                            include_history: bool = True) -> str:
        """生成HTML格式报告
        
        Args:
            include_charts: 是否包含图表
            include_history: 是否包含历史记录
            
        Returns:
            HTML字符串
        """
        summary = self.monitor.get_summary()
        current = self.monitor.get_current_status()
        history = self.monitor.get_history(limit=200) if include_history else []
        alerts = self.monitor.get_alerts(limit=50)
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCR服务资源使用报告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            color: #1a1a2e;
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .header .subtitle {{
            color: #666;
            font-size: 14px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }}
        .stat-card .label {{
            color: #888;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}
        .stat-card .value {{
            font-size: 32px;
            font-weight: 700;
            color: #1a1a2e;
        }}
        .stat-card .unit {{
            font-size: 14px;
            color: #888;
            margin-left: 4px;
        }}
        .stat-card.memory .value {{ color: #4CAF50; }}
        .stat-card.cpu .value {{ color: #2196F3; }}
        .stat-card.thread .value {{ color: #FF9800; }}
        .stat-card.ocr .value {{ color: #9C27B0; }}
        .section {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }}
        .section h2 {{
            color: #1a1a2e;
            font-size: 18px;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid #f0f0f0;
        }}
        .chart-container {{
            width: 100%;
            height: 300px;
            position: relative;
        }}
        .bar-chart {{
            display: flex;
            align-items: flex-end;
            height: 200px;
            padding: 20px 0;
            gap: 8px;
        }}
        .bar {{
            flex: 1;
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            border-radius: 4px 4px 0 0;
            min-width: 20px;
            position: relative;
            transition: height 0.3s ease;
        }}
        .bar:hover {{
            opacity: 0.8;
        }}
        .bar-label {{
            position: absolute;
            bottom: -25px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 10px;
            color: #888;
            white-space: nowrap;
        }}
        .alerts-list {{
            max-height: 300px;
            overflow-y: auto;
        }}
        .alert-item {{
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .alert-item.warning {{
            background: #fff3e0;
            border-left: 4px solid #ff9800;
        }}
        .alert-item.error {{
            background: #ffebee;
            border-left: 4px solid #f44336;
        }}
        .alert-icon {{
            font-size: 20px;
        }}
        .alert-content {{
            flex: 1;
        }}
        .alert-type {{
            font-weight: 600;
            color: #333;
        }}
        .alert-message {{
            font-size: 13px;
            color: #666;
            margin-top: 4px;
        }}
        .alert-time {{
            font-size: 11px;
            color: #999;
        }}
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 8px;
        }}
        .progress-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }}
        .progress-fill.memory {{ background: linear-gradient(90deg, #4CAF50, #8BC34A); }}
        .progress-fill.cpu {{ background: linear-gradient(90deg, #2196F3, #03A9F4); }}
        .progress-fill.thread {{ background: linear-gradient(90deg, #FF9800, #FFC107); }}
        .table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .table th, .table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #f0f0f0;
        }}
        .table th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
            font-size: 12px;
            text-transform: uppercase;
        }}
        .table td {{
            color: #666;
            font-size: 13px;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: rgba(255,255,255,0.8);
            font-size: 12px;
        }}
        .no-data {{
            text-align: center;
            padding: 40px;
            color: #999;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 OCR服务资源使用报告</h1>
            <p class="subtitle">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card memory">
                <div class="label">当前内存使用</div>
                <div class="value">{current['current']['memory_rss_mb']:.1f}<span class="unit">MB</span></div>
                <div class="progress-bar">
                    <div class="progress-fill memory" style="width: {min(current['current']['memory_percent'], 100)}%"></div>
                </div>
            </div>
            <div class="stat-card cpu">
                <div class="label">CPU使用率</div>
                <div class="value">{current['current']['cpu_percent']:.1f}<span class="unit">%</span></div>
                <div class="progress-bar">
                    <div class="progress-fill cpu" style="width: {min(current['current']['cpu_percent'], 100)}%"></div>
                </div>
            </div>
            <div class="stat-card thread">
                <div class="label">线程数量</div>
                <div class="value">{current['current']['thread_count']}<span class="unit">个</span></div>
            </div>
            <div class="stat-card ocr">
                <div class="label">OCR操作次数</div>
                <div class="value">{current['ocr_stats']['operation_count']}<span class="unit">次</span></div>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 资源使用摘要</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>指标</th>
                        <th>最小值</th>
                        <th>最大值</th>
                        <th>平均值</th>
                        <th>当前值</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>内存使用率 (%)</td>
                        <td>{summary.get('memory', {}).get('min_percent', 'N/A')}</td>
                        <td>{summary.get('memory', {}).get('max_percent', 'N/A')}</td>
                        <td>{summary.get('memory', {}).get('avg_percent', 'N/A')}</td>
                        <td>{current['current']['memory_percent']:.2f}</td>
                    </tr>
                    <tr>
                        <td>CPU使用率 (%)</td>
                        <td>{summary.get('cpu', {}).get('min_percent', 'N/A')}</td>
                        <td>{summary.get('cpu', {}).get('max_percent', 'N/A')}</td>
                        <td>{summary.get('cpu', {}).get('avg_percent', 'N/A')}</td>
                        <td>{current['current']['cpu_percent']:.2f}</td>
                    </tr>
                    <tr>
                        <td>线程数量</td>
                        <td>{summary.get('threads', {}).get('min', 'N/A')}</td>
                        <td>{summary.get('threads', {}).get('max', 'N/A')}</td>
                        <td>-</td>
                        <td>{current['current']['thread_count']}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        {self._generate_history_chart_html(history) if include_history and history else ''}
        
        {self._generate_alerts_html(alerts)}
        
        <div class="footer">
            <p>OCR服务资源监控报告 | 运行时间: {current['uptime_seconds']:.0f}秒</p>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def _generate_history_chart_html(self, history: List[Dict[str, Any]]) -> str:
        """生成历史数据图表HTML"""
        if not history:
            return '<div class="section"><h2>📉 历史趋势</h2><div class="no-data">暂无历史数据</div></div>'
        
        max_memory = max(h['memory_percent'] for h in history) if history else 1
        max_memory = max(max_memory, 1)
        
        bars_html = ""
        for i, h in enumerate(history[-30:]):
            height = (h['memory_percent'] / max_memory) * 100
            time_label = h['timestamp'].split('T')[1][:8] if 'T' in h['timestamp'] else h['timestamp'][-8:]
            bars_html += f'<div class="bar" style="height: {height}%" title="内存: {h["memory_percent"]:.1f}%, CPU: {h["cpu_percent"]:.1f}%, 线程: {h["thread_count"]}"><span class="bar-label">{time_label}</span></div>'
        
        return f"""<div class="section">
            <h2>📉 内存使用趋势（最近30个采样点）</h2>
            <div class="bar-chart">
                {bars_html}
            </div>
        </div>"""
    
    def _generate_alerts_html(self, alerts: List[Dict[str, Any]]) -> str:
        """生成告警列表HTML"""
        if not alerts:
            return '<div class="section"><h2>⚠️ 告警记录</h2><div class="no-data">暂无告警记录</div></div>'
        
        alerts_html = ""
        for alert in alerts[-10:]:
            alert_class = "warning" if alert['alert_type'] in ['memory', 'thread'] else "error"
            icon = "⚠️" if alert_class == "warning" else "🔴"
            alerts_html += f"""<div class="alert-item {alert_class}">
                <span class="alert-icon">{icon}</span>
                <div class="alert-content">
                    <div class="alert-type">{alert['alert_type'].upper()} 告警</div>
                    <div class="alert-message">{alert['message']}</div>
                </div>
                <span class="alert-time">{alert['timestamp'].split('T')[1][:8] if 'T' in alert['timestamp'] else alert['timestamp'][-8:]}</span>
            </div>"""
        
        return f"""<div class="section">
            <h2>⚠️ 告警记录（最近10条）</h2>
            <div class="alerts-list">
                {alerts_html}
            </div>
        </div>"""
    
    def save_report(self, 
                   output_path: str,
                   format: str = "html",
                   include_history: bool = True) -> bool:
        """保存报告到文件
        
        Args:
            output_path: 输出文件路径
            format: 报告格式 (json/html)
            include_history: 是否包含历史记录
            
        Returns:
            是否保存成功
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == "json":
                report = self.generate_json_report(include_history=include_history)
                content = json.dumps(report, ensure_ascii=False, indent=2)
            else:
                content = self.generate_html_report(include_history=include_history)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"资源报告已保存: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存资源报告失败: {e}", exc_info=True)
            return False


def generate_resource_report(output_path: str, format: str = "html") -> bool:
    """生成资源报告的便捷函数
    
    Args:
        output_path: 输出文件路径
        format: 报告格式 (json/html)
        
    Returns:
        是否生成成功
    """
    generator = ResourceReportGenerator()
    return generator.save_report(output_path, format=format)
