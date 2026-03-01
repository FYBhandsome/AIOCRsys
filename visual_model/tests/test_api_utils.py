#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试 - API工具函数测试
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException

from app.api.api_utils import (
    handle_api_errors,
    api_response,
    validate_pagination,
    validate_id,
    validate_required,
    validate_length,
    validate_range,
    validate_in_list,
    PaginationHelper,
    RequestContext,
    generate_request_id
)
from app.core.exceptions import ValidationException


class TestHandleApiErrors:
    """API错误处理装饰器测试"""
    
    @pytest.mark.asyncio
    async def test_success_execution(self):
        """测试成功执行"""
        @handle_api_errors("测试操作")
        async def test_func():
            return {"data": "test"}
        
        result = await test_func()
        assert result["success"] is True
        assert result["data"] == "test"
        assert "request_id" in result
    
    @pytest.mark.asyncio
    async def test_http_exception_passthrough(self):
        """测试HTTP异常直接传递"""
        @handle_api_errors("测试操作")
        async def test_func():
            raise HTTPException(status_code=404, detail="未找到")
        
        with pytest.raises(HTTPException) as exc_info:
            await test_func()
        
        assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_value_error_conversion(self):
        """测试ValueError转换为HTTP异常"""
        @handle_api_errors("测试操作")
        async def test_func():
            raise ValueError("参数错误")
        
        with pytest.raises(HTTPException) as exc_info:
            await test_func()
        
        assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_generic_exception_conversion(self):
        """测试通用异常转换"""
        @handle_api_errors("测试操作")
        async def test_func():
            raise Exception("未知错误")
        
        with pytest.raises(HTTPException) as exc_info:
            await test_func()
        
        assert exc_info.value.status_code == 500


class TestApiResponse:
    """API响应封装装饰器测试"""
    
    @pytest.mark.asyncio
    async def test_dict_response(self):
        """测试字典响应"""
        @api_response
        async def test_func():
            return {"id": 1, "name": "test"}
        
        result = await test_func()
        assert result["success"] is True
        assert result["data"]["id"] == 1
    
    @pytest.mark.asyncio
    async def test_list_response(self):
        """测试列表响应"""
        @api_response
        async def test_func():
            return [1, 2, 3]
        
        result = await test_func()
        assert result["success"] is True
        assert result["data"] == [1, 2, 3]
    
    @pytest.mark.asyncio
    async def test_none_response(self):
        """测试None响应"""
        @api_response
        async def test_func():
            return None
        
        result = await test_func()
        assert result["success"] is True
        assert result["message"] == "操作成功"
    
    @pytest.mark.asyncio
    async def test_already_formatted_response(self):
        """测试已格式化响应"""
        @api_response
        async def test_func():
            return {"success": False, "message": "自定义错误"}
        
        result = await test_func()
        assert result["success"] is False
        assert result["message"] == "自定义错误"


class TestValidatePagination:
    """分页参数验证测试"""
    
    def test_valid_pagination(self):
        """测试有效分页参数"""
        page, page_size = validate_pagination(1, 20)
        assert page == 1
        assert page_size == 20
    
    def test_invalid_page(self):
        """测试无效页码"""
        with pytest.raises(ValidationException):
            validate_pagination(0, 20)
        
        with pytest.raises(ValidationException):
            validate_pagination(-1, 20)
    
    def test_invalid_page_size(self):
        """测试无效每页数量"""
        with pytest.raises(ValidationException):
            validate_pagination(1, 0)
        
        with pytest.raises(ValidationException):
            validate_pagination(1, -1)
    
    def test_page_size_exceeds_max(self):
        """测试每页数量超过最大值"""
        with pytest.raises(ValidationException):
            validate_pagination(1, 200, max_page_size=100)


class TestValidateId:
    """ID参数验证测试"""
    
    def test_valid_id(self):
        """测试有效ID"""
        result = validate_id("123", "测试ID")
        assert result == "123"
    
    def test_empty_id(self):
        """测试空ID"""
        with pytest.raises(ValidationException):
            validate_id("", "测试ID")
        
        with pytest.raises(ValidationException):
            validate_id(None, "测试ID")
    
    def test_whitespace_id(self):
        """测试空白ID"""
        with pytest.raises(ValidationException):
            validate_id("   ", "测试ID")
    
    def test_numeric_id_conversion(self):
        """测试数字ID转换"""
        result = validate_id(123, "测试ID")
        assert result == "123"


class TestValidateRequired:
    """必填字段验证测试"""
    
    def test_valid_value(self):
        """测试有效值"""
        result = validate_required("test", "字段")
        assert result == "test"
    
    def test_none_value(self):
        """测试None值"""
        with pytest.raises(ValidationException):
            validate_required(None, "字段")
    
    def test_empty_string(self):
        """测试空字符串"""
        with pytest.raises(ValidationException):
            validate_required("", "字段")
    
    def test_whitespace_string(self):
        """测试空白字符串"""
        with pytest.raises(ValidationException):
            validate_required("   ", "字段")


class TestValidateLength:
    """字符串长度验证测试"""
    
    def test_valid_length(self):
        """测试有效长度"""
        result = validate_length("test", "字段", min_len=1, max_len=10)
        assert result == "test"
    
    def test_too_short(self):
        """测试过短"""
        with pytest.raises(ValidationException):
            validate_length("ab", "字段", min_len=3)
    
    def test_too_long(self):
        """测试过长"""
        with pytest.raises(ValidationException):
            validate_length("abcdefghijk", "字段", max_len=10)


class TestValidateRange:
    """数值范围验证测试"""
    
    def test_valid_range(self):
        """测试有效范围"""
        result = validate_range(50, "数值", min_val=0, max_val=100)
        assert result == 50
    
    def test_below_min(self):
        """测试低于最小值"""
        with pytest.raises(ValidationException):
            validate_range(-1, "数值", min_val=0)
    
    def test_above_max(self):
        """测试高于最大值"""
        with pytest.raises(ValidationException):
            validate_range(101, "数值", max_val=100)


class TestValidateInList:
    """列表值验证测试"""
    
    def test_valid_value(self):
        """测试有效值"""
        result = validate_in_list("a", "选项", ["a", "b", "c"])
        assert result == "a"
    
    def test_invalid_value(self):
        """测试无效值"""
        with pytest.raises(ValidationException):
            validate_in_list("d", "选项", ["a", "b", "c"])


class TestPaginationHelper:
    """分页助手测试"""
    
    def test_offset_calculation(self):
        """测试偏移量计算"""
        helper = PaginationHelper(page=2, page_size=20)
        offset, limit = helper.get_offset_limit()
        assert offset == 20
        assert limit == 20
    
    def test_paged_result(self):
        """测试分页结果生成"""
        helper = PaginationHelper(page=1, page_size=10)
        result = helper.get_paged_result(
            items=[1, 2, 3],
            total=25
        )
        
        assert result["success"] is True
        assert result["data"]["items"] == [1, 2, 3]
        assert result["data"]["total"] == 25
        assert result["data"]["page"] == 1
        assert result["data"]["page_size"] == 10
        assert result["data"]["total_pages"] == 3


class TestRequestContext:
    """请求上下文测试"""
    
    def test_request_id_generation(self):
        """测试请求ID生成"""
        ctx = RequestContext()
        assert ctx.request_id.startswith("req_")
    
    def test_elapsed_ms(self):
        """测试耗时计算"""
        import time
        ctx = RequestContext()
        time.sleep(0.01)
        elapsed = ctx.elapsed_ms()
        assert elapsed >= 10


class TestGenerateRequestId:
    """请求ID生成测试"""
    
    def test_unique_ids(self):
        """测试唯一性"""
        ids = [generate_request_id() for _ in range(100)]
        assert len(set(ids)) == 100
    
    def test_format(self):
        """测试格式"""
        request_id = generate_request_id()
        assert request_id.startswith("req_")
        assert len(request_id) == 16
