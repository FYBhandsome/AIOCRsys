#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三者格式兼容性测试
测试Excel表格、数据库模型、JSON响应三者字段映射和格式兼容性
"""
import pytest
import json
import logging
from typing import Dict, Any
from app.services.rag_comprehensive_service import FieldMapping, DataValidator

logger = logging.getLogger(__name__)


class TestFieldMapping:
    """测试字段映射"""
    
    def test_json_to_db_mapping_exists(self):
        """测试JSON到数据库的字段映射存在"""
        assert hasattr(FieldMapping, 'JSON_TO_DB')
        assert isinstance(FieldMapping.JSON_TO_DB, dict)
        assert len(FieldMapping.JSON_TO_DB) > 0
    
    def test_json_to_excel_mapping_exists(self):
        """测试JSON到Excel的字段映射存在"""
        assert hasattr(FieldMapping, 'JSON_TO_EXCEL')
        assert isinstance(FieldMapping.JSON_TO_EXCEL, dict)
        assert len(FieldMapping.JSON_TO_EXCEL) > 0
    
    def test_required_fields_defined(self):
        """测试必需字段已定义"""
        assert hasattr(FieldMapping, 'REQUIRED_FIELDS')
        assert isinstance(FieldMapping.REQUIRED_FIELDS, list)
        assert len(FieldMapping.REQUIRED_FIELDS) > 0
    
    def test_key_score_fields_in_mapping(self):
        """测试关键字段在映射中"""
        key_fields = [
            'a1_score', 'a2_score', 'a3_score', 'a_total_score',
            'b_raw_score',
            'c1_score', 'c2_score', 'c3_score', 'c4_score', 'c_total_score',
            'total_score'
        ]
        for field in key_fields:
            assert field in FieldMapping.JSON_TO_DB, f"{field} 不在JSON_TO_DB映射中"
    
    def test_student_info_fields_in_mapping(self):
        """测试学生信息字段在映射中"""
        student_fields = ['student_id', 'student_name', 'class_name', 'major']
        for field in student_fields:
            assert field in FieldMapping.JSON_TO_DB, f"{field} 不在JSON_TO_DB映射中"
            assert field in FieldMapping.JSON_TO_EXCEL, f"{field} 不在JSON_TO_EXCEL映射中"


class TestDataValidator:
    """测试数据验证器"""
    
    def test_validate_comprehensive_score_success(self):
        """测试验证综评数据成功"""
        test_data = {
            'student_id': '2023001',
            'student_name': '张三',
            'class_name': '230521班',
            'major': '计算机科学',
            'a1_score': 90.0,
            'a2_score': 5.0,
            'a3_score': 0.0,
            'a_total_score': 95.0,
            'b_raw_score': 85.0,
            'c1_score': 3.0,
            'c2_score': 2.0,
            'c3_score': 1.0,
            'c4_score': 4.0,
            'c_total_score': 10.0,
            'total_score': 85.5
        }
        
        is_valid, errors, cleaned_data = DataValidator.validate_comprehensive_score(test_data)
        
        assert is_valid, f"验证失败: {errors}"
        assert len(errors) == 0
        assert cleaned_data['student_id'] == '2023001'
        assert cleaned_data['a1_score'] == 90.0
    
    def test_validate_missing_required_fields(self):
        """测试缺少必需字段"""
        test_data = {
            'student_id': '2023001',
            'a1_score': 90.0
        }
        
        is_valid, errors, cleaned_data = DataValidator.validate_comprehensive_score(test_data)
        
        assert not is_valid
        assert len(errors) > 0
    
    def test_validate_type_conversion(self):
        """测试类型转换"""
        test_data = {
            'student_id': '2023001',
            'student_name': '张三',
            'class_name': '230521班',
            'major': '计算机科学',
            'a1_score': '90.5',
            'a2_score': '5',
            'a3_score': 0,
            'a_total_score': '95.5',
            'b_raw_score': 85.0,
            'c1_score': '3.0',
            'c2_score': 2,
            'c3_score': '1',
            'c4_score': 4.0,
            'c_total_score': '10',
            'total_score': 85.5
        }
        
        is_valid, errors, cleaned_data = DataValidator.validate_comprehensive_score(test_data)
        
        assert is_valid
        assert isinstance(cleaned_data['a1_score'], float)
        assert cleaned_data['a1_score'] == 90.5
        assert isinstance(cleaned_data['a2_score'], float)
        assert cleaned_data['a2_score'] == 5.0
    
    def test_validate_negative_scores(self):
        """测试负数分数处理"""
        test_data = {
            'student_id': '2023001',
            'student_name': '张三',
            'class_name': '230521班',
            'major': '计算机科学',
            'a1_score': -10.0,
            'a2_score': 5.0,
            'a3_score': 0.0,
            'a_total_score': -5.0,
            'b_raw_score': 85.0,
            'c1_score': -3.0,
            'c2_score': 2.0,
            'c3_score': 1.0,
            'c4_score': 4.0,
            'c_total_score': 4.0,
            'total_score': 80.0
        }
        
        is_valid, errors, cleaned_data = DataValidator.validate_comprehensive_score(test_data)
        
        assert is_valid
        assert cleaned_data['a1_score'] == 0.0
        assert cleaned_data['a_total_score'] == 0.0
        assert cleaned_data['c1_score'] == 0.0
    
    def test_convert_to_db_format(self):
        """测试转换为数据库格式"""
        test_data = {
            'student_id': '2023001',
            'student_name': '张三',
            'a1_score': 90.0,
            'total_score': 85.5
        }
        
        db_data = DataValidator.convert_to_db_format(test_data)
        
        assert db_data['student_id'] == '2023001'
        assert db_data['student_name'] == '张三'
        assert db_data['a1_score'] == 90.0
        assert db_data['total_score'] == 85.5
    
    def test_convert_to_excel_format(self):
        """测试转换为Excel格式"""
        test_data = {
            'student_id': '2023001',
            'student_name': '张三',
            'a1_score': 90.0,
            'a2_score': 5.0,
            'a3_score': 0.0,
            'a_total_score': 95.0,
            'b_raw_score': 85.0,
            'c1_score': 3.0,
            'c2_score': 2.0,
            'c3_score': 1.0,
            'c4_score': 4.0,
            'c_total_score': 10.0,
            'total_score': 85.5
        }
        
        excel_data = DataValidator.convert_to_excel_format(test_data)
        
        assert excel_data['姓名'] == '张三'
        assert excel_data['学号'] == '2023001'
        assert excel_data['A1—基础分'] == 90.0
        assert excel_data['A2—附加分'] == 5.0
        assert excel_data['A3—扣分项'] == 0.0
        assert excel_data['思想道德素质(A)总分'] == 95.0
        assert excel_data['学习成绩'] == 85.0
        assert excel_data['C1—科技竞赛项目'] == 3.0
        assert excel_data['C2—体育竞技项目'] == 2.0
        assert excel_data['C3—文化类竞赛项目'] == 1.0
        assert excel_data['C4—创新创业实践项目'] == 4.0
        assert excel_data['素质拓展(C)总分'] == 10.0
        assert excel_data['综合测评总成绩8%'] == 85.5


class TestThreeWayCompatibility:
    """测试三者格式兼容性"""
    
    def test_end_to_end_format_flow(self):
        """测试端到端格式流程：JSON -> 验证 -> DB格式 -> Excel格式"""
        original_json = {
            'student_id': '2023001',
            'student_name': '张三',
            'class_name': '230521班',
            'major': '计算机科学',
            'a1_score': 90.0,
            'a2_score': 5.0,
            'a3_score': 0.0,
            'a_total_score': 95.0,
            'b_raw_score': 85.0,
            'c1_score': 3.0,
            'c2_score': 2.0,
            'c3_score': 1.0,
            'c4_score': 4.0,
            'c_total_score': 10.0,
            'total_score': 85.5
        }
        
        is_valid, errors, cleaned_data = DataValidator.validate_comprehensive_score(original_json)
        assert is_valid
        
        db_data = DataValidator.convert_to_db_format(cleaned_data)
        assert db_data['student_id'] == original_json['student_id']
        assert db_data['a1_score'] == original_json['a1_score']
        
        excel_data = DataValidator.convert_to_excel_format(cleaned_data)
        assert excel_data['姓名'] == original_json['student_name']
        assert excel_data['A1—基础分'] == original_json['a1_score']
        assert excel_data['综合测评总成绩8%'] == original_json['total_score']
    
    def test_json_serialization_deserialization(self):
        """测试JSON序列化和反序列化"""
        test_data = {
            'student_id': '2023001',
            'student_name': '张三',
            'a1_score': 90.5,
            'total_score': 85.5
        }
        
        json_str = json.dumps(test_data, ensure_ascii=False)
        parsed_data = json.loads(json_str)
        
        assert parsed_data['student_id'] == test_data['student_id']
        assert parsed_data['student_name'] == test_data['student_name']
        assert parsed_data['a1_score'] == test_data['a1_score']
        assert parsed_data['total_score'] == test_data['total_score']
    
    def test_field_consistency_across_mappings(self):
        """测试字段在不同映射中的一致性"""
        common_fields = set(FieldMapping.JSON_TO_DB.keys()) & set(FieldMapping.JSON_TO_EXCEL.keys())
        
        assert len(common_fields) > 0
        
        for field in common_fields:
            assert field in FieldMapping.JSON_TO_DB
            assert field in FieldMapping.JSON_TO_EXCEL


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
