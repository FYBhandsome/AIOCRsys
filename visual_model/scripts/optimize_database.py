#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库表结构优化迁移脚本
兼容两种Excel成绩单格式
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = 'D:/PaddleOCR/visual_model/data/database.db'
BACKUP_PATH = 'D:/PaddleOCR/visual_model/data/database_backup'


def backup_database():
    """备份数据库"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"{BACKUP_PATH}_{timestamp}.db"
    
    if os.path.exists(DB_PATH):
        import shutil
        shutil.copy2(DB_PATH, backup_file)
        print(f"数据库已备份到: {backup_file}")
        return backup_file
    return None


def optimize_database():
    """优化数据库表结构"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=== 开始优化数据库表结构 ===")
    
    # 1. 备份现有数据
    print("\n1. 备份现有数据...")
    
    # 2. 删除旧表（按依赖顺序）
    tables_to_drop = [
        'score_details',
        'comprehensive_score_history',
        'academic_score_history',
        'download_logs',
        'file_access_permissions',
        'file_backups',
        'file_chunks',
        'file_metadata',
        'certificate_images',
        'certificate_batches',
        'certificates',
        'upload_records',
        'comprehensive_scores',
        'academic_scores',
        'comprehensive_score_configs',
        'files',
        'students',
        'classes',
        'users'
    ]
    
    print("\n2. 清除现有表...")
    for table in tables_to_drop:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"  - 删除表: {table}")
        except Exception as e:
            print(f"  - 删除表 {table} 失败: {e}")
    
    conn.commit()
    
    # 3. 创建优化后的表结构
    print("\n3. 创建优化后的表结构...")
    
    # 用户表
    cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        email VARCHAR(100) UNIQUE,
        phone VARCHAR(20),
        student_id VARCHAR(50),
        teacher_id VARCHAR(50),
        role VARCHAR(20) DEFAULT 'student',
        status VARCHAR(20) DEFAULT 'active',
        last_login TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("  - 创建表: users")
    
    # 班级表
    cursor.execute('''
    CREATE TABLE classes (
        id VARCHAR(50) PRIMARY KEY,
        name VARCHAR(100),
        grade VARCHAR(20),
        major VARCHAR(100),
        college VARCHAR(100),
        student_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("  - 创建表: classes")
    
    # 学生表（优化后，兼容两种格式）
    cursor.execute('''
    CREATE TABLE students (
        id VARCHAR(50) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        gender VARCHAR(10),
        college VARCHAR(100),
        major VARCHAR(100),
        class_name VARCHAR(50),
        grade VARCHAR(20),
        enrollment_year INTEGER,
        phone VARCHAR(20),
        email VARCHAR(100),
        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("  - 创建表: students")
    
    # 学业成绩表（优化后，兼容两种Excel格式）
    cursor.execute('''
    CREATE TABLE academic_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id VARCHAR(50) NOT NULL,
        student_name VARCHAR(100),
        
        -- 来自学生成绩单.xlsx的字段
        total_score REAL DEFAULT 0,
        course_count INTEGER DEFAULT 0,
        total_credits REAL DEFAULT 0,
        earned_credits REAL DEFAULT 0,
        arithmetic_average REAL DEFAULT 0,
        arithmetic_average_rank INTEGER,
        weighted_average REAL DEFAULT 0,
        weighted_average_rank INTEGER,
        average_gpa REAL DEFAULT 0,
        average_gpa_rank INTEGER,
        failed_course_count INTEGER DEFAULT 0,
        
        -- 学期信息
        semester VARCHAR(20),
        academic_year VARCHAR(20),
        
        -- 来源追踪
        source_file VARCHAR(255),
        source_type VARCHAR(20) DEFAULT 'score_sheet',
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        UNIQUE(student_id, semester, academic_year),
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
    ''')
    print("  - 创建表: academic_scores")
    
    # 综测配置表
    cursor.execute('''
    CREATE TABLE comprehensive_score_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100),
        a_weight REAL DEFAULT 20.0,
        b_weight REAL DEFAULT 70.0,
        c_weight REAL DEFAULT 10.0,
        academic_score_field VARCHAR(50) DEFAULT 'weighted_average',
        academic_score_scale REAL DEFAULT 1.0,
        rules TEXT,
        is_default BOOLEAN DEFAULT 0,
        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("  - 创建表: comprehensive_score_configs")
    
    # 综测成绩表（优化后，兼容综测计算表格格式）
    cursor.execute('''
    CREATE TABLE comprehensive_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id VARCHAR(50) NOT NULL,
        student_name VARCHAR(100),
        class_name VARCHAR(50),
        major VARCHAR(100),
        
        -- A类成绩（思想道德素质）
        a1_score REAL DEFAULT 0,
        a2_score REAL DEFAULT 0,
        a3_score REAL DEFAULT 0,
        a_total_score REAL DEFAULT 0,
        a_weighted_score REAL DEFAULT 0,
        
        -- B类成绩（学习成绩）
        b_raw_score REAL DEFAULT 0,
        b_weighted_score REAL DEFAULT 0,
        
        -- C类成绩（素质拓展）
        c1_score REAL DEFAULT 0,
        c2_score REAL DEFAULT 0,
        c3_score REAL DEFAULT 0,
        c4_score REAL DEFAULT 0,
        c_total_score REAL DEFAULT 0,
        c_weighted_score REAL DEFAULT 0,
        
        -- 总成绩
        total_score REAL DEFAULT 0,
        ranking INTEGER,
        
        -- 学期信息
        semester VARCHAR(20),
        academic_year VARCHAR(20),
        config_id INTEGER,
        
        -- 来源追踪
        source_file VARCHAR(255),
        source_type VARCHAR(20) DEFAULT 'comprehensive_table',
        
        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        UNIQUE(student_id, semester, academic_year),
        FOREIGN KEY (student_id) REFERENCES students(id),
        FOREIGN KEY (config_id) REFERENCES comprehensive_score_configs(id)
    )
    ''')
    print("  - 创建表: comprehensive_scores")
    
    # 加减分明细表
    cursor.execute('''
    CREATE TABLE score_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id VARCHAR(50) NOT NULL,
        comprehensive_score_id INTEGER,
        
        category VARCHAR(10),
        sub_category VARCHAR(10),
        item_name VARCHAR(255),
        item_description TEXT,
        score REAL DEFAULT 0,
        
        semester VARCHAR(20),
        academic_year VARCHAR(20),
        
        source VARCHAR(50),
        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (student_id) REFERENCES students(id),
        FOREIGN KEY (comprehensive_score_id) REFERENCES comprehensive_scores(id)
    )
    ''')
    print("  - 创建表: score_details")
    
    # 证书表
    cursor.execute('''
    CREATE TABLE certificates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id VARCHAR(50) NOT NULL,
        
        certificate_no VARCHAR(100),
        certificate_type VARCHAR(50),
        title VARCHAR(255),
        level VARCHAR(50),
        issuer VARCHAR(255),
        issue_date VARCHAR(50),
        expiry_date VARCHAR(50),
        
        category VARCHAR(10) DEFAULT 'C',
        sub_category VARCHAR(10),
        score REAL DEFAULT 0,
        classification_reason TEXT,
        
        raw_text TEXT,
        ocr_result TEXT,
        certificate_info TEXT,
        
        status VARCHAR(20) DEFAULT 'pending',
        reviewed_by VARCHAR(50),
        reviewed_at TIMESTAMP,
        review_comment TEXT,
        
        image_count INTEGER DEFAULT 0,
        primary_image_id INTEGER,
        
        source VARCHAR(20) DEFAULT 'upload',
        upload_batch_id VARCHAR(50),
        
        is_valid BOOLEAN DEFAULT 1,
        invalid_reason TEXT,
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
    ''')
    print("  - 创建表: certificates")
    
    # 证书图片表
    cursor.execute('''
    CREATE TABLE certificate_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        certificate_id INTEGER NOT NULL,
        student_id VARCHAR(50),
        
        file_id VARCHAR(50),
        filename VARCHAR(255) NOT NULL,
        file_path VARCHAR(500) NOT NULL,
        file_size INTEGER DEFAULT 0,
        file_hash VARCHAR(64),
        
        image_width INTEGER,
        image_height INTEGER,
        image_format VARCHAR(10),
        
        is_primary BOOLEAN DEFAULT 0,
        image_order INTEGER DEFAULT 0,
        page_number INTEGER,
        
        ocr_processed BOOLEAN DEFAULT 0,
        ocr_text TEXT,
        ocr_result TEXT,
        
        thumbnail_path VARCHAR(500),
        
        upload_ip VARCHAR(50),
        upload_device VARCHAR(100),
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (certificate_id) REFERENCES certificates(id),
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
    ''')
    print("  - 创建表: certificate_images")
    
    # 文件元数据表
    cursor.execute('''
    CREATE TABLE file_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id VARCHAR(100) UNIQUE NOT NULL,
        original_filename VARCHAR(255) NOT NULL,
        stored_filename VARCHAR(255) NOT NULL,
        
        file_type VARCHAR(50) NOT NULL,
        file_category VARCHAR(50),
        mime_type VARCHAR(100),
        file_extension VARCHAR(20),
        
        file_size INTEGER DEFAULT 0,
        file_hash VARCHAR(64),
        
        storage_path VARCHAR(500) NOT NULL,
        storage_directory VARCHAR(255),
        
        owner_id VARCHAR(50) NOT NULL,
        owner_type VARCHAR(20) DEFAULT 'student',
        
        upload_batch_id VARCHAR(50),
        chunk_upload BOOLEAN DEFAULT 0,
        chunk_count INTEGER DEFAULT 0,
        chunk_uploaded INTEGER DEFAULT 0,
        
        status VARCHAR(20) DEFAULT 'active',
        is_encrypted BOOLEAN DEFAULT 0,
        is_public BOOLEAN DEFAULT 0,
        
        access_count INTEGER DEFAULT 0,
        download_count INTEGER DEFAULT 0,
        
        last_accessed_at TIMESTAMP,
        archived_at TIMESTAMP,
        
        metadata TEXT,
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("  - 创建表: file_metadata")
    
    # 上传记录表
    cursor.execute('''
    CREATE TABLE upload_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id VARCHAR(50),
        file_name VARCHAR(255),
        file_type VARCHAR(50),
        
        upload_by VARCHAR(50),
        upload_role VARCHAR(20) DEFAULT 'student',
        
        academic_year VARCHAR(20),
        semester VARCHAR(20),
        class_id VARCHAR(50),
        
        status VARCHAR(20) DEFAULT 'pending',
        processed_count INTEGER DEFAULT 0,
        failed_count INTEGER DEFAULT 0,
        
        error_message TEXT,
        processing_log TEXT,
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed_at TIMESTAMP
    )
    ''')
    print("  - 创建表: upload_records")
    
    # 下载日志表
    cursor.execute('''
    CREATE TABLE download_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id VARCHAR(100),
        file_name VARCHAR(255),
        
        downloader_id VARCHAR(50),
        downloader_type VARCHAR(20),
        downloader_ip VARCHAR(50),
        
        download_status VARCHAR(20) DEFAULT 'success',
        download_size INTEGER DEFAULT 0,
        error_message TEXT,
        
        user_agent VARCHAR(500),
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("  - 创建表: download_logs")
    
    # 学业成绩历史表
    cursor.execute('''
    CREATE TABLE academic_score_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        academic_score_id INTEGER,
        student_id VARCHAR(50),
        
        version INTEGER DEFAULT 1,
        
        total_score REAL DEFAULT 0,
        course_count INTEGER DEFAULT 0,
        total_credits REAL DEFAULT 0,
        earned_credits REAL DEFAULT 0,
        arithmetic_average REAL DEFAULT 0,
        weighted_average REAL DEFAULT 0,
        average_gpa REAL DEFAULT 0,
        average_credit_gpa REAL DEFAULT 0,
        failed_course_count INTEGER DEFAULT 0,
        
        semester VARCHAR(20),
        academic_year VARCHAR(20),
        
        source_file VARCHAR(255),
        raw_data TEXT,
        
        change_type VARCHAR(20) DEFAULT 'create',
        change_reason TEXT,
        changed_by VARCHAR(50),
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
    ''')
    print("  - 创建表: academic_score_history")
    
    # 综测成绩历史表
    cursor.execute('''
    CREATE TABLE comprehensive_score_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        comprehensive_score_id INTEGER,
        student_id VARCHAR(50),
        
        version INTEGER DEFAULT 1,
        
        a_total_score REAL DEFAULT 0,
        a1_score REAL DEFAULT 0,
        a2_score REAL DEFAULT 0,
        a3_score REAL DEFAULT 0,
        
        b_total_score REAL DEFAULT 0,
        
        c_total_score REAL DEFAULT 0,
        c1_score REAL DEFAULT 0,
        c2_score REAL DEFAULT 0,
        c3_score REAL DEFAULT 0,
        c4_score REAL DEFAULT 0,
        
        total_score REAL DEFAULT 0,
        
        semester VARCHAR(20),
        academic_year VARCHAR(20),
        
        config_id INTEGER,
        raw_data TEXT,
        
        change_type VARCHAR(20) DEFAULT 'create',
        change_reason TEXT,
        changed_by VARCHAR(50),
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
    ''')
    print("  - 创建表: comprehensive_score_history")
    
    # 4. 创建索引
    print("\n4. 创建索引...")
    
    indexes = [
        "CREATE INDEX idx_students_class ON students(class_name)",
        "CREATE INDEX idx_students_major ON students(major)",
        "CREATE INDEX idx_academic_scores_student ON academic_scores(student_id)",
        "CREATE INDEX idx_academic_scores_semester ON academic_scores(semester, academic_year)",
        "CREATE INDEX idx_comprehensive_scores_student ON comprehensive_scores(student_id)",
        "CREATE INDEX idx_comprehensive_scores_ranking ON comprehensive_scores(ranking)",
        "CREATE INDEX idx_certificates_student ON certificates(student_id)",
        "CREATE INDEX idx_certificates_status ON certificates(status)",
        "CREATE INDEX idx_file_metadata_owner ON file_metadata(owner_id)",
        "CREATE INDEX idx_file_metadata_type ON file_metadata(file_type)",
    ]
    
    for idx_sql in indexes:
        try:
            cursor.execute(idx_sql)
            print(f"  - 创建索引: {idx_sql.split('INDEX')[1].split('ON')[0].strip()}")
        except Exception as e:
            print(f"  - 创建索引失败: {e}")
    
    # 5. 插入默认配置
    print("\n5. 插入默认配置...")
    cursor.execute('''
    INSERT INTO comprehensive_score_configs 
    (name, a_weight, b_weight, c_weight, academic_score_field, is_default, status)
    VALUES 
    ('默认配置', 20.0, 70.0, 10.0, 'weighted_average', 1, 'active')
    ''')
    print("  - 插入默认综测配置")
    
    # 6. 插入默认管理员账户
    print("\n6. 插入默认管理员账户...")
    cursor.execute('''
    INSERT INTO users (username, password_hash, role, status)
    VALUES ('admin', 'admin123', 'admin', 'active')
    ''')
    print("  - 插入默认管理员账户 (admin/admin123)")
    
    conn.commit()
    conn.close()
    
    print("\n=== 数据库优化完成 ===")
    print(f"数据库路径: {DB_PATH}")


def verify_database():
    """验证数据库结构"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n=== 验证数据库结构 ===")
    
    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print(f"\n共有 {len(tables)} 个表:")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        print(f"\n  {table_name} ({len(columns)} 字段, {count} 行)")
    
    conn.close()


if __name__ == '__main__':
    print("=" * 60)
    print("数据库表结构优化迁移脚本")
    print("=" * 60)
    
    # 备份数据库
    backup_database()
    
    # 优化数据库
    optimize_database()
    
    # 验证数据库
    verify_database()
