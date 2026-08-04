# Legalizes 🇨🇱

**智利人工智能法律助手**

Legalizes 是一个全栈 SaaS 平台，使律师、法学学生、企业和自然人能够查询智利法规、获得有理有据的法律咨询并生成专业法律文件。

## 🏛️ 规范基础

- **CC** —— 《民法典》
- **CPC** —— 《民事诉讼法典》
- **CPP** —— 《刑事诉讼法典》
- **CT** —— 《税法典》
- **第 21.719 号法律** —— 《个人数据保护法》

## 🚀 功能特性

### AI 法律助手
- 自然语言咨询
- 附规范引用的有据回答
- 对话上下文
- 专注于智利法律

### 规范检索器
- 37 部以上智利现行法规
- 按法典、类别和内容检索
- 条文详细查看
- 高级筛选

### 文件生成器
- 经验证的专业模板
- 起诉状（抚养费、解雇）
- 合同（租赁、服务提供）
- 通知函
- 简单授权书

### 仪表盘
- 使用指标
- 活动历史
- 积分管理
- 用户资料

## 🛠️ 技术栈

### 前端
- React 18 + TypeScript
- Tailwind CSS
- React Router DOM
- TanStack Query
- Zustand（全局状态）
- Framer Motion
- Recharts

### 后端
- Node.js + Express + TypeScript
- Supabase (PostgreSQL)
- JWT 认证
- bcryptjs

## 📁 项目结构

```
legalizes/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout.tsx
│   │   │   ├── AuthModal.tsx
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── LawSearch.tsx
│   │   │   └── DocumentGenerator.tsx
│   │   ├── pages/
│   │   │   ├── Home.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Chat.tsx
│   │   │   ├── Laws.tsx
│   │   │   ├── Documents.tsx
│   │   │   └── Profile.tsx
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── useChat.ts
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── utils.ts
│   │   └── styles/
│   │       └── globals.css
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── backend/
│   ├── src/
│   │   ├── routes/
│   │   │   ├── auth.ts
│   │   │   ├── chat.ts
│   │   │   ├── laws.ts
│   │   │   ├── documents.ts
│   │   │   └── users.ts
│   │   ├── middleware/
│   │   │   └── auth.ts
│   │   ├── utils/
│   │   │   └── chileanLaws.ts
│   │   └── index.ts
│   ├── package.json
│   └── tsconfig.json
└── shared/
    └── types/
        └── index.ts
```

## 🚀 安装与使用

### 要求
- Node.js 18+
- npm 或 yarn
- Supabase 账户

### 1. 克隆并配置

```bash
git clone <repo-url>
cd legalizes
```

### 2. 后端

```bash
cd backend
npm install
```

创建 `.env` 文件：
```env
PORT=3001
JWT_SECRET=tu-secret-key-super-seguro
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_KEY=tu-service-key
FRONTEND_URL=http://localhost:5173
```

```bash
npm run dev
```

### 3. 前端

```bash
cd frontend
npm install
```

创建 `.env` 文件：
```env
VITE_API_URL=http://localhost:3001/api
```

```bash
npm run dev
```

### 4. 数据库（Supabase）

在 Supabase 的 SQL Editor 中执行以下 SQL：

```sql
-- 用户表
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  nombre TEXT,
  apellido TEXT,
  rut TEXT,
  empresa TEXT,
  tipo_usuario TEXT DEFAULT 'abogado',
  plan TEXT DEFAULT 'free',
  creditos INTEGER DEFAULT 100,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 对话表
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  title TEXT,
  messages JSONB DEFAULT '[]',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 文档表
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  template_id TEXT,
  title TEXT,
  content TEXT,
  variables JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 扣减积分的函数
CREATE OR REPLACE FUNCTION decrement_credits(user_id UUID, amount INTEGER)
RETURNS VOID AS $$
BEGIN
  UPDATE users 
  SET creditos = GREATEST(0, creditos - amount)
  WHERE id = user_id;
END;
$$ LANGUAGE plpgsql;
```

## 📝 许可

MIT License - VibeCodingChile.cl

## 📞 联系方式

- 电子邮件：contacto@vibecodingchile.cl
- 电话：+56 9 2964 8142
- 网站：[vibecodingchile.cl](https://vibecodingchile.cl)

---

**免责声明：** Legalizes 是一种法律辅助工具。AI 生成的回答在用于正式法律程序前，必须由持照律师核验。
