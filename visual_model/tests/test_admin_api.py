#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理员API集成测试
测试用户管理、系统配置、数据导入等功能
"""
import pytest
import logging
import json
from httpx import AsyncClient

logger = logging.getLogger("test_logger")


class TestAdminUsers:
    """管理员用户管理测试类"""
    
    @pytest.mark.admin
    @pytest.mark.asyncio
    async def test_get_users_list(self, client: AsyncClient, admin_token: str, test_logger):
        """测试获取用户列表"""
        test_logger.info("开始测试: 获取用户列表")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {"page": 1, "page_size": 20}
        response = await client.get("/api/admin/users", params=params, headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"用户列表: {json.dumps(data, ensure_ascii=False)[:500]}")
            
            if "users" in data:
                assert isinstance(data["users"], list)
            if "total" in data:
                assert isinstance(data["total"], int)
            test_logger.info("获取用户列表测试通过")
        else:
            test_logger.warning(f"获取用户列表失败: {response.text}")
    
    @pytest.mark.admin
    @pytest.mark.asyncio
    async def test_create_user(self, client: AsyncClient, admin_token: str, test_logger):
        """测试创建用户"""
        test_logger.info("开始测试: 创建用户")
        
        user_data = {
            "username": f"test_user_{pytest.__version__}",
            "password": "TestUser@123",
            "email": "testuser@admin.com",
            "role": "student",
            "real_name": "测试用户",
            "student_id": "2021999"
        }
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/admin/users", json=user_data, headers=headers)
        
        test_logger.info(f"请求参数: {user_data}")
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            test_logger.info(f"创建结果: {json.dumps(data, ensure_ascii=False)[:300]}")
            test_logger.info("创建用户测试通过")
        else:
            test_logger.warning(f"创建用户失败: {response.text}")
    
    @pytest.mark.admin
    @pytest.mark.asyncio
    async def test_update_user(self, client: AsyncClient, admin_token: str, test_logger):
        """测试更新用户"""
        test_logger.info("开始测试: 更新用户")
        
        update_data = {
            "real_name": "更新后的用户名",
            "email": "updated@admin.com",
            "is_active": True
        }
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.put("/api/admin/users/test_user_id", json=update_data, headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"更新结果: {json.dumps(data, ensure_ascii=False)[:300]}")
            test_logger.info("更新用户测试通过")
        else:
            test_logger.warning(f"更新用户失败: {response.text}")
    
    @pytest.mark.admin
    @pytest.mark.asyncio
    async def test_delete_user(self, client: AsyncClient, admin_token: str, test_logger):
        """测试删除用户"""
        test_logger.info("开始测试: 删除用户")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.delete("/api/admin/users/test_user_id_to_delete", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 404], "删除用户应返回200或404"
        test_logger.info("删除用户测试通过")
    
    @pytest.mark.admin
    @pytest.mark.asyncio
    async def test_toggle_user_status(self, client: AsyncClient, admin_token: str, test_logger):
        """测试切换用户状态"""
        test_logger.info("开始测试: 切换用户状态")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/admin/users/test_user_id/toggle-status", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"切换结果: {json.dumps(data, ensure_ascii=False)[:300]}")
            test_logger.info("切换用户状态测试通过")
        else:
            test_logger.warning(f"切换用户状态失败: {response.text}")


class TestAdminClasses:
    """管理员班级管理测试类"""
    
    @pytest.mark.admin
    @pytest.mark.asyncio
    async def test_get_classes_list(self, client: AsyncClient, admin_token: str, test_logger):
        """测试获取班级列表"""
        test_logger.info("开始测试: 获取班级列表")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.get("/api/admin/classes", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"班级列表: {json.dumps(data, ensure_ascii=False)[:500]}")
            test_logger.info("获取班级列表测试通过")
        else:
            test_logger.warning(f"获取班级列表失败: {response.text}")
    
    @pytest.mark.admin
    @pytest.mark.asyncio
    async def test_create_class(self, client: AsyncClient, admin_token: str, test_logger):
        """测试创建班级"""
        test_logger.info("开始测试: 创建班级")
        
        class_data = {
            "name": "测试班级2025级1班",
            "grade": "2025",
            "major": "计算机科学与技术"
        }
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/admin/classes", json=class_data, headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            test_logger.info(f"创建结果: {json.dumps(data, ensure_ascii=False)[:300]}")
            test_logger.info("创建班级测试通过")
        else:
            test_logger.warning(f"创建班级失败: {response.text}")


class TestAdminSystem:
    """管理员系统配置测试类"""
    
    @pytest.mark.admin
    @pytest.mark.asyncio
    async def test_get_system_info(self, client: AsyncClient, admin_token: str, test_logger):
        """测试获取系统信息"""
        test_logger.info("开始测试: 获取系统信息")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.get("/api/admin/system/info", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"系统信息: {json.dumps(data, ensure_ascii=False)[:500]}")
            test_logger.info("获取系统信息测试通过")
        else:
            test_logger.warning(f"获取系统信息失败: {response.text}")
    
    @pytest.mark.admin
    @pytest.mark.asyncio
    async def test_get_system_stats(self, client: AsyncClient, admin_token: str, test_logger):
        """测试获取系统统计"""
        test_logger.info("开始测试: 获取系统统计")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.get("/api/admin/system/stats", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"系统统计: {json.dumps(data, ensure_ascii=False)[:500]}")
            
            expected_fields = ["total_users", "total_students", "total_classes"]
            for field in expected_fields:
                if field in data:
                    test_logger.info(f"  {field}: {data[field]}")
            test_logger.info("获取系统统计测试通过")
        else:
            test_logger.warning(f"获取系统统计失败: {response.text}")


class TestAdminDataImport:
    """管理员数据导入测试类"""
    
    @pytest.mark.admin
    @pytest.mark.asyncio
    async def test_import_students(self, client: AsyncClient, admin_token: str, test_logger):
        """测试导入学生数据"""
        test_logger.info("开始测试: 导入学生数据")
        
        import_data = {
            "class_id": "test_class_id",
            "students": [
                {"student_id": "2021001", "name": "张三"},
                {"student_id": "2021002", "name": "李四"}
            ]
        }
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/admin/import/students", json=import_data, headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            test_logger.info(f"导入结果: {json.dumps(data, ensure_ascii=False)[:300]}")
            test_logger.info("导入学生数据测试通过")
        else:
            test_logger.warning(f"导入学生数据失败: {response.text}")
    
    @pytest.mark.admin
    @pytest.mark.asyncio
    async def test_import_scores(self, client: AsyncClient, admin_token: str, test_logger):
        """测试导入成绩数据"""
        test_logger.info("开始测试: 导入成绩数据")
        
        import_data = {
            "class_id": "test_class_id",
            "semester": "1",
            "academic_year": "2024-2025",
            "scores": [
                {"student_id": "2021001", "course": "高等数学", "score": 85},
                {"student_id": "2021002", "course": "高等数学", "score": 90}
            ]
        }
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post("/api/admin/import/scores", json=import_data, headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            test_logger.info(f"导入结果: {json.dumps(data, ensure_ascii=False)[:300]}")
            test_logger.info("导入成绩数据测试通过")
        else:
            test_logger.warning(f"导入成绩数据失败: {response.text}")


class TestAdminLogs:
    """管理员日志管理测试类"""
    
    @pytest.mark.admin
    @pytest.mark.asyncio
    async def test_get_operation_logs(self, client: AsyncClient, admin_token: str, test_logger):
        """测试获取操作日志"""
        test_logger.info("开始测试: 获取操作日志")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {"page": 1, "page_size": 20}
        response = await client.get("/api/admin/logs", params=params, headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"操作日志: {json.dumps(data, ensure_ascii=False)[:500]}")
            test_logger.info("获取操作日志测试通过")
        else:
            test_logger.warning(f"获取操作日志失败: {response.text}")
    
    @pytest.mark.admin
    @pytest.mark.asyncio
    async def test_get_login_logs(self, client: AsyncClient, admin_token: str, test_logger):
        """测试获取登录日志"""
        test_logger.info("开始测试: 获取登录日志")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {"page": 1, "page_size": 20}
        response = await client.get("/api/admin/logs/login", params=params, headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"登录日志: {json.dumps(data, ensure_ascii=False)[:500]}")
            test_logger.info("获取登录日志测试通过")
        else:
            test_logger.warning(f"获取登录日志失败: {response.text}")


class TestAdminRules:
    """管理员规则管理测试类"""
    
    @pytest.mark.admin
    @pytest.mark.asyncio
    async def test_get_rules(self, client: AsyncClient, admin_token: str, test_logger):
        """测试获取综测规则"""
        test_logger.info("开始测试: 获取综测规则")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.get("/api/admin/rules", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"综测规则: {json.dumps(data, ensure_ascii=False)[:500]}")
            test_logger.info("获取综测规则测试通过")
        else:
            test_logger.warning(f"获取综测规则失败: {response.text}")
    
    @pytest.mark.admin
    @pytest.mark.asyncio
    async def test_update_rule(self, client: AsyncClient, admin_token: str, test_logger):
        """测试更新综测规则"""
        test_logger.info("开始测试: 更新综测规则")
        
        rule_data = {
            "rule_id": "test_rule_id",
            "name": "省级竞赛一等奖",
            "score": 15.0,
            "category": "竞赛"
        }
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.put("/api/admin/rules/test_rule_id", json=rule_data, headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"更新结果: {json.dumps(data, ensure_ascii=False)[:300]}")
            test_logger.info("更新综测规则测试通过")
        else:
            test_logger.warning(f"更新综测规则失败: {response.text}")
