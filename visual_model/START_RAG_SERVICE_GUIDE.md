# 启动RAG服务并运行端到端测试指南

## 当前状态

- ✅ visual_model服务运行在端口8001
- ❌ RAG服务未在端口8010上正确运行（当前端口8010有其他服务）
- ✅ 所有Mock测试通过（16/16）
- ✅ 全量测试通过（288/288）
- ⏭️ 2个端到端测试跳过（需要真实RAG服务）

## 启动RAG服务的步骤

### 方法1：使用批处理文件（推荐）

在 `d:\PaddleOCR\PaddleOCRRAG` 目录下运行：

```bash
cd d:\PaddleOCR\PaddleOCRRAG
run.bat
```

### 方法2：直接使用uvicorn

在 `d:\PaddleOCR\PaddleOCRRAG` 目录下运行：

```bash
cd d:\PaddleOCR\PaddleOCRRAG
uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
```

## 验证RAG服务是否启动成功

启动服务后，在浏览器中访问：

```
http://localhost:8010/docs
```

应该能看到FastAPI的API文档页面。

## 运行端到端测试

RAG服务启动成功后，在另一个终端运行：

```bash
cd d:\PaddleOCR\visual_model
python -m pytest tests/test_rag_integration.py::TestRAGIntegrationE2E -v --tb=short
```

或者运行完整的RAG集成测试：

```bash
cd d:\PaddleOCR\visual_model
python -m pytest tests/test_rag_integration.py -v --tb=short
```

## 或者使用测试脚本

也可以使用我们创建的测试脚本：

```bash
cd d:\PaddleOCR\visual_model
python start_rag_and_test.py
```

## 端到端测试内容

跳过的两个测试会验证：

1. **test_rag_chat_end_to_end**: 测试聊天端到端流程
   - 发送消息："省级竞赛加多少分？"
   - 验证返回的回复是否有效
   - 验证响应时间是否合理

2. **test_rag_calculate_score_end_to_end**: 测试计算加分端到端流程
   - 发送证书信息："蓝桥杯全国软件和信息技术专业人才大赛 省级一等奖"
   - 验证返回的分数和类别
   - 验证响应时间是否合理

## 已完成的工作

即使没有运行真实的RAG服务，我们已经完成了：

1. ✅ 创建了完整的RAG集成测试框架
2. ✅ 修复了RAGClient的API路径问题
3. ✅ 添加了RAGClient的timeout参数支持
4. ✅ 所有Mock测试通过（16个）
5. ✅ 异常处理测试通过（3个）
6. ✅ API兼容性验证通过（2个）
7. ✅ 数据库模型兼容性验证通过
8. ✅ 数据库迁移状态验证通过
9. ✅ 全量测试通过率100%（288/288）
10. ✅ 创建了完整的测试报告

## 注意事项

- 确保端口8010没有被其他服务占用
- 如果端口8010被占用，可以修改RAG服务使用其他端口，然后同步修改visual_model的配置
- visual_model的RAG服务URL配置在 `config.py` 的 `RAG_BASE_URL` 中
