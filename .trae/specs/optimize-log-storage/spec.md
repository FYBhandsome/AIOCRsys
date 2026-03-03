# 日志存储系统优化 Spec

## Why
当前 `D:\PaddleOCR\logs` 目录存在日志文件组织混乱、内容重复冗余、配置不一致等问题，导致调试困难、磁盘空间浪费、日志管理效率低下。需要对日志存储系统进行全面优化，建立统一、规范、高效的日志管理机制。

## What Changes
- 统一日志目录结构，建立清晰的服务分类存储方案
- 消除日志内容重复，确保每条日志只写入一个目标文件
- 统一日志配置模块，建立集中化的日志配置管理
- 优化日志轮转和归档策略，平衡调试需求与磁盘空间管理
- 清理历史冗余日志文件，建立日志清理机制

## Impact
- Affected specs: 日志管理能力、系统运维能力
- Affected code: 
  - `shared_utils/unified_logger.py` - 统一日志模块
  - `PaddleOCRRAG/app/core/logger.py` - RAG日志模块
  - `visual_model/app/core/enhanced_logger.py` - Visual Model日志模块
  - `visual_model/app/core/logger.py` - 兼容层
  - `start.py` - 启动脚本日志配置
  - `PaddleOCRRAG/app/main.py` - RAG服务入口
  - `visual_model/main.py` - Visual Model服务入口

## ADDED Requirements

### Requirement: 统一日志目录结构
系统 SHALL 采用以下目录结构存储日志文件：

```
logs/
├── startup/                    # 启动日志（保留）
│   └── startup_{YYYY-MM-DD}.log
├── visual_model/               # Visual Model服务日志
│   ├── app_{YYYY-MM-DD}.log    # 常规日志
│   └── error_{YYYY-MM-DD}.log  # 错误日志
├── rag/                        # RAG服务日志
│   ├── app_{YYYY-MM-DD}.log    # 常规日志
│   └── error_{YYYY-MM-DD}.log  # 错误日志
├── frontend/                   # 前端日志（如有）
│   └── app_{YYYY-MM-DD}.log
└── archive/                    # 归档日志（可选）
    └── {service_name}/
        └── {YYYY-MM}/
```

#### Scenario: 日志文件创建
- **WHEN** 服务启动并初始化日志系统
- **THEN** 日志文件应创建在对应服务的子目录下
- **AND** 文件名应包含日期标识
- **AND** 根目录下不应有散乱的日志文件

### Requirement: 统一日志配置入口
系统 SHALL 通过 `shared_utils/unified_logger.py` 提供统一的日志配置接口，所有服务模块应使用此统一接口。

#### Scenario: 服务日志初始化
- **WHEN** 服务模块初始化日志系统
- **THEN** 应调用 `setup_logging(service_name="xxx")` 统一接口
- **AND** 日志应自动写入正确的服务子目录
- **AND** 不应在各服务模块中重复定义日志目录路径

### Requirement: 消除日志重复写入
系统 SHALL 确保每条日志记录只写入一个目标日志文件，避免同一内容写入多个文件。

#### Scenario: 日志写入去重
- **WHEN** 产生一条日志记录
- **THEN** 该记录应只写入当前服务的日志文件
- **AND** 不应同时写入根目录和服务子目录
- **AND** 不应同时写入多个相同级别的日志文件

### Requirement: 统一日志轮转策略
系统 SHALL 采用以下日志轮转策略：

| 参数 | 值 | 说明 |
|------|-----|------|
| 单文件最大大小 | 50 MB | 超过此大小触发轮转 |
| 保留文件数量 | 10 个 | 每个服务保留的历史文件数 |
| 自动清理周期 | 30 天 | 超过此天数的日志自动删除 |
| 文件命名格式 | `{name}_{YYYY-MM-DD}_{seq}.log` | 轮转后的文件名 |

#### Scenario: 日志文件轮转
- **WHEN** 日志文件大小超过50MB
- **THEN** 系统应自动轮转日志文件
- **AND** 创建新的日志文件继续写入
- **AND** 保留的历史文件不超过10个

#### Scenario: 历史日志清理
- **WHEN** 日志文件超过30天
- **THEN** 系统应自动删除该日志文件
- **AND** 在服务启动时执行清理检查

### Requirement: 统一日志格式
系统 SHALL 采用统一的日志格式：

**文件日志格式：**
```
{YYYY-MM-DD HH:MM:SS.mmm} | {LEVEL:8} | {logger}:{line} | {function} | {message}
```

**控制台日志格式：**
- 支持彩色输出
- 包含请求ID、用户ID等上下文信息
- 时间戳精确到毫秒

#### Scenario: 日志格式一致性
- **WHEN** 查看任意服务的日志文件
- **THEN** 日志格式应保持一致
- **AND** 时间戳格式统一
- **AND** 日志级别对齐

### Requirement: 日志级别分层
系统 SHALL 按以下规则分层输出日志：

| 输出目标 | 日志级别 | 说明 |
|----------|----------|------|
| 控制台 | INFO及以上 | 避免控制台输出过多调试信息 |
| 常规日志文件 | DEBUG及以上 | 完整记录所有日志 |
| 错误日志文件 | ERROR及以上 | 仅记录错误和严重问题 |

#### Scenario: 错误日志独立存储
- **WHEN** 产生ERROR或更高级别的日志
- **THEN** 该日志应同时写入常规日志文件和错误日志文件
- **AND** 错误日志文件便于快速定位问题

### Requirement: 清理历史冗余文件
系统 SHALL 在优化实施时清理以下冗余日志文件：

- 根目录下的散乱日志文件（`logs/*.log`）
- 重复的日志文件
- 空日志文件

#### Scenario: 冗余文件清理
- **WHEN** 执行日志系统优化
- **THEN** 应备份有价值的日志内容
- **AND** 删除根目录下的散乱日志文件
- **AND** 保留服务子目录下的有效日志

## MODIFIED Requirements

### Requirement: unified_logger.py 模块增强
原 `shared_utils/unified_logger.py` 模块 SHALL 增加以下功能：

1. 强制使用子目录存储日志
2. 统一文件命名规范
3. 增强日志轮转配置
4. 添加日志清理工具函数

### Requirement: 服务模块日志配置统一
各服务模块 SHALL 修改日志初始化方式：

**修改前（示例）：**
```python
# PaddleOCRRAG/app/core/logger.py 自定义日志目录
UNIFIED_LOG_DIR = PROJECT_ROOT / "logs" / "rag"
```

**修改后：**
```python
# 使用统一日志模块
from shared_utils.unified_logger import setup_logging, get_logger
setup_logging(service_name="rag")
```

## REMOVED Requirements

### Requirement: 废弃独立的日志配置模块
**Reason**: 存在多个重复的日志配置模块导致配置不一致
**Migration**: 
- `PaddleOCRRAG/app/core/logger.py` 改为兼容层，导入统一模块
- `visual_model/app/core/enhanced_logger.py` 保留但简化，主要逻辑移至统一模块
- `visual_model/app/core/logger.py` 保持为兼容层

### Requirement: 废弃根目录散乱日志
**Reason**: 根目录下的散乱日志文件破坏了目录结构的一致性
**Migration**: 清理根目录下的日志文件，迁移有价值的内容到对应服务子目录
