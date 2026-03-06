# 飞桨OCR照片数据存储兼容性测试 - 产品需求文档

## Overview
- **Summary**: 确保通过飞桨OCR处理的上传照片数据能够正确存储到数据库中对应的AI模型记录中。通过创建具有代表性的测试照片集，系统性验证从照片上传、OCR识别到数据存储整个流程的数据传递兼容性。
- **Purpose**: 解决照片上传、OCR识别和数据存储流程中的数据传递问题，确保在不同照片格式、分辨率和光照条件下，数据都能准确、完整地传递并存储到对应模型记录中。
- **Target Users**: 开发团队、测试团队、系统管理员

## Goals
- 创建涵盖不同格式（JPG、PNG）、不同分辨率、不同光照条件的代表性测试照片集
- 系统性验证照片上传→OCR识别→数据存储完整流程的兼容性
- 确保Certificate和CertificateImage模型的数据完整性和一致性
- 验证OCR结果正确存储到数据库的对应字段中
- 建立端到端的自动化测试流程

## Non-Goals (Out of Scope)
- 不涉及OCR识别准确率的优化（仅验证数据传递）
- 不涉及前端UI界面的修改
- 不涉及数据库性能优化
- 不涉及照片内容的真实性验证

## Background & Context

### 现有业务流程

项目已具备完整的证书照片上传、OCR识别和数据存储流程：

1. **照片上传层** (`app/api/certificate_upload.py`)
   - API: `POST /certificate/upload`
   - 接收多文件上传，支持JPG、PNG等格式
   - 调用证书存储服务处理

2. **存储服务层** (`app/services/certificate_storage_service.py`)
   - 生成批次ID和证书记录
   - 保存照片到本地文件系统
   - 创建Certificate和CertificateImage数据库记录
   - 记录文件路径、哈希值、尺寸等元数据

3. **OCR识别层** (`app/services/ocr_service.py`)
   - 封装PaddleOCR进行文本识别
   - 支持图像缩放和预处理
   - 提取证书结构化信息（姓名、学号、奖项、级别等）

4. **数据模型层** (`app/models/tortoise_models.py`)
   - `Certificate`模型：存储证书基本信息和OCR结果
   - `CertificateImage`模型：存储照片文件信息和OCR处理状态

### 现有测试资源

项目已有testphoto目录，包含：
- ”高教社杯“全国大学生数学建模竞赛省一.jpg
- 优秀文明宿舍.png
- 四级成绩.jpg
- 蓝桥杯大赛省三.png
- 软件著作权.jpg

### 技术栈
- **后端框架**: FastAPI + Tortoise ORM
- **OCR引擎**: PaddleOCR
- **数据库**: SQLite
- **图像处理**: PIL (Pillow)
- **测试框架**: pytest

## Functional Requirements

### FR-1: 测试照片集创建
创建涵盖多种场景的测试照片集，包括：
- 不同文件格式：JPG、PNG
- 不同分辨率：低(640x480)、中(1280x960)、高(2560x1920)
- 不同光照条件：正常光照、偏暗、偏亮、逆光
- 不同角度：正拍、轻微倾斜、严重倾斜
- 不同清晰度：清晰、轻微模糊、严重模糊
- 现有真实证书照片的复用

### FR-2: 端到端流程测试
验证完整的业务流程：
- 照片文件上传API调用
- 文件验证和存储
- Certificate和CertificateImage记录创建
- OCR识别触发和执行
- OCR结果提取和结构化
- 数据存储到数据库对应字段
- 结果查询和验证

### FR-3: 数据完整性验证
验证数据库记录的完整性：
- Certificate模型所有字段正确填充
- CertificateImage模型所有字段正确填充
- OCR原始文本存储(raw_text)
- OCR详细结果存储(ocr_result)
- 结构化证书信息存储(certificate_info)
- 外键关联完整性(certificate_id)
- 图片数量统计正确性(image_count)

### FR-4: 多场景兼容性测试
测试不同照片场景下的数据兼容性：
- JPG格式照片处理
- PNG格式照片处理
- 不同分辨率照片处理
- 不同文件大小照片处理
- 多张照片批量上传处理
- 单张照片处理

### FR-5: 测试自动化脚本开发
开发自动化测试脚本：
- pytest测试用例编写
- 测试数据准备和清理
- 测试结果断言和验证
- 测试报告生成

## Non-Functional Requirements

### NFR-1: 测试可靠性
- 测试用例应具有确定性，相同输入应产生相同结果
- 测试应独立运行，不依赖外部状态
- 测试失败应提供清晰的错误信息

### NFR-2: 测试执行效率
- 单个测试用例执行时间不超过30秒
- 完整测试套件执行时间不超过10分钟
- 支持选择性运行特定测试用例

### NFR-3: 数据隔离
- 测试数据应与生产数据完全隔离
- 测试完成后应清理所有测试数据
- 测试不应影响现有系统功能

### NFR-4: 可维护性
- 测试代码应具有良好的可读性和注释
- 测试用例应遵循项目代码规范
- 测试应易于扩展和维护

## Constraints

### 技术约束
- 必须使用现有的pytest测试框架
- 必须使用现有的数据库模型（Certificate、CertificateImage）
- 必须使用现有的API接口和服务层
- 测试照片必须存储在项目testphoto目录下

### 业务约束
- 测试不能修改现有真实数据
- 测试应模拟真实的业务场景
- 测试应覆盖主要的证书类型

### 时间约束
- 测试开发应在可接受的时间范围内完成
- 测试执行应高效，不占用过多开发时间

## Dependencies
- 现有的证书上传API (`app/api/certificate_upload.py`)
- 现有的证书存储服务 (`app/services/certificate_storage_service.py`)
- 现有的OCR服务 (`app/services/ocr_service.py`)
- 现有的数据库模型 (`app/models/tortoise_models.py`)
- 现有的testphoto目录和测试照片
- pytest测试框架和现有测试基础设施

## Assumptions
- 现有的业务流程代码是正确的
- PaddleOCR服务可用且能正常工作
- 数据库连接和操作正常
- 文件系统有足够的存储空间用于测试照片
- 测试环境与生产环境配置一致
- 现有的testphoto照片可以用于测试

## Acceptance Criteria

### AC-1: 测试照片集创建完成
- **Given**: 项目testphoto目录存在
- **When**: 执行测试照片集创建脚本
- **Then**: 
  - 生成至少15张测试照片
  - 涵盖JPG和PNG两种格式
  - 涵盖至少3种不同分辨率
  - 涵盖至少3种不同光照/质量场景
  - 所有测试照片可读且可被PIL打开
- **Verification**: `programmatic`
- **Notes**: 测试照片应存储在testphoto/test目录下

### AC-2: 单张JPG照片上传和存储成功
- **Given**: 系统正常运行，测试数据库已初始化
- **When**: 上传一张JPG格式的证书照片
- **Then**:
  - Certificate记录成功创建
  - CertificateImage记录成功创建
  - 照片文件成功保存到文件系统
  - 文件哈希值正确计算
  - 图片尺寸正确读取
  - 外键关联正确建立
- **Verification**: `programmatic`

### AC-3: 单张PNG照片上传和存储成功
- **Given**: 系统正常运行，测试数据库已初始化
- **When**: 上传一张PNG格式的证书照片
- **Then**:
  - Certificate记录成功创建
  - CertificateImage记录成功创建
  - 照片文件成功保存到文件系统
  - 文件哈希值正确计算
  - 图片尺寸正确读取
  - 外键关联正确建立
- **Verification**: `programmatic`

### AC-4: OCR识别结果正确存储
- **Given**: 上传了一张证书照片并创建了数据库记录
- **When**: 触发OCR识别处理
- **Then**:
  - CertificateImage.ocr_processed设置为True
  - CertificateImage.ocr_text存储原始识别文本
  - CertificateImage.ocr_result存储详细OCR结果JSON
  - Certificate.raw_text存储合并文本
  - Certificate.ocr_result存储详细结果
  - Certificate.certificate_info存储结构化信息
  - 证书基本字段（title、level、issuer等）尝试填充
- **Verification**: `programmatic`

### AC-5: 多张照片批量上传成功
- **Given**: 系统正常运行，测试数据库已初始化
- **When**: 同时上传3-5张证书照片
- **Then**:
  - 成功创建1个Certificate记录
  - 成功创建N个CertificateImage记录（N=照片数量）
  - Certificate.image_count正确设置为N
  - Certificate.primary_image_id正确设置为第一张照片ID
  - 所有照片文件成功保存
  - 所有数据库记录正确关联
- **Verification**: `programmatic`

### AC-6: 不同分辨率照片处理兼容性
- **Given**: 准备低、中、高三种分辨率的测试照片
- **When**: 分别上传不同分辨率的照片
- **Then**:
  - 所有分辨率照片都能成功上传
  - 图片尺寸正确记录到CertificateImage
  - OCR能正常处理不同分辨率
  - 数据库记录完整无缺失
- **Verification**: `programmatic`

### AC-7: 数据查询验证
- **Given**: 已上传照片并完成OCR处理
- **When**: 通过API查询证书数据
- **Then**:
  - 能正确查询Certificate记录
  - 能正确查询关联的CertificateImage记录
  - OCR结果字段能正确返回
  - 数据结构与API文档一致
- **Verification**: `programmatic`

### AC-8: 测试清理完成
- **Given**: 测试执行完毕
- **When**: 执行测试清理逻辑
- **Then**:
  - 所有测试创建的Certificate记录被删除
  - 所有测试创建的CertificateImage记录被删除
  - 所有测试创建的CertificateBatch记录被删除
  - 测试上传的照片文件被清理
  - 数据库恢复到测试前状态
- **Verification**: `programmatic`

### AC-9: 测试报告生成
- **Given**: 所有测试用例执行完毕
- **When**: 生成测试报告
- **Then**:
  - 报告包含测试总数、通过数、失败数
  - 报告包含每个测试场景的结果
  - 报告包含失败测试的详细错误信息
  - 报告包含数据完整性验证结果
- **Verification**: `human-judgment`

## Open Questions
- [ ] 是否需要测试PDF格式的证书？（现有代码中看到PDF处理逻辑）
- [ ] 是否需要测试极端大文件（超过10MB）？
- [ ] 测试照片是否需要包含真实的个人信息，还是使用模糊处理的测试数据？
- [ ] 是否需要性能测试（如100张照片批量上传）？
- [ ] OCR识别失败的场景是否需要特别测试？
