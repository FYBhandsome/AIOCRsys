# 开发测试模式增强与系统诊断修复规范

## Why

用户反馈前端应用主页目录无法正常显示，业务逻辑存在缺陷，需要在开发测试阶段提供无认证障碍的测试环境，同时系统性诊断并修复所有问题。

## What Changes

- 添加开发测试模式配置，绕过认证与权限控制
- 优化启动脚本支持开发测试模式
- 系统性诊断主页目录显示异常
- 完善前后端API衔接与业务逻辑
- 开发自动化测试脚本
- 更新README.md使用教程

## Impact

- Affected specs: 认证模块、启动脚本、前端路由、API接口
- Affected code:
  - `start.py` - 启动脚本
  - `visual_model/app/core/auth_middleware.py` - 认证中间件
  - `PaddleOCRRAG/app/core/dependencies.py` - RAG依赖
  - `fronted/front/src/router/index.js` - 前端路由
  - `fronted/front/src/services/api.js` - 前端API
  - `README.md` - 使用文档

## ADDED Requirements

### Requirement: 开发测试模式配置

系统 SHALL 支持开发测试模式，在该模式下绕过所有认证与权限控制。

#### Scenario: 启动开发测试模式
- **WHEN** 用户使用 `python start.py --dev` 启动系统
- **THEN** 所有后端服务应以开发模式运行
- **AND** 所有API接口无需认证即可访问
- **AND** 所有功能模块开放全部操作权限

#### Scenario: 认证绕过日志记录
- **WHEN** 系统处于开发测试模式
- **THEN** 所有绕过认证的操作应记录日志
- **AND** 日志应包含 `[DEV_MODE]` 标记
- **AND** 日志应包含操作追溯信息

#### Scenario: 开发模式环境变量
- **WHEN** 启动开发测试模式
- **THEN** 应设置环境变量 `DEV_MODE=true`
- **AND** 应设置 `DISABLE_AUTH=true`
- **AND** 应在控制台显示醒目的开发模式提示

### Requirement: 主页目录显示修复

系统 SHALL 正确显示主页目录内容。

#### Scenario: 路由配置正确
- **WHEN** 用户访问主页
- **THEN** 主页目录应正确显示所有菜单项
- **AND** 所有菜单项应可点击
- **AND** 菜单项应根据用户角色正确过滤

#### Scenario: 数据加载正常
- **WHEN** 主页组件挂载
- **THEN** 应正确加载用户信息
- **AND** 应正确加载菜单配置
- **AND** 加载失败时应显示错误提示

### Requirement: 前后端API衔接验证

系统 SHALL 确保前后端API正确对接。

#### Scenario: API一致性验证
- **WHEN** 前端发起API请求
- **THEN** 后端应正确响应
- **AND** 数据结构应与前端期望匹配
- **AND** 错误响应应有明确的错误信息

#### Scenario: API测试覆盖
- **WHEN** 执行自动化测试
- **THEN** 所有API接口应被测试覆盖
- **AND** 测试成功率应达到100%

### Requirement: 启动脚本增强

系统 SHALL 提供增强的启动脚本支持开发测试模式。

#### Scenario: 命令行参数支持
- **WHEN** 用户执行 `python start.py --help`
- **THEN** 应显示帮助信息
- **AND** 应列出所有可用参数

#### Scenario: 开发模式启动
- **WHEN** 用户执行 `python start.py --dev`
- **THEN** 应以开发测试模式启动所有服务
- **AND** 应显示开发模式提示信息
- **AND** 应自动创建测试账号（如不存在）

### Requirement: 使用教程更新

系统 SHALL 提供详细的使用教程。

#### Scenario: README更新
- **WHEN** 用户查看README.md
- **THEN** 应包含开发测试模式使用说明
- **AND** 应包含详细的操作步骤
- **AND** 应包含常见问题解答

## MODIFIED Requirements

### Requirement: 认证中间件开发模式支持

原 `visual_model/app/core/auth_middleware.py` SHALL 支持开发模式：

**修改前：**
```python
# 所有请求都需要认证
async def verify_token(request):
    # 验证JWT token
    ...
```

**修改后：**
```python
async def verify_token(request):
    # 开发模式绕过认证
    if os.getenv('DISABLE_AUTH', 'false').lower() == 'true':
        logger.warning("[DEV_MODE] 认证已绕过")
        return DevUser()  # 返回开发用户
    # 正常验证JWT token
    ...
```

### Requirement: 启动脚本参数支持

原 `start.py` SHALL 支持命令行参数：

**修改前：**
```python
def main():
    manager = StartupManager()
    manager.run()
```

**修改后：**
```python
def main():
    parser = argparse.ArgumentParser(description='综测计算助手启动脚本')
    parser.add_argument('--dev', action='store_true', help='开发测试模式（禁用认证）')
    parser.add_argument('--no-frontend', action='store_true', help='不启动前端')
    parser.add_argument('--no-rag', action='store_true', help='不启动RAG服务')
    args = parser.parse_args()
    
    if args.dev:
        os.environ['DEV_MODE'] = 'true'
        os.environ['DISABLE_AUTH'] = 'true'
    
    manager = StartupManager(dev_mode=args.dev)
    manager.run()
```

## REMOVED Requirements

无移除的需求。

## 技术方案

### 1. 开发测试模式实现

#### 后端认证绕过

**Visual Model 后端：**
```python
# visual_model/app/core/auth_middleware.py
import os
from typing import Optional

class DevUser:
    """开发模式用户"""
    id: str = "dev_admin"
    username: str = "dev_admin"
    role: str = "admin"
    name: str = "开发模式用户"

async def get_current_user(request):
    if os.getenv('DISABLE_AUTH', 'false').lower() == 'true':
        logger.warning(f"[DEV_MODE] 认证绕过 - 路径: {request.url.path}")
        return DevUser()
    # 正常认证流程
    ...
```

**RAG 后端：**
```python
# PaddleOCRRAG/app/core/dependencies.py
async def get_current_user(request):
    if os.getenv('DISABLE_AUTH', 'false').lower() == 'true':
        logger.warning(f"[DEV_MODE] RAG认证绕过")
        return {"user_id": "dev_user", "role": "admin"}
    # 正常认证流程
    ...
```

#### 前端认证绕过

```javascript
// fronted/front/src/router/index.js
const DISABLE_AUTH = import.meta.env.DEV && 
  import.meta.env.VITE_DISABLE_AUTH === 'true'

router.beforeEach((to, from, next) => {
  if (DISABLE_AUTH) {
    // 自动设置开发用户
    if (!userStore.checkAuth()) {
      userStore.login({
        id: 'dev_admin',
        username: 'dev_admin',
        role: 'admin'
      }, 'dev-token')
    }
    next()
    return
  }
  // 正常认证流程
  ...
})
```

### 2. 启动脚本增强

```python
# start.py 增强版
class StartupManager:
    def __init__(self, dev_mode=False):
        self.dev_mode = dev_mode
        if dev_mode:
            self._setup_dev_environment()
    
    def _setup_dev_environment(self):
        """配置开发环境"""
        os.environ['DEV_MODE'] = 'true'
        os.environ['DISABLE_AUTH'] = 'true'
        print("\n" + "="*60)
        print("⚠️  开发测试模式已启用")
        print("   - 所有认证已禁用")
        print("   - 所有权限已开放")
        print("   - 仅用于开发测试，请勿用于生产环境")
        print("="*60 + "\n")
```

### 3. 自动化测试脚本

```javascript
// tests/api_full_test.js
const API_BASE_URL = 'http://localhost:8001/api/v1'
const RAG_BASE_URL = 'http://localhost:8010'

async function runAllTests() {
  const results = {
    total: 0,
    passed: 0,
    failed: 0,
    errors: []
  }
  
  // 测试所有API端点
  await testHealthEndpoints(results)
  await testAuthEndpoints(results)
  await testStudentEndpoints(results)
  await testTeacherEndpoints(results)
  await testAdminEndpoints(results)
  await testFileEndpoints(results)
  await testRAGEndpoints(results)
  
  return results
}
```

## 验收标准

1. ✅ 执行 `python start.py --dev` 可启动开发测试模式
2. ✅ 开发模式下所有API无需认证即可访问
3. ✅ 主页目录正确显示所有菜单项
4. ✅ 所有自动化测试通过
5. ✅ README.md包含详细使用教程
