# 飞桨OCR照片数据存储兼容性测试 - 验证清单

## 测试照片集验证
- [x] 测试照片目录testphoto/test已创建
- [x] 生成至少15张测试照片
- [x] 测试照片包含JPG和PNG两种格式
- [x] 测试照片包含至少3种不同分辨率（低/中/高）
- [x] 测试照片包含至少3种不同质量场景
- [x] 所有测试照片可被PIL正常打开和读取
- [x] 测试照片命名规范清晰，易于识别场景

## 数据库模型验证
- [x] Certificate模型的所有字段定义正确
- [x] CertificateImage模型的所有字段定义正确
- [x] Certificate和CertificateImage的外键关联正确
- [x] OCR相关字段（ocr_processed、ocr_text、ocr_result）存在
- [x] 证书信息字段（title、level、issuer、issue_date等）存在
- [x] 图片元数据字段（file_path、file_hash、image_width、image_height）存在

## 单张照片上传验证
- [x] JPG格式照片上传API调用成功
- [x] Certificate记录成功创建到数据库
- [x] CertificateImage记录成功创建到数据库
- [x] 照片文件成功保存到文件系统
- [x] 文件哈希值正确计算并存储
- [x] 图片尺寸正确读取并存储
- [x] 外键关联（certificate_id）正确建立
- [x] PNG格式照片上传同样通过以上验证

## OCR识别与存储验证
- [x] OCR识别可以正常触发
- [x] CertificateImage.ocr_processed被设置为True
- [x] CertificateImage.ocr_text包含识别的原始文本
- [x] CertificateImage.ocr_result包含详细的OCR结果JSON
- [x] Certificate.raw_text包含合并后的文本
- [x] Certificate.ocr_result包含详细结果
- [x] Certificate.certificate_info包含结构化的证书信息
- [x] 证书基本字段（title、level、issuer等）被尝试填充

## 批量上传验证
- [x] 3-5张照片批量上传API调用成功
- [x] 只创建1个Certificate记录
- [x] 创建N个CertificateImage记录（N=照片数量）
- [x] Certificate.image_count正确设置为N
- [x] Certificate.primary_image_id正确设置为第一张照片ID
- [x] 所有照片文件成功保存
- [x] 所有CertificateImage记录正确关联到同一Certificate
- [x] image_order按上传顺序正确设置

## 多场景兼容性验证
- [x] 低分辨率(640x480)照片处理成功
- [x] 中分辨率(1280x960)照片处理成功
- [x] 高分辨率(2560x1920)照片处理成功
- [x] CertificateImage.image_width和image_height正确记录
- [x] 不同分辨率下OCR都能正常处理
- [x] 所有场景下数据库记录完整无缺失
- [x] 不同文件大小的照片都能正常处理

## 数据查询验证
- [x] GET /certificate/{id} API返回正确数据
- [x] 返回数据包含关联的CertificateImage列表
- [x] OCR相关字段在返回数据中正确显示
- [x] 返回数据结构与API文档一致
- [x] 可以查询单个CertificateImage的详情
- [x] 关联查询（Certificate -> CertificateImage）工作正常

## 测试清理验证
- [x] 测试前数据库状态已知且可重现
- [x] 测试后所有测试创建的Certificate记录被删除
- [x] 测试后所有测试创建的CertificateImage记录被删除
- [x] 测试后所有测试创建的CertificateBatch记录被删除
- [x] 测试上传的照片文件被清理
- [x] 数据库恢复到测试前的干净状态
- [x] 测试数据与生产数据完全隔离

## 测试执行验证
- [x] 所有测试用例可以独立运行
- [x] 测试执行不依赖外部状态
- [x] 单个测试用例执行时间不超过30秒
- [x] 完整测试套件执行时间不超过10分钟
- [x] 测试失败提供清晰的错误信息
- [x] 测试代码具有良好的可读性和注释
- [x] 测试遵循项目代码规范

## 测试报告验证
- [x] 测试报告包含测试总数、通过数、失败数
- [x] 测试报告包含每个测试场景的结果
- [x] 失败测试包含详细的错误信息
- [x] 报告包含数据完整性验证结果
- [x] 报告格式清晰易读
- [x] 报告可以被团队成员理解和使用

## 端到端流程验证
- [x] 完整的照片上传→OCR识别→数据存储流程工作正常
- [x] 从用户上传照片到数据可查询的端到端延迟可接受
- [x] 异常情况有适当的错误处理
- [x] 系统在各种测试场景下保持稳定
- [x] 没有数据丢失或数据不一致的情况
