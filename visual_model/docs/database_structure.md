# 数据库结构文档

## 综测计算助手 - 数据库设计

**文档版本**: 1.0  
**更新日期**: 2026-03-01  
**数据库类型**: SQLite / MySQL / PostgreSQL (Tortoise ORM支持)

---

## 数据表概览

| 表名 | 描述 | 主要字段 |
|------|------|----------|
| users | 用户信息表 | id, username, role, student_id |
| classes | 班级信息表 | id, name, grade, major |
| students | 学生信息表 | id, name, class_name, total_score |
| academic_scores | 学业成绩表 | student_id, semester, weighted_average |
| comprehensive_scores | 综测成绩表 | student_id, total_score, ranking |
| comprehensive_score_configs | 综测配置表 | name, a_weight, b_weight, c_weight |
| score_details | 综测明细表 | student_id, category_type, score |
| certificates | 证书信息表 | student_id, title, category, status |
| certificate_images | 证书图片表 | certificate_id, file_path |
| files | 文件管理表 | id, filename, file_path |

---

## 详细表结构

### 1. users (用户信息表)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,        -- 用户名
    email VARCHAR(255) UNIQUE,                   -- 邮箱
    password VARCHAR(255) NOT NULL,              -- 密码(加密)
    role VARCHAR(20) DEFAULT 'student',          -- 角色: student, teacher, admin
    
    student_id VARCHAR(50) UNIQUE,               -- 学号
    real_name VARCHAR(100),                      -- 真实姓名
    class_id VARCHAR(50),                        -- 班级ID
    
    is_active BOOLEAN DEFAULT TRUE,              -- 是否激活
    is_email_verified BOOLEAN DEFAULT FALSE,     -- 邮箱验证状态
    
    reset_token VARCHAR(255),                    -- 密码重置令牌
    reset_token_expires DATETIME,                -- 令牌过期时间
    verification_code VARCHAR(10),               -- 验证码
    code_expires_at DATETIME,                    -- 验证码过期时间
    
    last_login DATETIME,                         -- 最后登录时间
    extra_info JSON,                             -- 扩展信息
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**索引**:
- `idx_users_username` ON (username)
- `idx_users_student_id` ON (student_id)
- `idx_users_role` ON (role)

---

### 2. classes (班级信息表)

```sql
CREATE TABLE classes (
    id VARCHAR(50) PRIMARY KEY,                  -- 班级编号
    name VARCHAR(100) NOT NULL,                  -- 班级名称
    grade VARCHAR(20),                           -- 年级
    major VARCHAR(100),                          -- 专业
    college VARCHAR(100),                        -- 学院
    student_count INTEGER DEFAULT 0,             -- 学生人数
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

### 3. students (学生信息表)

```sql
CREATE TABLE students (
    id VARCHAR(50) PRIMARY KEY,                  -- 学号
    name VARCHAR(100) NOT NULL,                  -- 姓名
    college VARCHAR(100),                        -- 学院
    major VARCHAR(100),                          -- 专业
    class_name VARCHAR(50),                      -- 班级
    grade VARCHAR(20),                           -- 年级
    
    total_score FLOAT DEFAULT 0.0,               -- 综测总成绩
    dormitory_number VARCHAR(50),                -- 宿舍编号
    dormitory_score FLOAT,                       -- 宿舍成绩
    physical_test_score FLOAT,                   -- 体测成绩
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**索引**:
- `idx_students_class_name` ON (class_name)
- `idx_students_grade` ON (grade)

---

### 4. academic_scores (学业成绩表)

```sql
CREATE TABLE academic_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(50) NOT NULL,             -- 学号
    student_name VARCHAR(100),                   -- 姓名
    college VARCHAR(100),                        -- 学院
    grade VARCHAR(20),                           -- 年级
    major VARCHAR(100),                          -- 专业
    class_name VARCHAR(50),                      -- 班级
    
    -- 成绩统计
    total_score FLOAT DEFAULT 0.0,               -- 总分
    total_required_credits FLOAT DEFAULT 0.0,    -- 总应获得学分
    course_count INTEGER DEFAULT 0,              -- 门数
    total_credits FLOAT DEFAULT 0.0,             -- 总学分
    earned_credits FLOAT DEFAULT 0.0,            -- 获得学分
    failed_credits FLOAT DEFAULT 0.0,            -- 不及格学分
    
    -- 通过率和平均分
    pass_rate FLOAT DEFAULT 0.0,                 -- 通过率(%)
    arithmetic_average FLOAT DEFAULT 0.0,        -- 算术平均分
    arithmetic_average_rank INTEGER,             -- 算术平均分排名
    weighted_average FLOAT DEFAULT 0.0,          -- 学分加权平均分
    weighted_average_rank INTEGER,               -- 学分加权平均分排名
    
    -- 绩点相关
    average_gpa FLOAT DEFAULT 0.0,               -- 平均绩点
    average_gpa_rank INTEGER,                    -- 平均绩点排名
    average_credit_gpa FLOAT DEFAULT 0.0,        -- 平均学分绩点
    average_credit_gpa_rank INTEGER,             -- 平均学分绩点排名
    credit_gpa_sum FLOAT DEFAULT 0.0,            -- 学分绩点和
    credit_gpa_sum_rank INTEGER,                 -- 学分绩点和排名
    
    failed_course_count INTEGER DEFAULT 0,       -- 不及格门次
    
    -- 学期信息
    semester VARCHAR(20),                        -- 学期 (如: 2024-1)
    academic_year VARCHAR(20),                   -- 学年 (如: 2024-2025)
    
    -- 来源追踪
    source_file VARCHAR(255),                    -- 来源文件名
    source_type VARCHAR(20) DEFAULT 'score_sheet',
    remarks TEXT,                                -- 备注
    details JSON,                                -- 详细课程成绩
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_id) REFERENCES students(id),
    UNIQUE (student_id, semester, academic_year)
);
```

**索引**:
- `idx_academic_scores_student_id` ON (student_id)
- `idx_academic_scores_semester` ON (semester, academic_year)

---

### 5. comprehensive_scores (综测成绩表)

```sql
CREATE TABLE comprehensive_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(50) NOT NULL,             -- 学号
    student_name VARCHAR(100),                   -- 姓名
    class_name VARCHAR(50),                      -- 班级
    major VARCHAR(100),                          -- 专业
    
    -- A类材料成绩 (思想道德素质)
    a_total_score FLOAT DEFAULT 0.0,             -- A类总成绩
    a1_score FLOAT DEFAULT 0.0,                  -- A1类成绩
    a2_score FLOAT DEFAULT 0.0,                  -- A2类成绩
    a3_score FLOAT DEFAULT 0.0,                  -- A3类成绩
    a_weighted_score FLOAT DEFAULT 0.0,          -- A类加权成绩(20%)
    
    -- B类材料成绩 (学习成绩)
    b_raw_score FLOAT DEFAULT 0.0,               -- B类原始成绩
    b_weighted_score FLOAT DEFAULT 0.0,          -- B类加权成绩(70%)
    
    -- C类材料成绩 (素质拓展)
    c_total_score FLOAT DEFAULT 0.0,             -- C类总成绩
    c1_score FLOAT DEFAULT 0.0,                  -- C1类-科技竞赛
    c2_score FLOAT DEFAULT 0.0,                  -- C2类-体育竞技
    c3_score FLOAT DEFAULT 0.0,                  -- C3类-文化竞赛
    c4_score FLOAT DEFAULT 0.0,                  -- C4类-创新创业
    c_weighted_score FLOAT DEFAULT 0.0,          -- C类加权成绩(10%)
    
    -- 总成绩
    total_score FLOAT DEFAULT 0.0,               -- 综测总成绩
    ranking INTEGER,                             -- 班级排名
    
    -- 学期信息
    semester VARCHAR(20) NOT NULL,               -- 学期
    academic_year VARCHAR(20) NOT NULL,          -- 学年
    
    config_id INTEGER,                           -- 配置ID
    source_file VARCHAR(255),                    -- 来源文件
    source_type VARCHAR(20) DEFAULT 'comprehensive_table',
    remarks TEXT,                                -- 备注
    details JSON,                                -- 详细分数信息
    status VARCHAR(20) DEFAULT 'active',         -- 状态
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (student_id, semester, academic_year)
);
```

**索引**:
- `idx_comprehensive_scores_student_id` ON (student_id)
- `idx_comprehensive_scores_ranking` ON (ranking)
- `idx_comprehensive_scores_semester` ON (semester, academic_year)

---

### 6. comprehensive_score_configs (综测配置表)

```sql
CREATE TABLE comprehensive_score_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,                  -- 配置名称
    description TEXT,                            -- 配置描述
    
    -- 权重配置 (总和应为100)
    a_weight FLOAT DEFAULT 20.0,                 -- A类权重(%)
    b_weight FLOAT DEFAULT 70.0,                 -- B类权重(%)
    c_weight FLOAT DEFAULT 10.0,                 -- C类权重(%)
    
    -- 学业成绩配置
    academic_score_field VARCHAR(50) DEFAULT 'weighted_average',
    academic_score_scale FLOAT DEFAULT 1.0,      -- 缩放系数
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    
    -- 适用范围
    applicable_grade VARCHAR(20),
    applicable_semester VARCHAR(20),
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

### 7. score_details (综测明细表)

```sql
CREATE TABLE score_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(50) NOT NULL,             -- 学生ID
    semester VARCHAR(20) NOT NULL,               -- 学期
    academic_year VARCHAR(20) NOT NULL,          -- 学年
    
    category_type VARCHAR(10) NOT NULL,          -- 类别: A1, A2, A3, C1, C2, C3, C4
    item_name VARCHAR(255) NOT NULL,             -- 项目名称
    score FLOAT DEFAULT 0.0,                     -- 分数(正数加分,负数扣分)
    
    description TEXT,                            -- 详细说明
    source VARCHAR(50),                          -- 来源: manual, import, ocr
    certificate_id INTEGER,                      -- 关联证书ID
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**索引**:
- `idx_score_details_student_id` ON (student_id)
- `idx_score_details_category_type` ON (category_type)
- `idx_score_details_semester` ON (semester, academic_year)

---

### 8. certificates (证书信息表)

```sql
CREATE TABLE certificates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(50) NOT NULL,             -- 学生ID
    
    -- 证书基本信息
    certificate_no VARCHAR(100),                 -- 证书编号
    certificate_type VARCHAR(50),                -- 证书类型
    title VARCHAR(255),                          -- 证书标题
    level VARCHAR(50),                           -- 级别: 国家级,省级,市级,校级
    issuer VARCHAR(255),                         -- 颁发机构
    issue_date VARCHAR(50),                      -- 颁发日期
    expiry_date VARCHAR(50),                     -- 有效期
    
    -- 分类信息
    category VARCHAR(10) DEFAULT 'C',            -- 类别: A, C
    sub_category VARCHAR(10),                    -- 子类别: C1, C2, C3, C4
    score FLOAT DEFAULT 0.0,                     -- 加分分数
    classification_reason TEXT,                  -- 分类原因
    
    -- OCR信息
    raw_text TEXT,                               -- OCR原始文本
    ocr_result JSON,                             -- OCR详细结果
    certificate_info JSON,                       -- 结构化信息
    
    -- 审核状态
    status VARCHAR(20) DEFAULT 'pending',        -- pending, approved, rejected
    reviewed_by VARCHAR(50),                     -- 审核人
    reviewed_at DATETIME,                        -- 审核时间
    review_comment TEXT,                         -- 审核意见
    
    -- 图片信息
    image_count INTEGER DEFAULT 0,               -- 图片数量
    primary_image_id INTEGER,                    -- 主图片ID
    
    -- 来源信息
    source VARCHAR(20) DEFAULT 'upload',         -- upload, import, manual
    upload_batch_id VARCHAR(50),                 -- 上传批次ID
    
    is_valid BOOLEAN DEFAULT TRUE,               -- 是否有效
    invalid_reason TEXT,                         -- 无效原因
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**索引**:
- `idx_certificates_student_id` ON (student_id)
- `idx_certificates_category` ON (category)
- `idx_certificates_status` ON (status)
- `idx_certificates_student_status` ON (student_id, status)

---

### 9. certificate_images (证书图片表)

```sql
CREATE TABLE certificate_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    certificate_id INTEGER NOT NULL,             -- 关联证书ID
    student_id VARCHAR(50) NOT NULL,             -- 学生ID(冗余)
    
    -- 文件信息
    file_id VARCHAR(50),                         -- 文件管理ID
    filename VARCHAR(255) NOT NULL,              -- 原始文件名
    file_path VARCHAR(500) NOT NULL,             -- 存储路径
    file_size INTEGER DEFAULT 0,                 -- 文件大小
    file_hash VARCHAR(64),                       -- MD5哈希
    
    -- 图片信息
    image_width INTEGER,                         -- 宽度
    image_height INTEGER,                        -- 高度
    image_format VARCHAR(10),                    -- 格式: jpg, png, pdf
    
    -- 排序信息
    is_primary BOOLEAN DEFAULT FALSE,            -- 是否主图片
    image_order INTEGER DEFAULT 0,               -- 排序顺序
    page_number INTEGER,                         -- 页码
    
    -- OCR信息
    ocr_processed BOOLEAN DEFAULT FALSE,         -- 是否已OCR
    ocr_text TEXT,                               -- OCR文本
    ocr_result JSON,                             -- OCR结果
    
    thumbnail_path VARCHAR(500),                 -- 缩略图路径
    
    -- 上传信息
    upload_ip VARCHAR(50),                       -- 上传IP
    upload_device VARCHAR(100),                  -- 上传设备
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (certificate_id) REFERENCES certificates(id)
);
```

---

### 10. files (文件管理表)

```sql
CREATE TABLE files (
    id VARCHAR(50) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,              -- 文件名
    file_path VARCHAR(500) NOT NULL,             -- 存储路径
    file_size INTEGER NOT NULL,                  -- 文件大小
    file_type VARCHAR(50) NOT NULL,              -- 文件类型
    student_id VARCHAR(50),                      -- 关联学生ID
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 综测成绩计算规则

### 成绩组成

| 类别 | 权重 | 说明 |
|------|------|------|
| A类 | 20% | 思想道德素质 (A1+A2+A3) |
| B类 | 70% | 学业成绩 (加权平均分) |
| C类 | 10% | 素质拓展 (C1+C2+C3+C4) |

### A类材料明细

| 子类 | 项目 | 分值范围 |
|------|------|----------|
| A1 | 思想政治表现 | -10 ~ +10 |
| A2 | 道德品质表现 | -10 ~ +10 |
| A3 | 集体活动参与 | -10 ~ +10 |

### C类材料明细

| 子类 | 项目 | 说明 |
|------|------|------|
| C1 | 科技竞赛 | 学科竞赛、科研项目 |
| C2 | 体育竞技 | 体育比赛、运动会 |
| C3 | 文化竞赛 | 文艺活动、演讲比赛 |
| C4 | 创新创业 | 创业项目、专利软著 |

---

## 变更记录

| 日期 | 版本 | 变更内容 | 变更人 |
|------|------|----------|--------|
| 2026-03-01 | 1.0 | 初始版本 | System |

---

## 注意事项

1. 所有时间字段使用 `DATETIME` 类型，存储UTC时间
2. `student_id` 字段为学号，格式通常为 `202300502128`
3. `semester` 字段格式为 `1`、`2` 表示第一、第二学期
4. `academic_year` 字段格式为 `2024-2025`
5. 删除操作建议使用软删除（设置 `is_valid = FALSE`）
