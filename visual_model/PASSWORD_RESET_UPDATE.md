# 密码重置功能更新 🔐

## 更新时间
2025-11-08

## 重要变更
密码重置功能已从**基于链接**的方式改为**基于邮箱验证码**的方式。

---

## 快速开始

### 用户使用步骤
1. 访问 `/forgot-password` 页面
2. 输入注册邮箱
3. 点击"发送验证码"
4. 在邮箱中查收6位验证码
5. 输入验证码和新密码
6. 完成密码重置

### 验证码特性
- **验证码长度**: 6位数字
- **有效期**: 2分钟
- **重用机制**: 2分钟内同一邮箱使用相同验证码
- **安全性**: 使用后立即清除

---

## 技术实现

### 数据库变更
新增字段：
- `verification_code` (VARCHAR(10)): 验证码
- `code_expires_at` (TIMESTAMP): 过期时间

### API 接口

#### 1. 发送验证码
```http
POST /auth/password/reset-request
{
  "email": "user@example.com"
}
```

#### 2. 验证并重置
```http
POST /auth/password/reset-confirm
{
  "email": "user@example.com",
  "verification_code": "123456",
  "new_password": "newPassword123"
}
```

---

## 部署说明

### 1. 运行数据库迁移
```bash
cd visual_model
python scripts/migrate_add_verification_code.py
```

### 2. 重启服务
```bash
python main.py
```

### 3. 测试
访问 http://localhost:8000/forgot-password 测试功能

---

## 修改的文件

### 后端
- ✅ `app/models/tortoise_models.py` - 数据库模型
- ✅ `app/models/auth.py` - API 数据模型
- ✅ `app/core/email_service.py` - 邮件服务
- ✅ `app/api/auth.py` - API 接口
- ✅ `scripts/migrate_add_verification_code.py` - 迁移脚本

### 前端
- ✅ `fronted/front/src/views/ForgotPassword.vue` - 密码重置页面

---

## 功能特性

### ✨ 用户体验
- 美观的渐变界面
- 倒计时功能
- 实时表单验证
- 自动跳转登录

### 🔒 安全性
- 验证码2分钟有效
- 使用后立即清除
- 防邮箱枚举
- 密码加密存储

---

## 常见问题

**Q: 收不到验证码邮件？**
A: 检查垃圾邮件文件夹，确认邮件服务已启用

**Q: 验证码过期了？**
A: 点击"重新发送"获取新验证码

**Q: 可以重复使用验证码吗？**
A: 不可以，验证码使用一次后立即失效

---

## API 错误码

| 错误信息 | 说明 |
|---------|------|
| `验证码错误` | 输入的验证码不正确 |
| `验证码已过期，请重新获取` | 验证码超过2分钟 |
| `邮箱不存在` | 该邮箱未注册 |
| `请先获取验证码` | 未发送验证码就尝试重置 |

---

## 监控建议

- 验证码发送成功率
- 验证码验证成功率
- 密码重置成功率
- 平均完成时间

---

## 兼容性说明

- 旧的基于 token 的接口仍然保留
- `/reset-password` 路由保留但不推荐使用
- 推荐使用新的 `/forgot-password` 页面

---

## 技术栈
- **后端**: FastAPI, Tortoise ORM, SQLite
- **前端**: Vue 3, Element Plus
- **邮件**: SMTP

---

**版本**: 2.0.0  
**状态**: ✅ 已完成并测试  
**提交**: 已推送到 GitHub (AI_OCRsys 分支)

