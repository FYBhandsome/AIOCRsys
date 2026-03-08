from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "academic_score_history" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "academic_score_id" INT NOT NULL /* 关联的学业成绩ID */,
    "student_id" VARCHAR(50) NOT NULL /* 学号 */,
    "version" INT NOT NULL DEFAULT 1 /* 版本号 */,
    "total_score" REAL NOT NULL DEFAULT 0 /* 总分 */,
    "course_count" INT NOT NULL DEFAULT 0 /* 门数 */,
    "total_credits" REAL NOT NULL DEFAULT 0 /* 总学分 */,
    "earned_credits" REAL NOT NULL DEFAULT 0 /* 获得学分 */,
    "arithmetic_average" REAL NOT NULL DEFAULT 0 /* 算术平均分 */,
    "weighted_average" REAL NOT NULL DEFAULT 0 /* 学分加权平均分 */,
    "average_gpa" REAL NOT NULL DEFAULT 0 /* 平均绩点 */,
    "average_credit_gpa" REAL NOT NULL DEFAULT 0 /* 平均学分绩点 */,
    "failed_course_count" INT NOT NULL DEFAULT 0 /* 不及格门次 */,
    "semester" VARCHAR(20) NOT NULL /* 学期 */,
    "academic_year" VARCHAR(20) NOT NULL /* 学年 */,
    "source_file" VARCHAR(255) /* 来源文件名 */,
    "raw_data" JSON /* 原始数据快照 */,
    "change_type" VARCHAR(20) NOT NULL DEFAULT 'create' /* 变更类型: create, update, import */,
    "change_reason" TEXT /* 变更原因 */,
    "changed_by" VARCHAR(50) /* 操作人 */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* 学业成绩历史记录表 */;
CREATE INDEX IF NOT EXISTS "idx_academic_sc_student_85d2e3" ON "academic_score_history" ("student_id");
CREATE INDEX IF NOT EXISTS "idx_academic_sc_academi_41ddbc" ON "academic_score_history" ("academic_score_id");
CREATE INDEX IF NOT EXISTS "idx_academic_sc_semeste_4d754f" ON "academic_score_history" ("semester", "academic_year");
CREATE TABLE IF NOT EXISTS "certificates" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "student_id" VARCHAR(50) NOT NULL /* 学生ID（学号） */,
    "filename" VARCHAR(255) /* 原始文件名 */,
    "certificate_no" VARCHAR(100) /* 证书编号 */,
    "certificate_type" VARCHAR(50) /* 证书类型：四级、六级、竞赛、活动、荣誉等 */,
    "title" VARCHAR(255) /* 证书标题\/名称 */,
    "level" VARCHAR(50) /* 证书级别：国家级、省级、市级、校级、院级 */,
    "issuer" VARCHAR(255) /* 颁发机构 */,
    "issue_date" VARCHAR(50) /* 颁发日期 */,
    "expiry_date" VARCHAR(50) /* 有效期至 */,
    "category" VARCHAR(10) NOT NULL DEFAULT 'C' /* 证书类别: A-思想道德, C-素质拓展 */,
    "sub_category" VARCHAR(10) /* 子类别: C1-科技类, C2-体育类, C3-文化类, C4-创新创业 */,
    "score" REAL NOT NULL DEFAULT 0 /* 证书加分分数 */,
    "classification_reason" TEXT /* 分类原因\/评分依据 */,
    "raw_text" TEXT /* OCR识别原始文本 */,
    "ocr_result" JSON /* OCR识别详细结果 */,
    "certificate_info" JSON /* 证书结构化信息 */,
    "status" VARCHAR(20) NOT NULL DEFAULT 'pending' /* 状态: pending(待审核), approved(已通过), rejected(已拒绝), cancelled(已取消) */,
    "reviewed_by" VARCHAR(50) /* 审核人 */,
    "reviewed_at" TIMESTAMP /* 审核时间 */,
    "review_comment" TEXT /* 审核意见 */,
    "image_count" INT NOT NULL DEFAULT 0 /* 关联图片数量 */,
    "primary_image_id" INT /* 主图片ID */,
    "source" VARCHAR(20) NOT NULL DEFAULT 'upload' /* 来源: upload(上传), import(导入), manual(手动录入) */,
    "upload_batch_id" VARCHAR(50) /* 上传批次ID */,
    "is_valid" INT NOT NULL DEFAULT 1 /* 是否有效 */,
    "invalid_reason" TEXT /* 无效原因 */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* 证书基本信息表 */;
CREATE INDEX IF NOT EXISTS "idx_certificate_student_45bbc2" ON "certificates" ("student_id");
CREATE INDEX IF NOT EXISTS "idx_certificate_categor_9bffcb" ON "certificates" ("category");
CREATE INDEX IF NOT EXISTS "idx_certificate_sub_cat_17255e" ON "certificates" ("sub_category");
CREATE INDEX IF NOT EXISTS "idx_certificate_status_5a8bdc" ON "certificates" ("status");
CREATE INDEX IF NOT EXISTS "idx_certificate_certifi_7e88cc" ON "certificates" ("certificate_type");
CREATE INDEX IF NOT EXISTS "idx_certificate_level_ad7f54" ON "certificates" ("level");
CREATE INDEX IF NOT EXISTS "idx_certificate_issue_d_8f1964" ON "certificates" ("issue_date");
CREATE INDEX IF NOT EXISTS "idx_certificate_student_e95cbe" ON "certificates" ("student_id", "status");
CREATE TABLE IF NOT EXISTS "certificate_batches" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "batch_id" VARCHAR(50) NOT NULL UNIQUE /* 批次唯一标识 */,
    "student_id" VARCHAR(50) NOT NULL /* 学生ID */,
    "total_count" INT NOT NULL DEFAULT 0 /* 总上传数量 */,
    "success_count" INT NOT NULL DEFAULT 0 /* 成功处理数量 */,
    "failed_count" INT NOT NULL DEFAULT 0 /* 失败数量 */,
    "status" VARCHAR(20) NOT NULL DEFAULT 'pending' /* 状态: pending, processing, completed, failed */,
    "error_message" TEXT /* 错误信息 */,
    "processing_log" JSON /* 处理日志 */,
    "upload_ip" VARCHAR(50) /* 上传IP */,
    "upload_device" VARCHAR(100) /* 上传设备 */,
    "started_at" TIMESTAMP /* 开始处理时间 */,
    "completed_at" TIMESTAMP /* 完成时间 */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* 证书上传批次表 */;
CREATE INDEX IF NOT EXISTS "idx_certificate_batch_i_d7c631" ON "certificate_batches" ("batch_id");
CREATE INDEX IF NOT EXISTS "idx_certificate_student_fe7a4b" ON "certificate_batches" ("student_id");
CREATE INDEX IF NOT EXISTS "idx_certificate_status_bd17a1" ON "certificate_batches" ("status");
CREATE INDEX IF NOT EXISTS "idx_certificate_created_56cb76" ON "certificate_batches" ("created_at");
CREATE TABLE IF NOT EXISTS "chat_histories" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "user_id" VARCHAR(50) NOT NULL /* 用户ID */,
    "session_id" VARCHAR(100) NOT NULL /* 会话ID */,
    "role" VARCHAR(20) NOT NULL /* 角色: user, assistant */,
    "content" TEXT NOT NULL /* 消息内容 */,
    "message_type" VARCHAR(20) NOT NULL DEFAULT 'text' /* 消息类型: text, image, file */,
    "metadata" JSON /* 元数据 */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* 对话历史表 */;
CREATE INDEX IF NOT EXISTS "idx_chat_histor_user_id_62e455" ON "chat_histories" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_chat_histor_session_60c778" ON "chat_histories" ("session_id");
CREATE INDEX IF NOT EXISTS "idx_chat_histor_created_dff2cc" ON "chat_histories" ("created_at");
CREATE TABLE IF NOT EXISTS "classes" (
    "id" VARCHAR(50) NOT NULL PRIMARY KEY /* 班级编号，如230521 */,
    "name" VARCHAR(100) NOT NULL /* 班级名称 */,
    "grade" VARCHAR(20) NOT NULL /* 年级 */,
    "major" VARCHAR(100) NOT NULL /* 专业 */,
    "college" VARCHAR(100) NOT NULL /* 学院 */,
    "student_count" INT NOT NULL DEFAULT 0 /* 学生人数 */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* 班级信息表 */;
CREATE TABLE IF NOT EXISTS "comprehensive_score_configs" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(100) NOT NULL /* 配置名称 */,
    "description" TEXT /* 配置描述 */,
    "a_weight" REAL NOT NULL DEFAULT 20 /* A类材料权重（%） */,
    "b_weight" REAL NOT NULL DEFAULT 70 /* B类材料（学习成绩）权重（%） */,
    "c_weight" REAL NOT NULL DEFAULT 10 /* C类材料权重（%） */,
    "academic_score_field" VARCHAR(50) NOT NULL DEFAULT 'weighted_average' /* 学业成绩使用的字段 */,
    "academic_score_scale" REAL NOT NULL DEFAULT 1 /* 学业成绩缩放系数（GPA转百分制时用25） */,
    "is_active" INT NOT NULL DEFAULT 1 /* 是否启用此配置 */,
    "is_default" INT NOT NULL DEFAULT 0 /* 是否为默认配置 */,
    "applicable_grade" VARCHAR(20) /* 适用年级 */,
    "applicable_semester" VARCHAR(20) /* 适用学期 */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* 综测成绩配置表 */;
CREATE TABLE IF NOT EXISTS "comprehensive_score_history" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "comprehensive_score_id" INT NOT NULL /* 关联的综测成绩ID */,
    "student_id" VARCHAR(50) NOT NULL /* 学号 */,
    "version" INT NOT NULL DEFAULT 1 /* 版本号 */,
    "a_total_score" REAL NOT NULL DEFAULT 0 /* A类总分 */,
    "a1_score" REAL NOT NULL DEFAULT 0 /* A1类成绩 */,
    "a2_score" REAL NOT NULL DEFAULT 0 /* A2类成绩 */,
    "a3_score" REAL NOT NULL DEFAULT 0 /* A3类成绩 */,
    "b_total_score" REAL NOT NULL DEFAULT 0 /* B类总分 */,
    "c_total_score" REAL NOT NULL DEFAULT 0 /* C类总分 */,
    "c1_score" REAL NOT NULL DEFAULT 0 /* C1类成绩 */,
    "c2_score" REAL NOT NULL DEFAULT 0 /* C2类成绩 */,
    "c3_score" REAL NOT NULL DEFAULT 0 /* C3类成绩 */,
    "c4_score" REAL NOT NULL DEFAULT 0 /* C4类成绩 */,
    "total_score" REAL NOT NULL DEFAULT 0 /* 综测总成绩 */,
    "semester" VARCHAR(20) NOT NULL /* 学期 */,
    "academic_year" VARCHAR(20) NOT NULL /* 学年 */,
    "config_id" INT /* 使用的配置ID */,
    "raw_data" JSON /* 原始数据快照 */,
    "change_type" VARCHAR(20) NOT NULL DEFAULT 'create' /* 变更类型: create, update, calculate */,
    "change_reason" TEXT /* 变更原因 */,
    "changed_by" VARCHAR(50) /* 操作人 */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* 综测成绩历史记录表 */;
CREATE INDEX IF NOT EXISTS "idx_comprehensi_student_07694f" ON "comprehensive_score_history" ("student_id");
CREATE INDEX IF NOT EXISTS "idx_comprehensi_compreh_98cfd7" ON "comprehensive_score_history" ("comprehensive_score_id");
CREATE INDEX IF NOT EXISTS "idx_comprehensi_semeste_706351" ON "comprehensive_score_history" ("semester", "academic_year");
CREATE TABLE IF NOT EXISTS "download_logs" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "file_id" VARCHAR(100) NOT NULL /* 文件ID */,
    "file_name" VARCHAR(255) NOT NULL /* 文件名 */,
    "downloader_id" VARCHAR(50) NOT NULL /* 下载者ID */,
    "downloader_type" VARCHAR(20) NOT NULL /* 下载者类型 */,
    "downloader_ip" VARCHAR(50) /* 下载IP */,
    "download_status" VARCHAR(20) NOT NULL DEFAULT 'success' /* 下载状态: success, failed, denied */,
    "download_size" INT NOT NULL DEFAULT 0 /* 下载大小(字节) */,
    "error_message" TEXT /* 错误信息 */,
    "user_agent" VARCHAR(500) /* 用户代理 */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* 下载日志表 */;
CREATE INDEX IF NOT EXISTS "idx_download_lo_file_id_c759ca" ON "download_logs" ("file_id");
CREATE INDEX IF NOT EXISTS "idx_download_lo_downloa_630200" ON "download_logs" ("downloader_id");
CREATE INDEX IF NOT EXISTS "idx_download_lo_created_90bdbb" ON "download_logs" ("created_at");
CREATE TABLE IF NOT EXISTS "files" (
    "id" VARCHAR(50) NOT NULL PRIMARY KEY,
    "filename" VARCHAR(255) NOT NULL,
    "file_path" VARCHAR(500) NOT NULL,
    "file_size" INT NOT NULL,
    "file_type" VARCHAR(50) NOT NULL,
    "student_id" VARCHAR(50) /* 关联学生ID */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* 文件表 */;
CREATE TABLE IF NOT EXISTS "file_access_permissions" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "file_id" VARCHAR(100) NOT NULL /* 文件ID */,
    "user_id" VARCHAR(50) /* 用户ID */,
    "role_type" VARCHAR(20) /* 角色类型: student, teacher, admin */,
    "permission_type" VARCHAR(20) NOT NULL /* 权限类型: read, write, delete, download */,
    "granted_by" VARCHAR(50) /* 授权人 */,
    "granted_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP /* 授权时间 */,
    "expires_at" TIMESTAMP /* 过期时间 */,
    "is_active" INT NOT NULL DEFAULT 1 /* 是否有效 */,
    CONSTRAINT "uid_file_access_file_id_62b230" UNIQUE ("file_id", "user_id", "permission_type")
) /* 文件访问权限表 */;
CREATE INDEX IF NOT EXISTS "idx_file_access_file_id_52979d" ON "file_access_permissions" ("file_id");
CREATE INDEX IF NOT EXISTS "idx_file_access_user_id_378c8e" ON "file_access_permissions" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_file_access_role_ty_9333f7" ON "file_access_permissions" ("role_type");
CREATE TABLE IF NOT EXISTS "file_backups" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "original_file_id" VARCHAR(100) NOT NULL /* 原文件ID */,
    "backup_file_id" VARCHAR(100) NOT NULL /* 备份文件ID */,
    "backup_path" VARCHAR(500) NOT NULL /* 备份存储路径 */,
    "backup_size" INT NOT NULL DEFAULT 0 /* 备份大小(字节) */,
    "backup_type" VARCHAR(20) NOT NULL DEFAULT 'full' /* 备份类型: full, incremental */,
    "backup_reason" VARCHAR(100) /* 备份原因 */,
    "status" VARCHAR(20) NOT NULL DEFAULT 'active' /* 状态: active, archived, deleted */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* 文件备份表 */;
CREATE INDEX IF NOT EXISTS "idx_file_backup_origina_43e38d" ON "file_backups" ("original_file_id");
CREATE INDEX IF NOT EXISTS "idx_file_backup_backup__f7f93f" ON "file_backups" ("backup_file_id");
CREATE INDEX IF NOT EXISTS "idx_file_backup_created_cc65a9" ON "file_backups" ("created_at");
CREATE TABLE IF NOT EXISTS "file_chunks" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "file_id" VARCHAR(100) NOT NULL /* 关联文件ID */,
    "chunk_index" INT NOT NULL /* 分片序号 */,
    "chunk_hash" VARCHAR(64) /* 分片MD5哈希 */,
    "chunk_size" INT NOT NULL DEFAULT 0 /* 分片大小(字节) */,
    "chunk_path" VARCHAR(500) /* 分片存储路径 */,
    "status" VARCHAR(20) NOT NULL DEFAULT 'pending' /* 状态: pending, uploaded, merged, failed */,
    "upload_ip" VARCHAR(50) /* 上传IP */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "uploaded_at" TIMESTAMP /* 上传完成时间 */,
    CONSTRAINT "uid_file_chunks_file_id_8b3a2b" UNIQUE ("file_id", "chunk_index")
) /* 文件分片表 */;
CREATE INDEX IF NOT EXISTS "idx_file_chunks_file_id_8198a5" ON "file_chunks" ("file_id");
CREATE INDEX IF NOT EXISTS "idx_file_chunks_file_id_8b3a2b" ON "file_chunks" ("file_id", "chunk_index");
CREATE TABLE IF NOT EXISTS "file_metadata" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "file_id" VARCHAR(100) NOT NULL UNIQUE /* 文件唯一标识 */,
    "original_filename" VARCHAR(255) NOT NULL /* 原始文件名 */,
    "stored_filename" VARCHAR(255) NOT NULL /* 存储文件名 */,
    "file_type" VARCHAR(50) NOT NULL /* 文件类型: transcript, photo, certificate, template, result */,
    "file_category" VARCHAR(50) NOT NULL /* 文件分类: score_sheet, id_photo, certificate_photo, comprehensive_result */,
    "mime_type" VARCHAR(100) /* MIME类型 */,
    "file_extension" VARCHAR(20) /* 文件扩展名 */,
    "file_size" INT NOT NULL DEFAULT 0 /* 文件大小(字节) */,
    "file_hash" VARCHAR(64) /* 文件MD5哈希 */,
    "storage_path" VARCHAR(500) NOT NULL /* 存储路径 */,
    "storage_directory" VARCHAR(255) NOT NULL /* 存储目录 */,
    "owner_id" VARCHAR(50) NOT NULL /* 所有者ID(学号\/工号) */,
    "owner_type" VARCHAR(20) NOT NULL DEFAULT 'student' /* 所有者类型: student, teacher, admin */,
    "upload_batch_id" VARCHAR(50) /* 上传批次ID */,
    "chunk_upload" INT NOT NULL DEFAULT 0 /* 是否分片上传 */,
    "chunk_count" INT NOT NULL DEFAULT 0 /* 分片总数 */,
    "chunk_uploaded" INT NOT NULL DEFAULT 0 /* 已上传分片数 */,
    "status" VARCHAR(20) NOT NULL DEFAULT 'active' /* 状态: active, archived, deleted, corrupted */,
    "is_encrypted" INT NOT NULL DEFAULT 0 /* 是否加密 */,
    "is_public" INT NOT NULL DEFAULT 0 /* 是否公开 */,
    "access_count" INT NOT NULL DEFAULT 0 /* 访问次数 */,
    "download_count" INT NOT NULL DEFAULT 0 /* 下载次数 */,
    "last_accessed_at" TIMESTAMP /* 最后访问时间 */,
    "archived_at" TIMESTAMP /* 归档时间 */,
    "metadata" JSON /* 扩展元数据 */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* 文件元数据表 */;
CREATE INDEX IF NOT EXISTS "idx_file_metada_file_id_bea2e6" ON "file_metadata" ("file_id");
CREATE INDEX IF NOT EXISTS "idx_file_metada_owner_i_6f268c" ON "file_metadata" ("owner_id");
CREATE INDEX IF NOT EXISTS "idx_file_metada_file_ty_10f508" ON "file_metadata" ("file_type");
CREATE INDEX IF NOT EXISTS "idx_file_metada_file_ca_e1a0a6" ON "file_metadata" ("file_category");
CREATE INDEX IF NOT EXISTS "idx_file_metada_status_f8c364" ON "file_metadata" ("status");
CREATE INDEX IF NOT EXISTS "idx_file_metada_owner_i_3a6193" ON "file_metadata" ("owner_id", "file_type");
CREATE INDEX IF NOT EXISTS "idx_file_metada_created_5b23be" ON "file_metadata" ("created_at");
CREATE TABLE IF NOT EXISTS "score_details" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "student_id" VARCHAR(50) NOT NULL /* 学生ID */,
    "semester" VARCHAR(20) NOT NULL /* 学期 */,
    "academic_year" VARCHAR(20) NOT NULL /* 学年 */,
    "category_type" VARCHAR(10) NOT NULL /* 类别: A1, A2, A3, C1, C2, C3, C4 */,
    "item_name" VARCHAR(255) NOT NULL /* 项目名称 */,
    "score" REAL NOT NULL DEFAULT 0 /* 分数（正数为加分，负数为扣分） */,
    "description" TEXT /* 详细说明 */,
    "source" VARCHAR(50) /* 来源：manual(手动录入), import(导入), ocr(OCR识别) */,
    "certificate_id" INT /* 关联证书ID */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* 综测加减分明细表 */;
CREATE INDEX IF NOT EXISTS "idx_score_detai_student_3f4964" ON "score_details" ("student_id");
CREATE INDEX IF NOT EXISTS "idx_score_detai_categor_7f4def" ON "score_details" ("category_type");
CREATE INDEX IF NOT EXISTS "idx_score_detai_semeste_aeaf3f" ON "score_details" ("semester", "academic_year");
CREATE TABLE IF NOT EXISTS "students" (
    "id" VARCHAR(50) NOT NULL PRIMARY KEY /* 学号 */,
    "name" VARCHAR(100) NOT NULL /* 姓名 */,
    "college" VARCHAR(100) NOT NULL /* 学院 */,
    "major" VARCHAR(100) NOT NULL /* 专业 */,
    "class_name" VARCHAR(50) NOT NULL /* 班级 */,
    "grade" VARCHAR(20) NOT NULL /* 年级 */,
    "total_score" REAL NOT NULL DEFAULT 0 /* 综测总成绩 */,
    "dormitory_number" VARCHAR(50) /* 宿舍编号 */,
    "dormitory_score" REAL /* 宿舍成绩 */,
    "physical_test_score" REAL /* 体测成绩 */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* 学生信息表 */;
CREATE INDEX IF NOT EXISTS "idx_students_class_n_834cd6" ON "students" ("class_name");
CREATE INDEX IF NOT EXISTS "idx_students_grade_98a8f8" ON "students" ("grade");
CREATE INDEX IF NOT EXISTS "idx_students_major_d50df6" ON "students" ("major");
CREATE INDEX IF NOT EXISTS "idx_students_college_d85c58" ON "students" ("college");
CREATE INDEX IF NOT EXISTS "idx_students_class_n_ee947a" ON "students" ("class_name", "grade");
CREATE INDEX IF NOT EXISTS "idx_students_name_351ac0" ON "students" ("name");
CREATE TABLE IF NOT EXISTS "academic_scores" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "student_name" VARCHAR(100) NOT NULL /* 姓名 */,
    "college" VARCHAR(100) /* 学院 */,
    "grade" VARCHAR(20) /* 年级 */,
    "major" VARCHAR(100) /* 专业 */,
    "class_name" VARCHAR(50) /* 班级 */,
    "total_score" REAL NOT NULL DEFAULT 0 /* 总分 */,
    "total_required_credits" REAL NOT NULL DEFAULT 0 /* 总应获得学分 */,
    "course_count" INT NOT NULL DEFAULT 0 /* 门数 */,
    "total_credits" REAL NOT NULL DEFAULT 0 /* 总学分 */,
    "earned_credits" REAL NOT NULL DEFAULT 0 /* 获得学分 */,
    "failed_credits" REAL NOT NULL DEFAULT 0 /* 不及格学分 */,
    "pass_rate" REAL NOT NULL DEFAULT 0 /* 通过率（%） */,
    "arithmetic_average" REAL NOT NULL DEFAULT 0 /* 算术平均分 */,
    "arithmetic_average_rank" INT /* 算术平均分排名 */,
    "weighted_average" REAL NOT NULL DEFAULT 0 /* 学分加权平均分 */,
    "weighted_average_rank" INT /* 学分加权平均分排名 */,
    "average_gpa" REAL NOT NULL DEFAULT 0 /* 平均绩点 */,
    "average_gpa_rank" INT /* 平均绩点排名 */,
    "average_credit_gpa" REAL NOT NULL DEFAULT 0 /* 平均学分绩点 */,
    "average_credit_gpa_rank" INT /* 平均学分绩点排名 */,
    "credit_gpa_sum" REAL NOT NULL DEFAULT 0 /* 学分绩点和 */,
    "credit_gpa_sum_rank" INT /* 学分绩点和排名 */,
    "failed_course_count" INT NOT NULL DEFAULT 0 /* 不及格门次 */,
    "semester" VARCHAR(20) /* 学期，如：2024-1 */,
    "academic_year" VARCHAR(20) /* 学年，如：2024-2025 */,
    "source_file" VARCHAR(255) /* 来源文件名 */,
    "source_type" VARCHAR(20) NOT NULL DEFAULT 'score_sheet' /* 来源类型 */,
    "remarks" TEXT /* 备注 */,
    "details" JSON /* 详细课程成绩信息 */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "student_id" VARCHAR(50) REFERENCES "students" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_academic_sc_student_64e98d" UNIQUE ("student_id", "semester", "academic_year")
) /* 学业成绩表 */;
CREATE INDEX IF NOT EXISTS "idx_academic_sc_student_45a3e1" ON "academic_scores" ("student_id");
CREATE INDEX IF NOT EXISTS "idx_academic_sc_class_n_5f7643" ON "academic_scores" ("class_name");
CREATE INDEX IF NOT EXISTS "idx_academic_sc_academi_58983d" ON "academic_scores" ("academic_year");
CREATE INDEX IF NOT EXISTS "idx_academic_sc_semeste_0dd2b3" ON "academic_scores" ("semester");
CREATE INDEX IF NOT EXISTS "idx_academic_sc_academi_9b23f1" ON "academic_scores" ("academic_year", "semester");
CREATE INDEX IF NOT EXISTS "idx_academic_sc_class_n_9921ca" ON "academic_scores" ("class_name", "academic_year");
CREATE INDEX IF NOT EXISTS "idx_academic_sc_weighte_01b0ce" ON "academic_scores" ("weighted_average");
CREATE INDEX IF NOT EXISTS "idx_academic_sc_average_2456cc" ON "academic_scores" ("average_gpa");
CREATE TABLE IF NOT EXISTS "certificate_images" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "file_id" VARCHAR(50) /* 文件管理ID */,
    "filename" VARCHAR(255) NOT NULL /* 原始文件名 */,
    "file_path" VARCHAR(500) NOT NULL /* 文件存储路径 */,
    "file_size" INT NOT NULL DEFAULT 0 /* 文件大小(字节) */,
    "file_hash" VARCHAR(64) /* 文件MD5哈希值 */,
    "image_width" INT /* 图片宽度 */,
    "image_height" INT /* 图片高度 */,
    "image_format" VARCHAR(10) /* 图片格式: jpg, png, pdf等 */,
    "is_primary" INT NOT NULL DEFAULT 0 /* 是否为主图片 */,
    "image_order" INT NOT NULL DEFAULT 0 /* 图片排序顺序 */,
    "page_number" INT /* 页码（多页证书） */,
    "ocr_processed" INT NOT NULL DEFAULT 0 /* 是否已进行OCR处理 */,
    "ocr_text" TEXT /* 该图片OCR识别文本 */,
    "ocr_result" JSON /* 该图片OCR详细结果 */,
    "thumbnail_path" VARCHAR(500) /* 缩略图路径 */,
    "upload_ip" VARCHAR(50) /* 上传IP地址 */,
    "upload_device" VARCHAR(100) /* 上传设备信息 */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "certificate_id" INT NOT NULL REFERENCES "certificates" ("id") ON DELETE CASCADE /* 关联证书 */,
    "student_id" VARCHAR(50) NOT NULL REFERENCES "students" ("id") ON DELETE CASCADE /* 学生 */
) /* 证书图片表 */;
CREATE INDEX IF NOT EXISTS "idx_certificate_certifi_02dbde" ON "certificate_images" ("certificate_id");
CREATE INDEX IF NOT EXISTS "idx_certificate_student_76da04" ON "certificate_images" ("student_id");
CREATE INDEX IF NOT EXISTS "idx_certificate_file_ha_a61b66" ON "certificate_images" ("file_hash");
CREATE INDEX IF NOT EXISTS "idx_certificate_is_prim_241c83" ON "certificate_images" ("is_primary");
CREATE INDEX IF NOT EXISTS "idx_certificate_certifi_cc71a4" ON "certificate_images" ("certificate_id", "image_order");
CREATE TABLE IF NOT EXISTS "class_students" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "class_id_id" VARCHAR(50) NOT NULL REFERENCES "classes" ("id") ON DELETE CASCADE /* 班级 */,
    "student_id" VARCHAR(50) NOT NULL REFERENCES "students" ("id") ON DELETE CASCADE /* 学生 */,
    CONSTRAINT "uid_class_stude_class_i_15a61a" UNIQUE ("class_id_id", "student_id")
) /* 班级学生关联表 */;
CREATE TABLE IF NOT EXISTS "comprehensive_scores" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "student_name" VARCHAR(100) /* 姓名 */,
    "class_name" VARCHAR(50) /* 班级 */,
    "major" VARCHAR(100) /* 专业 */,
    "a_total_score" REAL NOT NULL DEFAULT 0 /* A类材料总成绩 */,
    "a1_score" REAL NOT NULL DEFAULT 0 /* A1类成绩 */,
    "a2_score" REAL NOT NULL DEFAULT 0 /* A2类成绩 */,
    "a3_score" REAL NOT NULL DEFAULT 0 /* A3类成绩 */,
    "a_weighted_score" REAL NOT NULL DEFAULT 0 /* A类加权成绩(20%) */,
    "b_raw_score" REAL NOT NULL DEFAULT 0 /* B类原始成绩 */,
    "b_weighted_score" REAL NOT NULL DEFAULT 0 /* B类加权成绩(70%) */,
    "b_total_score" REAL NOT NULL DEFAULT 0 /* B类总成绩（学业成绩） */,
    "c_total_score" REAL NOT NULL DEFAULT 0 /* C类材料总成绩 */,
    "c1_score" REAL NOT NULL DEFAULT 0 /* C1类成绩-科技竞赛 */,
    "c2_score" REAL NOT NULL DEFAULT 0 /* C2类成绩-体育竞技 */,
    "c3_score" REAL NOT NULL DEFAULT 0 /* C3类成绩-文化竞赛 */,
    "c4_score" REAL NOT NULL DEFAULT 0 /* C4类成绩-创新创业 */,
    "c_weighted_score" REAL NOT NULL DEFAULT 0 /* C类加权成绩(10%) */,
    "total_score" REAL NOT NULL DEFAULT 0 /* 综测总成绩 */,
    "ranking" INT /* 班级排名 */,
    "semester" VARCHAR(20) NOT NULL /* 学期，如：1 */,
    "academic_year" VARCHAR(20) NOT NULL /* 学年，如：2024-2025 */,
    "config_id" INT /* 使用的配置ID */,
    "source_file" VARCHAR(255) /* 来源文件名 */,
    "source_type" VARCHAR(20) NOT NULL DEFAULT 'comprehensive_table' /* 来源类型 */,
    "remarks" TEXT /* 备注 */,
    "details" JSON /* 详细分数信息 */,
    "status" VARCHAR(20) NOT NULL DEFAULT 'active' /* 状态 */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "student_id" VARCHAR(50) NOT NULL REFERENCES "students" ("id") ON DELETE CASCADE /* 关联学生 */,
    CONSTRAINT "uid_comprehensi_student_c3ec92" UNIQUE ("student_id", "semester", "academic_year")
) /* 综测类别总成绩表 */;
CREATE INDEX IF NOT EXISTS "idx_comprehensi_student_032950" ON "comprehensive_scores" ("student_id");
CREATE INDEX IF NOT EXISTS "idx_comprehensi_ranking_ba4949" ON "comprehensive_scores" ("ranking");
CREATE INDEX IF NOT EXISTS "idx_comprehensi_semeste_d7c187" ON "comprehensive_scores" ("semester", "academic_year");
CREATE TABLE IF NOT EXISTS "system_settings" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "setting_key" VARCHAR(100) NOT NULL UNIQUE /* 设置键 */,
    "setting_value" TEXT NOT NULL /* 设置值(JSON) */,
    "setting_type" VARCHAR(20) NOT NULL DEFAULT 'string' /* 设置类型: string, number, boolean, json */,
    "description" VARCHAR(255) /* 设置描述 */,
    "category" VARCHAR(50) NOT NULL DEFAULT 'general' /* 设置分类 */,
    "is_public" INT NOT NULL DEFAULT 0 /* 是否公开(非管理员可见) */,
    "is_editable" INT NOT NULL DEFAULT 1 /* 是否可编辑 */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(50) /* 最后更新人 */
) /* 系统设置表 */;
CREATE INDEX IF NOT EXISTS "idx_system_sett_setting_95149c" ON "system_settings" ("setting_key");
CREATE INDEX IF NOT EXISTS "idx_system_sett_categor_853a93" ON "system_settings" ("category");
CREATE TABLE IF NOT EXISTS "upload_records" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "file_id" VARCHAR(50) NOT NULL /* 关联文件ID */,
    "file_name" VARCHAR(255) NOT NULL /* 文件名 */,
    "file_type" VARCHAR(50) NOT NULL /* 文件类型: score_sheet, certificate, template */,
    "upload_by" VARCHAR(50) NOT NULL /* 上传者 */,
    "upload_role" VARCHAR(20) NOT NULL DEFAULT 'student' /* 上传者角色 */,
    "academic_year" VARCHAR(20) /* 学年 */,
    "semester" VARCHAR(20) /* 学期 */,
    "class_id" VARCHAR(50) /* 班级ID */,
    "status" VARCHAR(20) NOT NULL DEFAULT 'pending' /* 状态: pending, processing, completed, failed */,
    "processed_count" INT NOT NULL DEFAULT 0 /* 处理成功数量 */,
    "failed_count" INT NOT NULL DEFAULT 0 /* 处理失败数量 */,
    "error_message" TEXT /* 错误信息 */,
    "processing_log" TEXT /* 处理日志 */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "processed_at" TIMESTAMP /* 处理完成时间 */
) /* 上传记录表 */;
CREATE INDEX IF NOT EXISTS "idx_upload_reco_upload__d70b1c" ON "upload_records" ("upload_by");
CREATE INDEX IF NOT EXISTS "idx_upload_reco_file_ty_f44d80" ON "upload_records" ("file_type");
CREATE INDEX IF NOT EXISTS "idx_upload_reco_status_01dee0" ON "upload_records" ("status");
CREATE TABLE IF NOT EXISTS "users" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "username" VARCHAR(50) NOT NULL UNIQUE /* 用户名 */,
    "email" VARCHAR(255) UNIQUE /* 邮箱 */,
    "password" VARCHAR(255) NOT NULL /* 密码（加密存储） */,
    "role" VARCHAR(20) NOT NULL DEFAULT 'student' /* 角色：student, teacher, admin */,
    "student_id" VARCHAR(50) UNIQUE /* 学号 */,
    "real_name" VARCHAR(100) /* 真实姓名 */,
    "class_id" VARCHAR(50) /* 班级ID */,
    "is_active" INT NOT NULL DEFAULT 1 /* 是否激活 */,
    "is_email_verified" INT NOT NULL DEFAULT 0 /* 邮箱是否验证 */,
    "reset_token" VARCHAR(255) /* 密码重置令牌 */,
    "reset_token_expires" TIMESTAMP /* 重置令牌过期时间 */,
    "verification_code" VARCHAR(10) /* 验证码 */,
    "code_expires_at" TIMESTAMP /* 验证码过期时间 */,
    "last_login" TIMESTAMP /* 最后登录时间 */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "extra_info" JSON /* 其他信息 */
) /* 用户信息表 */;
CREATE INDEX IF NOT EXISTS "idx_users_class_i_2ac6c5" ON "users" ("class_id");
CREATE INDEX IF NOT EXISTS "idx_users_role_35db31" ON "users" ("role");
CREATE INDEX IF NOT EXISTS "idx_users_student_5a86ca" ON "users" ("student_id");
CREATE INDEX IF NOT EXISTS "idx_users_is_acti_7e4021" ON "users" ("is_active");
CREATE INDEX IF NOT EXISTS "idx_users_class_i_42f2fa" ON "users" ("class_id", "role");
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
