# 数据库管理脚本

本目录包含数据库管理和维护的脚本工具。

## 脚本列表

### 核心脚本

| 脚本 | 功能 | 使用方法 |
|------|------|----------|
| `db_manager.py` | 统一数据库管理（初始化、迁移、备份、恢复） | `python scripts/db_manager.py --help` |
| `verify_db_structure.py` | 验证数据库结构与模型定义一致性 | `python scripts/verify_db_structure.py` |
| `manage.py` | Django风格的管理命令入口 | `python scripts/manage.py --help` |

### 辅助脚本

| 脚本 | 功能 |
|------|------|
| `create_test_users.py` | 创建测试用户账户 |
| `check_users.py` | 检查用户账户状态 |
| `download_models.py` | 下载OCR模型文件 |
| `analyze_excel.py` | 分析Excel文件结构 |
| `generate_test_report.py` | 生成测试报告 |

## 数据库管理命令

### 初始化数据库
```bash
python scripts/db_manager.py init
```

### 检查数据库表
```bash
python scripts/db_manager.py check
```

### 执行数据库迁移
```bash
python scripts/db_manager.py migrate
```

### 备份数据库
```bash
python scripts/db_manager.py backup
```

### 重置数据库（危险操作）
```bash
python scripts/db_manager.py reset --yes
```

### 创建示例数据
```bash
python scripts/db_manager.py sample
```

## Aerich 迁移命令

项目使用Aerich进行数据库迁移管理：

```bash
# 初始化迁移
aerich init -t app.core.db_config.TORTOISE_ORM

# 初始化数据库
aerich init-db

# 生成迁移文件
aerich migrate --name "description"

# 执行迁移
aerich upgrade
```

## 注意事项

1. 执行迁移前请先备份数据库
2. 生产环境请谨慎使用reset命令
3. 迁移文件存放在 `migrations/models/` 目录
