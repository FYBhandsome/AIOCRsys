# 端口冲突问题解决 - 实施计划

## 问题分析

通过全面审计发现，端口冲突的根本原因是：
- **visual_model** 默认端口：8001
- **PaddleOCRRAG** 备用端口列表包含：8001（这是冲突源！）

## 端口使用全景图

| 服务 | 默认端口 | 备用端口 | 虚拟环境 | 说明 |
|------|---------|---------|---------|------|
| visual_model | 8001 | 8002, 8003, 8004, 8005, 8006 | venv | 主后端API服务 |
| PaddleOCRRAG | 8000 | 8010, 8011, 8012, 8013, 8014 | .conda | RAG智能问答服务 |
| 前端 | 5173 | 5174, 5175, 5176, 5177, 5178 | Node.js | Vue.js前端应用 |

## 实施任务

## [x] Task 1: 修复PaddleOCRRAG备用端口配置
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 修改start.py中RAG服务的备用端口列表
  - 移除8001，改用8010-8014
  - 确保与visual_model端口完全隔离
- **Success Criteria**:
  - RAG服务不再使用8001作为备用端口
  - 端口配置无重叠
- **Test Requirements**:
  - `programmatic` TR-1.1: 验证start.py中RAG备用端口已更新
  - `programmatic` TR-1.2: 验证RAG和visual_model端口无重叠
- **Notes**: 修改d:\PaddleOCR\start.py第124行

## [ ] Task 2: 验证PaddleOCRRAG独立启动
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 检查PaddleOCRRAG的main.py端口配置
  - 检查PaddleOCRRAG的run.bat端口配置
  - 确保硬编码端口与配置一致
- **Success Criteria**:
  - PaddleOCRRAG所有端口配置统一为8000
- **Test Requirements**:
  - `programmatic` TR-2.1: 验证PaddleOCRRAG/main.py端口为8000
  - `programmatic` TR-2.2: 验证PaddleOCRRAG/run.bat端口为8000
- **Notes**: 两个文件都需要检查

## [x] Task 3: 验证visual_model配置
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 检查visual_model的config.py端口配置
  - 检查visual_model的.env配置
  - 验证RAG_BASE_URL指向正确的RAG服务端口
- **Success Criteria**:
  - visual_model端口配置正确为8001
  - RAG_BASE_URL指向http://localhost:8000
- **Test Requirements**:
  - `programmatic` TR-3.1: 验证config.py中PORT=8001
  - `programmatic` TR-3.2: 验证config.py中RAG_BASE_URL=http://localhost:8000
- **Notes**: 确保跨服务调用地址正确

## [ ] Task 4: 验证前端配置
- **Priority**: P1
- **Depends On**: Task 3
- **Description**: 
  - 检查前端.env配置
  - 验证API_BASE_URL指向正确的visual_model端口
- **Success Criteria**:
  - 前端API地址指向http://localhost:8001/api
- **Test Requirements**:
  - `programmatic` TR-4.1: 验证前端.env中VITE_API_BASE_URL配置正确
- **Notes**: 前端应该调用visual_model，不是直接调用RAG

## [ ] Task 5: 创建端口配置文档
- **Priority**: P1
- **Depends On**: Task 1-4
- **Description**: 
  - 创建端口配置说明文档
  - 记录各服务端口分配
  - 说明端口冲突解决历史
- **Success Criteria**:
  - 文档完整记录端口配置
- **Test Requirements**:
  - `human-judgement` TR-5.1: 文档包含完整的端口分配表
  - `human-judgement` TR-5.2: 文档说明清晰易懂
- **Notes**: 保存到项目根目录docs文件夹

## [ ] Task 6: 验证系统启动
- **Priority**: P0
- **Depends On**: Task 1-4
- **Description**: 
  - 测试各服务独立启动
  - 测试统一启动脚本start.py
  - 验证无端口冲突错误
- **Success Criteria**:
  - 所有服务正常启动，无端口冲突
- **Test Requirements**:
  - `programmatic` TR-6.1: visual_model可在8001端口正常启动
  - `programmatic` TR-6.2: PaddleOCRRAG可在8000端口正常启动
  - `programmatic` TR-6.3: 无"address already in use"错误
- **Notes**: 先关闭所有现有进程再测试

## [x] Task 7: 功能验证测试
- **Priority**: P1
- **Depends On**: Task 6
- **Description**: 
  - 验证前后端通信正常
  - 验证visual_model与RAG服务通信正常
  - 执行基本功能测试
- **Success Criteria**:
  - 系统各组件通信正常
- **Test Requirements**:
  - `programmatic` TR-7.1: 前端可正常访问visual_model API
  - `programmatic` TR-7.2: visual_model可正常调用RAG服务
  - `programmatic` TR-7.3: 健康检查端点响应正常
- **Notes**: 重点测试跨服务调用
