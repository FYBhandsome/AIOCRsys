#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综测计算助手 - 集成测试
测试所有API接口功能
"""
import pytest
import asyncio
import os
import sys
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/visual_model")

from app.core.app_factory import create_app
from config import settings

API_PREFIX = settings.API_V1_STR


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def app():
    """创建测试应用实例"""
    test_app = create_app()
    yield test_app


@pytest.fixture
async def client(app):
    """创建异步HTTP测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def admin_token(client):
    """获取管理员令牌"""
    response = await client.post(f"{API_PREFIX}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token", "")
    return ""


@pytest.fixture
async def teacher_token(client):
    """获取教师令牌"""
    response = await client.post(f"{API_PREFIX}/auth/login", json={
        "username": "teacher",
        "password": "teacher123"
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token", "")
    return ""


@pytest.fixture
async def student_token(client):
    """获取学生令牌"""
    response = await client.post(f"{API_PREFIX}/auth/login", json={
        "username": "student_202300502128",
        "password": "student123"
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token", "")
    return ""


class TestHealthCheck:
    """健康检查测试"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """测试健康检查端点"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestAuthAPI:
    """认证API测试"""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client):
        """测试登录成功"""
        response = await client.post(f"{API_PREFIX}/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client):
        """测试登录失败 - 错误密码"""
        response = await client.post(f"{API_PREFIX}/auth/login", json={
            "username": "admin",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client):
        """测试登录失败 - 不存在的用户"""
        response = await client.post(f"{API_PREFIX}/auth/login", json={
            "username": "nonexistent",
            "password": "password123"
        })
        assert response.status_code == 401
        
    @pytest.mark.asyncio
    async def test_get_current_user(self, client, admin_token):
        """测试获取当前用户信息"""
        if not admin_token:
            pytest.skip("无法获取管理员令牌")
            
        response = await client.get(
            f"{API_PREFIX}/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "role" in data
        
    @pytest.mark.asyncio
    async def test_logout(self, client, admin_token):
        """测试登出"""
        if not admin_token:
            pytest.skip("无法获取管理员令牌")
            
        response = await client.post(
            f"{API_PREFIX}/auth/logout",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200


class TestTeacherAPI:
    """教师API测试"""
    
    @pytest.mark.asyncio
    async def test_get_students(self, client, admin_token):
        """测试获取学生列表"""
        if not admin_token:
            pytest.skip("无法获取管理员令牌")
            
        response = await client.get(
            f"{API_PREFIX}/teacher/students",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [200, 403]
        
    @pytest.mark.asyncio
    async def test_get_classes(self, client, admin_token):
        """测试获取班级列表"""
        if not admin_token:
            pytest.skip("无法获取管理员令牌")
            
        response = await client.get(
            f"{API_PREFIX}/teacher/classes",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [200, 403]


class TestStudentAPI:
    """学生API测试"""
    
    @pytest.mark.asyncio
    async def test_get_scores_summary(self, client, student_token):
        """测试获取成绩摘要"""
        if not student_token:
            pytest.skip("无法获取学生令牌")
            
        response = await client.get(
            f"{API_PREFIX}/student/scores/summary",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code in [200, 403, 404]
        
    @pytest.mark.asyncio
    async def test_get_upload_history(self, client, student_token):
        """测试获取上传历史"""
        if not student_token:
            pytest.skip("无法获取学生令牌")
            
        response = await client.get(
            f"{API_PREFIX}/student/uploads",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code in [200, 403, 404]


class TestAdminAPI:
    """管理员API测试"""
    
    @pytest.mark.asyncio
    async def test_get_users(self, client, admin_token):
        """测试获取用户列表"""
        if not admin_token:
            pytest.skip("无法获取管理员令牌")
            
        response = await client.get(
            f"{API_PREFIX}/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [200, 403]
        
    @pytest.mark.asyncio
    async def test_get_settings(self, client, admin_token):
        """测试获取系统设置"""
        if not admin_token:
            pytest.skip("无法获取管理员令牌")
            
        response = await client.get(
            f"{API_PREFIX}/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [200, 403, 404]


class TestRoleBasedAccess:
    """基于角色的访问控制测试"""
    
    @pytest.mark.asyncio
    async def test_student_cannot_access_admin(self, client, student_token):
        """测试学生无法访问管理员接口"""
        if not student_token:
            pytest.skip("无法获取学生令牌")
            
        response = await client.get(
            f"{API_PREFIX}/admin/users",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 403
        
    @pytest.mark.asyncio
    async def test_teacher_cannot_access_admin_users(self, client, teacher_token):
        """测试教师无法访问管理员用户管理接口"""
        if not teacher_token:
            pytest.skip("无法获取教师令牌")
            
        response = await client.get(
            f"{API_PREFIX}/admin/users",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        assert response.status_code == 403


class TestErrorHandling:
    """错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_404_not_found(self, client):
        """测试404错误"""
        response = await client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        """测试未授权访问"""
        response = await client.get(f"{API_PREFIX}/auth/me")
        assert response.status_code == 401
        
    @pytest.mark.asyncio
    async def test_invalid_token(self, client):
        """测试无效令牌"""
        response = await client.get(
            f"{API_PREFIX}/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
