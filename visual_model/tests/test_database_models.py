#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模型测试文件
测试所有数据库模型的CRUD操作、关联关系和业务逻辑
"""
import pytest
import asyncio
from datetime import datetime
from tortoise import Tortoise
from tortoise.exceptions import DoesNotExist, IntegrityError

from app.models.tortoise_models import (
    User, Student, Class, ClassStudent,
    AcademicScore, ComprehensiveScore, ComprehensiveScoreConfig, ScoreDetail,
    Certificate, CertificateImage, CertificateBatch,
    AcademicScoreHistory, ComprehensiveScoreHistory,
    File, FileMetadata, FileChunk, FileBackup, FileAccessPermission, DownloadLog, UploadRecord,
    SystemSetting, ChatHistory
)
from app.core.security import get_password_hash


@pytest.fixture(scope="function")
async def setup_test_db():
    """设置测试数据库"""
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["app.models.tortoise_models"]}
    )
    await Tortoise.generate_schemas()
    
    yield
    
    await Tortoise.close_connections()


class TestStudentModel:
    """学生模型测试"""
    
    @pytest.mark.asyncio
    async def test_create_student(self, setup_test_db):
        """测试创建学生"""
        student = await Student.create(
            id="202300502101",
            name="张三",
            college="计算机学院",
            major="计算机科学与技术",
            class_name="计算机2301",
            grade="2023",
            gender="男"
        )
        
        assert student.id == "202300502101"
        assert student.name == "张三"
        assert student.college == "计算机学院"
        assert student.major == "计算机科学与技术"
        assert student.class_name == "计算机2301"
        assert student.grade == "2023"
    
    @pytest.mark.asyncio
    async def test_read_student(self, setup_test_db):
        """测试读取学生"""
        await Student.create(
            id="202300502102",
            name="李四",
            college="计算机学院",
            major="软件工程",
            class_name="软件2301",
            grade="2023"
        )
        
        student = await Student.get(id="202300502102")
        assert student.name == "李四"
        assert student.major == "软件工程"
    
    @pytest.mark.asyncio
    async def test_update_student(self, setup_test_db):
        """测试更新学生"""
        student = await Student.create(
            id="202300502103",
            name="王五",
            college="计算机学院",
            major="计算机科学与技术",
            class_name="计算机2301",
            grade="2023"
        )
        
        student.name = "王五六"
        student.major = "人工智能"
        await student.save()
        
        updated = await Student.get(id="202300502103")
        assert updated.name == "王五六"
        assert updated.major == "人工智能"
    
    @pytest.mark.asyncio
    async def test_delete_student(self, setup_test_db):
        """测试删除学生"""
        student = await Student.create(
            id="202300502104",
            name="赵六",
            college="计算机学院",
            major="计算机科学与技术",
            class_name="计算机2301",
            grade="2023"
        )
        
        await student.delete()
        
        with pytest.raises(DoesNotExist):
            await Student.get(id="202300502104")


class TestAcademicScoreModel:
    """学业成绩模型测试"""
    
    @pytest.mark.asyncio
    async def test_create_academic_score(self, setup_test_db):
        """测试创建学业成绩"""
        student = await Student.create(
            id="202300502201",
            name="测试学生1",
            college="计算机学院",
            major="计算机科学与技术",
            class_name="计算机2301",
            grade="2023"
        )
        
        score = await AcademicScore.create(
            student=student,
            student_name="测试学生1",
            academic_year="2023-2024",
            semester="1",
            total_score=85.5,
            total_credits=20.0
        )
        
        assert score.student_id == student.id
        assert score.student_name == "测试学生1"
        assert score.total_score == 85.5
    
    @pytest.mark.asyncio
    async def test_academic_score_prefetch_student(self, setup_test_db):
        """测试学业成绩关联学生查询"""
        student = await Student.create(
            id="202300502203",
            name="测试学生3",
            college="计算机学院",
            major="计算机科学与技术",
            class_name="计算机2301",
            grade="2023"
        )
        
        await AcademicScore.create(
            student=student,
            student_name="测试学生3",
            academic_year="2023-2024",
            semester="1",
            total_score=85.5
        )
        
        scores = await AcademicScore.filter(student_id=student.id).prefetch_related('student')
        assert len(scores) == 1
        assert scores[0].student.name == "测试学生3"


class TestComprehensiveScoreModel:
    """综测成绩模型测试"""
    
    @pytest.mark.asyncio
    async def test_create_comprehensive_score(self, setup_test_db):
        """测试创建综测成绩"""
        student = await Student.create(
            id="202300502301",
            name="综测学生1",
            college="计算机学院",
            major="计算机科学与技术",
            class_name="计算机2301",
            grade="2023"
        )
        
        score = await ComprehensiveScore.create(
            student=student,
            academic_year="2023-2024",
            semester="1",
            a_total_score=15.0,
            b_raw_score=80.0,
            b_weighted_score=56.0,
            b_total_score=80.0,
            c_total_score=8.0,
            total_score=79.0
        )
        
        assert score.student_id == student.id
        assert score.a_total_score == 15.0
        assert score.b_raw_score == 80.0
        assert score.b_weighted_score == 56.0
        assert score.b_total_score == 80.0
        assert score.c_total_score == 8.0
        assert score.total_score == 79.0
    
    @pytest.mark.asyncio
    async def test_comprehensive_score_fields(self, setup_test_db):
        """测试综测成绩字段完整性"""
        student = await Student.create(
            id="202300502302",
            name="综测学生2",
            college="计算机学院",
            major="计算机科学与技术",
            class_name="计算机2301",
            grade="2023"
        )
        
        score = await ComprehensiveScore.create(
            student=student,
            academic_year="2023-2024",
            semester="1"
        )
        
        assert hasattr(score, 'b_raw_score')
        assert hasattr(score, 'b_weighted_score')
        assert hasattr(score, 'b_total_score')
        assert score.b_raw_score == 0.0
        assert score.b_weighted_score == 0.0
        assert score.b_total_score == 0.0
    
    @pytest.mark.asyncio
    async def test_comprehensive_score_prefetch_student(self, setup_test_db):
        """测试综测成绩关联学生查询"""
        student = await Student.create(
            id="202300502303",
            name="综测学生3",
            college="计算机学院",
            major="计算机科学与技术",
            class_name="计算机2301",
            grade="2023"
        )
        
        await ComprehensiveScore.create(
            student=student,
            academic_year="2023-2024",
            semester="1",
            total_score=85.0
        )
        
        scores = await ComprehensiveScore.filter(student_id=student.id).prefetch_related('student')
        assert len(scores) == 1
        assert scores[0].student.name == "综测学生3"


class TestCertificateModel:
    """证书模型测试"""
    
    @pytest.mark.asyncio
    async def test_create_certificate(self, setup_test_db):
        """测试创建证书"""
        student = await Student.create(
            id="202300502401",
            name="证书学生1",
            college="计算机学院",
            major="计算机科学与技术",
            class_name="计算机2301",
            grade="2023"
        )
        
        certificate = await Certificate.create(
            student_id=student.id,
            title="蓝桥杯",
            category="C",
            level="省级",
            score=15.0,
            academic_year="2023-2024",
            semester="1"
        )
        
        assert certificate.student_id == student.id
        assert certificate.title == "蓝桥杯"
        assert certificate.category == "C"
        assert certificate.level == "省级"
        assert certificate.score == 15.0
    
    @pytest.mark.asyncio
    async def test_certificate_prefetch_student(self, setup_test_db):
        """测试证书关联学生查询"""
        student = await Student.create(
            id="202300502402",
            name="证书学生2",
            college="计算机学院",
            major="计算机科学与技术",
            class_name="计算机2301",
            grade="2023"
        )
        
        await Certificate.create(
            student_id=student.id,
            title="英语四级",
            category="C",
            level="国家级",
            score=5.0,
            academic_year="2023-2024",
            semester="1"
        )
        
        certificates = await Certificate.filter(student_id=student.id)
        assert len(certificates) == 1
        assert certificates[0].title == "英语四级"


class TestCertificateImageModel:
    """证书图片模型测试"""
    
    @pytest.mark.asyncio
    async def test_create_certificate_image(self, setup_test_db):
        """测试创建证书图片"""
        student = await Student.create(
            id="202300502501",
            name="图片学生1",
            college="计算机学院",
            major="计算机科学与技术",
            class_name="计算机2301",
            grade="2023"
        )
        
        certificate = await Certificate.create(
            student_id=student.id,
            title="测试证书",
            category="C",
            academic_year="2023-2024",
            semester="1"
        )
        
        image = await CertificateImage.create(
            certificate=certificate,
            student=student,
            filename="test.jpg",
            file_path="/uploads/test.jpg",
            file_size=1024
        )
        
        assert image.certificate_id == certificate.id
        assert image.student_id == student.id
        assert image.filename == "test.jpg"
    
    @pytest.mark.asyncio
    async def test_certificate_image_prefetch_relations(self, setup_test_db):
        """测试证书图片关联查询"""
        student = await Student.create(
            id="202300502502",
            name="图片学生2",
            college="计算机学院",
            major="计算机科学与技术",
            class_name="计算机2301",
            grade="2023"
        )
        
        certificate = await Certificate.create(
            student_id=student.id,
            title="测试证书2",
            category="C",
            academic_year="2023-2024",
            semester="1"
        )
        
        await CertificateImage.create(
            certificate=certificate,
            student=student,
            filename="test2.jpg",
            file_path="/uploads/test2.jpg"
        )
        
        images = await CertificateImage.filter(certificate_id=certificate.id).prefetch_related('certificate', 'student')
        assert len(images) == 1
        assert images[0].student.name == "图片学生2"
        assert images[0].certificate.title == "测试证书2"


class TestClassStudentModel:
    """班级学生关联模型测试"""
    
    @pytest.mark.asyncio
    async def test_create_class_student(self, setup_test_db):
        """测试创建班级学生关联"""
        cls = await Class.create(
            id="test_class_001",
            name="测试班级1",
            grade="2023",
            major="计算机科学与技术",
            college="计算机学院"
        )
        
        student = await Student.create(
            id="202300502601",
            name="班级学生1",
            college="计算机学院",
            major="计算机科学与技术",
            class_name="测试班级1",
            grade="2023"
        )
        
        class_student = await ClassStudent.create(
            class_id=cls,
            student=student
        )
        
        assert class_student.class_id.id == cls.id
        assert class_student.student_id == student.id
    
    @pytest.mark.asyncio
    async def test_class_student_unique_constraint(self, setup_test_db):
        """测试班级学生唯一约束"""
        cls = await Class.create(
            id="test_class_002",
            name="测试班级2",
            grade="2023",
            major="计算机科学与技术",
            college="计算机学院"
        )
        
        student = await Student.create(
            id="202300502602",
            name="班级学生2",
            college="计算机学院",
            major="计算机科学与技术",
            class_name="测试班级2",
            grade="2023"
        )
        
        await ClassStudent.create(
            class_id=cls,
            student=student
        )
        
        with pytest.raises(IntegrityError):
            await ClassStudent.create(
                class_id=cls,
                student=student
            )


class TestUserModel:
    """用户模型测试"""
    
    @pytest.mark.asyncio
    async def test_create_user(self, setup_test_db):
        """测试创建用户"""
        user = await User.create(
            username="testuser1",
            password=get_password_hash("password123"),
            role="student",
            email="test1@example.com",
            real_name="测试用户1"
        )
        
        assert user.username == "testuser1"
        assert user.role == "student"
        assert user.email == "test1@example.com"
    
    @pytest.mark.asyncio
    async def test_user_unique_username(self, setup_test_db):
        """测试用户名唯一约束"""
        await User.create(
            username="testuser2",
            password=get_password_hash("password123"),
            role="student",
            email="test2@example.com"
        )
        
        with pytest.raises(IntegrityError):
            await User.create(
                username="testuser2",
                password=get_password_hash("password456"),
                role="teacher",
                email="test3@example.com"
            )
    
    @pytest.mark.asyncio
    async def test_user_email_can_be_empty_string(self, setup_test_db):
        """测试用户邮箱可以是空字符串"""
        user = await User.create(
            username="testuser3",
            password=get_password_hash("password123"),
            role="student",
            email=""
        )
        
        assert user.email == ""


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_student_scores_relation(self, setup_test_db):
        """测试学生与成绩的关联关系"""
        student = await Student.create(
            id="202300502701",
            name="关联学生1",
            college="计算机学院",
            major="计算机科学与技术",
            class_name="计算机2301",
            grade="2023"
        )
        
        await AcademicScore.create(
            student=student,
            student_name="关联学生1",
            academic_year="2023-2024",
            semester="1",
            total_score=85.0
        )
        
        await ComprehensiveScore.create(
            student=student,
            academic_year="2023-2024",
            semester="1",
            total_score=85.0
        )
        
        academic_scores = await AcademicScore.filter(student_id=student.id)
        assert len(academic_scores) == 1
        
        comp_scores = await ComprehensiveScore.filter(student_id=student.id)
        assert len(comp_scores) == 1
    
    @pytest.mark.asyncio
    async def test_certificate_full_flow(self, setup_test_db):
        """测试证书完整流程"""
        student = await Student.create(
            id="202300502702",
            name="证书流程学生",
            college="计算机学院",
            major="计算机科学与技术",
            class_name="计算机2301",
            grade="2023"
        )
        
        certificate = await Certificate.create(
            student_id=student.id,
            title="蓝桥杯",
            category="C",
            level="省级",
            score=15.0,
            academic_year="2023-2024",
            semester="1"
        )
        
        image1 = await CertificateImage.create(
            certificate=certificate,
            student=student,
            filename="cert1.jpg",
            file_path="/uploads/cert1.jpg"
        )
        
        image2 = await CertificateImage.create(
            certificate=certificate,
            student=student,
            filename="cert2.jpg",
            file_path="/uploads/cert2.jpg"
        )
        
        cert_with_images = await Certificate.get(id=certificate.id).prefetch_related('images')
        assert len(cert_with_images.images) == 2
    
    @pytest.mark.asyncio
    async def test_comprehensive_score_calculation(self, setup_test_db):
        """测试综测成绩计算逻辑"""
        student = await Student.create(
            id="202300502703",
            name="综测计算学生",
            college="计算机学院",
            major="计算机科学与技术",
            class_name="计算机2301",
            grade="2023"
        )
        
        a_score = 15.0
        b_raw = 80.0
        b_weighted = b_raw * 0.7
        c_score = 8.0
        total = a_score + b_weighted + c_score
        
        score = await ComprehensiveScore.create(
            student=student,
            academic_year="2023-2024",
            semester="1",
            a_total_score=a_score,
            b_raw_score=b_raw,
            b_weighted_score=b_weighted,
            b_total_score=b_raw,
            c_total_score=c_score,
            total_score=total
        )
        
        saved = await ComprehensiveScore.get(id=score.id)
        assert saved.a_total_score == a_score
        assert saved.b_raw_score == b_raw
        assert saved.b_weighted_score == b_weighted
        assert saved.total_score == total


class TestModelConsistency:
    """模型一致性测试"""
    
    @pytest.mark.asyncio
    async def test_all_models_have_created_at(self, setup_test_db):
        """测试所有模型都有created_at字段"""
        student = await Student.create(
            id="202300502801", 
            name="测试", 
            college="计算机学院", 
            major="计算机", 
            class_name="计算机2301", 
            grade="2023"
        )
        
        cls = await Class.create(id="test_class_003", name="测试班级", grade="2023", major="计算机", college="计算机学院")
        
        certificate = await Certificate.create(
            student_id=student.id,
            title="测试证书",
            category="C",
            academic_year="2023-2024",
            semester="1"
        )
        
        user = await User.create(username="consistency_test", password="test", role="student")
        
        assert hasattr(student, 'created_at')
        assert hasattr(cls, 'created_at')
        assert hasattr(certificate, 'created_at')
        assert hasattr(user, 'created_at')
    
    @pytest.mark.asyncio
    async def test_foreign_key_cascade(self, setup_test_db):
        """测试外键级联删除"""
        student = await Student.create(
            id="202300502802",
            name="级联测试学生",
            college="计算机学院",
            major="计算机科学与技术",
            class_name="计算机2301",
            grade="2023"
        )
        
        certificate = await Certificate.create(
            student_id=student.id,
            title="级联测试证书",
            category="C",
            academic_year="2023-2024",
            semester="1"
        )
        
        image = await CertificateImage.create(
            certificate=certificate,
            student=student,
            filename="cascade.jpg",
            file_path="/uploads/cascade.jpg"
        )
        
        await certificate.delete()
        
        with pytest.raises(DoesNotExist):
            await CertificateImage.get(id=image.id)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
