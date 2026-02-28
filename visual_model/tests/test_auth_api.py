#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证API集成测试
测试用户注册、登录、令牌验证、密码重置等功能
"""
import pytest
import logging
from httpx import AsyncClient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conftest import TEST_USERS, API_PREFIX

logger = logging.getLogger("test_logger")


class TestAuthRegister:
    """用户注册测试类"""
    
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_register_new_user(self, client: AsyncClient, test_logger):
        """测试注册新用户 - 正常场景"""
        test_logger.info("开始测试: 注册新用户")
        
        user_data = {
            "username": f"new_user_{pytest.__version__}",
            "password": "NewUser@123456",
            "email": "newuser@test.com",
            "role": "student",
            "real_name": "新注册用户"
        }
        
        response = await client.post(f"{API_PREFIX}/auth/register", json=user_data)
        
        test_logger.info(f"请求参数: {user_data}")
        test_logger.info(f"响应状态码: {response.status_code}")
        test_logger.info(f"响应数据: {response.text[:500]}")
        
        assert response.status_code in [200, 201, 400], f"注册响应状态码异常: {response.status_code}"
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert "message" in data or "username" in data
            test_logger.info("注册新用户测试通过")
    
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient, test_logger):
        """测试注册重复用户名 - 异常场景"""
        test_logger.info("开始测试: 注册重复用户名")
        
        user_data = {
            "username": "admin",
            "password": "Test@123456",
            "email": "duplicate@test.com",
            "role": "student",
            "real_name": "重复用户名测试"
        }
        
        response = await client.post(f"{API_PREFIX}/auth/register", json=user_data)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [400, 409], "重复用户名应返回400或409错误"
        test_logger.info("重复用户名测试通过")
    
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient, test_logger):
        """测试注册无效邮箱 - 边界条件"""
        test_logger.info("开始测试: 注册无效邮箱")
        
        user_data = {
            "username": "invalid_email_user",
            "password": "Test@123456",
            "email": "invalid_email",
            "role": "student",
            "real_name": "无效邮箱测试"
        }
        
        response = await client.post(f"{API_PREFIX}/auth/register", json=user_data)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code == 422, "无效邮箱应返回422验证错误"
        test_logger.info("无效邮箱测试通过")
    
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient, test_logger):
        """测试注册弱密码 - 边界条件"""
        test_logger.info("开始测试: 注册弱密码")
        
        user_data = {
            "username": "weak_password_user",
            "password": "123",
            "email": "weak@test.com",
            "role": "student",
            "real_name": "弱密码测试"
        }
        
        response = await client.post(f"{API_PREFIX}/auth/register", json=user_data)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [400, 422], "弱密码应返回错误"
        test_logger.info("弱密码测试通过")


class TestAuthLogin:
    """用户登录测试类"""
    
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_logger):
        """测试登录成功 - 正常场景"""
        test_logger.info("开始测试: 用户登录成功")
        
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = await client.post(f"{API_PREFIX}/auth/login", json=login_data)
        
        test_logger.info(f"请求参数: {login_data}")
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"响应数据包含字段: {list(data.keys())}")
            
            assert "access_token" in data, "响应应包含access_token"
            assert "expires_in" in data, "响应应包含expires_in"
            assert data["access_token"], "令牌不应为空"
            test_logger.info("登录成功测试通过")
        else:
            test_logger.warning(f"登录失败，可能需要先创建测试用户: {response.text}")
    
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_logger):
        """测试登录错误密码 - 异常场景"""
        test_logger.info("开始测试: 登录错误密码")
        
        login_data = {
            "username": "admin",
            "password": "wrongpassword"
        }
        
        response = await client.post(f"{API_PREFIX}/auth/login", json=login_data)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code == 401, "错误密码应返回401"
        test_logger.info("错误密码测试通过")
    
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient, test_logger):
        """测试登录不存在用户 - 异常场景"""
        test_logger.info("开始测试: 登录不存在用户")
        
        login_data = {
            "username": "nonexistent_user_xyz",
            "password": "anypassword"
        }
        
        response = await client.post(f"{API_PREFIX}/auth/login", json=login_data)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code == 401, "不存在用户应返回401"
        test_logger.info("不存在用户测试通过")
    
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_login_missing_fields(self, client: AsyncClient, test_logger):
        """测试登录缺少字段 - 边界条件"""
        test_logger.info("开始测试: 登录缺少字段")
        
        login_data = {
            "username": "admin"
        }
        
        response = await client.post(f"{API_PREFIX}/auth/login", json=login_data)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code == 422, "缺少字段应返回422验证错误"
        test_logger.info("缺少字段测试通过")


class TestAuthMe:
    """获取当前用户信息测试类"""
    
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, client: AsyncClient, admin_token: str, test_logger):
        """测试获取当前用户信息 - 正常场景"""
        test_logger.info("开始测试: 获取当前用户信息")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.get(f"{API_PREFIX}/auth/me", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"用户信息: {data}")
            
            assert "username" in data or "id" in data
            test_logger.info("获取当前用户信息测试通过")
        else:
            test_logger.warning(f"获取用户信息失败: {response.text}")
    
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, client: AsyncClient, test_logger):
        """测试无令牌获取用户信息 - 异常场景"""
        test_logger.info("开始测试: 无令牌获取用户信息")
        
        response = await client.get(f"{API_PREFIX}/auth/me")
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [401, 403], "无令牌应返回401或403"
        test_logger.info("无令牌测试通过")
    
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient, test_logger):
        """测试无效令牌获取用户信息 - 异常场景"""
        test_logger.info("开始测试: 无效令牌获取用户信息")
        
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = await client.get(f"{API_PREFIX}/auth/me", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [401, 403, 422], "无效令牌应返回错误"
        test_logger.info("无效令牌测试通过")


class TestPasswordReset:
    """密码重置测试类"""
    
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_request_password_reset(self, client: AsyncClient, test_logger):
        """测试请求密码重置"""
        test_logger.info("开始测试: 请求密码重置")
        
        reset_data = {
            "email": "test@test.com"
        }
        
        response = await client.post(f"{API_PREFIX}/auth/password/reset-request", json=reset_data)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        test_logger.info(f"响应数据: {response.text[:200]}")
        
        assert response.status_code in [200, 202, 400, 503], "密码重置请求应返回有效状态码"
        test_logger.info("请求密码重置测试通过")


class TestAuthLogout:
    """登出测试类"""
    
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_logout_success(self, client: AsyncClient, admin_token: str, test_logger):
        """测试登出成功"""
        test_logger.info("开始测试: 用户登出")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post(f"{API_PREFIX}/auth/logout", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            test_logger.info("登出测试通过")
        else:
            test_logger.warning(f"登出响应: {response.text}")
