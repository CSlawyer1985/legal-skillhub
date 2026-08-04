# FastAPI（Python）Web 安全规范（FastAPI 0.128.x、Python 3.x）（[PyPI][1]）

本文档定位为一份**安全规范**，用于支持：

1. 为新 FastAPI 代码提供**默认安全**的代码生成。
2. 对现有 FastAPI 代码进行**安全审查／漏洞排查**（被动式“工作中发现即提示”和主动式“扫描代码库并报告发现”）。

本文刻意以一组**规范性要求**（“MUST／SHOULD／MAY”）加**审计规则**（不良模式长什么样、如何检测、如何修复／缓解）的形式写成。

FastAPI 通常搭配 ASGI 服务器（如 Uvicorn）部署，并构建在 Starlette 和 Pydantic 之上，因此本规范在涉及安全影响时覆盖这些层面。（[PyPI][1]）

---

## 0）安全、边界与反滥用约束（必须遵守）

- 不得请求、输出、记录或提交机密信息（API 密钥、密码、私钥、会话 Cookie、签名密钥、含凭据的数据库 URL）。
- 不得通过禁用保护来“修复”安全问题（例如削弱认证、放宽 CORS、跳过签名校验、关闭验证、关闭 TLS 校验、在带凭据的情况下添加 `allow_origins=["*"]`）。
- 审计时必须提供**基于证据的发现**：引用能够佐证结论的文件路径、代码片段和配置值。
- 必须诚实地处理不确定性：如果某项保护可能存在于基础设施层（反向代理、WAF、CDN、服务网格），应报告为“应用代码中不可见；需在运行时／配置中验证”。
- 必须正确认识浏览器控制机制：

  - CORS **不是**认证机制，它只影响浏览器。
  - CSRF 防御适用于浏览器自动附带凭据（Cookie）的场景；对于纯 header 令牌型 API，通常不适用。（[OWASP Cheat Sheet Series][2]）

---

## 1）运行模式

### 1.1 生成模式（默认）

当被要求编写新的 FastAPI 代码或修改现有代码时：

- 必须遵守本规范中的每一项**MUST**要求。
- 应当遵守每一项**SHOULD**要求，除非用户明确另有要求。
- 必须优先选用默认安全的 API 和经过验证的库，而不是自行编写安全代码。
- 必须避免引入新的高风险汇点（shell 执行、不安全的反序列化、动态 eval、不可信模板渲染、不安全的文件服务、不安全的跳转、任意外发请求）。

### 1.2 被动审查模式（编辑期间始终开启）

在 FastAPI 代码库中任何位置工作时（即使用户没有要求安全扫描）：

- 必须“留意”所触及或附近代码中对本规范的违反。
- 应当及时指出问题，附简要说明和安全修复建议。

### 1.3 主动审计模式（明确要求扫描）

当用户要求“扫描”“审计”或“排查漏洞”时：

- 必须系统性地搜索代码库中违反本规范之处。
- 必须以结构化格式输出发现（见 §2.3）。

建议的审计顺序：

1. 应用入口点／部署脚本／Dockerfile／Procfile／Helm／Terraform。
2. ASGI 服务器配置（Uvicorn／Gunicorn）、代理设置、debug／reload 设置。
3. FastAPI 应用配置（文档暴露、中间件、可信主机、CORS）。
4. 认证／授权设计（依赖项、JWT／会话处理、密码存储）。
5. Cookie／会话使用及 CSRF（如使用 Cookie）。
6. 输入验证与输出塑形（Pydantic 模型、批量赋值、过度数据暴露）。
7. 模板渲染与 XSS／SSTI（如提供 HTML）。
8. 文件处理（上传和下载）、StaticFiles、Range 支持。
9. 注入类（SQL、命令执行、不安全反序列化）。
10. 出站请求（SSRF）、跳转处理、WebSocket 安全。

---

## 2）定义与审查指引

### 2.1 不可信输入（除非证明可信，否则视为攻击者可控）

示例包括：

- 查询参数／路径参数
- JSON 请求体（包括嵌套字段）
- 请求头（包括 `Host`、`Origin`、`X-Forwarded-*`）
- Cookie（包括会话 Cookie）
- 文件上传（multipart 部分）
- WebSocket 握手期间的 WebSocket 消息、查询参数和请求头（[Starlette][3]）
- 来自外部系统的任何数据（webhook、第三方 API、消息队列）
- 任何源自用户的持久化用户内容（数据库行）

### 2.2 状态变更请求

如果请求能够创建／更新／删除数据、改变认证／会话状态、触发副作用（购买、发送邮件、发送 webhook）或发起特权操作，则该请求属于状态变更请求。

### 2.3 审计发现的规定输出格式

对发现的每个问题，输出：

- 规则 ID：
- 严重级别：严重／高／中／低
- 位置：文件路径＋函数／路由名称＋行号
- 证据：确切的代码／配置片段
- 影响：可能出什么问题、谁能利用
- 修复：安全的变更（优先最小 diff）
- 缓解：若无法立即修复时的纵深防御
- 误报说明：不确定时应核验什么

---

## 3）安全基线：最低生产配置（生产环境必须满足）

这是防止常见 FastAPI／ASGI 配置错误的最简“生产基线”。

基线目标：

- 生产环境无 debug 回溯信息或自动重载。（[PyPI][4]）
- 在生产的 ASGI 服务器配置下运行（worker、超时、资源控制）。（[PyPI][4]）
- 启用 Host 请求头校验（TrustedHostMiddleware 或等效方案）。（[PyPI][5]）
- 除非明确需要，否则禁用 CORS；如启用，须严格且最小权限。（[OWASP Cheat Sheet Series][6]）
- 通过依赖项一致地强制执行认证（避免“哎呀，这条路由忘了加认证”）。（[FastAPI][7]）
- 如使用 Cookie／会话，Cookie 标志须安全且 CSRF 已妥善处理。（[OWASP Cheat Sheet Series][8]）
- 在边缘层存在请求大小限制和 multipart 限制，并在应用中按需验证（以缓解内存／CPU 型 DoS）。（[advisories.gitlab.com][9]）
- 及时修补依赖，尤其是 Starlette／python-multipart（历史上存在多个 DoS 和路径穿越通告）。（[advisories.gitlab.com][10]）

---

## 4）规则（生成＋审计）

每条规则包含：要求做法、不安全模式、检测提示、补救措施。

### FASTAPI-DEPLOY-001：生产环境不得使用自动重载／仅开发用服务器模式

严重级别：高（若用于生产）

要求：

- 生产环境不得以自动重载／监听模式运行（例如 Uvicorn reload）。
- 生产环境必须以生产进程模型（例如适当配置多个 worker）和稳定的服务器设置运行。（[PyPI][4]）

不安全模式：

- 生产入口点使用 `uvicorn ... --reload`（或等效的 `reload=True` 配置）。
- Docker／Procfile／systemd 命令在生产中以 `--reload` 运行。

检测提示：

- 搜索 `--reload`、`reload=True`、`watchfiles`、`fastapi dev`、“development”运行脚本。
- 检查 Docker CMD／ENTRYPOINT、Procfile、systemd 单元、shell 脚本。

修复：

- 生产环境移除 reload；以稳定设置和明确的 worker 配置运行 Uvicorn／Gunicorn。（[PyPI][4]）

注意：

- 本地开发使用 reload 没有问题。仅在明确用作生产入口点时标记。

---

### FASTAPI-DEPLOY-002：生产环境必须禁用 Debug 模式

严重级别：严重

要求：

- 生产环境不得启用 debug 回溯信息（FastAPI／Starlette 的 debug 模式可能暴露敏感内部信息并使某些利用链更容易）。（[PyPI][5]）
- 任何向客户端返回详细堆栈跟踪的配置都必须视为敏感。

不安全模式：

- `app = FastAPI(debug=True)`（或 Starlette 的 `debug=True`），或等效的环境开关在生产中启用 debug。（[PyPI][5]）
- 向最终用户暴露回溯信息的服务器／日志配置。

检测提示：

- 搜索 `debug=True`、`DEBUG = True`、映射到 debug 的环境标志。
- 审查异常中间件和错误处理器设置。

修复：

- 确保 debug 仅在本地开发／测试中启用。
- 向客户端返回通用错误响应；内部记录详细信息。

---

### FASTAPI-OPENAPI-001：生产环境的 OpenAPI 与交互式文档必须禁用或加以保护

严重级别：中（在敏感／内部应用中可为高）

要求：

- 面向公众的服务在生产环境应当禁用 `/docs`、`/redoc` 和 `/openapi.json`，除非有明确的业务需求。
- 如保留启用，必须加以保护（例如认证、网络白名单或仅限内部路由）。
- 不得假设“隐蔽即安全”；应把文档暴露视为信息泄露放大器。

不安全模式：

- 内部／管理 API 的 `/docs` 和 `/openapi.json` 可公开访问。
- 文档与生产环境使用同一主机名且无访问控制。

检测提示：

- 查找 `FastAPI(docs_url=..., redoc_url=..., openapi_url=...)` 或默认值。
- 检查反向代理路由和白名单。

修复：

- 生产环境禁用文档端点（`docs_url=None`、`redoc_url=None`、`openapi_url=None`）或在边缘层限制访问。

---

### FASTAPI-AUTH-001：认证必须明确，并通过依赖项一致地强制执行

严重级别：高

要求：

- 必须将认证实现为依赖项（或路由级依赖项），使受保护端点不会“忘记”认证。
- 特权路由／端点必须默认“拒绝”；真正公开的路由须显式标注。
- 应当在路由边界集中执行认证（例如为已认证端点使用受保护的 `APIRouter`）。（[FastAPI][7]）

不安全模式：

- 在各处理器中零散地做临时认证检查（容易遗漏）。
- 受保护与不受保护端点混杂，且无明确策略。

检测提示：

- 识别路由和端点；检查受保护的端点是否包含 `Depends(...)`／`Security(...)`。
- 搜索处理器内部的 `if user is None: raise ...` 模式（应使用依赖项代替）。

修复：

- 将认证移入依赖项，并用 `Depends()`／`Security()` 一致地附加到路由／端点。（[FastAPI][7]）

---

### FASTAPI-AUTH-002：使用标准认证传输方式；避免在 URL 中放置机密

严重级别：高

要求：

- 令牌认证应当使用 `Authorization: Bearer <token>` 请求头，而非查询参数。（[FastAPI][11]）
- 可避免时，不得将机密（令牌、含长期有效机密的重置链接、API 密钥）放入查询字符串。

不安全模式：

- 用 `?token=...`、`?api_key=...`、`?auth=...` 作为主要认证方式。
- 长期有效的访问令牌嵌入 URL（通过日志、referrer、缓存泄露）。

检测提示：

- 搜索 `token`、`api_key`、`key`、`secret`、`password` 等参数名。
- 查找无正当理由使用查询 API 密钥的安全方案。

修复：

- 将令牌移入 Authorization 请求头；轮换／缩短有效期；敏感值使用 POST 请求体。

---

### FASTAPI-AUTH-003：密码存储必须使用强哈希；严禁明文存储密码

严重级别：严重

要求：

- 必须使用强且慢的密码哈希方案存储密码（例如 Argon2id、bcrypt）。
- 不得存储明文密码，也不得以可逆加密作为主要保护手段。
- 应当使用成熟库进行哈希和校验（不要自己造轮子）。

不安全模式：

- 数据库中存储明文密码。
- 使用快速哈希（如 SHA256）而未使用正确的密码哈希 KDF。
- 在 API 响应中返回密码哈希。

检测提示：

- 搜索持久化的 `password=` 字段，查找对密码使用 `hashlib.md5/sha1/sha256` 的情况。
- 检查响应模型中是否包含密码／哈希字段。

修复：

- 迁移到正确的密码哈希库；增加登录时重新哈希的升级路径。

---

### FASTAPI-AUTH-004：JWT 校验必须严格；JWT 不得携带机密

严重级别：高

要求：

- 必须校验 JWT 签名并强制执行算法白名单。
- 必须校验与系统相适应的标准声明（至少 `exp`；多服务或多租户场景通常还需 `iss`／`aud`）。
- 必须认识到 JWT 内容对客户端可见；不得在 JWT 载荷中放入机密。（[FastAPI][12]）

不安全模式：

- `jwt.decode(..., options={"verify_signature": False})` 或等效写法。
- 接受 `alg=none`／算法混淆。
- 用 JWT 载荷存储敏感机密（API 密钥、密码）。

检测提示：

- 搜索 `jwt.decode`、`python-jose`、`PyJWT`、`verify_signature`。
- 检查是否缺失 exp 校验或过期时间过长。

修复：

- 强制执行严格校验（签名、允许的算法、exp 以及任何必需的签发者／受众约束）。
- 只存储你愿意向客户端暴露的标识符／声明。（[FastAPI][12]）

---

### FASTAPI-AUTHZ-001：授权必须按对象、按属性强制执行

严重级别：高

要求：

- 只要通过用户可控的标识符（路径／查询／请求体中的 ID）访问资源，就必须执行对象级授权。
- 必须执行属性级授权和响应塑形，以防止“过度数据暴露”（例如仅管理员可见的字段）。（[OWASP Foundation][13]）

不安全模式：

- `GET /users/{id}` 返回用户记录，但未验证调用方是否有权访问该 `id`。
- 响应模型包含内部字段（角色、权限、账单数据、密码哈希）。

检测提示：

- 枚举接受 ID 的端点；追踪是否执行了授权检查。
- 比较公开与内部字段的响应模型。

修复：

- 增加对象级检查（所有权、ACL、租户边界）。
- 使用只包含允许字段的专用响应模型。

---

### FASTAPI-SESS-001：如使用基于 Cookie 的会话和 TLS，生产环境的 Cookie 属性必须安全

严重级别：高（仅当启用 TLS 时）

要求（生产环境、HTTPS）：

- 必须将会话 Cookie 设置为仅通过 HTTPS 发送（secure）。重要提示：仅在配置了 TLS 的生产环境中设置 `Secure`。在本地 HTTP 开发环境运行时，不要在 Cookie 上设置 `Secure` 属性。应根据应用是否处于生产模式有条件地执行此操作。还应包含类似 `SESSION_COOKIE_SECURE` 的属性，以便在 HTTP 测试时可禁用 `Secure` Cookie。
- 必须为会话 Cookie 设置 HttpOnly（JS 不可访问）。
- 应当使用 `SameSite=Lax`（若用户体验允许可用 `Strict`）；如需跨站 Cookie，须记录 CSRF 影响并增加补偿性控制。（[OWASP Cheat Sheet Series][8]）
- 如使用 Starlette 的 `SessionMiddleware`，生产环境必须设置 `https_only=True` 并选择合适的 `same_site`。（[PyPI][5]）

不安全模式：

- 会话 Cookie 无 Secure／HttpOnly。
- 已认证的状态变更端点使用 `SameSite=None` Cookie 且无 CSRF 防护。

检测提示：

- 搜索 `SessionMiddleware(` 并检查 `https_only`、`same_site` 等参数。
- 搜索 `set_cookie(` 用法及 Cookie 标志。

修复：

- 设置安全的 Cookie 属性；高特权会话优先采用短有效期。（[OWASP Cheat Sheet Series][8]）

---

### FASTAPI-SESS-002：不得在签名会话 Cookie 中存储敏感机密

严重级别：高

要求：

- 必须假定基于 Cookie 的会话数据对客户端可读（签名≠加密）；除非在服务端加密，否则不得存储机密或 PII。
- Cookie 中只存储不透明标识符（如会话 ID）或非敏感状态；敏感会话状态存储在服务端。（[OWASP Cheat Sheet Series][8]）

不安全模式：

- 将访问令牌、刷新令牌或 PII 直接存储在 Cookie 会话载荷中。
- 把“签名 Cookie”当作机密存储。

检测提示：

- 搜索 `request.session[...] =` 或等效的 `session[...] =` 模式；识别存储了哪些内容。
- 识别 `SessionMiddleware` 或其他 Cookie 会话机制的使用。

修复：

- 将敏感值移入服务端存储；保持 Cookie 最小化。

---

### FASTAPI-CSRF-001：基于 Cookie 认证的状态变更请求必须受到 CSRF 防护

严重级别：高

注意：仅在使用基于 Cookie 的认证时适用。如果应用使用基于请求头或令牌的认证（如 Authorization 请求头），则不存在 CSRF 问题。

要求：

- 必须保护所有依赖 Cookie 认证的状态变更端点（POST／PUT／PATCH／DELETE）。
- 应当使用经过验证的 CSRF 方案（同步器令牌模式或经过充分审查的中间件），而不是自行实现。（[OWASP Cheat Sheet Series][2]）
- 可以增加纵深防御（Origin／Referer 检查、SameSite Cookie、Fetch Metadata），但对基于 Cookie 认证的应用，令牌是主要防御手段。（[OWASP Cheat Sheet Series][2]）
- 重要提示：如果不使用 Cookie 认证（认证经由 `Authorization` 请求头），CSRF 通常不适用。（[FastAPI][11]）

不安全模式：

- 基于 Cookie 认证的状态变更端点无 CSRF 校验。
- 用 GET 执行状态变更动作（放大 CSRF 风险）。

检测提示：

- 枚举使用 GET 以外方法的路由；判断是否用 Cookie 进行认证。
- 查找 CSRF 令牌的生成／校验逻辑或中间件。

修复：

- 在使用 Cookie 认证的状态变更动作上增加 CSRF 令牌（并校验）。（[OWASP Cheat Sheet Series][2]）

---

### FASTAPI-VALID-001：请求解析与校验必须以 schema 驱动；防止批量赋值

严重级别：中（尤其是写入数据库的 API）

要求：

- 应当使用 Pydantic 模型处理请求体，而不是接受任意的 `dict`／`Any`。
- 应当在适当时配置模型拒绝意外字段（防止“批量赋值”类漏洞）。
- 在将标识符（ID、邮箱、URL）用于访问控制或副作用之前，必须进行校验和规范化。（[OWASP Cheat Sheet Series][14]）

不安全模式：

- `payload = await request.json()` 之后接 `Model(**payload)`，或用 `payload` 直接写库（无白名单）。
- 写端点模型静默接受未知字段。

检测提示：

- 搜索 `await request.json()`、`request.body()`、`dict` 类型请求体、`Any` 类型请求体。
- 查找执行 `db.update(**payload)` 或 `Model(**payload)` 且输入未经过滤的端点。

修复：

- 使用带白名单字段的显式 Pydantic 模型；写端点拒绝额外字段。（[OWASP Cheat Sheet Series][14]）

---

### FASTAPI-RESP-001：通过响应模型和显式序列化防止过度数据暴露

严重级别：中

要求：

- 必须定义只包含预期字段的响应模型（尤其针对用户对象、认证相关对象、账单对象）。
- 应当将“创建输入”“数据库／内部”和“公开输出”分别使用独立模型，避免泄露敏感字段。（[FastAPI][15]）

不安全模式：

- 返回包含内部列的 ORM 对象或 dict。
- 复用“数据库模型”作为响应模型（包含 `password_hash`、`is_admin` 等）。

检测提示：

- 查找返回 `user`（ORM 实例）的端点。
- 检查返回敏感资源的端点是否省略 `response_model`。

修复：

- 增加显式响应模型；创建排除敏感字段的“公开”schema。（[FastAPI][15]）

---

### FASTAPI-XSS-001：防止 HTML 响应和模板中的反射型／存储型 XSS

严重级别：高（如果服务提供 HTML）

要求：

- 渲染 HTML 时必须使用启用自动转义的模板。
- 不得将不可信内容标记为安全（不得对用户可控数据进行不安全的“原始 HTML”渲染）。
- 当服务提供的 HTML 包含任何用户内容时，应当部署 CSP。（[OWASP Cheat Sheet Series][16]）

不安全模式：

- 未转义／未净化即将用户内容直接渲染进 HTML。
- 禁用自动转义或使用“原始 HTML”功能而不做净化。

检测提示：

- 搜索模板渲染和拼接 HTML 的字符串拼接。
- 审查模板中的“不安全”过滤器／结构和未加引号的属性。

修复：

- 保持自动转义开启；仅在绝对必要时使用可信净化器净化用户 HTML；增加 CSP。（[OWASP Cheat Sheet Series][16]）

注意：

- 如果应用是纯 JSON API，XSS 通常是客户端／应用侧的问题，但错误页／文档页仍可能渲染 HTML。

---

### FASTAPI-SSTI-001：绝不渲染不可信模板（服务端模板注入）

严重级别：严重

要求：

- 不得渲染包含用户可控模板语法的模板。
- 必须将受不可信输入影响的“字符串模板”渲染视为危险。
- 如果绝对必须使用不可信模板（罕见、高风险）：

  - 必须使用沙箱化模板方案并限制能力。
  - 必须假设沙箱逃逸可能发生；增加隔离和严格白名单。（[OWASP Foundation][17]）

不安全模式：

- 通过普通 Jinja 环境渲染从用户输入或数据库加载的模板。
- 使用用户可控字符串动态构建模板。

检测提示：

- 搜索 Jinja 的 `Environment.from_string`、`Template(...)` 或类似用法。
- 追踪模板字符串的来源（请求、数据库、上传、管理面板）。

修复：

- 改用不可执行的模板方案（简单字符串替换）。
- 如确有必要，使用 Jinja 的沙箱环境并加强隔离。（[jinja.palletsprojects.com][18]）

---

### FASTAPI-HEADERS-001：设置必要的安全响应头（应用内或边缘层）

严重级别：中

要求（典型 API／Web 应用）：

- 应当设置：

  - `X-Content-Type-Options: nosniff`
  - 点击劫持防护（提供 HTML 时设置 `X-Frame-Options` 和／或 CSP 的 `frame-ancestors`）
  - 酌情设置 `Referrer-Policy` 和 `Permissions-Policy`

注意：

- 响应头可能由代理／CDN 设置。如果应用代码中不可见，标记为“在边缘层验证”。（[OWASP Cheat Sheet Series][6]）

不安全模式：

- 提供 HTML 或敏感 API 的应用在任何位置（应用或边缘）都没有安全响应头。

检测提示：

- 搜索设置响应头的中间件；检查反向代理配置。

修复：

- 集中设置响应头（中间件）或通过反向代理／CDN 设置。

---

### FASTAPI-CORS-001：CORS 必须明确且最小权限

严重级别：中（与凭据组合配置错误时为高）

要求：

- 如不需要 CORS，必须保持禁用。
- 如需要 CORS：

  - 必须白名单可信来源（不得反射任意来源）。
  - 不得将携带凭据的请求与通配符来源组合（这不安全，且通常会被合规中间件拒绝）。（[OWASP Cheat Sheet Series][6]）
  - 应当限制允许的方法和请求头。

不安全模式：

- `allow_origins=["*"]` 与 `allow_credentials=True` 组合。
- 不经验证即反射 `Origin`。
- 广泛使用 `allow_origin_regex=".*"`。

检测提示：

- 搜索 `CORSMiddleware` 配置。
- 查找 `allow_origins=["*"]`、`allow_credentials=True`、`allow_origin_regex`。

修复：

- 使用显式的来源白名单和最小的方法／请求头；除非必需，否则关闭凭据。（[OWASP Cheat Sheet Series][6]）

---

### FASTAPI-HOST-001：生产环境必须校验 Host 请求头

严重级别：低

要求：

- 应当使用 `TrustedHostMiddleware`（或边缘层等效方案）限制可接受的 Host 值。（[PyPI][5]）
- 未经校验，不得在安全敏感决策中信任 `Host` 请求头。

不安全模式：

- 未做 Host 校验，却基于请求 Host 生成外部 URL（密码重置链接、回调 URL）。
- 在宽松代理背后的应用中允许任意 Host 请求头。

检测提示：

- 搜索 `TrustedHostMiddleware` 用法。
- 搜索使用 `request.url`、`request.base_url` 或基于 Host 的值构建外部 URL 的逻辑。

修复：

- 生产环境配置严格的允许主机列表；如可能，在边缘层同样强制执行。

---

### FASTAPI-PROXY-001：反向代理信任必须正确配置

严重级别：高（位于代理之后时）

要求：

- 如位于反向代理之后，必须正确配置转发请求头信任。
- 不得盲目信任来自开放互联网的 `X-Forwarded-*` 请求头。
- 如使用 Uvicorn 的代理请求头支持，必须限制哪些 IP 可以提供转发请求头。（[PyPI][4]）

不安全模式：

- 广泛启用代理请求头而不限制可信代理 IP。
- 未建立正确信任边界即使用转发请求头判断“是否安全”“是否内部”“客户端 IP”。

检测提示：

- 搜索 `--proxy-headers`、`--forwarded-allow-ips` 或等效配置。
- 搜索对 `request.client.host`、`request.url.scheme`、`request.headers["x-forwarded-for"]` 的安全敏感使用。

修复：

- 仅在确定位于已知代理之后时才配置 Uvicorn 的代理请求头，并将 `forwarded_allow_ips` 限制为该代理。（[PyPI][4]）
- 即使在代理之后也应保持 Host 白名单。

---

### FASTAPI-LIMITS-001：必须执行请求和 multipart 限制以防止 DoS

严重级别：低

要求：

- 必须在边缘层（反向代理／负载均衡器）执行请求大小限制，并在应用中按需校验。
- 必须对 multipart/form-data 处理特别审查；历史漏洞包括无界缓冲和 DoS 向量。（[advisories.gitlab.com][9]）
- 应当对高成本端点做限流和／或每 IP／每用户节流。

不安全模式：

- 接受任意大的 JSON 请求体或 multipart 表单。
- 解析 multipart 表单而无大小／字段数量控制。

检测提示：

- 识别文件上传端点和 `multipart/form-data` 用法。
- 查找缺失的代理层限制（nginx `client_max_body_size`、ALB 限制等）和缺失的应用层检查。

修复：

- 强制执行严格的请求体限制和 multipart 约束；保持 Starlette 和 python-multipart 更新到已修补版本。（[advisories.gitlab.com][9]）

---

### FASTAPI-FILES-001：防止路径穿越和不安全的静态文件暴露

严重级别：高

要求：

- 未经严格校验和安全的基准目录约束，不得将用户可控的文件路径传给 `FileResponse`／文件系统调用。
- 如使用 `StaticFiles`，必须保持 Starlette 更新并了解其安全历史（旧版本存在路径穿越通告）。（[advisories.gitlab.com][10]）
- 不得从静态根目录将用户上传内容作为可执行／活动内容（尤其是 HTML／JS）提供，除非有安全处理。

不安全模式：

- `FileResponse(request.query_params["path"])`
- 挂载 `StaticFiles(directory="uploads")`，而上传目录包含 HTML／JS／SVG 且以内联方式提供。

检测提示：

- 在路由中搜索 `FileResponse(`、`StaticFiles(`、`open(`。
- 追踪路径是否源自不可信输入。

修复：

- 对文件使用不透明 ID；将 ID 映射到服务端存储的路径。
- 适当时将不可信内容作为附件下载提供。

---

### FASTAPI-FILES-002：缓解文件服务端点的 Range 请求头 DoS

严重级别：低（如果受影响版本且启用了文件服务）

要求：

- 如使用 `FileResponse`／`StaticFiles`，必须保持 Starlette 已修补已知的文件服务 DoS 问题。
- 必须将异常的 `Range` 请求头处理与文件服务视为 DoS 攻击面。（[advisories.gitlab.com][19]）

不安全模式：

- 使用存在漏洞的 Starlette 版本提供大文件。
- 文件端点无限流／CDN 屏蔽。

检测提示：

- 识别 Starlette 版本；若在受影响范围内，予以标记。
- 查找 `FileResponse` 和 `StaticFiles` 的使用。

修复：

- 按通告指引将 Starlette 升级到已修复版本。（[advisories.gitlab.com][19]）
- 适当时为文件端点增加边缘缓存／限流。

---

### FASTAPI-UPLOAD-001：文件上传必须校验、安全存储、安全提供

严重级别：中

要求：

- 必须强制执行上传大小限制（应用层＋边缘层）。
- 必须使用白名单和内容检查校验文件类型（不仅看扩展名）。（[OWASP Cheat Sheet Series][20]）
- 应当生成服务端文件名（随机 ID），避免信任原始文件名。
- 除非明确预期，必须以安全方式提供潜在活动格式（下载附件）。

不安全模式：

- 接受任意文件类型并内联返回。
- 使用用户提供的文件名作为存储路径。

检测提示：

- 查找上传处理器以及文件的写入位置和方式。
- 查找上传目录的直接暴露。

修复：

- 实现白名单校验＋安全存储＋安全提供；如适用增加扫描／隔离。（[OWASP Cheat Sheet Series][20]）

---

### FASTAPI-INJECT-001：防止 SQL 注入（使用参数化查询／ORM）

严重级别：高

要求：

- 必须使用参数化查询或在底层做参数化的 ORM。
- 不得用字符串拼接／f-string 配合不可信输入构建 SQL。（[OWASP Cheat Sheet Series][21]）

不安全模式：

- `f"SELECT ... WHERE id={user_id}"`
- `"... WHERE name = '%s'" % user_input`

检测提示：

- 在 Python 字符串中搜索靠近 `.execute(...)` 的 SQL 关键字。
- 追踪不可信数据进入数据库调用。

修复：

- 替换为参数化查询／ORM 查询 API；查询前校验类型。（[OWASP Cheat Sheet Series][21]）

---

### FASTAPI-INJECT-002：防止操作系统命令注入

严重级别：严重至中高（取决于暴露面）

要求：

- 必须避免使用不可信输入执行 shell 命令。
- 如确需 subprocess：

  - 必须以列表形式传参（而非字符串）
  - 不得对攻击者影响的字符串使用 `shell=True`
  - 对任何可变组件应当使用严格白名单（[OWASP Cheat Sheet Series][22]）

不安全模式：

- `os.system(user_input)`
- `subprocess.run(f"cmd {user}", shell=True)`
- 将用户字符串传入 `bash -c`、`sh -c`、PowerShell 等。

检测提示：

- 搜索 `os.system`、`subprocess`、`Popen`、`shell=True`。
- 追踪从请求／数据库进入这些调用的数据。

修复：

- 用库 API 代替 shell 命令。
- 如不可避免，硬编码命令并白名单校验参数；在支持处使用 `--` 分隔符。（[OWASP Cheat Sheet Series][22]）

---

### FASTAPI-SSRF-001：防止出站 HTTP 中的服务端请求伪造（SSRF）

严重级别：中（在云／VPC 环境中可为高）

- 注：对于小型独立项目，这一点不太重要。在部署到 LAN 或与其他服务共置同一服务器时最为重要。

要求：

- 必须将向用户提供 URL 发起的出站请求视为高风险。
- 应当对任何受用户影响的 URL 抓取进行校验并限制目的地（白名单主机／域名）。
- 应当阻止访问 localhost／私有 IP 段／链路本地地址以及云元数据端点。
- 必须将协议限制为 http／https。
- 应当设置超时并谨慎控制跳转。（[OWASP Cheat Sheet Series][23]）

不安全模式：

- `httpx.get(request.query_params["url"])`
- 接受任意 URL 的“URL 预览／导入／webhook 测试器”功能。

检测提示：

- 搜索 `requests`、`httpx`、`urllib`、`aiohttp` 中 URL 源自请求／数据库的调用。
- 识别名为 `fetch`、`preview`、`proxy`、`webhook`、`import` 的端点。

修复：

- 实现严格的 URL 解析＋白名单；增加出站管控；设置短超时；如不需要则禁用跳转。（[OWASP Cheat Sheet Series][23]）

---

### FASTAPI-REDIRECT-001：防止开放跳转

严重级别：低

要求：

- 必须校验源自不可信输入的跳转目标（`next`、`redirect`、`return_to`）。
- 应当优先只跳转到同站相对路径或域名白名单。（[OWASP Cheat Sheet Series][24]）

不安全模式：

- 返回 `RedirectResponse(next)`，其中 `next` 为用户可控且未校验。

检测提示：

- 搜索 `RedirectResponse(` 或跳转逻辑，检查目标的来源。

修复：

- 只允许相对路径或白名单域名；回退到安全默认值。（[OWASP Cheat Sheet Series][24]）

---

### FASTAPI-WS-001：WebSocket 端点必须认证并防止跨站滥用

严重级别：中至高（取决于数据／权限）

要求：

- 必须对任何非公开频道的 WebSocket 连接进行认证（WebSocket 本身不提供认证）。（[OWASP Cheat Sheet Series][25]）
- 应当为基于浏览器的 WebSocket 客户端执行适当的 Origin／CSRF 类防护（Origin 校验是常用控制手段）。
- 应当对消息频率和连接尝试限流；关闭空闲／滥用连接。

不安全模式：

- `@app.websocket(...)` 未做认证检查即接受并信任连接。
- 用查询字符串令牌认证而不考虑泄露／轮换问题。

检测提示：

- 搜索 `@app.websocket`／`websocket_endpoint`，检查在执行敏感操作前是否完成认证。
- 审查 Origin 检查、令牌解析和逐连接授权。

修复：

- 在握手期间要求认证（例如令牌或会话），并对动作／消息强制执行授权。
- 对基于浏览器的客户端在适当时校验 Origin；应用限流和超时。（[OWASP Cheat Sheet Series][25]）

---

### FASTAPI-SUPPLY-001：依赖与补丁卫生（聚焦安全相关依赖）

严重级别：低

要求：

- 应当固定并定期更新安全关键依赖（FastAPI、Starlette、Uvicorn、Pydantic、python-multipart、认证／JWT 库）。
- 必须及时响应已知安全通告。
- 因历史 CVE，必须将文件服务和 multipart 解析依赖视为安全敏感。（[advisories.gitlab.com][10]）

审计重点示例（历史）：

- Starlette StaticFiles 路径穿越（0.27.0 修复）。（[advisories.gitlab.com][10]）
- Starlette multipart/form-data DoS（0.40.0 修复）。（[advisories.gitlab.com][9]）
- Starlette FileResponse Range 请求头 DoS（0.49.1 修复）。（[advisories.gitlab.com][19]）

检测提示：

- 检查 `requirements.txt`、锁文件、容器镜像和运行时环境中的实际安装版本。
- 将文件上传／文件服务功能映射到依赖版本。

修复：

- 按通告升级到已修补版本；为受影响行为增加回归测试。

---

## 5）实用扫描启发式（如何“打猎”）

主动扫描时，使用这些高信号模式：

- 开发服务器／debug：

  - `--reload`、`reload=True`、`debug=True`、`FastAPI(debug=True)`（[PyPI][4]）
- OpenAPI／文档暴露：

  - `/docs`、`/redoc`、`/openapi.json`、`docs_url=`、`openapi_url=`
- 认证执行缺口：

  - 应当有 `Depends()`／`Security()` 的端点缺失；路由没有一致的依赖边界（[FastAPI][7]）
  - 查询参数中的令牌（`token=`、`api_key=`、`key=`）（[FastAPI][11]）
- 会话／Cookie＋CSRF：

  - `SessionMiddleware(` 及 Cookie 标志（`https_only`、`same_site`）（[PyPI][5]）
  - 使用 Cookie 认证但无 CSRF 检查的 POST／PUT／PATCH／DELETE 处理器（[OWASP Cheat Sheet Series][2]）
- 输入校验与批量赋值：

  - `await request.json()` 后直接以 dict 写库；接受额外字段的模型（[OWASP Cheat Sheet Series][14]）
- 过度数据暴露：

  - 无 `response_model` 返回 ORM 对象或 dict；响应包含密码／角色／内部字段（[FastAPI][15]）
- CORS：

  - `CORSMiddleware` 带 `allow_origins=["*"]`、`allow_origin_regex=".*"`、`allow_credentials=True`（[OWASP Cheat Sheet Series][6]）
- 文件：

  - `FileResponse(` 使用用户可控路径；`StaticFiles(` 暴露上传目录（[advisories.gitlab.com][10]）
- 上传／multipart：

  - `multipart/form-data` 端点无大小／字段约束；过时的 Starlette／python-multipart（[advisories.gitlab.com][9]）
- 注入：

  - 用 f-string／拼接生成 SQL 字符串进入 `.execute(...)`（[OWASP Cheat Sheet Series][21]）
  - `subprocess.*`、`shell=True`、`os.system`（[OWASP Cheat Sheet Series][22]）
- SSRF：

  - `httpx.get/post` 或 `requests.*` 的 URL 来自请求／数据库，无白名单／超时（[OWASP Cheat Sheet Series][23]）
- 跳转：

  - 未校验的 `RedirectResponse(next)`（[OWASP Cheat Sheet Series][24]）
- WebSocket：

  - `@app.websocket` 处理器无认证／Origin 检查；生产配置中使用 `ws://`（[FastAPI][27]）

始终尝试确认：

- 数据来源（不可信 vs 可信）
- 汇点类型（SQL／subprocess／文件／模板／http／跳转／ws）
- 存在的防护控制（校验、白名单、中间件、边缘控制）
- 已安装依赖版本是否落入易受攻击范围（[advisories.gitlab.com][10]）

---

## 6）来源（访问日期 2026-01-27）

主要框架文档：

- FastAPI（PyPI 元数据、版本）——`https://pypi.org/project/fastapi/`（[PyPI][1]）
- FastAPI 文档：安全“第一步”（Authorization Bearer 请求头约定）——`https://fastapi.tiangolo.com/tutorial/security/first-steps/`（[FastAPI][11]）
- FastAPI 参考：依赖项（`Depends`、`Security`）——`https://fastapi.tiangolo.com/reference/dependencies/`（[FastAPI][7]）
- FastAPI 参考：APIRouter（路由级依赖项）——`https://fastapi.tiangolo.com/reference/apirouter/`（[FastAPI][28]）
- FastAPI 文档：WebSocket——`https://fastapi.tiangolo.com/advanced/websockets/`（[FastAPI][27]）

ASGI／服务器技术栈文档：

- Starlette（PyPI、通用能力）——`https://pypi.org/project/starlette/`（[PyPI][5]）
- Starlette 文档：WebSocket——`https://starlette.dev/websockets/`（[Starlette][3]）
- Uvicorn（PyPI 元数据）——`https://pypi.org/project/uvicorn/`（[PyPI][4]）
- Pydantic 文档（v2.12.x）——`https://docs.pydantic.dev/latest/`（[Pydantic][29]）

安全标准与速查表：

- OWASP Cheat Sheet Series：会话管理——`https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][8]）
- OWASP Cheat Sheet Series：CSRF 防护——`https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][2]）
- OWASP Cheat Sheet Series：XSS 防护——`https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][16]）
- OWASP Cheat Sheet Series：批量赋值——`https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][14]）
- OWASP API Security Top 10（2023）——`https://owasp.org/API-Security/editions/2023/en/0x11-t10/`（[OWASP Foundation][13]）
- OWASP Cheat Sheet Series：SQL 注入防护——`https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][21]）
- OWASP Cheat Sheet Series：OS 命令注入防御——`https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][22]）
- OWASP Cheat Sheet Series：SSRF 防护——`https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][23]）
- OWASP Cheat Sheet Series：文件上传——`https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][20]）
- OWASP Cheat Sheet Series：未经验证的跳转与转发——`https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][24]）
- OWASP Cheat Sheet Series：HTTP 安全响应头——`https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][6]）
- OWASP Cheat Sheet Series：WebSocket 安全——`https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][25]）
- OWASP WSTG：服务端模板注入测试——`https://owasp.org/www-project-web-security-testing-guide/v41/4-Web_Application_Security_Testing/07-Input_Validation_Testing/18-Testing_for_Server_Side_Template_Injection`（[OWASP Foundation][17]）
- OWASP WSTG：WebSocket 测试——`https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/11-Client-side_Testing/10-Testing_WebSockets`（[OWASP Foundation][26]）

模板安全参考：

- Jinja：沙箱——`https://jinja.palletsprojects.com/en/stable/sandbox/`（[jinja.palletsprojects.com][18]）

选定的供应链／通告参考（Starlette 示例）：

- CVE-2023-29159（StaticFiles 路径穿越；0.27.0 修复）——`https://advisories.gitlab.com/pkg/pypi/starlette/CVE-2023-29159/`（[advisories.gitlab.com][10]）
- CVE-2024-47874（multipart/form-data DoS；0.40.0 修复）——`https://advisories.gitlab.com/pkg/pypi/starlette/CVE-2024-47874/`（[advisories.gitlab.com][9]）
- CVE-2025-62727（FileResponse Range 请求头 DoS；0.49.1 修复）——`https://advisories.gitlab.com/pkg/pypi/starlette/CVE-2025-62727/`（[advisories.gitlab.com][19]）

[1]: https://pypi.org/project/fastapi/ "https://pypi.org/project/fastapi/"
[2]: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html"
[3]: https://starlette.dev/websockets/?utm_source=chatgpt.com "Websockets"
[4]: https://pypi.org/project/uvicorn/ "https://pypi.org/project/uvicorn/"
[5]: https://pypi.org/project/starlette/ "https://pypi.org/project/starlette/"
[6]: https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html?utm_source=chatgpt.com "HTTP Security Response Headers Cheat Sheet"
[7]: https://fastapi.tiangolo.com/reference/dependencies/?utm_source=chatgpt.com "Dependencies - Depends() and Security() - FastAPI"
[8]: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html"
[9]: https://advisories.gitlab.com/pkg/pypi/starlette/CVE-2024-47874/ "Starlette Denial of service (DoS) via multipart/form-data | GitLab Advisory Database"
[10]: https://advisories.gitlab.com/pkg/pypi/starlette/CVE-2023-29159/ "Starlette has Path Traversal vulnerability in StaticFiles | GitLab Advisory Database"
[11]: https://fastapi.tiangolo.com/tutorial/security/first-steps/?utm_source=chatgpt.com "Security - First Steps - FastAPI"
[12]: https://fastapi.tiangolo.com/tutorial/response-model/ "https://fastapi.tiangolo.com/tutorial/response-model/"
[13]: https://owasp.org/API-Security/editions/2023/en/0x11-t10/ "https://owasp.org/API-Security/editions/2023/en/0x11-t10/"
[14]: https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html"
[15]: https://fastapi.tiangolo.com/tutorial/extra-models/ "https://fastapi.tiangolo.com/tutorial/extra-models/"
[16]: https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html"
[17]: https://owasp.org/www-project-web-security-testing-guide/v41/4-Web_Application_Security_Testing/07-Input_Validation_Testing/18-Testing_for_Server_Side_Template_Injection?utm_source=chatgpt.com "Testing for Server Side Template Injection"
[18]: https://jinja.palletsprojects.com/en/stable/sandbox/?utm_source=chatgpt.com "Sandbox — Jinja Documentation (3.1.x)"
[19]: https://advisories.gitlab.com/pkg/pypi/starlette/CVE-2025-62727/ "Starlette vulnerable to O(n^2) DoS via Range header merging in ``starlette.responses.FileResponse`` | GitLab Advisory Database"
[20]: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html"
[21]: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html"
[22]: https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html"
[23]: https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html"
[24]: https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html?utm_source=chatgpt.com "Unvalidated Redirects and Forwards Cheat Sheet"
[25]: https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html?utm_source=chatgpt.com "WebSocket Security - OWASP Cheat Sheet Series"
[26]: https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/11-Client-side_Testing/10-Testing_WebSockets?utm_source=chatgpt.com "WSTG - Latest | OWASP Foundation"
[27]: https://fastapi.tiangolo.com/advanced/websockets/?utm_source=chatgpt.com "WebSockets - FastAPI"
[28]: https://fastapi.tiangolo.com/reference/apirouter/?utm_source=chatgpt.com "APIRouter class - FastAPI"
[29]: https://docs.pydantic.dev/latest/ "https://docs.pydantic.dev/latest/"
