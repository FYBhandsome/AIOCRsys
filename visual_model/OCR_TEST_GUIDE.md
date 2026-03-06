# OCR识别与数据存储测试说明

## 概述

本文档说明如何运行OCR识别与数据存储的测试用例。

## 测试用例

测试用例位于 `tests/test_certificate_api.py` 文件中的 `TestCertificateOCRProcessing` 类，包含以下测试：

1. **test_ocr_processing_trigger** - OCR识别触发测试
2. **test_ocr_processed_flag** - 验证CertificateImage.ocr_processed被设置为True
3. **test_ocr_text_content** - 验证CertificateImage.ocr_text包含识别的原始文本
4. **test_ocr_result_json** - 验证CertificateImage.ocr_result包含详细的OCR结果JSON
5. **test_certificate_raw_text** - 验证Certificate.raw_text包含合并文本
6. **test_certificate_ocr_result** - 验证Certificate.ocr_result包含详细结果
7. **test_certificate_info_structured** - 验证Certificate.certificate_info包含结构化的证书信息
8. **test_certificate_basic_fields** - 验证证书基本字段（title、level、issuer等）被尝试填充

## 前置条件

### 1. 虚拟环境激活

确保visual_model的虚拟环境已激活：

```powershell
# 在PowerShell中
D:\PaddleOCR\visual_model\venv\Scripts\Activate.ps1
```

### 2. 依赖安装

确保已安装所有依赖：

```powershell
cd D:\PaddleOCR\visual_model
pip install -r requirements.txt
pip install -r tests/requirements.txt
pip install pytest-timeout
```

### 3. PaddleOCR模型

确保PaddleOCR模型已下载或可以正常访问。

### 4. 测试照片

确保testphoto/test目录下有测试照片。

## 运行测试

### 运行所有OCR测试

```powershell
cd D:\PaddleOCR\visual_model
python -m pytest tests/test_certificate_api.py::TestCertificateOCRProcessing -v -s
```

### 运行单个OCR测试

```powershell
# 运行OCR触发测试
python -m pytest tests/test_certificate_api.py::TestCertificateOCRProcessing::test_ocr_processing_trigger -v -s

# 运行所有测试并生成报告
python -m pytest tests/test_certificate_api.py::TestCertificateOCRProcessing -v --html=reports/ocr_test_report.html
```

### 带标记运行测试

```powershell
# 只运行OCR相关测试
python -m pytest -m ocr -v -s

# 运行证书和OCR相关测试
python -m pytest -m "certificate and ocr" -v -s
```

## 测试超时设置

由于OCR处理可能需要较长时间，我们在pytest.ini中设置了超时时间为300秒（5分钟）。

## 测试验证结果

测试通过标准：

1. **OCR识别触发测试** - 成功上传证书并触发OCR处理
2. **ocr_processed标记** - CertificateImage.ocr_processed = True
3. **ocr_text内容** - CertificateImage.ocr_text包含非空字符串
4. **ocr_result JSON** - CertificateImage.ocr_result是列表，包含text、score、box字段
5. **raw_text合并** - Certificate.raw_text包含合并的文本
6. **ocr_result详细** - Certificate.ocr_result包含详细结果
7. **certificate_info结构化** - Certificate.certificate_info包含success、raw_text、confidence字段
8. **基本字段填充** - 验证证书基本字段被尝试填充

## 新增文件

1. **app/services/certificate_ocr_processing_service.py** - OCR处理服务
2. **tests/test_certificate_api.py** - 已添加TestCertificateOCRProcessing测试类
3. **pytest.ini** - 已添加超时配置
4. **tests/conftest.py** - 已添加ocr标记
5. **app/api/certificate_upload.py** - 已添加OCR触发API端点
6. **app/services/certificate_storage_service.py** - 已集成OCR自动触发

## API端点

新增的API端点：

1. **POST /api/v1/certificate/{certificate_id}/ocr/trigger** - 手动触发证书OCR处理
2. **POST /api/v1/certificate/image/{image_id}/ocr/trigger** - 手动触发单张图片OCR处理

## 注意事项

1. 首次运行OCR测试时，PaddleOCR会下载模型，可能需要较长时间
2. 测试照片的质量会影响OCR识别结果
3. OCR识别有不确定性，某些测试可能因为识别结果而有差异
4. 建议先运行单个测试验证环境配置，再运行完整测试套件
