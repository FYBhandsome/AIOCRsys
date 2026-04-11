from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


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


MODELS_STATE = (
    "eJztXWtz2zbW/isaz+xMOqN0RYrXfHMcZ+t306aTtO+7s21Hwwtos5FElaKSenf6318cgB"
    "fwJhMUKcAKP9R1SBxaegAC5/Kcc/57tYl8tN5/e+05PtqE3kcvitHVq9l/r7bOBn5pHjCf"
    "XTm7XXEbLiSOuyYSTjp0tYex5J7j7pPY8RJ8O3DWe4Qv+WjvxeEuCaMtCP160F3D+PWgIc"
    "X59WCoyuLXg4mQ/evBsgwLnuFHHn5IuL0/PtxwVAXfNS3310MQLCz8ADdA+K6zcMsj8V0b"
    "HnzYhn8c0CqJ7lHygGL8+F9+udonBx9tk1Xow5A92qB9gu/Nma/3iJz46rff8KVw66M/8T"
    "etSuJ7v1x5a2e/XxE4yb8r8nApf3zDAPavV59X/zQw4AsK7x8S5K+czyh27rM/S/+xut85"
    "9EPvPq2CEK390mzTr0uur5LHHbl2t03ekoEwCe7Ki9aHzbYYvHtMHqJtPjrcJnD1Hm3x38"
    "OfAl9L4gPM+PawXqdrJFsEFPpiCAWSkfFR4BzWsG5AurZssovM0kgvedEWlhz+NHvyBe/h"
    "r7xUFc3UrKWhWXgI+ST5FfMv+vWK704FCQI//HT1F7nvJA4dQSa7wC2b9GxaygjePDhxM4"
    "RVuQqY+CtUwcygO4ZmdqGAs3jrjuIJ75XtL/FPbeFXX7oWZDfOn6s12t4nD/ifymJxBMf/"
    "vf5w8931hxd41Dfw9AjvCXTP+CG9pdJ7AHYBLoZrje65cGVEekGaLr9hECU7lW0YqjSI3s"
    "d41+DBMxcQjyYyNdjBHbMPmmoXMNV2LNUalBvn9yjmgTIXEA4lPjyX9AiVZmGWD7fOb3tJ"
    "Sjiu5hL5/Zeo3gVWvR1VvQZqEiXOmmpjdVTfriOn5XyvyFVwDUBwrNNp8e2iCVljscRKnK"
    "4ujG7IHkHyzfufX7+7nf344fbm7uPd+x/ggZvH/R/r4ibRvf5Yhwn5vh9ur981AhujPw5h"
    "jPUtD/8Ik30PjJseIQ/cyMY7rrV0Tfx7YJvZiSbNNHjRId4jDOqB6p4d1deq2NOK7GBwN4"
    "Ft6wgbK4ZuLjruGoOotNXF3H8NS7l05Vqo2ETb9twn6qISgCzxnhA44bon1HVRCaDW0ALr"
    "FPrSA3eHtfSkA3wHKhiAwYV1SUoCmO0F+JOswDNBjbNM6kP6W+EsEo6zE4fJwwYloZf7d3"
    "gAbxaXAHnThV3EMNWA2HjggzA1U6IFXkcOL9ztJw6F48gTeukeg9osR+DH15e2yuUUGlg3"
    "qbk0eZZ8k7AEC77Yv+GnswD0taWki7+KIe/Sb5UXvvC7ToP4l4D14HNt+WU5GZY+gy2NxZ"
    "gLV5LjtQCLe3tvEBW/vBuhlmcxUy2795oui0u2tNmtRdJlXuDXd7U3PEGqRd88CeJfAAa3"
    "/WHDtfjrojIs/Bacdc3ypFjyZdR4l3uLtPilfgR28Ys8c6X0c9C2SAv209Y9Mann1lUVMS"
    "iz7JTOxANGRnjAjC5iw1QC4mgB55ZtqfC74qgLVXvZFdiRY701Zk5XtGuCkkBOg+mNkOMf"
    "uhyo7/H77yH8vDUftaYsJhxxwzR0/BPZYGLq4FrUUGD0p9qout4FaV1vhxruNWJNUOLHOh"
    "M7H4vpikSnV/sHhMgpcBR10zNdSg2UY2HHaOPEnxqCEz+hP1uOREZE+ILW7QW4DD1Uo2dy"
    "63c/3f7rJ6LT7VOdLoPtxffX//qmpO29e//DP7LhDMw3796/rsDrowQrEA3w/s/H9z80w8"
    "uIVOD9eYu/9y9+6CXz2TrcJ7+dGWzLRUTD84x2QqsWIAUin0Zw8oQARMcnpIo9QBbtk/uY"
    "PIU8oDohWId2iA+wQQl8g+8k4Qa1at+MZGVq/FT02+yXsTabEymo+Dv477frx3RlHHsd7r"
    "6//fjT9fc/lqbgzfVPt3BHLVs/6dUXRmVa8ofM/u/up+9m8M/Zv9//cFudqXzcT/++gs/k"
    "HJJotY2+rByfIeJmVzNgShN72Pk9J7YsOU2s0IlNP3yd1dzECn+a09xIDz/zMdV9Ekfg4A"
    "HLPvh0jC/e4PbB6kx4v/0neiTg3uEP6Wy9Jq0qTcz4WDxJOlD/ypZGdrX4FLHzJU8/qKwY"
    "/B3xN0PUkXNz/fHm+s3tFQHTdbxPX5zYX5VQhTuRGlWu5GPrtzbqhr0Cn7Ipy+U7fMxH8e"
    "PVU9kw2bh596SY1QMjc0JujL60wIJYBipoBe4CyDi6zp0z0/aYIpdm9nKGB+uqBeIWaB+q"
    "ZpF4MfEyOSRItiSxyoZ0midzZCroZJefSLuZMli4nUbtGSz1KegOY6Ps+dx0rQaKAmEAa6"
    "FDwoBhaW0vwN0bQX47UcfrsChTT9IykITt/hnFe/hw3ZcvI3G+Ras0YcnuqhyIjsIEnvIF"
    "JqL6RFSfiOoTUX1cJsbE55WD0sgF+8QpHZRqx7fkJz4jP8gTz05oGtJEgLk4AswIRjQwYP"
    "oY0RfHdBnDQYFMTQ5sJz7L+fgsEGYAl2cd6HYSACsjGQtAX9qgTtueSw1w8L0bCCwbhK+Y"
    "itHRY3T2yP+Ds73npxVVxM5IK6KEg6vmOfDhsDMCjWUUvZpRkfmMhrTns3Czi+JEji0nBR"
    "J/wn2TZ7Sdb1QTFL7tsPCnr4OBOnqizs1Aouj5K/eRf9VnUsIBNzTPB26R7sEO7/aqFTS8"
    "l3/iEl0E5YRyiWpEibME+29QnIRB6DnEeqvF+Nnb82Ohfa8Y2LnYpeV6CrxORDM1AycL+h"
    "QUvtYgPitaCdDrro73Rn3hWF3+wtW8X7Aevug9kBdojP6AX67ylcRJDvt0bIENfcfI1TX6"
    "jNb013C/x38f3rZMuFR3M33UFO2fj1Ov8hJCz6auBHdvsmqvRTiap2jH2McVWG28Ve1YGe"
    "FaQNnykNTaY3ebbcSlc9UkhSPObuBmoJzAsRinUmN1Z++J9knG3Wh453YdzYgCI8N3aU3H"
    "Xw/LxQJOXcXwy1dMx8e2uOXrbnbF8Cn/AA5kegVv3cBJcizwUruaJNtTEiZ8zqhcQKppMy"
    "zISLEt2/o73ZkwxnbQlaYw/v5E9R4OmHMBqWCma15XVebtCCAk4LpG5Y0wyU/2rUELtXzF"
    "sNTKGCiVLFP9VKKjcnnBCwnhE2dblkK8JgC1uSR2gNXPEz7GK8Ho/7z45lJyYawjvX8kZ/"
    "jFi/7chfEjN8IVMeEQG+YCinbolB8JieKWEizlgDg3f3lUIEbmjH7tm0aXdoPqgzf3V7Pr"
    "l+ApUHz4GSyhOqIOQffANeezG3zP9NUFKDyQFmCopG+Ap/fKGle6aahHFNRalI31S3BMTF"
    "VO+MrXXX1RnpYbBbC3yW6jWulNPCPqS+KnJZx3V80vL19mJpu+VIz8svYSnqcQe46kfJDf"
    "+1eDH3wCufnHMjGPS+43wsTKWFmklFxn8uzYjGSonE9NMfzR+wSI2h4g/r2hfCD63uSBor"
    "+TqdGy21pg+zSIKmcECWLRCQafZ0pYGcGz8P7mA8HbyMyFuhsJvNJyYh95MV7Pe/h+NfTb"
    "2QNlKan4A7XZYIsKmAjOb8O0T5+NcSgEjM8o3AYN3r32OWmSlWpmqvY1nQqSsUaObNkrO6"
    "RxGh41K5c4o/a7Q1sfYGuaAFMF54WxWCivZum4F6DrWjqoYA5xVCytb+YzZ7eLo8/Ih7s+"
    "ZMwWNcPx3Rj9jryEuYv1YuLM8H1814Nc7vWauY2NRvizvmV908smH6EozecQfeEmLVTExJ"
    "/++ZTJxFrIUeKnLVREB+AtjAW3oUNgyNaDjl6mZ0JeyMA4WgmFzhKets2msbzDscpOVUmp"
    "3iFDWYDPxfY6UrzPrayFG5KmwEmwr0gJJtaz+eq6EdAqC2bG9LQVr6tLcWB6/S7GOMWPK4"
    "oWF+WiSVR4zVQNkahcjrCw/H/C6ObSmnKJM2pNh906cvxGpanggL+a0WEvSH6IAyor1i0y"
    "FiyoO27gkaCpjq9unO3BWb8A7UjLA6S05ggZIYcqRL/RynUS74GTKdMgKnw7L+YFcDdtmr"
    "HTefGPHmRbfXbWTSi/jqI1crZtkaBCrIKwi+XGeilyulf1hTBIvqumGmzI4uQj8/X79+9K"
    "R+bru+qZ+PP3r28/vFC+Kbv86ptOuCV49XD11SWFL2lDR4ssKiQ9GXxiLF8OY3mqfnhxE0"
    "s+PAcTvWJ7NHi/Xqdyb//5Aa1JfKRhmuts87tNWlBAVK2swhfJtZPWyvz9NQ5Z/zUoVVfH"
    "Gft0zLwjbZ/qaf3Y+81aVSf2fptohdVvBUCuspDqZMPAFGTFr/JVcJzJn6ujVap9nbdfHD"
    "kT+X5o8n0fg+JkS2IoFK/Ka1XXVboUFxn9EgJMcpgUl5fkIAeuaRktTl9bRUqwr42W3Srt"
    "wIK9bPuD56H9nhvXmpxoZEldTV2lgf4FZElrGedFJL5FMZWeNVikQFe3lwqh3OniEb3MqO"
    "98tosjeKPI71602UEtan8+oytBDtckiuMoXm3wp2ysXNbuxKkJCvfh2LpiEypKMCjPYRQf"
    "TrEyVuvovo57OwWlLikZAaW8VQOHXQ98ScuJpN71cNfDJU+FhK/6QvO4+1EOrS7Fx0efQ7"
    "6gVE1QInBJPXtEexX1gXmU1El8Csb9HIZlSdk4IAEYgZTbWd5Nvl4+SK4+9HH7V2Rlm26X"
    "dBgl2v5XPcVTXOcS3P90YoVXoqHO/+PO7TxA0M25XYQnuCvTMCSkDv7sEmepW2WatC2HTZ"
    "KIyXldPKSrV7v0XVt821BLY/Xg7B+yqjOrlJlUL1ND/X6UsBTFPpqazQzvASfTweeWZUSE"
    "65dsARSTkCRB05HFPSuk1sywLu/nUGyGLMidkzxwr+JMSDzQJXDZLdoHb4we9CsUoHcymv"
    "QjRpNeN5oIcvvwPw3Lut13y8qIdouzUNsqZON6i4AQI3U4XlVL7Up7HNoxnp+NvAs5E5Jo"
    "Q/7+DXiuNM8ipUaAcbpYdsxoKy9iQ+uwhg2tdQnDrSaK+pfQb9oynqCo51LCydOskqe7Lp"
    "R9QU7XgO/AK5di80B6cXBDWohJhant+JZ4TIMo3jQZtEdKslTkhO8JJWuEtCnQg0Xwavb7"
    "DkI8JM7jB/2LcA1f8IAxSmq4P8WBZgTPyIJuNSJZGrSGoOhQNefiZD/RkJRoxtbj3UVyKd"
    "FxYXa1L23ILEVWAKWJTIf+LmY72QFI28PG5cK2IiV8g8YoYrXCtKA6WVpmlLgs6HXWocFR"
    "cnRgpKHwQBplRLxZFDVZ2TYRmixtBVCE0bI0j5QyKIIMMu0mgCVvyQ5WRvjBabkk+ptvKL"
    "WyEVPhDgHlIRrn5PmU70ge8G6+dcI1t8ukLin8DTEDFcq36kY+JxI6TC6MJAHBhCXEB/B+"
    "L4ef9eIJE/x8rHPUnZ7CrZcTbp3S6C5uYtMP31K4iydeWhc8n409Rprc8PTry0pvEXeq11"
    "gfjau3jvLbKEbh/faf6JFgfYc/KBT4agC2uafQc1m5bQmec1psMuNFNLyxGAL8xRG1lW+u"
    "P95cv7m9alrFA4D7sXiSzAu4K5jlF7UZyPOwkx6c5Dts80JB5CZiEnN7fpSThAeuHsjIsD"
    "sfSXcDkh7gk57DFm2DorbykdqGF3ykq3k3WtFhj+KCTwTcfTwHeQ+sKT92PHZQhjzHqcaI"
    "iD/STJ0WRF92ryw1diZssXx5VIWSlHhcNdJrBN7tfriOYo/G0ZrL+M/Gi4fTsqEyqaWa6q"
    "sZvD/zGZTyhlNWlq610TbhrKLIiIgHGKq6Zs0cdYUWknU7RofO7TNPMwIpXBzLuSp3xrzO"
    "LGByFHe2QzMIQEU6/Hnns6yPuvhlvkGJw9ujnJWRLFShK9qS7U4uZzxiciNehLdJaNYGtL"
    "64arKIyI3jthAM6W4EmUuU9xrs0CKYHc5r+HBZM0foYFJUqmGBKHpoEpYG8MFsS1WXC13t"
    "WNN4HC293Q7iJfHLQ+BncT+tD+MoOvt97PhcyOYC4qHVkan1b444gvbi/B5x9UbMBcRjqS"
    "FleUrLqzHCm9F6jZpKehxpJVeIiIeUekOhg6c0kGaOVO7CSlU50RTP3NFMW1rwtBEbOvY0"
    "qc8XpD5PUfiLm9j+xWzTXe/UcrZg3wgKyBXK52kBuUHL17J4tJmMDF5PWI4rdpZ4DUj2HC"
    "lFhZ82JttEnzQyf0k/NzUL2ez8U8zPKZj2dDBtOqkvYkOvn9TZC8UZ1KuIibcYeLfrqWrw"
    "JdCqmNPgVE5V5m2VedF2ZlCV386JPnUB9Klos4vRA9ruw8/oI2lR3qQA1kcdVwPZ8SvS+b"
    "y7MoigFZfhQ+utoq98VhObVnQzEbLbVcLOD+igGJYnao82aJ/QtE/Hc3y0Cb3VI3LimqZY"
    "L/IUO9tP8BlTxtbRB0065oA6ZjYRvAGLqpzwPBjdhiy6vmWGxnEIkxOBF9mylHBcZdPxzh"
    "y0GDZVS7qYhbOivR322bFV0UTWkdOyh9YkK/AGIDqak/3bBjf7dXaiGaZOCpvadv1c49JU"
    "moB+8/7n1+9uZz9+uL25+3iX0lty45LcJIdhnmb+4fb6XRV1pQ/gikxYKznYkkGr9oFWlQ"
    "laVVZol32gXcoE7VJWaFdfSEkr5PfaievC4qEuzAsHNmOTMAtz1F+oi791rJk3MvTuCmxP"
    "ftQrcsIBf50DzlbglGuZu6cs8yZhiVBvXuamPMu8r6JXk5QH9LrTIq3w5NIejYpTuyvHi+"
    "D1no2apPDZuHk2arfXR+32ZFK7bxrU7pfA0PSBV6xacMnxSVEb3ZUD8z76uCeTPn7ToI+/"
    "BC63TmLorpphDvjLgXkfRd2TSVG/aVDUX2bVy/QlsMFlW+daH8w1mTDXGjHXVYXUjXMX2e"
    "/dHVijn6InqJNNwuLn4Al1UpFFneyrvsimvJQDYlJqLVlorAZza3iLkRBefrWUz0SL23YP"
    "0QxddYeJK3aOczEyslBDDBNIfEUiFPyuOL0yoYZPKikHbDmQrgnKAjdN26nCrS5U7SX+oc"
    "sBO/5zQXjPWaWLlRG+U2iBGWQFOGhvKVvRYO8IDNS5aMTQO0Z0iD20yhLOO28aZTHhgUfD"
    "hHKnBrIXEjflSUHjrWJQETtjEYMyj4fSe55Cv6hpIMe2EaONE39qyBhor9PBiAhf2LTUqe"
    "GhGtVJjtIcPkqccN0Ab3t5CEZEsuoQbM1qXaXtYaFSxICdv0epF/FMet07XoL3kcYdpGh1"
    "L8euMSUmXGhiwpRCeBETWyvkeyGJEUzamuRJEs+f238C1hfA878hpvFVJ7Z/OnbOyflfUf"
    "O7F/WfDWoXVnIn0n+b6KjFhiYm/tNM/OdbMohdRhKWDGI/bw3fdju3Iibc1i29rEsPSogF"
    "XVE+t92bURK5YkOs0DkDQyoHm5wE5GzF8ynV6G8ScYrcPpi7gjA3nyB2MZiXKV3Gok7pkn"
    "tevD7z4gmaF4WD4iUx5nksiWpaQYYxdyyqIn9Gd1DOTnA+44ffNzuG2oiO9VgKbVVuuG6v"
    "eNXwaVwVhPee0xRiOXZatDzgrG9LM6WgbVZo7zlDX0InQC9wMwcqvD3/+PEaDnTDgwkzUe"
    "Zh1dUl8bMGBp1OVZfoLQv3q8JpWZ64p5oeF3JnbFeaGwTHupVqav7mGK5RikKeDPqQjY/3"
    "q+yLcYPPCMrWLJZ2nLYRNFK3XEda+LGlvw49gGPFXZG0SVa8dbFYqNm6l61OKQNYHwpPi7"
    "hckOfEHjkgnyI8FxEImCI8FzqxvEUiR3WWH+sw1jp4zusuf2AET3CXlxqRuYTVHug6t+u8"
    "7TGFG332cpbt7hqyaPNvi/ZeBwceqcmItftu3vZ6xZwmiIqWZ1MBnbMVaWyeh+5Ytj9Arp"
    "6p1I/Q/D4I42deRlyb0oyXgSQldj6jeN8YLGldw4zE+Rat0rjtM5ssB6IDr8vLLKtDsmPA"
    "LyWF92kqojMV0ZmK6ExFdL6GEhfSbLqXWbhCMowvskyFHNBeZDUKOaC9yKITckB7kbUlpI"
    "B2qmNwNqgvKftejiDdZabay4HtlE9/NYJfDNI/ePulszKSZcSWSm3mXdMhFISgvYJi8LUY"
    "acJwnA7qD872nj/VviJ2zlR7Qiq4ap4D4AoZRpCrGBB8ezWjIvMZDVvPZ56z9g7r7Cni9x"
    "eKJf6Qe760hJqgcB4LOwPpG2EgSRMTKHr+yn3kX/iZlHDADQ0411qge7SbrBxRo4kydBHM"
    "EkoZEkMteRN92WLTyX8XNaZesrfnx+gjfjpwtY6651dqaOECBdv04TBHOhzjvtlKDGkbXi"
    "GAWCw3hCm9w4oXXJKreTcyCFQWytke2bdFcUEOKd6oifExNOMjA5/jAGFExJtaxTLsbAaM"
    "n6RJEOJNgS0JyQSsZKW1yjsEB8A1QfEgsxuntVjo/dbw8OoPAxWvXdUgKh/O8tUuYxfnru"
    "+q3kmh0Rdg3/0o13Je8VfPahA9o6tgf/A8RLvKHl3TRU2tV7NUZo6fh08Ufz7z0TZE/fbv"
    "0Zb5ah/+p2FbadXYanLnY+Y1BihKGq+tAv3ZWwQvstRUS7XUjrWth/ZKojiO4tUGr4A0z7"
    "arL6YmKHwjsXXFJpX6gkHr8o3iizns8QaMgWsqk9S+u5SlhAOeZoqqS6L5IQgha115JNU9"
    "vNsmfmwXn5wyk1NmaKfM25B8uZo35m1a3bjdDQPmWWf3C2s8tbhc2CGjlqtq332GtIJG94"
    "OMoiIe94v0seAlMeB74jqKwU4cGzsH/wFOLHOh5wnmKGcgwYVTeS7JCM7DOrPjswIcrzOj"
    "JPRcV+HQ1rSwPLVB47yNJUFl8b9Nmu6k6Q6g6V4TT9CPKN6E+z2dhEbNtzbuSU145RCR1S"
    "6X6acbu24Adj5CeQk2A4qyddCZ20Sf1KV/YQNYxABPt6T8q9D35bfjgcpMkvwjjrJzYopQ"
    "ThHKZxChZNY9l69KktO7cFTJcmIXOwAHpCUh4aBatg/1P1RTLZMPU81tPkuQ4+FNdD5z/E"
    "24lSOgUN21OdBvEJVgt2COMnYSQCWaz77EIdA/aWl5/P80KiLHVNzHzjbhpiOWpYS/BMbS"
    "srJZkIeOmIHEbw+UJaWyBypo07qgth50TZq4LCuhFMP7cxfip/WY7rLkANM96AETeGbW8J"
    "N3tp/J7GZgHJ3eSyw1a5ikdLmund687sTKpuLM7ddY8LC7ajGy07vzJ01rlwzsZU/TFoL4"
    "d7+TDc0O541B/YLnI7wPt856VbKL6acvX5sYvCPax7Vp4FC+mmTF68A070ZKu7myujmgrk"
    "tKADT7/ksMN2/wsCImF9C6q0ON5IUDVcF94DbpgdUrUXiUAGOKHWeIsSIlmJ1Xglsqdl6K"
    "E6+roiJ2RgZqgB9w9RTGrKMiIDiGW3zmb9A2cdZyOCdSBNtSVJ+EXqYUVXZ1c6aonmHPvq"
    "QOxa9mdNh85sTeA/7Fz5xvkvjcpkDxBbmAxFmuNw+H7aerFsOV3pw/abd6MK6f2UraA5mq"
    "1p6h2ja8kqFq6OCSMJYLJTv52wQ1tHCAVq4uusSJyXdbkZX8VGD4mNRk+E6B4UYKkpTWF7"
    "t8u6/QipQEdd+Zt15HViCyljYF58HZc9mzZSnxCmgO6PdvoFSA5pE+Swuvz8o1tA4L19Ba"
    "1y3casKY04AtC4m2X9kVK5X9SmHi9ceUpSRav9J7Y56JMbVDWx+QesqaSsdBISuSs4zNqQ"
    "2K7+H/NFtVDquKfjrOROySkPA1Xqi3siRhT6bqBZmq9belZxu2kqhkfIXiHYJzwvKyKrRf"
    "G3dBnF/ie5Q4pFxmi2sivz9/0juxYYfy+icUSlAqimJ28VLUhKrt1JAfkEUGVD/XUWi2NS"
    "wybVEQKrIHtngpjvsioi9bhqVeZDMV//Twq3QPnejIpVR5KMvOZ1XJKZ5/4W6NnhhW3wDi"
    "jKML3LAgaGG5Xq9yAqO4N0rkB95c30ZhCXxKpSK+klbwgtaXePfoA3uDqASgMzaktKA/+/"
    "zXyubCxpwxkls6dD7bPURJNJ95KE7CIPRIueQEbXZr8hvWhNJm8eINovL5yzsrrKBcM5O6"
    "V/D8vJrRDqD7B4Tw1IT+qj47+aVS51CZ5mmDLQ/uN6ckJNgb8D3W+0+teDdenUz0ZwKTzs"
    "fKqEsK97iUCrqoBrRV9nT9hFNgcLfWM6od0egWL1OXZXKLE5R4ozolIYmWr5RBHVD8nHv+"
    "OjJVOfFHpfQRBwqYH8bISzg1k0ZhuSA3DYRoDXNpVPOyp6Wj/cnIiAeYdVnROsYv2E7gf8"
    "f/80lVefyPrlv0yFodBZBXrStLnbMSLE3CboywVdF/RunbadDMdRLvgbceQV1U+CHKRgwM"
    "1QQHrqsqstQooGF4ilsd6aOph1XRM2YftnvomfTDdmafyFTEOvhedGiqEPsELSWXkoiXkr"
    "Zl1M2uzPNRmChZAJEbUlZQNKp+oFaCjSzOwhB+JtyTU4n84HqK48NOGk5/uF+hrRc/Zp+I"
    "Y5uuisq3TTsklt41CnSerRmjtju469DjR7uQkw5qxfDAzllIdQqmZeN4j8GqmOAd22Jrz7"
    "kQ1Be3S+edEXgxrQtK1FNBNKprZ5+kNQ57EZua5CVjN2F7cUG806iyoL8ydlNpe0qVgx4z"
    "XhGVbLL1QFeBhGH0KLR0SRPMssDKs9ves5mVkaxncynOVOGbnTy543RrnljAl8oC9ntObF"
    "lymlihE0s+vBjC70fgirzBm224vmrg+7K358fovpRz4pORndORTRQAv9vX3NxKVbwgc8UY"
    "BmhJJvLa+7l0fwB/pS2mdj7l36bcH4aSu0cbtE8QcbM4nuOjTeitHpETTwzdwRm6whogDB"
    "wUla3rAbuGO6PKyMiCKVS4lMOVWN4JOGCtCcqCrY7MXlyJEUqvlDZhDmxrguKxTePFquq+"
    "ml0r89m1iv9bzmc3+Pcb/PsN/N4Ld6UbbfAIa7DmHk/Qhru5dklIPN62BbHhlIqiLaCElh"
    "30KuE0DkEfNKg6vG/XkdOiHeQSFWwDEBnNi/jtkSglNYSDYAGkfNfITWMNLZ1cQyMj8RgP"
    "qFi0LHExBhvXS2aMfbJB/eb9z6/f3c5+/HB7c/fxLjWuc1Wf3Cz7zz/cXr+runuZb1uboP"
    "bmrhUx4UQJy0VGrlC7gUY15NP9UWO0dt1Hh9jjy1LJJYQDbZiGjn8im7wMirNxtgdn/YKQ"
    "hqilYlE2HIkY6d/MZ+FmF8UJ4W+BRZNejbz4xfubDzSFix4VkhC52FwCLoumLtgrADJWVz"
    "IMtAJbkdG9JNDQFIvJV3cJLp3JV3ehEyvSV5fSUZv8dAVT9YiPjg7q7J4rnBVsK/hWZxw7"
    "nN/d5q2d/Z5aC8S3dh9jY5j+unF+j+LUCRet1+g+y4gvROYzVoA+hcsFJ3XD5sIQ715D7c"
    "ytm3ltQ3nMQt32l/0TxsapAZiucg48GREJICWL1TYMVRpI6R7CAWguIB5ODSmkMZbSqzHW"
    "OCu0tPV2XqQlKfHAmksEXiDkCN1USx3HfC5AcwHxWIKPuD+Ww3uKkyhx1it+p1pFTgLXGh"
    "vkTBMASEUsEyFJ3GNRvAkh8XC1PWxcvlBSk6xw/41OmHmWSnzEgSKB4tUENv/abpDtub7H"
    "Qluylb17eNyHHt4PErRPegDeIi8B6FqgL/NNRS7QJw/YRThKJg/YhU4srwesgRlBdsKGLL"
    "fX6QPe/vMDWjstgbPU5XWdPuxjtquea/fsPON/Zcs4u1rMfEskZePcnwrLTfG8O3icGNsf"
    "vIBch8kTIIHheDIy8BDGUfr8USlV7xrinbphn9j1xRoWKCYYNxhoQ/rgH/cJ2nxESUI/Sd"
    "0TXxowP+qPJ0NXezq2O2vWC9yskK3lukBxDY6Ux20b3oMRSz/o6hN6LFNiJ7rr8HRXBusa"
    "gMeYmSUx0VELdr3ZutqRa3KOfnkpTp+d9aHBpGvn9NQExXveWJD1xdJ7ASlAHXkiZ6f1pP"
    "Dx0jercmctAhS3ddlgkS9X/4lJww3q0prPXJrQPp/9nrazFO8ePUppO+Kuk47SxhxoS0j9"
    "sAKJOJ19Cs2KqTGbPrS57Wxph8kLzcrhD73wOhIv8MFp6qjcrEDXSGm9JdQxtGxPOX2zH7"
    "awB/JDquRyTwkrecZJyRWaY3NC4KbhACuwFZkwn1ymF+FZm1ymFzqxNddNNjsul2pQlhKu"
    "fLHFTAyD5BPoLsnkcHsxVYZRDsRwM38mpe0+IC+Kyw6QpvvzY16htMRmTIZ2dgqxleywur"
    "bI8gtanEJtwyvdkrAy7eOfSHXKhcBLdfOWFg2Qq139SFkR0cfGDklZO6TJpTS/vB5HQ7mG"
    "T23dPFJjEV5CXElIPMJTH50zgVtyFrHdWho76MixwItdm0tjYYTEz0Hp2FsselWjHw3ZOG"
    "qymJ/ENhOTpC56FWLwUPgq8LvMXmzwi6vPMCx1Tq7yDEKKiQwPqDy1RChjnk9pY2WEA1pQ"
    "7GVR1J5JhW3u7u67OILKp+R3YIakdbZlavGefkTEXze3QVJ0AXl7oRXNgxVS2MLOi1nYit"
    "d1Bxm6KxaZb26Aq2ISoavbSwVKhai6eHRRHEfxCh9Ye6cpP6+dN1ATFL4z27pik5ogpeze"
    "k6Mao9AGir1ttY7ueXCvSwoHvrRz6KRDU+B3zC45N/BTYOki4g/1wFJxoPJPbVVWtrLb7N"
    "nhWl52Pn9tJbgFBUL2xOtfD4Ds0zqp7YEPPKI7CVZXocaYujQ71aZgh/etTZEVgiUOlzRU"
    "US4RG+5XaWMcpj4FNcSo0BTT6KV/tcc0YM3wOt1ZGdEEWXZd9vW4D28io01a77krpLnAIM"
    "pVfzjthUOoUm5Hds4ZQhc7vAd8SYO+XeFkZcQ7zXVSfM60FkpW2rHoKFVu89q9YOMZgOd1"
    "p0vmRy+85rSGoNQdRYUV5x5u65CjwBKzfJGz5o4nl4SEG7qmCaXAdNdGclZZmnzrI5Cxi8"
    "6QfMzfQk4y3q8ReGA8+suOhPfzsaxB6Vp9RnGI/1afppU1eRlo8IUKV54G2wFLHuqzyjQN"
    "2ERHCTYePyGuNJqKmPCdhFXxbMXzs2QPDSGN9MT15FHrCuhW6M9d2JjzfNx/1fIIydxYzf"
    "MAnEzPpCHqr8+lxS4EunF5JKMdTy5f4bRGYeGvYbHH0Zexn6rUSVPi6P0A8GTvSZ9AQF1c"
    "tjetAvv0jpU6sq6j+7DhdOvQizWXlGzC2cQF0yBUTMp+/4qneor0XWikb0ohu4iJraWQoT"
    "/x11yF2yCqz2t7X92ylGSddXXFJMlFvjEoJWWwnrpiIqrXWFf1Hq4aYqrpnfmxqKpTjHkq"
    "rNr+Uj0dJJ0im/NhI5vYQtlzFudgRARHjbqjOL7DAF4NDhDT4c8TwJG6EWwT1EQmbT9lGJ"
    "EBjhgBsF7aafLX/wPqLFA7"
)
