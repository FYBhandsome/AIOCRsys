# 脚本工具说明

## 📁 目录结构

```
scripts/
├── manage.py                      # 统一管理工具入口（推荐使用）⭐
├── optimize.py                    # 项目优化工具
├── db_manager.py                  # 数据库管理工具
├── download_models.py             # 模型下载工具
├── import_comprehensive_data.py   # 综合测评数据导入脚本
├── verify_import.py               # 数据导入验证脚本
└── README.md                      # 本文档
```

## 🚀 快速开始

### 使用统一管理工具（推荐）⭐

**所有功能都通过 `manage.py` 统一管理，这是推荐的使用方式：**

```bash
# 显示帮助菜单
python scripts/manage.py

# 数据库管理
python scripts/manage.py db init                        # 初始化数据库
python scripts/manage.py db backup                      # 备份数据库
python scripts/manage.py db check                       # 检查数据库表
python scripts/manage.py db migrate                    # 执行所有迁移
python scripts/manage.py db reset                       # 重置数据库（危险操作）
python scripts/manage.py db sample                      # 创建示例数据

# 模型下载
python scripts/manage.py download                       # 下载OCR模型

# 综合测评数据导入
python scripts/import_comprehensive_data.py            # 导入综合测评数据

# 数据导入验证
python scripts/verify_import.py                        # 验证导入结果

# 项目优化
python scripts/optimize.py                              # 执行项目优化
```

### 直接使用单个脚本

虽然可以通过 `manage.py` 统一调用，但也可以直接使用单个脚本：

```bash
# 数据库管理
python scripts/db_manager.py init
python scripts/db_manager.py backup
python scripts/db_manager.py migrate

# 模型下载
python scripts/download_models.py

# 综合测评数据导入
python scripts/import_comprehensive_data.py

# 数据导入验证
python scripts/verify_import.py

# 项目优化
python scripts/optimize.py
```

## 📋 工具详细说明

### 1. 统一管理工具 (manage.py) ⭐

**整合了所有脚本功能的统一入口，推荐使用此工具**

#### 功能模块

1. **数据库管理 (db)**

   - 调用 `db_manager.py` 的所有功能
   - 统一的参数传递
   - 一致的错误处理
2. **模型下载 (download)**

   - 调用 `download_models.py`
   - 下载OCR模型

#### 优势

- ✅ 统一的命令行接口
- ✅ 一致的错误处理
- ✅ 更好的用户体验
- ✅ 便于维护和扩展
- ✅ 完善的帮助信息

### 2. 数据库管理工具 (db_manager.py)

**完整的数据库管理功能**

**功能：**

- 数据库初始化
- 数据库备份
- 数据迁移
- 数据清理
- 统计信息查看
- 示例数据创建

**使用示例：**

```bash
# 通过manage.py调用（推荐）
python scripts/manage.py db init
python scripts/manage.py db backup
python scripts/manage.py db check
python scripts/manage.py db migrate
python scripts/manage.py db reset

# 或直接调用
python scripts/db_manager.py init
python scripts/db_manager.py backup
python scripts/db_manager.py check
```

**可用命令：**

- `init` - 初始化数据库
- `check` - 检查数据库表
- `migrate` - 执行所有迁移
- `migrate-users` - 修复users表schema
- `migrate-academic` - 创建academic_scores表
- `migrate-config` - 创建综测配置表
- `backup` - 备份数据库
- `reset` - 重置数据库（⚠️ 危险操作，会删除所有数据）
- `sample` - 创建示例数据

### 3. 模型下载工具 (download_models.py)

下载PaddleOCR所需的模型文件。

**功能：**

- 下载检测模型
- 下载识别模型
- 下载分类模型
- 验证模型完整性

**使用：**

```bash
python scripts/manage.py download
# 或
python scripts/download_models.py
```

### 4. 综合测评数据导入脚本 (import_comprehensive_data.py)

将Excel中的综合测评数据导入到数据库中。

**功能：**

- 读取Excel文件
- 验证数据完整性
- 导入学生信息
- 导入学业成绩
- 导入综测成绩
- 生成导入报告

**使用：**

```bash
python scripts/import_comprehensive_data.py
```

### 5. 数据导入验证脚本 (verify_import.py)

验证综合测评数据导入结果的完整性和准确性。

**功能：**

- 读取Excel文件
- 查询数据库中的数据
- 验证数据完整性
- 验证数据准确性
- 生成验证报告

**使用：**

```bash
python scripts/verify_import.py
```

### 6. 项目优化工具 (optimize.py) 

**全面的项目优化和清理工具**

**功能：**

- 清理临时文件（.pyc, .pyo, .log等）
- 删除空目录
- 优化SQLite数据库（VACUUM操作）
- 检查未使用的导入（基础检查）
- 生成详细的优化报告
- 计算项目大小统计

**清理的文件类型：**

- Python缓存文件：`.pyc`, `.pyo`, `.pyd`
- 日志文件：`.log`, `.tmp`
- 系统文件：`.DS_Store`, `Thumbs.db`
- 环境文件：`.env.local`

**跳过的目录：**

- `__pycache__`, `.pytest_cache`
- `node_modules`, `.git`
- `.vscode`, `.idea`
- `temp`, `tmp`

**使用：**

```bash
# 直接运行优化
python scripts/optimize.py

# 查看优化报告
# 报告会显示：
# - 清理的临时文件数量
# - 删除的空目录数量
# - 数据库优化状态
# - 项目总大小
# - 优化建议
```

**输出示例：**

```
=== 项目优化报告 ===
清理临时文件: 25 个
清理空目录: 3 个
数据库优化: 成功
项目大小: 156.78 MB
优化建议:
  - 定期清理临时文件以节省空间
```

**安全特性：**

- ✅ 只清理安全的临时文件
- ✅ 跳过重要的系统目录
- ✅ 详细的操作日志
- ✅ 异常处理和错误恢复

## 🔧 开发说明

### 添加新工具

1. 在 `scripts/` 目录下创建新的Python文件
2. 实现 `main()` 函数作为入口点
3. 在 `manage.py` 中添加对应的命令和调用逻辑
4. 更新此README文档

### 代码规范

- 所有脚本都应该有详细的文档字符串
- 使用logging而不是print进行日志输出
- 提供清晰的错误提示
- 支持命令行参数
- 提供 `--help` 选项
- 脚本应该具有幂等性

## 📖 最佳实践

### 数据库操作

1. **备份优先**：任何数据库操作前先备份
2. **测试环境**：先在测试环境验证
3. **回滚准备**：准备好回滚方案
4. **日志记录**：详细记录所有操作

### 脚本开发

1. **幂等性**：脚本应该可以重复执行
2. **错误处理**：完善的异常处理
3. **参数验证**：验证所有输入参数
4. **文档完整**：提供使用说明

## 🐛 故障排查

### 问题1：脚本执行失败

**检查项：**

- Python版本是否正确 (3.9+)
- 依赖是否安装完整
- 工作目录是否正确
- 权限是否足够

**解决：**

```bash
# 检查Python版本
python --version

# 安装依赖
pip install -r requirements.txt

# 以管理员权限运行
sudo python scripts/manage.py <命令>
```

### 问题2：数据库备份失败

**可能原因：**

- 磁盘空间不足
- 文件权限不足
- 数据库正在被占用

**解决：**

```bash
# 检查磁盘空间
df -h

# 检查文件权限
ls -la data/

# 停止服务后再备份
```

### 问题3：模型下载失败

**可能原因：**

- 网络连接问题
- 下载链接失效
- 磁盘空间不足

**解决：**

```bash
# 使用代理
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port

# 手动下载模型
wget <模型地址>
```

### 问题4：manage.py调用失败

**可能原因：**

- 脚本文件不存在
- Python路径问题
- 权限不足

**解决：**

```bash
# 检查脚本文件
ls -la scripts/

# 检查Python路径
which python

# 使用完整路径
python /path/to/scripts/manage.py <命令>
```

## 📚 相关文档

- [开发指南](../../docs/开发指南.md)
- [数据库设计](../../docs/数据库设计.md)
- [API文档](../../docs/API接口文档.md)
- [证书批量识别和算分功能说明](../../docs/证书批量识别和算分功能说明.md)

## 📞 技术支持

如遇到问题，请提供：

- 错误信息
- 执行的命令
- 系统环境信息
- 日志文件

## 🎯 使用示例

### 示例1：初始化数据库

```bash
# 1. 初始化数据库
python scripts/manage.py db init

# 2. 执行所有迁移
python scripts/manage.py db migrate

# 3. 检查数据库
python scripts/manage.py db check
```

### 示例2：备份数据库

```bash
# 1. 备份数据库
python scripts/manage.py db backup

# 2. 查看备份文件
ls -la data/database_backup_*.db
```

### 示例3：下载模型

```bash
# 下载所有OCR模型
python scripts/manage.py download
```

### 示例4：综合测评数据导入

```bash
# 1. 导入综合测评数据
python scripts/import_comprehensive_data.py

# 2. 验证导入结果
python scripts/verify_import.py
```

### 示例5：项目优化

```bash
# 执行项目优化
python scripts/optimize.py

# 查看优化效果
# 输出示例：
# === 项目优化报告 ===
# 清理临时文件: 15 个
# 清理空目录: 2 个  
# 数据库优化: 成功
# 项目大小: 128.45 MB
# 优化建议:
#   - 定期清理临时文件以节省空间
```

## 📊 命令对照表

| 功能           | 统一命令（推荐）                        | 直接调用                   |
| -------------- | --------------------------------------- | -------------------------- |
| 数据库初始化   | `manage.py db init`                   | `db_manager.py init`     |
| 数据库备份     | `manage.py db backup`                 | `db_manager.py backup`   |
| 数据库检查     | `manage.py db check`                  | `db_manager.py check`    |
| 数据库迁移     | `manage.py db migrate`                | `db_manager.py migrate`  |
| 模型下载       | `manage.py download`                  | `download_models.py`     |
| 综合测评数据导入 | -                                       | `import_comprehensive_data.py` |
| 数据导入验证   | -                                       | `verify_import.py`       |
| 项目优化       | -                                       | `optimize.py`            |

## 🔐 安全注意事项

1. **数据库操作**

   - 生产环境操作前务必备份
   - 危险操作需要确认
   - 不要在生产环境直接执行reset命令
2. **项目优化**
   - 优化前建议备份重要数据
   - 首次使用建议在测试环境验证
   - 注意检查清理的文件列表
   - 数据库优化会锁定数据库

---

**最后更新**: 2025-11-28  
**版本**: 4.0.0 (优化脚本结构，移除冗余功能)  
**维护者**: 项目团队
