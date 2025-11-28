#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件发送服务 - 仅支持验证码方式的密码重置
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime

from app.core.logger import logger
from config import settings


class EmailService:
    """邮件发送服务类"""
    
    def __init__(
        self,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
    ):
        """初始化邮件服务
        
        Args:
            smtp_server: SMTP服务器地址
            smtp_port: SMTP端口
            smtp_username: SMTP用户名
            smtp_password: SMTP密码
            from_email: 发件人邮箱
        """
        self.smtp_server = smtp_server or getattr(settings, 'SMTP_SERVER', 'smtp.qq.com')
        self.smtp_port = smtp_port or getattr(settings, 'SMTP_PORT', 587)
        self.smtp_username = smtp_username or getattr(settings, 'SMTP_USERNAME', '')
        self.smtp_password = smtp_password or getattr(settings, 'SMTP_PASSWORD', '')
        self.from_email = from_email or getattr(settings, 'FROM_EMAIL', self.smtp_username)
        
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html: Optional[str] = None
    ) -> bool:
        """发送邮件
        
        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            body: 邮件正文（纯文本）
            html: 邮件正文（HTML格式，可选）
            
        Returns:
            bool: 发送成功返回True，否则False
        """
        try:
            # 创建邮件对象
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # 添加纯文本内容
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # 添加HTML内容
            if html:
                html_part = MIMEText(html, 'html', 'utf-8')
                msg.attach(html_part)
            
            # 连接SMTP服务器并发送
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # 启用TLS加密
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"邮件发送成功: {to_email} - {subject}")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {to_email} - {e}")
            return False
    
    
    async def send_verification_code_email(
        self,
        to_email: str,
        username: str,
        verification_code: str
    ) -> bool:
        """发送验证码邮件（用于密码重置）
        
        Args:
            to_email: 收件人邮箱
            username: 用户名
            verification_code: 6位验证码
            
        Returns:
            bool: 发送成功返回True，否则False
        """
        subject = "综测计算助手 - 密码重置验证码"
        
        body = f"""
        您好 {username}，
        
        您正在进行密码重置操作。
        
        您的验证码是：{verification_code}
        
        验证码有效期为2分钟，请尽快使用。
        
        如果这不是您本人的操作，请忽略此邮件。
        
        ---
        综测计算助手团队
        """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: white;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .code-box {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    text-align: center;
                    padding: 20px;
                    margin: 30px 0;
                    border-radius: 10px;
                    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                }}
                .warning {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    color: #666;
                    font-size: 12px;
                }}
                .highlight {{
                    color: #667eea;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 密码重置验证码</h1>
                </div>
                <div class="content">
                    <p>您好 <strong>{username}</strong>，</p>
                    <p>您正在进行密码重置操作。</p>
                    <p>请使用以下验证码完成验证：</p>
                    <div class="code-box">
                        {verification_code}
                    </div>
                    <p style="text-align: center; color: #999; font-size: 14px;">
                        验证码有效期为 <span class="highlight">2分钟</span>，请尽快使用
                    </p>
                    <div class="warning">
                        <strong>⚠️ 安全提示：</strong>
                        <ul>
                            <li>如果这不是您本人的操作，请立即忽略此邮件</li>
                            <li>请勿将验证码透露给他人</li>
                            <li>验证码仅用于本次密码重置</li>
                        </ul>
                    </div>
                </div>
                <div class="footer">
                    <p>综测计算助手团队</p>
                    <p>{datetime.now().strftime('%Y年%m月%d日 %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, body, html)


def generate_verification_code() -> str:
    """生成6位数字验证码
    
    Returns:
        str: 6位数字验证码
    """
    import random
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])


# 创建全局邮件服务实例
email_service = EmailService()

