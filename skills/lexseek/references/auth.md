# 登录与认证

本 Skill 需要用户登录后才能使用法律检索功能。

## 登录流程

首次使用时需要登录，模型应该自动完成登录流程。

### 自动登录流程

1. **检查登录状态** - 检查是否已有有效的 API Key
2. **询问登录凭证** - 如果未登录，向用户询问手机号和密码，**同时告知用户注册链接**
3. **调用登录脚本** - 使用用户提供的凭证调用登录脚本
4. **继续执行** - 登录成功后继续处理用户请求

### 登录凭证

- 登录需要用户的**手机号**和**密码**
- 登录脚本路径：`scripts/lexseek.js`（相对于 Skill 根目录）
- **如果没有账号，请先注册**: https://lexseek.cn

### 登录脚本用法

模型需要将手机号和密码作为参数传递给登录脚本：

```bash
cd lexseek
node scripts/lexseek.js login --phone "手机号" --password "密码"
```

### 登出

如需清除登录凭证：

```bash
cd lexseek
node scripts/lexseek.js logout
```

## API 认证

本 Skill 通过调用外部法律 API 获取数据。API 配置通过环境变量管理：

- `LEXSEEK_API_URL` - API 服务地址（默认：https://api.lexseek.cn）
- `LEXSEEK_API_KEY` - API 认证密钥（登录后自动存储到 `.env`）

### 认证方式

法条搜索 API 需要在请求头中携带 API Key：

**Header**: `apikey: <用户的 API Key>`

### 检查登录状态

API 客户端会在每次请求时自动检查登录状态。如未登录，会抛出错误：

```
Error: 未登录，请先运行 node scripts/lexseek.js login 登录
```

## 本地存储

登录成功后，API Key 会保存到 Skill 目录下的 `.env` 文件中：

```
LEXSEEK_API_URL=https://api.lexseek.cn
LEXSEEK_API_KEY=your-api-key-here
```
