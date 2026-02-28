#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证API测试模块
测试用户登录、注册、密码重置等功能
"""
import pytest
from httpx import AsyncClient

from conftest_new import TEST_USERS, API_PREFIX


@pytest.mark.asyncio
@pytest.mark.auth
class TestAuthAPI:
    """认证API测试类"""
    
    async def test_login_success(self, client: AsyncClient, test_result):
        """测试登录成功"""
        test_result.start()
        
        response = await client.post(f"{API_PREFIX}/auth/login", json={
            "username": TEST_USERS["admin"]["username"],
            "password": TEST_USERS["admin"]["password"]
        })
        
        assert response.status_code == 200, f"登录失败: {response.text}"
        data = response.json()
        assert "access_token" in data, "响应中缺少access_token"
        assert "expires_in" in data, "响应中缺少expires_in"
        
        test_result.add_result("test_login_success", True, "登录成功")
        test_result.end()
    
    async def test_login_invalid_password(self, client: AsyncClient, test_result):
        """测试密码错误登录"""
        test_result.start()
        
        response = await client.post(f"{API_PREFIX}/auth/login", json={
            "username": TEST_USERS["admin"]["username"],
            "password": "wrong_password"
        })
        
        assert response.status_code == 401, "密码错误应该返回401"
        
        test_result.add_result("test_login_invalid_password", True, "密码错误正确返回401")
        test_result.end()
    
    async def test_login_invalid_username(self, client: AsyncClient, test_result):
        """测试用户名不存在登录"""
        test_result.start()
        
        response = await client.post(f"{API_PREFIX}/auth/login", json={
            "username": "nonexistent_user",
            "password": "any_password"
        })
        
        assert response.status_code == 401, "用户名不存在应该返回401"
        
        test_result.add_result("test_login_invalid_username", True, "用户名不存在正确返回401")
        test_result.end()
    
    async def test_get_current_user_info(self, client: AsyncClient, admin_token: str, test_result):
        """测试获取当前用户信息"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.get(f"{API_PREFIX}/auth/me", headers=headers)
        
        assert response.status_code == 200, f"获取用户信息失败: {response.text}"
        data = response.json()
        assert "username" in data or "id" in data, "响应中缺少用户信息"
        
        test_result.add_result("test_get_current_user_info", True, "获取用户信息成功")
        test_result.end()
    
    async def test_get_current_user_without_token(self, client: AsyncClient, test_result):
        """测试无token获取用户信息"""
        test_result.start()
        
        response = await client.get(f"{API_PREFIX}/auth/me")
        
        assert response.status_code == 401, "无token应该返回401"
        
        test_result.add_result("test_get_current_user_without_token", True, "无token正确返回401")
        test_result.end()
    
    async def test_logout(self, client: AsyncClient, admin_token: str, test_result):
        """测试登出"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post(f"{API_PREFIX}/auth/logout", headers=headers)
        
        assert response.status_code == 200, f"登出失败: {response.text}"
        
        test_result.add_result("test_logout", True, "登出成功")
        test_result.end()


@pytest.mark.asyncio
@pytest.mark.auth
class TestPasswordReset:
    """密码重置测试类"""
    
    async def test_request_password_reset(self, client: AsyncClient, test_result):
        """测试请求密码重置"""
        test_result.start()
        
        response = await client.post(f"{API_PREFIX}/auth/password/reset-request", json={
            "email": TEST_USERS["student"]["email"]
        })
        
        assert response.status_code in [200, 503], f"请求密码重置失败: {response.text}"
        
        test_result.add_result("test_request_password_reset", True, "请求密码重置成功")
        test_result.end()
    
    async def test_request_password_reset_invalid_email(self, client: AsyncClient, test_result):
        """测试无效邮箱请求密码重置"""
        test_result.start()
        
        response = await client.post(f"{API_PREFIX}/auth/password/reset-request", json={
            "email": "nonexistent@test.com"
        })
        
        assert response.status_code in [200, 400, 404], f"无效邮箱响应异常: {response.text}"
        
        test_result.add_result("test_request_password_reset_invalid_email", True, "无效邮箱处理正确")
        test_result.end()
