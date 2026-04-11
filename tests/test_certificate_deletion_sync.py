#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
证书删除同步测试脚本
==================

测试证书删除后前端显示数量的同步问题是否已修复。

测试流程：
1. 上传测试证书
2. 验证前端显示数量
3. 删除证书
4. 验证前端显示数量是否更新
"""

import asyncio
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.certificate_storage_service import get_certificate_storage_service
from app.models.tortoise_models import Certificate
from app.core.logger import get_logger
from config import settings

logger = get_logger(__name__)


async def test_certificate_deletion_sync():
    """测试证书删除同步"""
    
    logger.info("=" * 80)
    logger.info("开始测试证书删除同步功能")
    logger.info("=" * 80)
    
    service = get_certificate_storage_service()
    
    # 测试数据
    test_student_id = "TEST_DELETE_SYNC_001"
    test_user = "test_user"
    
    try:
        # 步骤1: 查询初始证书数量
        logger.info("\n步骤1: 查询初始证书数量")
        initial_count = await Certificate.filter(
            student_id=test_student_id,
            is_valid=True
        ).count()
        logger.info(f"初始证书数量: {initial_count}")
        
        # 步骤2: 上传测试证书
        logger.info("\n步骤2: 上传测试证书")
        test_image_path = project_root / "visual_model" / "testphoto"
        
        if not test_image_path.exists():
            logger.warning(f"测试图片目录不存在: {test_image_path}")
            logger.info("创建模拟测试...")
            # 创建模拟测试数据
            certificate = await Certificate.create(
                student_id=test_student_id,
                filename="test_certificate.jpg",
                file_path="/tmp/test_certificate.jpg",
                title="测试证书",
                category="C",
                score=5.0,
                status="approved",
                is_valid=True
            )
            certificate_id = certificate.id
            logger.info(f"创建测试证书: ID={certificate_id}")
        else:
            # 使用实际图片测试
            test_images = list(test_image_path.glob("*.jpg"))[:1]
            if not test_images:
                logger.error("未找到测试图片")
                return False
            
            with open(test_images[0], 'rb') as f:
                file_content = f.read()
            
            result = await service.upload_certificate_images(
                student_id=test_student_id,
                files=[("test_certificate.jpg", file_content)],
                certificate_info={"title": "测试证书"}
            )
            
            if not result["success"]:
                logger.error(f"上传失败: {result.get('error')}")
                return False
            
            certificate_id = result["certificate_id"]
            logger.info(f"上传成功: ID={certificate_id}")
        
        # 步骤3: 验证上传后数量
        logger.info("\n步骤3: 验证上传后数量")
        after_upload_count = await Certificate.filter(
            student_id=test_student_id,
            is_valid=True
        ).count()
        logger.info(f"上传后证书数量: {after_upload_count}")
        
        if after_upload_count != initial_count + 1:
            logger.error(f"数量不一致: 预期 {initial_count + 1}, 实际 {after_upload_count}")
            return False
        
        # 步骤4: 删除证书
        logger.info("\n步骤4: 删除证书")
        delete_result = await service.delete_certificate(certificate_id, test_user)
        
        if not delete_result["success"]:
            logger.error(f"删除失败: {delete_result.get('error')}")
            return False
        
        logger.info(f"删除成功: {delete_result}")
        
        # 步骤5: 验证删除后数量
        logger.info("\n步骤5: 验证删除后数量")
        after_delete_count = await Certificate.filter(
            student_id=test_student_id,
            is_valid=True
        ).count()
        logger.info(f"删除后证书数量: {after_delete_count}")
        
        if after_delete_count != initial_count:
            logger.error(f"数量不一致: 预期 {initial_count}, 实际 {after_delete_count}")
            return False
        
        # 步骤6: 验证证书状态
        logger.info("\n步骤6: 验证证书状态")
        deleted_cert = await Certificate.get_or_none(id=certificate_id)
        
        if not deleted_cert:
            logger.error("证书不存在")
            return False
        
        if deleted_cert.is_valid:
            logger.error("证书仍标记为有效")
            return False
        
        if deleted_cert.status != "deleted":
            logger.error(f"证书状态不正确: {deleted_cert.status}")
            return False
        
        logger.info(f"证书状态验证通过: is_valid={deleted_cert.is_valid}, status={deleted_cert.status}")
        
        # 步骤7: 清理测试数据
        logger.info("\n步骤7: 清理测试数据")
        await Certificate.filter(student_id=test_student_id).delete()
        logger.info("测试数据已清理")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ 所有测试通过！证书删除同步功能正常")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        return False


async def test_frontend_api_response():
    """测试前端API响应格式"""
    
    logger.info("\n" + "=" * 80)
    logger.info("测试前端API响应格式")
    logger.info("=" * 80)
    
    service = get_certificate_storage_service()
    
    test_student_id = "TEST_API_RESPONSE"
    
    try:
        # 创建测试证书
        certificate = await Certificate.create(
            student_id=test_student_id,
            filename="test.jpg",
            file_path="/tmp/test.jpg",
            title="测试证书",
            category="C",
            score=5.0,
            status="approved",
            is_valid=True
        )
        
        # 测试删除响应
        result = await service.delete_certificate(certificate.id, "test_user")
        
        logger.info(f"删除响应: {result}")
        
        # 验证响应格式
        required_fields = ["success", "message", "certificate_id", "student_id"]
        for field in required_fields:
            if field not in result:
                logger.error(f"缺少必要字段: {field}")
                return False
        
        logger.info("✅ API响应格式正确")
        
        # 清理
        await Certificate.filter(student_id=test_student_id).delete()
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        return False


async def main():
    """主函数"""
    
    logger.info("开始证书删除同步测试")
    
    # 测试1: 删除同步功能
    test1_passed = await test_certificate_deletion_sync()
    
    # 测试2: API响应格式
    test2_passed = await test_frontend_api_response()
    
    # 总结
    logger.info("\n" + "=" * 80)
    logger.info("测试总结")
    logger.info("=" * 80)
    logger.info(f"删除同步功能测试: {'✅ 通过' if test1_passed else '❌ 失败'}")
    logger.info(f"API响应格式测试: {'✅ 通过' if test2_passed else '❌ 失败'}")
    
    if test1_passed and test2_passed:
        logger.info("\n🎉 所有测试通过！")
        return 0
    else:
        logger.error("\n⚠️ 部分测试失败")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n测试被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"测试执行失败: {e}", exc_info=True)
        sys.exit(1)
