# 飞桨OCR照片数据存储兼容性测试 - 实施计划

## [x] Task 1: 测试照片集创建与准备
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 复用现有testphoto目录中的真实证书照片
  - 创建测试照片生成脚本，基于现有照片生成不同变体
  - 生成涵盖不同格式(JPG/PNG)、不同分辨率、不同质量的测试照片
  - 组织测试照片到testphoto/test目录，保持良好的文件命名规范
- **Acceptance Criteria Addressed**: [AC-1]
- **Test Requirements**:
  - `programmatic` TR-1.1: 验证测试照片目录创建成功
  - `programmatic` TR-1.2: 验证生成至少15张测试照片
  - `programmatic` TR-1.3: 验证包含JPG和PNG两种格式
  - `programmatic` TR-1.4: 验证包含至少3种不同分辨率
  - `programmatic` TR-1.5: 验证所有照片可被PIL正常打开
- **Notes**: 可以使用PIL库进行图像转换、缩放、调整亮度对比度等操作

## [x] Task 2: 现有测试代码分析与环境准备
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 分析现有tests目录中的测试代码结构
  - 查看conftest.py中的测试fixture配置
  - 了解test_certificate_api.py等相关测试
  - 准备测试数据库和测试环境
  - 确保测试不会影响生产数据
- **Acceptance Criteria Addressed**: [AC-8]
- **Test Requirements**:
  - `programmatic` TR-2.1: 验证测试环境可以正常初始化
  - `programmatic` TR-2.2: 验证测试fixture可用
  - `programmatic` TR-2.3: 验证数据库连接正常
  - `human-judgement` TR-2.4: 检查测试代码结构清晰易懂
- **Notes**: 使用现有的测试基础设施，避免重复造轮子

## [x] Task 3: 基础测试用例开发 - 单张照片上传
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 开发JPG格式单张照片上传测试
  - 开发PNG格式单张照片上传测试
  - 验证Certificate记录创建
  - 验证CertificateImage记录创建
  - 验证文件保存和元数据（哈希、尺寸等）正确性
- **Acceptance Criteria Addressed**: [AC-2, AC-3]
- **Test Requirements**:
  - `programmatic` TR-3.1: JPG照片上传成功，返回200状态
  - `programmatic` TR-3.2: Certificate记录正确创建，包含预期字段
  - `programmatic` TR-3.3: CertificateImage记录正确创建，包含预期字段
  - `programmatic` TR-3.4: 文件哈希值正确计算并存储
  - `programmatic` TR-3.5: 图片尺寸正确读取并存储
  - `programmatic` TR-3.6: PNG照片上传测试通过
- **Notes**: 先使用简单清晰的测试照片进行基础测试

## [x] Task 4: OCR识别与数据存储测试
- **Priority**: P0
- **Depends On**: Task 3
- **Description**: 
  - 开发OCR识别触发测试
  - 验证OCR结果存储到CertificateImage模型
  - 验证OCR结果存储到Certificate模型
  - 验证结构化证书信息提取和存储
  - 验证字段映射的正确性
- **Acceptance Criteria Addressed**: [AC-4]
- **Test Requirements**:
  - `programmatic` TR-4.1: OCR处理触发成功
  - `programmatic` TR-4.2: CertificateImage.ocr_processed设置为True
  - `programmatic` TR-4.3: CertificateImage.ocr_text包含识别文本
  - `programmatic` TR-4.4: CertificateImage.ocr_result包含详细JSON
  - `programmatic` TR-4.5: Certificate.raw_text包含合并文本
  - `programmatic` TR-4.6: Certificate.certificate_info包含结构化信息
  - `programmatic` TR-4.7: 证书基本字段（title/level/issuer等）尝试填充
- **Notes**: OCR处理可能需要较长时间，测试中设置合理超时

## [x] Task 5: 批量上传测试
- **Priority**: P1
- **Depends On**: Task 3
- **Description**: 
  - 开发3-5张照片批量上传测试
  - 验证image_count字段正确性
  - 验证primary_image_id设置正确
  - 验证多张照片与同一Certificate的关联
  - 验证image_order排序正确性
- **Acceptance Criteria Addressed**: [AC-5]
- **Test Requirements**:
  - `programmatic` TR-5.1: 批量上传成功，返回成功状态
  - `programmatic` TR-5.2: 只创建1个Certificate记录
  - `programmatic` TR-5.3: 创建N个CertificateImage记录（N=照片数量）
  - `programmatic` TR-5.4: Certificate.image_count = N
  - `programmatic` TR-5.5: Certificate.primary_image_id = 第一张照片ID
  - `programmatic` TR-5.6: image_order按上传顺序正确设置
- **Notes**: 测试混合JPG和PNG格式的批量上传

## [x] Task 6: 多场景兼容性测试
- **Priority**: P1
- **Depends On**: Task 3, Task 4
- **Description**: 
  - 测试不同分辨率照片（低/中/高）
  - 测试不同质量照片（清晰/模糊）
  - 测试不同文件大小
  - 验证所有场景下数据存储的完整性
- **Acceptance Criteria Addressed**: [AC-6]
- **Test Requirements**:
  - `programmatic` TR-6.1: 低分辨率(640x480)照片处理成功
  - `programmatic` TR-6.2: 中分辨率(1280x960)照片处理成功
  - `programmatic` TR-6.3: 高分辨率(2560x1920)照片处理成功
  - `programmatic` TR-6.4: CertificateImage.image_width/image_height正确记录
  - `programmatic` TR-6.5: 所有场景下数据库记录完整
- **Notes**: 使用参数化测试（pytest.mark.parametrize）减少重复代码

## [x] Task 7: 数据查询验证测试
- **Priority**: P1
- **Depends On**: Task 4, Task 5
- **Description**: 
  - 开发证书数据查询测试
  - 验证关联查询（Certificate -> CertificateImage）
  - 验证OCR结果字段的正确返回
  - 验证API返回数据结构的正确性
- **Acceptance Criteria Addressed**: [AC-7]
- **Test Requirements**:
  - `programmatic` TR-7.1: GET /certificate/{id} 返回正确数据
  - `programmatic` TR-7.2: 返回数据包含关联的CertificateImage列表
  - `programmatic` TR-7.3: OCR相关字段在返回数据中正确显示
  - `programmatic` TR-7.4: 数据结构与API文档一致
- **Notes**: 使用现有的API测试模式

## [x] Task 8: 测试清理和资源管理
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 开发测试fixture进行自动清理
  - 确保测试数据不污染生产数据库
  - 清理测试上传的文件
  - 清理创建的数据库记录
- **Acceptance Criteria Addressed**: [AC-8]
- **Test Requirements**:
  - `programmatic` TR-8.1: 测试前数据库状态已知
  - `programmatic` TR-8.2: 测试后Certificate记录被清理
  - `programmatic` TR-8.3: 测试后CertificateImage记录被清理
  - `programmatic` TR-8.4: 测试后CertificateBatch记录被清理
  - `programmatic` TR-8.5: 测试上传的文件被清理
- **Notes**: 使用pytest的yield fixture实现setup/teardown

## [x] Task 9: 测试报告生成与文档完善
- **Priority**: P2
- **Depends On**: Task 3-7
- **Description**: 
  - 运行完整测试套件
  - 生成详细的测试报告
  - 记录测试结果和发现的问题
  - 完善测试文档
- **Acceptance Criteria Addressed**: [AC-9]
- **Test Requirements**:
  - `human-judgement` TR-9.1: 测试报告包含测试总数、通过数、失败数
  - `human-judgement` TR-9.2: 测试报告包含每个测试场景的结果
  - `human-judgement` TR-9.3: 失败测试包含详细错误信息
  - `human-judgement` TR-9.4: 报告包含数据完整性验证结果
  - `programmatic` TR-9.5: 所有测试用例执行无错误
- **Notes**: 使用pytest-html或allure生成美观的测试报告
