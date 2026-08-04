# Next.js（TypeScript/JavaScript）Web 服务器安全规范（Next.js 16.1.x，Node.js 20.9+）

本文档设计为一份**安全规范**，用于支持：

1. 为新的 Next.js 后端代码（路由处理器 Route Handlers、API 路由 API Routes、服务端操作 Server Actions、代理/中间件 Proxy/Middleware）进行**默认安全的代码生成**。
2. 对现有 Next.js 代码仓库进行**安全审查/漏洞搜寻**（被动式"工作时发现问题"与主动式"扫描仓库并报告发现"）。

本文档特意以一组**规范性要求**（"MUST/SHOULD/MAY"，必须/应当/可以）加**审计规则**（不良模式长什么样、如何检测、如何修复/缓解）的形式编写。

目标范围：Next.js **16.1.x**（App Router 文档中显示的最新版本线）（[Next.js][1]），运行于 Node.js **20.9+**（依据 Next.js 系统要求）。（[Next.js][2]）

---

## 0) 安全、边界与反滥用约束（必须遵守 MUST FOLLOW）

* 不得（MUST NOT）请求、输出、记录或提交密钥（API 密钥、密码、私钥、会话 Cookie、OAuth 令牌、`process.env` 转储、含凭据的数据库 URL）。
* 不得（MUST NOT）通过禁用保护来"修复"安全问题（例如禁用源检查、将 CORS 放宽为 `*`、跳过授权检查、关闭 Cookie 安全标志、因"太麻烦"而关闭 CSP）。
* 审计时必须提供**基于证据的发现**：引用证明每项主张的文件路径、代码片段和配置值。
* 必须（MUST）诚实地对待不确定性：如果某项保护可能存在于基础设施层（反向代理、CDN、WAF、平台响应头），应报告为"在应用代码中不可见；需在运行时/配置中验证"。
* 必须（MUST）假定所有面向请求的服务端代码均可被攻击者触达，除非存在明确执行的认证边界（而不只是"UI 没有链接到它"）。
* 必须（MUST）将 TypeScript 类型视为**非安全边界**：类型不验证运行时输入；必须进行运行时检查。（[Next.js][3]）

---

## 1) 运行模式

### 1.1 生成模式（默认）

当被要求编写新的 Next.js 代码或修改现有代码时：

* 必须（MUST）遵守本规范中的每一项 **MUST** 要求。
* 应当（SHOULD）遵守每一项 **SHOULD** 要求，除非用户明确另有指示。
* 必须（MUST）优先选择默认安全的 API 和成熟的库，而非自定义安全代码。
* 必须（MUST）避免引入新的高风险汇点（sink）（动态代码执行、不安全的重定向、将用户文件作为 HTML 提供、SSRF URL 抓取、拼接 SQL 字符串等）。

### 1.2 被动审查模式（编辑时始终开启）

在 Next.js 代码仓库的任何位置工作时（即使用户未要求安全扫描）：

* 必须（MUST）"注意"被触碰/附近代码中违反本规范之处。
* 应当（SHOULD）在问题出现时提及，附带简要说明与安全修复方案。

### 1.3 主动审计模式（明确请求扫描）

当用户要求"扫描""审计"或"搜寻漏洞"时：

* 必须（MUST）系统地搜索代码库中违反本规范之处。
* 必须（MUST）以结构化格式输出发现（见第 2.3 节）。

推荐的审计顺序：

1. 部署入口与环境（Dockerfile、`package.json` 脚本、托管配置）。
2. Next.js 配置（`next.config.*`）、代理/中间件、路由模式。
3. 认证、会话、Cookie。
4. CSRF 防护与改变状态（state-changing）的端点（服务端操作 Server Actions、路由处理器 Route Handlers、API 路由 API Routes）。
5. XSS（React + CSP）与不安全的 HTML 渲染。
6. 缓存/数据泄露风险（静态渲染 + 缓存 + "use cache"）。
7. 文件处理（上传/下载）与路径遍历。
8. 注入类别（SQL/ORM 误用、命令执行、不安全的反序列化）。
9. 出站请求（SSRF）。
10. 重定向处理（开放重定向）。
11. CORS 与安全响应头。

---

## 2) 定义与审查指引

### 2.1 不受信任的输入（除非证明可信，否则视为攻击者可控）

在 Next.js 后端中，不受信任的输入包括：

App Router：

* 路由处理器参数与请求数据：

  * `context.params`（动态段）、搜索参数（`request.url`、`new URL(request.url).searchParams`）
  * `request.headers`、`request.cookies`
  * `await request.json()`、`await request.formData()`、`await request.text()`
* 服务端组件/服务端函数中使用的动态 API：

  * `headers()` 与 `cookies()` 的值（[Next.js][4]）

Pages Router：

* `pages/api/*` 处理器中的 `req.query`、`req.cookies`、`req.body`（[Next.js][3]）

此外：

* 来自外部系统的任何内容（Webhook、第三方 API、消息队列）
* 源自用户的任何持久化用户内容（数据库行）

### 2.2 改变状态的请求（state-changing request）

如果请求能够创建/更新/删除数据、改变认证/会话状态、触发副作用（购买、发送邮件、发送 Webhook）或发起特权操作，则该请求属于改变状态的请求。

针对 Next.js 的特别说明：

* **服务端操作（Server Actions）** 通过网络请求被调用，且可以改变状态；应将其视为改变状态的端点。（[Next.js][5]）

### 2.3 必需的审计发现格式

对发现的每个问题，输出：

* 规则 ID：
* 严重程度：严重（Critical）/ 高（High）/ 中（Medium）/ 低（Low）
* 位置：文件路径 + 函数/路由名称 + 行号
* 证据：精确的代码/配置片段
* 影响：可能出什么问题、谁可以利用
* 修复：安全的变更（优先最小差异）
* 缓解：如果立即修复困难时的纵深防御
* 误报说明：不确定时需要验证什么

---

## 3) 安全基线：最低生产配置（生产环境必须遵守）

这是防止常见 Next.js 后端错误配置的最小"生产基线"。

### 3.1 以生产模式运行 Next.js（必须）

* 必须（MUST）运行 `next build` + `next start`（或托管平台的等效方式），而不是 `next dev`。开发模式具有不同的错误/报告行为，并非为生产环境暴露而设计。（[Next.js][6]）
* 必须（MUST）确保生产环境中 `NODE_ENV=production`（Next.js 根据命令默认设置 `NODE_ENV`；验证运行时环境）。（[Next.js][7]）

### 3.2 自托管时在前端放置反向代理/边缘层（面向公网必须）

* 如果自托管，必须（MUST）在 Next.js 服务器前放置反向代理（如 nginx）或等效的边缘层，以处理格式错误的请求、慢速攻击、载荷大小限制、速率限制等类似问题。（[Next.js][8]）

### 3.3 基线响应头/Cookie 姿态（应当）

* 应当（SHOULD）在全局设置一组基线安全响应头（CSP、`X-Content-Type-Options`、通过 CSP `frame-ancestors` 和/或 `X-Frame-Options` 进行的点击劫持防御等）。Next.js 提供了通过代理/响应头实施 CSP 的指引。（[Next.js][7]）
* 必须（MUST）确保认证/会话 Cookie 按适用情况使用安全属性（`Secure`、`HttpOnly`、`SameSite`）。（[Next.js][9]）
重要说明：仅在**生产环境**中设置 `Secure`。在通过 HTTP 运行的本地开发环境中，不要在 Cookie 上设置 `Secure` 属性。应根据应用是否处于生产模式进行条件设置。还应包含类似 `SESSION_COOKIE_SECURE` 的属性，用于在通过 HTTP 测试时禁用 `Secure` Cookie。

### 3.4 服务端专用代码与客户端代码的清晰分离（必须）

* 必须（MUST）防止密钥与特权逻辑被打包进客户端代码。
* 必须（MUST）将 `NEXT_PUBLIC_*` 环境变量视为公开（浏览器可见且在构建时内联）。（[Next.js][7]）

---

## 4) 规则（生成 + 审计）

每条规则包含：必需做法、不安全模式、检测提示与修复方法。

### NEXT-DEPLOY-001：不得在生产环境运行 `next dev`；确保生产模式行为

严重程度：高（如处于生产环境）

说明：如果部署到特定的 Next.js 托管提供商，则无需担心此项。

必需：

* 必须（MUST NOT）将 `next dev` 或任何开发服务器模式部署到生产环境。
* 必须（MUST）确保任何公开部署均使用生产构建与生产运行时。（[Next.js][6]）

不安全模式：

* Docker `CMD`、Procfile、平台启动命令中的 `next dev`。
* 生产环境配置中的 `NODE_ENV=development`。
* 公开暴露的仅限调试/开发的端点或标志。

检测提示：

* 搜索 `package.json` 脚本和部署清单中的 `next dev`。
* 搜索基础设施中的 `NODE_ENV=development` 或缺失的 `NODE_ENV`。
* 检查 Kubernetes/PM2/systemd 入口中的 `next dev`。

修复：

* 在 CI/构建时使用 `next build`，运行时使用 `next start`（或平台原生的构建/运行方式）。
* 确保环境设置 `NODE_ENV=production`。

说明：

* 开发模式适合本地开发。仅当其被用作生产入口时才标记。

---

### NEXT-SUPPLY-001：保持在受支持的 Next.js 版本线上；及时修补安全公告

严重程度：高（已知漏洞版本为严重）

必需：

* 必须（MUST）运行受支持的 Next.js 版本线并及时应用安全更新。Next.js 有文档化的 LTS/支持政策。（[Next.js][10]）
* 必须（MUST）将已发布的安全公告视为紧急升级信号（例如升级到已修补的版本）。（[GitHub][11]）

不安全模式：

* 运行已停止维护（EOL）的 Next.js 主/次版本而无回溯的安全修复。
* 忽略安全公告，或将 `next` 锁定在易受攻击的版本范围。

检测提示：

* 检查 `package.json` 和锁文件中 `next` 的版本。
* 与 Next.js 支持政策和安全公告进行比对。

重要说明：任何旧于以下次版本的版本都易受 "react2shell" 漏洞影响（https://nextjs.org/blog/CVE-2025-66478）：
15.0.5
15.1.9
15.2.6
15.3.6
15.4.8
15.5.7
16.0.7

修复：

* 将 `next` 升级到受支持且已修补的版本。
* 增加依赖更新流程 + CI 检查。

---

### NEXT-SECRETS-001：密钥不得被提交或暴露给浏览器

严重程度：高（密钥暴露给客户端时为严重）

必需：

* 必须（MUST）将密钥存储于环境变量或密钥管理器中；必须（MUST NOT）提交 `.env*` 文件。
* 必须（MUST）将 `.env*` 视为敏感文件；Next.js 会警告"几乎不希望提交这些文件"。（[Next.js][7]）
* 必须（MUST）将任何 `NEXT_PUBLIC_*` 环境变量视为公开且浏览器可见（构建时内联进客户端包）。（[Next.js][7]）

不安全模式：

* 将 `.env`、`.env.local`、`.env.production` 提交到 git。
* `NEXT_PUBLIC_API_KEY`、`NEXT_PUBLIC_SECRET`、`NEXT_PUBLIC_DATABASE_URL` 等。
* 将 `process.env` 的值渲染进 HTML 或从 API 路由返回。

检测提示：

* 扫描 git 历史与仓库文件中的 `.env` 内容、`DB_PASS=`、`API_KEY=`、`SECRET=`。
* 搜索 `NEXT_PUBLIC_` 并审查任何看起来敏感的名称。
* 搜索客户端组件（`"use client"`）和共享模块中对 `process.env` 的使用。

修复：

* 将密钥移至仅服务端的环境变量（无 `NEXT_PUBLIC_` 前缀）。
* 确保 `.env*` 被忽略，密钥在部署时注入。
* 轮换已泄露的密钥。

---

### NEXT-SECRETS-002：避免服务端专用代码被打包进客户端的错误（服务端/客户端边界是安全边界）

严重程度：高

必需：

* 必须（MUST）确保仅服务端的模块（数据库客户端、依赖密钥的代码）不被导入客户端组件或其他客户端打包的代码路径。
* 应当（SHOULD）使用仅服务端的模式/层（例如专用 DAL 和仅服务端模块），并将边界违规视为安全漏洞。Next.js 明确讨论了敏感模块的"server-only"（仅服务端）概念。（[Next.js][6]）

不安全模式：

* 将数据库客户端、管理 SDK 或读取密钥的模块导入 `"use client"` 组件。
* 服务端与客户端代码共同导入的共享 `lib/` 模块引用了密钥。

检测提示：

* 搜索 `"use client"` 并检查其导入是否包含仅服务端的依赖。
* 查找从 `components/` 或其他客户端路径导入的数据库客户端包（`pg`、`mysql2`、`mongoose`、`prisma`、管理 SDK）。
* 搜索 UI 组件中对 `process.env` 的访问。

修复：

* 重构为 `lib/server/*`，且仅从服务端上下文（路由处理器、服务端组件、服务端操作）导入。
* 增加显式的"server-only"（仅服务端）防护模式（和/或测试），防止意外导入。

---

### NEXT-AUTH-001：每个受保护操作的认证/授权必须在服务端强制执行

严重程度：高

必需：

* 必须（MUST）在以下场景的服务端代码中强制执行认证/授权：

  * 路由处理器（`app/**/route.ts`）（[Next.js][1]）
  * API 路由（`pages/api/**`）（[Next.js][3]）
  * 服务端操作（由客户端调用的 `"use server"` 函数）（[Next.js][6]）
* 必须（MUST NOT）仅依赖客户端检查（隐藏 UI、客户端路由守卫）作为唯一保护。

不安全模式：

* 敏感路由处理器无会话验证。
* 服务端操作改变数据但不验证用户身份/权限。
* 仅在 React 组件中进行"授权"检查。

检测提示：

* 枚举所有路由处理器和 API 路由；对每个路由判断其是否需要认证。
* 搜索 `"use server"` 并审查所有导出的操作是否有认证检查。
* 搜索由查询参数/表单提交触发的管理操作。

修复：

* 集中认证辅助函数，并在每个受保护的端点/操作中调用。
* 为每个操作实施最小权限授权检查（角色/资源所有权）。

---

### NEXT-AUTH-002：基于代理/中间件的认证不得造成路由覆盖缺口

严重程度：高

必需：

* 如果使用 **Proxy**（代理）或 **Middleware**（中间件）进行认证检查，必须（MUST）确保其覆盖每个需要保护的路由。
* Next.js 文档指出，Proxy 可以使用 `matcher`，并且对于认证，建议 Proxy 在所有路由上运行。（[Next.js][12]）
* 必须（MUST）将 `matcher` 错误视为认证绕过风险。

不安全模式：

* 代理/中间件只匹配"页面"而不匹配 `/api/*`，或只匹配某些路由组。
* "黑名单"式匹配器遗漏了替代请求形式（框架内部变体、RSC 导航等）。

检测提示：

* 检查 `proxy.ts` / `middleware.ts` 及其 `matcher`。
* 将匹配器与完整路由集（包括 `app/api/**` 和 `pages/api/**`）进行比较。
* 确保静态资源和 Next.js 内部资源仅在有意的情况下被排除，且敏感路由已被包含。

修复：

* 优先对受保护路由前缀采用白名单，或全局运行代理并做内部允许/拒绝逻辑。
* 添加集成测试：在无认证的情况下请求受保护路由并断言被拒绝。

说明：

* 代理常用于"乐观检查"；其本身并非完整的授权系统。（[Next.js][12]）

---

### NEXT-CSRF-001：以 Cookie 认证的改变状态端点必须受 CSRF 保护

严重程度：高

- 重要说明：如果认证不使用 Cookie（即通过 Authorization 请求头或其他传递的令牌认证），则不存在 CSRF 风险。

必需：

* 必须（MUST）保护每个依赖 Cookie 进行认证的改变状态端点（POST/PUT/PATCH/DELETE）。
* 对于**服务端操作（Server Actions）**，Next.js 执行 Origin/Host 比较以帮助防止 CSRF；不要禁用或削弱它。（[Next.js][5]）
* 如果服务端操作必须可从额外受信任的来源调用（例如受信任的代理域名），必须（MUST）使用严格白名单的 `allowedOrigins`。（[Next.js][5]）
* 对于**路由处理器**和 **API 路由**，必须（MUST）显式实施 CSRF 保护（令牌和/或严格的 Origin/Referer + SameSite + 自定义请求头）。路由处理器是一个"逃生舱口"，需要应用层面的安全决策。（[Next.js][6]）

不安全模式：

* 改变状态且接受跨站请求的 POST 端点（包括服务端操作），无令牌/来源检查。
* `allowedOrigins: ['*']`（或宽泛通配符）或"回显 Origin"逻辑。
* 使用 GET 请求改变状态。

检测提示：

* 枚举所有改变状态的端点并确定认证机制。
* 搜索 `allowedOrigins` 并确认列表小而具体且有正当理由。（[Next.js][5]）
* 在路由处理器/API 路由中：查找缺失的 CSRF 令牌验证或缺失的 Origin/Referer 检查。

修复：

* 为 Cookie 认证端点实施 CSRF 令牌策略。
* 在兼容时保持 Cookie 为 `SameSite=Lax` 或 `Strict`；不要把 SameSite 单独视为充分。
* 对 JSON API 端点使用严格的 Origin 验证，尤其是不使用 CSRF 令牌时。

说明：

* XSS 可以击破 CSRF 防护；CSRF 防御不能替代 XSS 防护。

---

### NEXT-SESS-001：生产环境中会话 Cookie 必须使用安全属性

严重程度：中

必需（生产环境，HTTPS）：

* 必须（MUST）使用以下属性设置会话/认证 Cookie：

  * `Secure: true`（仅 HTTPS）重要说明：仅在**生产环境**中设置 `Secure`。在通过 HTTP 运行的本地开发环境中，不要在 Cookie 上设置 `Secure` 属性。应根据应用是否处于生产模式进行条件设置。还应包含类似 `SESSION_COOKIE_SECURE` 的属性，用于在通过 HTTP 测试时禁用 `Secure` Cookie。
  * `HttpOnly: true`（JS 不可读取）
  * `SameSite: 'Lax'`（推荐）或兼容时的 `'Strict'`
* 仅当确实需要跨站 Cookie 时才使用 `SameSite: 'none'`，且此时必须（MUST）同时设置 `Secure`。Next.js Cookie API 支持这些 Cookie 选项。（[Next.js][9]）

不安全模式：

* 生产环境中 `secure: false`。
* 认证 Cookie 的 `httpOnly: false`。
* 无明确需要时使用 `sameSite: 'none'`，尤其是对以 Cookie 认证的改变状态端点。

检测提示：

* 搜索设置 Cookie 的位置（`cookies().set(...)`、`Set-Cookie` 响应头、认证库的 Cookie 配置）。
* 审查路由处理器和服务端操作中使用的 Cookie 选项。（[Next.js][9]）

修复：

* 在认证/会话层设置安全的 Cookie 属性。
* 缩小 Cookie 作用域：除非明确需要子域级 Cookie，否则避免宽泛的 `domain`。

---

### NEXT-SESS-002：会话必须有界并抵御固定/重放攻击

严重程度：低

必需：

* 应当（SHOULD）设置与应用相称的有界会话生命周期。
* 应当（SHOULD）在登录和权限变更时轮换会话标识符。
* 必须（MUST NOT）将敏感密钥直接存储在客户端可读取的存储中（包括未加密的 Cookie）。

不安全模式：

* 长期存在的管理会话无轮换。
* 特权角色的"永远记住我"而无额外风险控制。
* 将访问令牌/刷新令牌存储在非 HttpOnly Cookie 或 localStorage 中。

检测提示：

* 审查认证库配置中的过期与轮换设置。
* 搜索 `localStorage.setItem('token'...)` 和非 HttpOnly Cookie 的使用。

修复：

* 特权会话使用短生命周期；通过轮换刷新。
* Cookie 中只存储不透明的会话 ID；敏感材料保留在服务端。

---

### NEXT-INPUT-001：运行时输入验证是强制性的（TypeScript 不是验证）

严重程度：高

必需：

* 必须（MUST）在运行时验证和规范化所有攻击者可控的输入（模式、类型检查、边界）。
* Next.js API 路由明确说明 `req.body` 的类型为 `any`，必须在使用前验证。（[Next.js][3]）
* 必须（MUST）验证服务端操作的参数（视为恶意输入）。（[Next.js][6]）

不安全模式：

* 直接信任 `req.body` 的结构。
* 将 `params.id`/`searchParams` 直接传入数据库查询或文件路径。
* 解析 JSON 后不经验证即假定类型。

检测提示：

* 识别接受 JSON/表单输入的端点，并检查是否存在模式验证。
* 搜索路由处理器中 `req.body.` 的使用和 `await request.json()` 的使用；验证是否存在验证逻辑。

修复：

* 添加模式验证（如 zod/yup/valibot），对无效输入以 4xx 拒绝。
* 将 ID 验证为严格类型（UUID/int）并强制长度/字符集约束。

---

### NEXT-HEADERS-001：必须设置基本安全响应头（在应用中或边缘层）

严重程度：低

必需（典型 Web 应用）：

* 应当（SHOULD）设置：

  * CSP（`Content-Security-Policy`）（见 NEXT-CSP-001）
  * `X-Content-Type-Options: nosniff`
  * 点击劫持防御（CSP 中的 `frame-ancestors` 和/或 `X-Frame-Options`）
  * 适当时的 `Referrer-Policy` 与 `Permissions-Policy`
* 必须（MUST）确保 Cookie 使用安全属性设置（见 NEXT-SESS-001）。（[Next.js][9]）

不安全模式：

* 任何位置（应用或边缘层）均无安全响应头。
* 无意中允许 iframe 嵌入。
* 因缺失 `nosniff` 而可能进行 `Content-Type` 嗅探。

检测提示：

* 检查 `proxy.ts` / 中间件中的 `response.headers.set(...)`。（[Next.js][7]）
* 如果在应用代码中不可见，标记为"在边缘层/CDN 验证"。

修复：

* 集中设置响应头（代理/中间件或其他集中机制）。
* 确保各路由之间的响应头一致。

---

### NEXT-CSP-001：使用 CSP 降低 XSS 影响；脚本优先使用 nonce（随机数）

严重程度：中

说明：最重要的是设置 CSP 的 script-src。其他指令不那么重要，为了便于开发通常可以省略。

必需：

* 应当（SHOULD）部署 CSP，理想情况下为脚本使用 nonce。
* 应当（SHOULD）遵循 Next.js 的 CSP 实施指引（包括 nonce 生成与响应头应用）。（[Next.js][7]）
* 必须（MUST NOT）将放宽 CSP 作为"修复"手段（例如 `script-src 'unsafe-inline'`），除非明确接受相应风险。

不安全模式：

* 展示用户生成 HTML/Markdown 的应用缺少 CSP。
* 无严格正当理由即广泛启用内联脚本或 eval 的 CSP。

检测提示：

* 搜索 `Content-Security-Policy` 响应头设置并检查其指令。
* 检查 `next/script` 的使用，以及当 CSP 要求时是否提供了 nonce。

修复：

* 按照 Next.js 指引实施 CSP；使用 nonce 并一致地应用。
* 减少内联脚本；避免 `eval`。

说明：

* CSP 是纵深防御；不能替代正确的输出编码与净化。

---

### NEXT-XSS-001：防止 React/Next 渲染中的反射型/存储型 XSS

严重程度：高

必需：

* 必须（MUST）依赖 React 的默认转义；未经净化不得将不受信任的 HTML 插入 DOM。
* 必须（MUST）将以下内容视为高风险汇点（sink）：

  * `dangerouslySetInnerHTML`
  * 将用户控制的字符串渲染进 `<script>` 标签或事件处理器属性
* 必须（MUST）避免将上传的 HTML 作为活动 HTML 提供（作为附件提供，或净化/转换）。

不安全模式：

* `<div dangerouslySetInnerHTML={{ __html: userContent }} />` 无净化器。
* 配置为允许原始 HTML 且无净化器的 Markdown 渲染器。
* 从路由处理器以 `Content-Type: text/html` 返回用户内容。

检测提示：

* 搜索 `dangerouslySetInnerHTML`、`__html:`。
* 搜索构建 HTML 的模板式字符串拼接。
* 审查任何"渲染 HTML"或"预览"功能。

修复：

* 使用维护良好的净化器净化不受信任的 HTML；优先严格白名单。
* 优先将用户内容作为文本而非 HTML 渲染。
* 添加 CSP 以降低影响。

---

### NEXT-ACTION-001：服务端操作必须像公共端点一样对待

严重程度：高（特权操作为严重）

必需：

* 必须（MUST）应用与路由处理器相同的控制：

  * 认证/授权
  * 输入验证
  * CSRF/来源保护
  * 敏感操作的速率限制
* 必须（MUST NOT）假定服务端操作"不可触达"或"内部使用"。
* 必须（MUST）理解服务端操作的请求保护机制：

  * Next.js 比较 Origin 与 host 以缓解 CSRF；额外来源必须通过 `allowedOrigins` 显式白名单。（[Next.js][5]）

不安全模式：

* 更新数据库状态但无认证检查的 `"use server"` 函数。
* 为"使其工作"而添加过宽的 `allowedOrigins`。

检测提示：

* 搜索 `"use server"` 并清点所有导出的操作。
* 识别任何执行特权写入的操作；确认其检查身份与权限。

修复：

* 用授权辅助函数包装操作（默认拒绝，fail closed）。
* 保持 `allowedOrigins` 最小并经过审计。

---

### NEXT-ACTION-002：不得通过服务端操作的闭包/绑定模式意外泄露密钥

严重程度：中（暴露重要密钥时为高）

必需：

* 必须（MUST）将服务端操作闭包捕获的值视为敏感信息，并进行有意的设计。
* Next.js 指出闭包捕获的值会被加密/签名，但通过 `.bind` 传递的值不会被加密；不要依赖 `.bind` 保护密钥。（[Next.js][6]）
* 如果跨部署为服务端操作使用稳定的加密密钥，必须（MUST）将其作为密钥处理并安全存储（不要提交/记录）。（[Next.js][6]）

不安全模式：

* `myAction.bind(null, process.env.SECRET)` 或绑定不应受客户端影响的敏感令牌/ID。
* 记录包含密钥的操作参数。

检测提示：

* 搜索服务端操作函数上的 `.bind(`。
* 搜索服务端操作附近的 `process.env` 使用。

修复：

* 避免将密钥绑定进操作；在操作内部于服务端获取密钥。
* 保持操作参数最小并经过验证。

---

### NEXT-CACHE-001：防止通过静态渲染和共享缓存造成数据泄露

严重程度：高（跨用户数据泄露时为严重）

必需：

* 必须（MUST）确保返回用户特定或敏感数据的页面/端点不被静态生成或以共享方式缓存。
* 路由处理器默认不缓存，但 GET 处理器可以选择缓存/静态行为；不要对用户特定数据这样做。（[Next.js][1]）
* 必须（MUST）将 `use cache` 及类似缓存机制视为潜在的跨用户缓存，除非明确证明为私有；不要在共享缓存中缓存用户特定的数据库结果。（[Next.js][1]）
* 应当（SHOULD）对敏感响应（认证/会话/用户数据 API）设置显式的 `Cache-Control: no-store` / `private`。

不安全模式：

* 在返回用户特定数据的路由上使用 `export const dynamic = 'force-static'`。（[Next.js][1]）
* 在查询用户特定数据的函数周围使用 `use cache`，而无用户特定的缓存键。（[Next.js][1]）
* 在启用缓存的 GET 端点上返回认证/会话响应。

检测提示：

* 搜索 `dynamic = 'force-static'`、`revalidate`、`use cache`、`cacheLife`、`unstable_cache`。
* 检查所有被缓存/静态化的 GET 路由处理器，确认其仅返回公开数据。
* 确认对 `cookies()`/`headers()`（动态 API）的使用没有被意外移除，从而把路由变成静态。（[Next.js][1]）

修复：

* 将敏感路由标记为动态并设置 `Cache-Control: no-store`。
* 如果确实需要缓存，确保缓存键包含用户身份（并存储于用户私有缓存中）。

---

### NEXT-FILES-001：用户上传必须经过验证、安全存储、安全提供

严重程度：中

必需：

* 必须（MUST）在边缘层和应用逻辑中强制上传大小限制。
* 必须（MUST）使用白名单和内容检查验证文件类型（不仅仅是扩展名）。
* 必须（MUST）将上传存储于 `public/` 目录之外（`public/` 下的任何内容默认作为静态内容提供）。
* 必须（MUST）安全地提供可能活动的格式（`Content-Disposition: attachment`），除非明确有意内联展示。

不安全模式：

* 接受任意文件类型并将其内联回传。
* 使用用户提供的文件名作为存储路径。
* 将上传写入 `public/uploads/` 并直接提供。

检测提示：

* 搜索 `formData()` / multipart 解析、`fs.writeFile`、存储 SDK 的使用。
* 查找 `public/` 下的任何写入路径。
* 查找设置 `Content-Type: text/html` 或内联提供用户文件的"下载"端点。

修复：

* 使用专用对象存储（S3/GCS）或静态根目录之外的安全服务端目录。
* 生成随机服务端文件名；单独存储元数据。

---

### NEXT-PATH-001：防止路径遍历与不安全的文件访问

严重程度：高

必需：

* 必须（MUST NOT）使用用户控制的字符串作为文件系统路径。
* 必须（MUST）验证和规范化标识符；使用白名单和安全的基础目录。
* 必须（MUST）避免基于请求参数读取任意文件。

不安全模式：

* `fs.readFile(request.nextUrl.searchParams.get('path'))`
* `path.join(base, userPath)` 无规范化 + 边界检查

检测提示：

* 搜索路由处理器/API 路由中 `fs.` 的使用。
* 搜索由请求参数输入的 `path.join`/`path.resolve`。

修复：

* 使用映射到服务端存储路径的不透明 ID。
* 强制解析后的路径保持在预期的基础目录内。
* 在创建 URL 时净化并禁止使用 `..`。

---

### NEXT-SSRF-001：使用用户影响 URL 的出站请求必须受到限制

严重程度：中（内网环境中为高）

说明：这主要只适用于部署在云/局域网环境中的应用，或同一台机器上有其他 HTTP 服务的应用。有时该功能不可避免地需要此能力（Webhook）。

必需：

* 必须（MUST）将任何对用户提供 URL 的服务端 `fetch()` 视为高风险。
* 应当（SHOULD）为 URL 抓取功能白名单目标（主机/域名）。
* 应当（SHOULD）阻止：

  * localhost / 私有 IP 段 / link-local
  * 云元数据端点
* 必须（MUST）将协议限制为 `http:` 和 `https:`。
* 应当（SHOULD）设置严格超时并限制重定向。

不安全模式：

* `await fetch(req.query.url)` 或 `await fetch((await request.json()).url)`
* 抓取任意 URL 的"URL 预览"端点。

检测提示：

* 搜索服务端代码中的 `fetch(` 并追踪 URL 来源。
* 查找"webhook 测试器""预览""从 URL 导入"功能。

修复：

* 解析 URL，强制 `http/https`，白名单主机名，重新解析 DNS/IP 以阻止私有网段。
* 设置超时（AbortSignal）并限制重定向。

---

### NEXT-REDIRECT-001：防止开放重定向（包括认证流程）

严重程度：低

必需：

* 必须（MUST）验证源自不受信任输入的跳转目标（如 `next`、`redirect`、`returnTo`）。
* 应当（SHOULD）优先只跳转到同站相对路径。
* 必须（MUST）对照白名单验证任何绝对 URL。
* 必须（MUST）确保 URL 为 `http` 或 `https:` 协议，禁止 `javascript:` 协议。

不安全模式：

* `redirect(searchParams.get('next')!)`
* `NextResponse.redirect(new URL(req.nextUrl.searchParams.get('to')!, req.url))` 无检查

检测提示：

* 搜索 `redirect(`（服务端组件/操作）和 `NextResponse.redirect`。
* 搜索 API 路由中的 `res.redirect(`。（[Next.js][3]）

修复：

* 只允许相对路径（`/path`），拒绝协议相对（`//evil.com`）或绝对 URL。
* 如果无效，回退到安全默认值（首页/仪表盘）。

---

### NEXT-CORS-001：CORS 必须明确且最小权限

严重程度：中（带凭据配置错误时为高）

必需：

* 如果不需要 CORS，必须（MUST）保持其禁用。
* Next.js API 路由默认不设置 CORS 响应头，即默认同源；只在确实需要时才启用 CORS。（[Next.js][3]）
* 如果启用 CORS：

  * 必须（MUST）白名单受信任的来源（不回显任意 Origin）
  * 必须（MUST）谨慎处理带凭据的请求（Cookie）；绝不可将宽泛来源与凭据组合。
  * 应当（SHOULD）限制方法与响应头。

不安全模式：

* `Access-Control-Allow-Origin: *` 搭配 `Access-Control-Allow-Credentials: true`
* 无验证地回显 `Origin`。

检测提示：

* 搜索 `Access-Control-Allow-Origin`、`cors`、"CORS" 中间件/包装器。
* 审查预检 `OPTIONS` 处理器。

修复：

* 实施严格的来源白名单和最小的方法/响应头。
* 确保除非必要且经过审查，Cookie 不跨源暴露。

---

### NEXT-WEBHOOK-001：Webhook 端点必须使用原始请求体验证真实性

严重程度：中

必需：

* 必须（MUST）使用**原始请求体**（而非重新序列化的解析对象）验证 Webhook 签名。
* Next.js 指出禁用请求体解析的用例之一就是验证 Webhook 请求的原始请求体。（[Next.js][3]）

不安全模式：

* 对 `JSON.stringify(req.body)` 验证 Webhook 签名（可能改变格式）。
* 接受无签名验证且无白名单的 Webhook。

检测提示：

* 查找 Webhook 端点（`/api/webhook`、`/app/api/**/webhook`）。
* 检查其是否使用原始请求体验证。

修复：

* 仅对这些 Webhook 路由禁用 Next.js 自动请求体解析，安全地读取原始字节，验证签名，然后解析。

---

### NEXT-INJECT-001：防止 SQL 注入（使用参数化查询 / ORM）

严重程度：高

必需：

* 必须（MUST）使用参数化查询或在底层参数化的 ORM。
* 必须（MUST NOT）通过字符串拼接/模板字符串与不受信任的输入构建 SQL。

不安全模式：

* ``db.query(`SELECT * FROM users WHERE id = ${id}`)``
* `"WHERE name = '" + user + "'"`

检测提示：

* 搜索 `SELECT`、`INSERT`、`UPDATE`、`DELETE` 字符串。
* 追踪不受信任的输入（`params`、`searchParams`、`req.query`、`req.body`、`request.json()`）进入数据库调用。

修复：

* 使用预处理语句 / ORM 查询 API。
* 在查询前验证和强制类型转换。

---

### NEXT-INJECT-002：防止操作系统命令注入与不安全的子进程使用

严重程度：严重至 高

必需：

* 必须（MUST）避免使用攻击者可控的输入执行操作系统命令。
* 如果必须使用子进程：

  * 必须（MUST）以数组形式传递参数（而非单个 shell 字符串）
  * 必须（MUST NOT）对受攻击者影响的字符串使用 `shell: true`
  * 应当（SHOULD）对任何可变组件使用严格白名单

不安全模式：

* `exec("convert " + filename)`
* `spawn("bash", ["-c", userInput])`
* `spawn(userInput, ["foo"])`

检测提示：

* 搜索 `child_process`、`exec`、`spawn`、`shell: true`。

修复：

* 使用库 API 而非 shell 命令。
* 硬编码命令并白名单验证过的参数（在支持的地方使用 `--` 分隔标志）。

---

### NEXT-INJECT-003：避免动态代码执行与不安全的反序列化

严重程度：高至 严重

必需：

* 必须（MUST NOT）对不受信任的字符串使用 `eval`、`new Function`、`vm.runIn*`。
* 必须（MUST）将反序列化复杂格式（YAML、XML、自定义序列化）视为有风险；使用安全解析器和严格模式。

不安全模式：

* `eval(req.body.code)`
* 使用非安全模式解析来自用户输入的 YAML。

检测提示：

* 搜索 `eval(`、`new Function`、`vm.`、非字面量的 `require(`。
* 搜索对不受信任输入使用 `js-yaml`、XML 解析器、自定义序列化器。

修复：

* 移除动态执行；使用安全解释器或严格解析器。
* 验证并约束输入。

---

### NEXT-LOG-001：日志记录不得泄露密钥或敏感响应头

严重程度：中

必需：

* 必须（MUST NOT）记录：

  * `Authorization` 请求头
  * Cookie / 会话令牌
  * 包含凭据的请求体
  * 环境变量或配置转储
* 应当（SHOULD）实施带脱敏的结构化日志。

不安全模式：

* 认证端点中的 `console.log(req.headers)`
* 服务端代码中的 `console.log(process.env)`

检测提示：

* 搜索服务端路由/操作中的 `console.log(`、`logger.info(`、`debug(`。
* 检查是否记录了请求头/Cookie/请求体。

修复：

* 脱敏敏感字段；只记录调试所需内容。
* 对客户端使用安全的错误消息；细节仅保留在服务端。

---

### NEXT-ERROR-001：错误处理不得在生产环境泄露实现细节

严重程度：低

必需：

* 必须（MUST NOT）在生产环境向终端用户暴露堆栈跟踪或内部错误细节。
* 确保生产模式行为（Next.js 生产环境错误处理与开发环境不同）。（[Next.js][6]）

不安全模式：

* 在 JSON 响应中返回 `err.stack`。
* 向未认证用户展示详细异常数据。

检测提示：

* 搜索 `res.status(500).json(err)` 或 `return Response.json(err)`。
* 验证错误响应已净化。

修复：

* 向客户端返回通用错误消息；细节在服务端记录并脱敏。

---

### NEXT-PROXY-001：代理/中间件不得引入响应头走私或不安全的响应头转发

严重程度：中

必需：

* 必须（MUST）在向上游复制/转发请求头时保持谨慎：

  * 除非有受信任的代理链，否则不转发攻击者控制的 `x-forwarded-*` 请求头。
  * 不向无关的出站服务转发 `Authorization`/Cookie。
* Next.js 代理模式经常修改响应头；确保这不会造成安全问题。

不安全模式：

* 盲目地将所有请求头克隆到出站 `fetch()` 调用。
* 未经白名单即信任 `x-forwarded-host` 或 `host` 来构造敏感的绝对 URL。

检测提示：

* 搜索 `headers()` 和 `request.headers` 的使用（尤其是用于 URL 构建时）。（[Next.js][4]）
* 搜索代理/中间件中的响应头重写。

修复：

* 显式白名单转发的响应头。
* 在用于构建回调 URL 或重定向前验证主机名。

---

### NEXT-HOST-001：基于 Host/Origin 构造的 URL 必须经过白名单

严重程度：中

必需：

* 必须（MUST NOT）直接从未经验证的 `Host` 请求头生成安全敏感的绝对 URL（密码重置链接、OAuth 回调 URL、邮件验证链接）。
* 对于服务端操作，Origin/Host 匹配是 CSRF 缓解的一部分；不要削弱它。（[Next.js][5]）

不安全模式：

* `const base = "https://" + request.headers.get("host")`
* 使用未经验证的 `x-forwarded-host` 生成绝对 URL。

检测提示：

* 搜索 `.get('host')`、`.get('x-forwarded-host')` 和绝对 URL 构建。
* 审查与认证相关的邮件链接生成代码。

修复：

* 使用配置的、经过白名单的应用规范源（如 `APP_ORIGIN=https://example.com`）。
* 白名单主机名；默认拒绝（fail closed）。

---

### NEXT-DOS-001：易被滥用的端点必须存在速率限制与资源控制

严重程度：中

必需：

* 应当（SHOULD）对以下内容实施速率限制/节流：

  * 登录、密码重置、注册
  * 昂贵的服务端操作
  * Webhook 接收
* 必须（MUST）实施请求大小限制（见 NEXT-LIMITS-001）。
* 如果自托管，必须（MUST）依赖反向代理提供额外保护。（[Next.js][8]）

不安全模式：

* 登录/重置端点无节流。
* 昂贵的操作无需认证或不受频率限制即可调用。

检测提示：

* 识别认证端点并检查是否存在速率限制。
* 搜索"发送邮件""收费""生成报告"流程。

修复：

* 添加边缘速率限制和应用级用户/IP 节流。
* 为繁重工作添加任务队列；适当时返回 202。

---

## 5) 实用扫描启发式（如何"搜寻"）

主动扫描时，使用这些高信号模式：

* 生产配置错误：

  * `next dev`、`NODE_ENV=development`、仅开发环境的启动命令（[Next.js][7]）
* 密钥暴露：

  * 提交了 `.env`，敏感变量带 `NEXT_PUBLIC_` 前缀（[Next.js][7]）
  * `"use client"` 模块中使用 `process.env`
* 认证覆盖：

  * `app/**/route.ts` 或 `pages/api/**` 无认证检查（[Next.js][1]）
  * 有数据库写入且无授权的 `"use server"` 操作（[Next.js][6]）
  * 排除敏感路由的 `proxy.ts` / `middleware.ts` 匹配器（[Next.js][12]）
* CSRF：

  * Cookie 认证的 POST/PUT/PATCH/DELETE 无令牌/来源检查
  * `serverActions.allowedOrigins` 过宽（[Next.js][5]）
* XSS：

  * `dangerouslySetInnerHTML`、原始 HTML Markdown 渲染
  * 缺失 CSP / 过于宽松的 CSP（[Next.js][7]）
* 缓存/数据泄露：

  * 敏感 GET 处理器上的 `dynamic = 'force-static'`（[Next.js][1]）
  * 用户特定数据周围的 `use cache`、`cacheLife`、`unstable_cache`（[Next.js][1]）
* 文件：

  * 将上传写入 `public/`
  * 带请求输入的 `fs.readFile` / `path.join`
* SSRF：

  * 从路由处理器/服务端操作发起 `fetch(userProvidedUrl)`
* 重定向：

  * `redirect(searchParams.get('next'))`、`NextResponse.redirect(...)`、`res.redirect(req.query.next)`（[Next.js][3]）
* CORS：

  * 通配符来源、来源回显、凭据 + 宽泛来源（[Next.js][3]）
* 限制：

  * `bodyParser: false` 的 API 路由且 Webhook 无原始请求体验证（[Next.js][3]）
  * 无正当理由提高的 `serverActions.bodySizeLimit`（[Next.js][5]）
* 依赖卫生：

  * 与支持政策/安全公告冲突的旧版 `next`（[Next.js][10]）

始终尝试确认：

* 数据来源（不受信任 vs 受信任）
* 汇点类型（HTML/DOM、SQL、子进程、文件、重定向、出站 HTTP）
* 存在的防护控制（模式验证、白名单、中间件/代理检查、授权辅助函数、边缘保护）

---

## 6) 来源（访问于 2026-01-27）

主要框架文档（Next.js）：

* Next.js 文档：安装（系统要求 / Node 版本）—— `https://nextjs.org/docs/app/getting-started/installation`
* Next.js 文档：路由处理器—— `https://nextjs.org/docs/app/getting-started/route-handlers`
* Next.js 文档：API 路由（Pages Router）—— `https://nextjs.org/docs/pages/building-your-application/routing/api-routes`
* Next.js 文档：环境变量—— `https://nextjs.org/docs/pages/guides/environment-variables`
* Next.js 文档：数据安全—— `https://nextjs.org/docs/app/guides/data-security`
* Next.js 文档：内容安全策略—— `https://nextjs.org/docs/app/guides/content-security-policy`
* Next.js 文档：代理—— `https://nextjs.org/docs/app/getting-started/proxy`
* Next.js 文档：`serverActions.allowedOrigins` 与 `serverActions.bodySizeLimit`—— `https://nextjs.org/docs/app/api-reference/config/next-config-js/serverActions`
* Next.js 文档：`cookies()`—— `https://nextjs.org/docs/app/api-reference/functions/cookies`
* Next.js 文档：`headers()`—— `https://nextjs.org/docs/app/api-reference/functions/headers`
* Next.js 文档：自托管（反向代理指引）—— `https://nextjs.org/docs/pages/guides/self-hosting`
* Next.js 文档：支持政策（受支持版本/LTS）—— `https://nextjs.org/docs/support-policy`

Next.js 安全指引与公告：

* Next.js 博客：如何思考 Next.js 中的安全—— `https://nextjs.org/blog/security-nextjs-server-components-actions`
* GitHub 安全公告：Next.js 通过服务端组件/服务端操作导致的拒绝服务（CVE-2026-23864）—— `https://github.com/advisories/GHSA-fq29-rrrv-cq2m`
* Next.js 博客：安全更新（安全公告上下文示例）—— `https://nextjs.org/blog/security-update`

通用 Web 安全参考（推荐基线）：

* OWASP Cheat Sheet Series（CSRF、会话管理、XSS 防护、SSRF 防护、文件上传、HTTP 响应头）—— `https://cheatsheetseries.owasp.org/`

[1]: https://nextjs.org/docs/app/getting-started/route-handlers "Getting Started: Route Handlers | Next.js"
[2]: https://nextjs.org/docs/app/getting-started/deploying?utm_source=chatgpt.com "Getting Started: Deploying"
[3]: https://nextjs.org/docs/pages/building-your-application/routing/api-routes "Routing: API Routes | Next.js"
[4]: https://nextjs.org/docs/app/api-reference/functions/headers "Functions: headers | Next.js"
[5]: https://nextjs.org/docs/app/api-reference/config/next-config-js/serverActions "next.config.js: serverActions | Next.js"
[6]: https://nextjs.org/blog/security-nextjs-server-components-actions "How to Think About Security in Next.js | Next.js"
[7]: https://nextjs.org/docs/pages/guides/environment-variables "Guides: Environment Variables | Next.js"
[8]: https://nextjs.org/docs/pages/guides/self-hosting?utm_source=chatgpt.com "Guides: Self-Hosting"
[9]: https://nextjs.org/docs/app/api-reference/functions/cookies "Functions: cookies | Next.js"
[10]: https://nextjs.org/blog/next-16?utm_source=chatgpt.com "Next.js 16"
[11]: https://github.com/vercel/next.js/security/advisories/GHSA-9g9p-9gw9-jx7f?utm_source=chatgpt.com "Denial of Service in Image Optimizer · Advisory"
[12]: https://nextjs.org/docs/pages/guides/authentication "Guides: Authentication | Next.js"
