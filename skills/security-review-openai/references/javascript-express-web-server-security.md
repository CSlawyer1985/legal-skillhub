# Express（Node.js）Web 安全规范（Express 5.x / 4.19.2+，Node.js LTS）

本文档设计为一份**安全规范**，用于支持：

1. 为新的 Express 应用和路由提供**默认安全的代码生成**。
2. 对现有 Express 代码进行**安全审查 / 漏洞排查**（被动式“在工作中发现问题”以及主动式“扫描代码库并报告发现”）。

本文档刻意以一组**规范性要求**（“必须/应当/可以”，MUST/SHOULD/MAY）加**审计规则**（不良模式长什么样、如何检测、如何修复/缓解）的形式编写。

---

## 0) 安全、边界与反滥用约束（必须遵守）

* 不得请求、输出、记录或提交密钥（API 密钥、密码、私钥、会话密钥、cookie、令牌）。
* 不得通过禁用防护机制来“修复”安全问题（例如削弱 cookie 标志、为基于 cookie 认证的应用禁用 CSRF 防护、启用宽松的 CORS、信任来自开放互联网的代理头、在生产环境开启调试/堆栈跟踪、在无替代方案的情况下禁用 TLS）。
* 审计时必须提供**基于证据的发现**：引用文件路径、代码片段、中间件/配置值以及支撑该结论的运行时假设。
* 必须诚实对待不确定性：如果防护措施可能存在于基础设施层（反向代理、网关、WAF、CDN），应报告为“在应用代码中不可见；需在运行时/配置层面验证”。
* 必须优先使用经过验证的库和平台控制，而非“自行开发”的加密/认证/会话/CSRF。Express 明确要求应用自行正确验证/处理用户输入；它不会自动完成这一点。（[Express][1]）

---

## 1) 运行模式

### 1.1 生成模式（默认）

当被要求编写新的 Express 代码或修改现有代码时：

* 必须遵守本规范中的每一条**必须（MUST）**要求。
* 应当遵守每一条**应当（SHOULD）**要求，除非用户明确另有要求。
* 必须优先使用默认安全的 API 和经过验证的库，而非自编安全代码。
* 必须避免引入新的高风险汇点（shell 执行、动态代码求值、不安全的重定向、将用户文件作为 HTML 提供、从未受信任的字符串渲染模板、不安全的文件系统路径、SSRF URL 抓取端点等）。

### 1.2 被动审查模式（编辑期间始终开启）

在 Express 代码库的任何位置工作时（即使用户并未要求安全扫描）：

* 必须“注意到”所接触/附近代码中对本规范的违反。
* 应当随时提请注意发现的问题，并附简要说明和安全的修复方式。

### 1.3 主动审计模式（明确的扫描请求）

当用户要求“扫描”“审计”或“排查漏洞”时：

* 必须系统性地搜索代码库中违反本规范之处。
* 必须以结构化格式输出发现（见 §2.3）。

建议的审计顺序：

1. 入口点（server/app 引导）、部署清单、Dockerfile、进程管理器配置、CI/CD。
2. Express 设置与中间件栈顺序（helmet、解析器、认证、会话、CSRF、CORS）。
3. 代理信任（`trust proxy`）以及 IP/协议/主机处理。（[Express][2]）
4. 认证流程、会话、cookie、密码重置链接、重定向处理。（[Express][1]）
5. 改变状态的路由与 CSRF 防护（基于 cookie 认证的应用）。（[OWASP Cheat Sheet Series][3]）
6. 模板渲染与 XSS 防御（HTML 生成、CSP、`res.locals`）。（[OWASP Cheat Sheet Series][4]）
7. 文件处理（上传 + 下载 + 静态文件）与路径穿越。（[Express][5]）
8. 注入类别（SQL、NoSQL、命令执行、不安全反序列化）。（[OWASP Cheat Sheet Series][6]）
9. 出站请求（SSRF）与 webhook/回调投递。（[OWASP Cheat Sheet Series][7]）
10. 速率限制 / 暴力破解防御 / 滥用控制。（[Express][1]）
11. 依赖卫生 / 锁文件 / npm audit / 易受攻击的 Express 版本。（[Express][1]）

---

## 2) 定义与审查指引

### 2.1 不受信任的输入（除非证明其可信，否则视为攻击者可控）

在 Express 中，常见的不受信任输入包括：

* `req.params`（路由参数）
* `req.query`（查询字符串参数；根据解析方式不同，可以是字符串/数组/对象）（[OWASP Cheat Sheet Series][8]）
* 来自 `express.json()`、`express.urlencoded()`、`express.text()`、`express.raw()` 的 `req.body`（[Express][5]）
* `req.headers` / `req.get(...)`
* `req.cookies` / `req.signedCookies`（如果使用了 cookie 解析中间件）
* 上传元数据和文件名（例如 multer 的 `file.originalname`、`file.mimetype`）
* 来自外部系统的任何数据（webhook、第三方 API、消息队列）
* 任何源自用户的持久化用户内容（数据库行）

特别说明（代理）：

* 如果启用了 `trust proxy`，则 `req.ip`、`req.hostname` 和 `req.protocol` 等值可能来源于 `X-Forwarded-*` 头，如果您的代理链没有正确覆盖/删除这些头，则它们**可能被攻击者控制**。（[Express][2]）

### 2.2 改变状态的请求

如果请求能够创建/更新/删除数据、改变认证/会话状态、触发副作用（购买、发送邮件、发送 webhook）或发起特权操作，则该请求属于改变状态的请求。

### 2.3 审计发现必填格式

对发现的每个问题，输出：

* 规则 ID：
* 严重性：严重 / 高 / 中 / 低
* 位置：文件路径 + 函数/路由/中间件名称 + 行号
* 证据：确切的代码/配置片段
* 影响：可能出什么问题、谁能利用
* 修复：安全的变更（优先最小差异）
* 缓解：若立即修复困难，采用纵深防御
* 误报说明：不确定时需要验证什么

---

## 3) 安全基线：最低生产配置（生产环境必须）

这是防止常见 Express 错误配置的“最低生产基线”。

最低基线目标：

* 使用并配置了 `helmet()`（在适用处尤其要配置 CSP），并减少指纹暴露（禁用 `x-powered-by`）。（[Express][1]）
* 存在自定义 404 处理器和自定义错误处理器，且生产环境不泄露内部堆栈跟踪。（[Express][1]）
* cookie/会话的使用是审慎的：

  * 不使用默认的会话 cookie 名称
  * cookie 在适当情况下使用安全属性（`Secure`、`HttpOnly`、`SameSite`）
  * 基于 cookie 的会话绝不存储密钥（客户端可读取这些内容）
  * 生产环境中服务端会话绝不使用 MemoryStore。（[Express][1]）
* 请求体解析有明确的限制（`express.json({ limit })`、`express.urlencoded({ limit, parameterLimit, depth })`）。（[Express][5]）
* `trust proxy` 显式配置以匹配您的代理拓扑；不要盲目设置为 `true`。（[Express][2]）
* 登录/认证端点具有暴力破解防护和速率限制。（[Express][1]）
* 依赖项定期审计/更新（`npm audit` + 漏洞公告响应）。（[Express][1]）

---

## 4) 规则（生成 + 审计）

每条规则包含：要求做法、不安全模式、检测提示和补救措施。

### EXPRESS-INPUT-001：将所有用户输入视为不受信任并加以验证

严重性：高

要求：

* 在将不受信任的输入用于安全敏感逻辑或危险汇点（数据库查询、重定向、文件系统、HTML 输出、shell 命令）之前，必须验证并规范化这些输入。在使用或传递这些不受信任的输入之前，确保其通过类型检查和结构检查。
* 在可行时应当采用白名单（已知良好）而非黑名单。
* 必须拒绝或安全处理 `req.query`、`req.params` 和 `req.body` 中的意外类型/形状。

不安全模式：

* 将 `req.query`、`req.params`、`req.body` 直接传入数据库/查询构建器、重定向、文件系统路径或模板。
* 假设 `req.query.foo` 始终是字符串（根据解析方式不同，它可能是数组/对象）。（[OWASP Cheat Sheet Series][8]）

检测提示：

* 识别“不受信任到汇点”的数据流：请求 → 汇点（`res.redirect`、SQL 执行、`sendFile`、`child_process`、模板渲染、出站抓取）。
* 搜索敏感调用中直接使用 `req.query.*`、`req.body.*`、`req.params.*` 的情况。

修复：

* 在路由边界添加模式验证（例如 zod/joi/express-validator）。
* 规范化类型（例如将 ID 强制转换为整数；在期望标量时拒绝数组）。

备注：

* Express 生产安全指引明确说明输入验证/处理是应用自身的责任。（[Express][1]）

---

### EXPRESS-REDIRECT-001：防止开放重定向；验证重定向目标

严重性：中

要求：

* 必须验证源自不受信任输入的重定向目标（`next`、`return_to`、`url`）。
* 应当仅白名单同站相对路径（首选）或严格的域名白名单。
* 验证失败时必须回退到安全的默认值。

不安全模式：

* 无验证的 `res.redirect(req.query.next)`。
* 使用不受信任 URL 的 `res.redirect(req.body.url)` 或 `res.location(...)`。

检测提示：

* 搜索 `res.redirect(` 和 `res.location(` 并追踪目标的来源。
* 查找名为 `next`、`redirect`、`return`、`url` 的查询参数。

修复：

* 仅允许相对路径（以 `/` 开头），并禁止 `//`、反斜杠及编码变体。
* 如果必须跨域重定向，则白名单确切的域名并强制使用 `https`。

备注：

* Express 文档将开放重定向列为危险用户输入，并展示了在重定向前验证主机名的做法。（[Express][1]）
* 保持 Express 更新：Express 曾有一个影响部分版本、与开放重定向相关的 CVE，升级是缓解措施的一部分。（[NVD][9]）

---

### EXPRESS-HEADERS-001：使用 Helmet（或等效方案）设置基本安全头

严重性：中

要求：

* 应当使用 `helmet()` 设置常见安全头。
* 对于渲染受用户影响内容的页面，应当切实地配置 CSP（尽可能避免 `unsafe-inline`）。
* 应当设置 `X-Content-Type-Options: nosniff`、点击劫持防御（`X-Frame-Options` 或 CSP `frame-ancestors`）以及适当的 referrer 策略。

注意：设置 CSP 的 script-src 最为重要。其他所有指令都没有那么重要，为了开发便利通常可以省略。

不安全模式：

* 应用代码中未设置安全头，也无证据表明在边缘层设置了安全头。
* 显示用户内容的应用缺少 CSP。
* 框架头配置错误，无意中允许点击劫持。

检测提示：

* 搜索 `helmet(` 的使用；检查 CSP 是否已配置或已禁用。
* 搜索用于设置安全头的 `res.setHeader(` / `res.set(`。
* 如果在应用代码中不可见，检查 nginx/CDN 配置；否则标记“需在边缘层验证”。

修复：

* 在中间件顺序的早期添加 `helmet()` 并配置：

  * CSP（`contentSecurityPolicy`）
  * 框架防护（`frameguard` 或 CSP `frame-ancestors`）
  * `X-Content-Type-Options`（`noSniff`）

备注：

* Express 生产安全最佳实践推荐 Helmet，并列出 Helmet 默认设置的头。（[Express][1]）
* 调整策略时，OWASP HTTP 头指引是有用的参考。（[OWASP Cheat Sheet Series][10]）

---

### EXPRESS-FINGERPRINT-001：通过禁用 `x-powered-by` 并定制错误/404 响应减少指纹暴露

严重性：低（纵深防御）

要求：

* 应当使用 `app.disable('x-powered-by')` 禁用 `X-Powered-By`。
* 应当提供自定义 404 处理器和自定义错误处理器，以避免产生明显不同的默认响应并控制信息泄露。

不安全模式：

* 保留了默认的 `X-Powered-By: Express` 响应头。
* 生产环境中使用具有可识别格式和/或堆栈跟踪的 Express 默认 404/错误响应。

检测提示：

* 搜索 `app.disable('x-powered-by')`。
* 检查中间件尾部是否有自定义 404（`app.use((req,res)=>...)`）和自定义错误处理器（`app.use((err,req,res,next)=>...)`）。
* 检查 `NODE_ENV` 是否已正确设置为生产行为（见 EXPRESS-ERROR-001）。（[Express][11]）

修复：

* 添加：

  * `app.disable('x-powered-by')`
  * 自定义 404 处理器
  * 在服务端记录日志、在客户端返回通用消息的自定义错误处理器

备注：

* Express 文档明确建议禁用 `x-powered-by` 并添加自己的 not-found 和错误处理器。（[Express][1]）

---

### EXPRESS-COOKIE-001：Cookie 必须使用安全属性并限定最小范围

严重性：中

要求：

* 必须为任何认证/会话 cookie 适当设置 cookie 标志：

  * 使用 HTTPS 时设置 `Secure`（生产环境）重要提示：仅在配置了 TLS 的生产环境中设置 `Secure`。在本地开发环境通过 HTTP 运行时，不要在 cookie 上设置 `Secure` 属性。应根据应用是否以生产模式运行来有条件地设置。还应包含类似 `SESSION_COOKIE_SECURE` 的属性，以便在通过 HTTP 测试时可禁用安全 cookie。
  * 认证/会话 cookie 设置 `HttpOnly`
  * 审慎设置 `SameSite`（`Lax` 是常见基线；兼容时用 `Strict`；`None` 仅在设置了 `Secure` 且有正当的跨站需求时使用）
* 应当避免宽泛地设置 `domain`（除非必要，避免“所有子域”）。
* 应当设置与风险和用户体验相匹配的有界过期时间。

不安全模式：

* 会话/认证 cookie 未设置 `HttpOnly`。
* 生产环境 HTTPS 下 cookie 未设置 `Secure`。
* `SameSite=None` + 基于 cookie 认证的改变状态端点未设 CSRF 防护。

检测提示：

* 搜索 `res.cookie(`、`Set-Cookie`、`cookie: { ... }`、`express-session`、`cookie-session`。
* 验证会话中间件配置中的 cookie 标志。

修复：

* 在会话/cookie 中间件配置中集中设置这些属性。

备注：

* Express 生产安全指引列出了 cookie 安全选项（`secure`、`httpOnly` 等）。（[Express][1]）
* `res.cookie()` 最终以选项设置 `Set-Cookie`；省略选项时默认遵循 RFC 6265 行为。（[Express][5]）
* 选择标志和生命周期时，OWASP 会话管理指引具有参考价值。（[OWASP Cheat Sheet Series][12]）

---

### EXPRESS-SESS-001：不要使用默认的会话 cookie 名称；避免会话指纹暴露

严重性：低（纵深防御）

要求：

* 应当覆盖默认的会话 cookie 名称（例如使用 `express-session` 时不要保留 `connect.sid`）。
* 除非有兼容性理由，应当使用通用名称（例如 `sessionId`）。

不安全模式：

* `express-session` 未配置 `name:`（使用默认 cookie 名称）。
* 同一域上的多个应用意外共享一个 cookie 名称。

检测提示：

* 搜索 `express-session` 配置块；检查是否存在 `name:`。

修复：

* 在 `express-session` 选项中设置 `name: 'sessionId'`（或类似名称）。

备注：

* Express 文档明确建议不要使用默认会话 cookie 名称以减少指纹暴露。（[Express][1]）

---

### EXPRESS-SESS-002：会话存储和生命周期必须生产安全

严重性：高

要求：

* 生产环境不得使用 `MemoryStore`（它不是为生产环境设计的）。
* 必须将会话密钥存储在源代码控制之外，并安全轮换。
* 应当在登录/权限变更时重新生成会话，以降低会话固定攻击风险。
* 不得在客户端可读取的 cookie 会话中存储敏感密钥。

不安全模式：

* `app.use(session({ store: new MemoryStore(), ... }))` 或缺失 store（默认为 MemoryStore）。
* 硬编码示例：仓库中的 `secret: 'keyboard cat'` / `secret: 's3Cur3'`。
* 使用 `cookie-session` 存储访问令牌、刷新令牌或 PII（个人身份信息）。

检测提示：

* 搜索 `express-session` 并检查 `MemoryStore` 的使用或缺失 `store`。
* 搜索会话配置中的 `secret:` 并检查是否硬编码。
* 查找 `req.session = ...` 模式以及是否存储了敏感数据。

修复：

* 使用生产级会话存储（Redis、数据库等）。
* 从环境变量/密钥管理器加载密钥。
* 登录时：`req.session.regenerate(...)` 或等效流程并安全地重新绑定权限。

备注：

* `express-session` 明确警告 `MemoryStore` 不适合生产环境。（[Express][1]）
* `express-session` 文档介绍了轮换密钥和会话重新生成以防范会话固定攻击。（[Express][1]）
* Express 指出基于 cookie 的会话会将数据序列化到 cookie 中，且 cookie 数据对客户端可见；应保持数据量小且不含密钥。（[Express][1]）

---

### EXPRESS-CSRF-001：基于 cookie 认证的改变状态请求必须受到 CSRF 防护

严重性：高

- 重要提示：如果认证不是通过 cookie 进行的（即通过认证头或其他传递的令牌认证），则不存在 CSRF 风险。

要求：

* 必须保护所有依赖 cookie 进行认证的改变状态端点（POST/PUT/PATCH/DELETE）。
* 应当使用经过充分理解的 CSRF 缓解措施（基于令牌是典型基线）。
* 可以增加纵深防御：Origin/Referer 验证、Fetch Metadata 强制、SameSite cookie、XHR/fetch 的自定义头要求——**但除非经过明确设计和论证，不得将其视为完整替代方案**。
* 如果基于表单的 CSRF 令牌不可行，则最低限度必须要求自定义 HTTP 头，因为这是第二强的方法。

重要提示：

* 如果认证通过 `Authorization: Bearer ...` 头进行（而非 cookie），经典的浏览器 CSRF 通常不适用；

不安全模式：

* 无 CSRF 防护、但改变状态且基于 cookie 认证的端点。
* 使用 GET 执行改变状态的操作（放大 CSRF 风险）。
* 仅检查用户可控字段的“CSRF 防护”。

检测提示：

* 枚举使用 GET/HEAD 以外方法的路由，并确认认证是否由 cookie 把关。
* 检查是否存在 CSRF 中间件和令牌检查。
* 也要检查 JSON API，而不仅是 HTML 表单。

修复：

* 为基于 cookie 认证的流程实现 CSRF 令牌。
* 在可行处添加 Origin/Referer 检查，并确保适当设置 SameSite。

备注：

* OWASP CSRF 指引和 OWASP Node.js 指引都推荐将反 CSRF 令牌作为 Web 应用的标准控制措施。（[OWASP Cheat Sheet Series][3]）

---

### EXPRESS-CORS-001：CORS 必须明确且遵循最小权限

严重性：中（配置不当并携带凭证时为高）

要求：

* 如果不需要 CORS，必须保持其禁用。
* 如果需要 CORS：

  * 必须白名单受信任的来源（未经验证不得反射任意 `Origin`）。
  * 不得将宽泛来源与凭证 cookie 结合（`Access-Control-Allow-Credentials: true`）。
  * 应当将方法、头和暴露的头限制在所需范围内。

不安全模式：

* `Access-Control-Allow-Origin: *` 与 `Access-Control-Allow-Credentials: true` 结合。
* 未经白名单验证为所有请求反射 `Origin`。
* 仅部分子集需要跨域访问时，却全局应用宽松的 CORS 中间件。

检测提示：

* 搜索 `cors(`、`Access-Control-Allow-Origin`、`Access-Control-Allow-Credentials`。
* 检查在跨域暴露的端点上是否使用 cookie 进行认证。

修复：

* 实现严格的来源白名单，并确保仅向预期来源提供凭证请求。
* 考虑按路由组拆分 CORS 配置，而非全局配置。

备注：

* OWASP HTTP 头指引涵盖响应头的安全影响（包括影响浏览器行为的头）；审查头配置状态时可作为参考。（[OWASP Cheat Sheet Series][10]）

---

### EXPRESS-PROXY-001：反向代理信任（`trust proxy`）必须正确配置

严重性：中（使用基于 IP 的认证时为高）

要求：

* 如果位于反向代理/负载均衡之后，必须配置 `app.set('trust proxy', ...)` 以匹配真实的代理链。
* 除非完全控制代理行为和头重写，不得盲目设置 `trust proxy = true`。
* 必须确保最后一个受信任的代理覆盖/删除 `X-Forwarded-For`、`X-Forwarded-Host` 和 `X-Forwarded-Proto`，以免客户端伪造它们。

不安全模式：

* 在直接暴露于互联网或位于未知代理之后的应用中设置 `app.set('trust proxy', true)`。
* 未正确配置代理信任就使用 `req.ip`、`req.protocol`、`req.hostname` 做安全决策。
* 以 `req.ip` 为键做速率限制，但转发头可被伪造。

检测提示：

* 搜索 `app.set('trust proxy'`。
* 检查基础设施文档（nginx/LB）中的头重写行为。
* 识别任何使用 `req.ip`、`req.ips`、`req.protocol`、`req.hostname` 的安全逻辑。

修复：

* 将 `trust proxy` 设置为跳数、明确的 IP/子网列表或与您的网络匹配的自定义函数。
* 确保代理覆盖转发头。

备注：

* Express 明确警告：当 `trust proxy` 为 `true` 时，客户端 IP 取自 `X-Forwarded-For`，如果代理不覆盖转发头，客户端可以提供任意值。它还描述了启用 trust proxy 会影响从转发头推导出的 `req.hostname` 和 `req.protocol`。（[Express][2]）

---

### EXPRESS-BODY-001：请求体大小和解析限制必须适当设置

严重性：低

要求：

* 应当为以下项设置明确的请求体大小限制：

  * `express.json({ limit })`
  * `express.urlencoded({ limit, parameterLimit, depth })`
* 应当只启用需要的解析器；不要默认对所有路由解析大型请求体。
* 应当在反向代理/网关层强制附加限制。

不安全模式：

* 无明确的请求体限制（接受任意大的 JSON/urlencoded）。
* 只有部分路由需要请求体时，却对所有路由全局应用解析器。
* `parameterLimit` 过高且无正当理由（DoS 风险）。

检测提示：

* 搜索 `express.json(` 并确认设置了 `limit`（或有意接受默认值）。
* 搜索 `express.urlencoded(` 并检查 `limit`、`parameterLimit` 和 `depth`。
* 审查上传/webhook 端点是否有特殊解析需求。

修复：

* 使用保守的默认值配置解析器，并在需要时按路由组覆盖。

备注：

* Express 文档介绍了 `express.json` 选项（包括 `limit`，默认为 100kb），并明确指出 `req.body` 不受信任且应被验证。（[Express][5]）
* Express 文档介绍了 `express.urlencoded` 选项，包括 `limit`、`parameterLimit` 和 `depth`。（[Express][5]）
* OWASP Node.js 指引也建议设置请求大小限制。（[OWASP Cheat Sheet Series][8]）

---

### EXPRESS-INPUT-002：防止 `req.query` 中的 HTTP 参数污染和类型混淆

严重性：中

要求：

* 必须将 `req.query` 值视为可能多值的（数组/对象），具体取决于查询解析方式。
* 对于安全敏感字段（例如 `role`、`isAdmin`、`redirect`、`amount`、`userId`），应当拒绝有歧义的多值参数。
* 如果担心参数污染，应当考虑显式解析或专用中间件。

不安全模式：

* 无类型检查的 `if (req.query.admin) { ... }`（数组/对象可能被强制为真值）。
* 将 `req.query` 直接传入 ORM/NoSQL 查询对象。

检测提示：

* 搜索对 `req.query.*` 的安全敏感比较，且无类型强制。
* 查找假设查询参数是字符串的代码。

修复：

* 验证形状：对某些参数强制仅限字符串，并拒绝数组/对象。
* 在适用且有文档说明的情况下，规范化查询解析设置（simple 与 extended）。

备注：

* OWASP Node.js 速查表明确强调 Express 查询解析可能产生字符串、数组或对象，并建议防止 HTTP 参数污染。（[OWASP Cheat Sheet Series][8]）

---

### EXPRESS-XSS-001：防止 HTML 响应和模板渲染中的反射型/存储型 XSS

严重性：高

要求：

* 必须在 HTML 输出中转义不受信任的内容（模板应默认自动转义；不要绕过）。
* 不得在未转义/未净化的情况下将不受信任的字符串注入 HTML。
* 对于渲染用户控制内容的应用，应当（通过 Helmet）设置 CSP。
* 应当确保 `res.locals` 不包含用于模板的用户控制输入，除非经过验证/转义。

不安全模式：

* `res.send("<div>" + req.query.q + "</div>")`
* 通过“安全”模板标志/过滤器传递不受信任的 HTML。
* 将不受信任的字符串写入 `res.locals` 后未转义直接渲染。

检测提示：

* 搜索包含用户输入的字符串的 `res.send(`。
* 搜索模板“安全”标志（引擎特定）并追踪数据来源。
* 搜索对 `res.locals` 的赋值，并判断其中是否可能包含不受信任的数据。

修复：

* 使用带自动转义的模板引擎；只传递经过验证的数据。
* 对于必须包含 HTML 的富文本，使用受信任的净化器和白名单策略。
* 添加包含切实指令的 CSP。

备注：

* Express API 文档明确警告 `res.locals`“不应包含用户控制的输入”，并经常用于向模板暴露 CSRF 令牌等。（[Express][5]）
* OWASP XSS 防护指引提供了标准的输出编码和策略建议。（[OWASP Cheat Sheet Series][4]）
* Helmet 可通过 CSP 等头缓解某些 XSS 类别。（[Express][1]）

---

### EXPRESS-TEMPLATE-001：绝不渲染不受信任的模板或模板路径（SSTI / LFI 风险）

严重性：严重（如果能证明模板字符串/路径受用户/攻击者控制）

要求：

* 不得渲染内容或模板路径/名称受不受信任输入影响的模板。
* 不得从用户控制的文件系统位置加载模板。
* 应当将“邮件模板编辑器”“主题引擎”和“类 CMS 模板存储”视为需要沙箱化和隔离的高风险设计。

不安全模式：

* `res.render(req.query.view, data)`，其中 `view` 未白名单化。
* 从包含用户输入的字符串渲染模板（引擎特定）。
* 从上传目录加载模板。

检测提示：

* 搜索第一个参数源自请求/数据库且未经白名单的 `res.render(`。
* 搜索由用户内容驱动的模板编译 API（引擎特定）。

修复：

* 使用白名单模板名称和固定模板目录。
* 如果需要用户自定义模板，实现严格的沙箱化并隔离执行。

备注：

* Express 的模板系统取决于所选引擎；如果用户输入影响模板选择或来源，应假定不安全。

---

### EXPRESS-FILES-001：防止路径穿越和不安全的文件提供（sendFile/download）

严重性：高

要求：

* 不得将用户控制的文件系统路径直接传给 `res.sendFile()` / `res.download()` / 文件系统 API。
* 当从目录提供用户所选文件时，应当使用带固定 `root` 和严格选项（例如拒绝点文件）的 `res.sendFile`。
* 在提供用户特定文件之前必须强制执行授权检查。

不安全模式：

* 无根目录限制的 `res.sendFile(req.query.path)` 或 `res.download(req.params.file)`。
* 接受 `..` 段、编码穿越或绝对路径的文件提供路由。

检测提示：

* 搜索 `res.sendFile(` 并追踪 `path` 参数的来源。
* 搜索 `res.download(` 并追踪 `path` 参数的来源。
* 查找对源自请求的路径执行 `fs.readFile`/`createReadStream` 的情况。

修复：

* 使用存储在服务端的标识到路径映射（数据库），而非客户端的原始路径。
* 在适当处使用 `root: <受信任的基目录>` 和 `dotfiles: 'deny'`；严格验证文件名部分。

备注：

* Express 的 `res.sendFile` 文档展示了将 `root` 选项和 `dotfiles: 'deny'` 作为安全提供配置的一部分。（[Express][5]）
* `res.download` 将文件作为附件传输，但仍必须控制/验证底层 `path`。（[Express][5]）

---

### EXPRESS-STATIC-001：加固 `express.static` / serve-static，绝不以活动内容形式提供不受信任的上传文件

严重性：中（如果提供不受信任的用户文件且对文件扩展名没有强健限制）

要求：

* 不得将用户上传内容从公共静态目录作为活动内容提供（尤其是 HTML/JS/SVG），除非明确有意为之且已沙箱化。如果确定内容为非活动内容（png、jpg 及其他图像等），则可能是安全的。在提供前验证图像文件扩展名是否在白名单内会更好。
* 应当将静态提供配置为：

  * 拒绝/忽略点文件
  * 如非必要，避免意外的目录索引
  * 对不可变资产应用适当的缓存控制

不安全模式：

* `app.use(express.static('uploads'))`，而用户可以上传任意文件。
* 从与应用同源的位置内联提供上传的 HTML 或 SVG。

检测提示：

* 搜索 `express.static(` 并识别被提供的目录。
* 将提供的目录与上传存储位置进行比对。
* 检查静态中间件中的 `dotfiles` 和 `index` 选项。

修复：

* 将上传内容存储在静态 Web 根目录之外，并通过受控路由提供，在适当处设置安全的 `Content-Type` 和 `Content-Disposition: attachment`。
* 配置 `express.static(root, { dotfiles: 'deny'|'ignore', index: false (如需要) })`。

备注：

* Express 文档介绍了 `express.static` 选项，包括 `dotfiles` 行为和 `index`。（[Express][5]）

---

### EXPRESS-UPLOAD-001：文件上传必须经过验证、安全存储并安全提供

严重性：低 - 中

要求：

* 应当强制上传大小限制（应用层 + 边缘层）。
* 必须使用白名单和内容检查来验证文件类型（不仅是文件扩展名）。
* 在可能的情况下，必须将上传内容存储在可执行/静态根目录之外。
* 应当生成服务端文件名（随机 ID）；不要信任原始文件名。
* 必须安全地提供潜在的活动格式（下载附件），除非明确有意为之。

不安全模式：

* 接受任意文件类型并内联返回。
* 使用 `file.originalname` 作为存储路径。
* 缺少大小/类型验证。

检测提示：

* 查找 multer/busboy/formidable 的使用并检查 `limits`。
* 检查上传文件的写入位置以及提供方式。
* 检查上传内容是否最终落在 `public/` 或任何 `express.static` 根目录下。

修复：

* 按照 OWASP 上传指引，实现白名单验证 + 安全存储 + 安全提供。

备注：

* OWASP 文件上传指引涵盖白名单、内容验证、存储和安全提供模式。（[OWASP Cheat Sheet Series][13]）

---

### EXPRESS-INJECT-001：防止 SQL 注入（使用参数化查询 / ORM）

严重性：高

要求：

* 必须使用参数化查询或在底层进行参数化的 ORM/查询构建器。
* 不得使用字符串拼接/模板字面量配合不受信任输入构建 SQL。

不安全模式：

* ``db.query(`SELECT * FROM users WHERE id = ${req.query.id}`)``
* `"SELECT ... WHERE name = '" + req.body.name + "'"`

检测提示：

* 在 JS/TS 中搜索 `SELECT`、`INSERT`、`UPDATE`、`DELETE` 字符串。
* 追踪进入 `.query(...)`、`.execute(...)` 或原始 SQL API 的不受信任输入。

修复：

* 替换为参数化查询（占位符）或 ORM 查询 API。
* 在查询前验证类型（例如整数 ID）。

备注：

* OWASP SQL 注入防护指引强烈支持参数化查询。（[OWASP Cheat Sheet Series][6]）

---

### EXPRESS-INJECT-002：防止 NoSQL 注入 / 操作符注入（Mongo 风格）

严重性：高（取决于应用）

要求：

* 必须验证由不受信任输入构建的任何查询对象的类型和模式。
* 如果用户输入被合并到查询对象中，必须防止操作符注入（例如 `$ne`、`$gt`、`$where`）。
* 在适当时应当考虑防御性库/中间件。

不安全模式：

* `collection.find(req.body)`，其中请求体受攻击者控制。
* 未经模式验证将 `req.query`/`req.body` 合并到 Mongo 查询中。

检测提示：

* 搜索参数源自请求的 `find(`、`findOne(`、`aggregate(` 调用。
* 检查 `{ ...req.query }` 或 `Object.assign(query, req.body)` 等模式。

修复：

* 在边界进行模式验证；仅从经过验证的字段显式构建查询对象。

备注：

* OWASP Node.js 速查表讨论了输入验证，并提到 Node 生态系统中常用于 NoSQL 场景净化的模块。（[OWASP Cheat Sheet Series][8]）

---

### EXPRESS-CMD-001：防止操作系统命令注入（child_process）

严重性：严重到高（取决于暴露程度），请证明其受用户/攻击者控制

要求：

* 必须避免使用不受信任输入执行 shell 命令。
* 如果必须使用子进程：

  * 必须避免对受攻击者影响的字符串使用 `exec()` / `execSync()`
  * 不得对受攻击者影响的数据使用 `shell: true`
  * 应当使用带参数数组和严格白名单的 `spawn()`。确保可执行文件是硬编码的或白名单化的，不要使用用户提供的命令名
  * 当子命令支持时，应当将用户控制的值放在 `--` 之后以避免标志注入

不安全模式：

* `exec(req.query.cmd)`
* `exec(`convert ${userPath} ...`)`
* `spawn('sh', ['-c', userString])`
* `spawn(userString, ['foo'])`

检测提示：

* 搜索 `child_process`、`exec(`、`execSync(`、`spawn(`、`fork(`。
* 追踪请求/数据库数据进入命令构造的过程。

修复：

* 如果可能，用 JavaScript 实现该功能或使用库，而不是子进程。
* 如果不可避免，硬编码命令并严格白名单参数。

备注：

* OWASP 操作系统命令注入防御指引涵盖避免 shell 和白名单模式。（[OWASP Cheat Sheet Series][14]）

---

### EXPRESS-SSRF-001：防止出站 HTTP 中的服务端请求伪造（SSRF）

严重性：中（云/局域网部署中为高）

注意：这主要仅适用于将部署在云/局域网环境、或同一主机上运行其他 http 服务的应用。有时该功能不可避免需要此能力（webhook）。

要求：

* 如果存在其他可达的私有 http 端点，必须将对用户提供的 URL 的出站请求视为高风险。
* 应当验证并限制任何受用户影响的 URL 抓取的目标（白名单主机/域名）。
* 应当阻止访问：

  * localhost / 私有 IP 范围 / 链路本地
  * 云元数据端点
* URL 抓取功能必须只允许 `http`/`https`（以避免 `file:`、`javascript:` 等协议）
* 应当设置超时并限制重定向。

不安全模式：

* `fetch(req.query.url)`
* 接受任意 URL 的“URL 预览”/“从 URL 导入”端点。

检测提示：

* 搜索 URL 源自用户/数据库的 `fetch(`、`axios(`、`got(`、`request(`、`node-fetch` 使用。
* 审查 webhook 测试器、预览器、图片抓取器。

修复：

* 强制协议白名单、主机白名单、DNS/IP 解析检查、超时和重定向策略。
* 考虑在基础设施层面进行网络出口控制。

备注：

* OWASP SSRF 防护指引提供了标准控制和常见陷阱。（[OWASP Cheat Sheet Series][7]）

---

### EXPRESS-ERROR-001：错误处理不得在生产环境泄露敏感细节

严重性：低

要求：

* 应当在中间件末尾定义集中式错误处理器（`app.use((err, req, res, next) => ...)`）。
* 生产环境必须避免向客户端返回堆栈跟踪、内部错误消息或密钥。
* 应当在服务端记录错误日志并进行适当的脱敏。
* 应当确保应用以生产设置运行，使默认行为不泄露细节。
* 生产环境的错误消息中不得记录或返回密钥、环境变量、会话、cookie 等敏感信息。

不安全模式：

* 向客户端返回 `err.stack`。
* 在生产环境使用仅开发用的错误中间件。
* `NODE_ENV` 保持为 development，导致冗长的错误响应。

检测提示：

* 确认存在最终的错误处理中间件。
* 搜索 `res.status(500).send(err)` 或类似代码。
* 检查生产环境变量和启动脚本。

修复：

* 添加生产安全的错误处理器，返回通用消息并在内部记录细节。
* 确保环境配置为生产行为。

备注：

* Express 生产安全指引建议自定义错误处理。（[Express][1]）
* Express 错误处理文档描述了默认错误处理器的行为，以及生产模式如何影响暴露的内容。（[Express][11]）

---

### EXPRESS-AUTH-001：防止针对认证端点的暴力破解攻击

严重性：中

注意：这高度依赖具体应用，虽然值得提请用户注意，但如果没有额外的复杂配置很难修复。建议告知用户，如果用户请求协助实施方案，则引导他们了解可能的解决方案。

要求：

* 应当保护登录/认证端点免受暴力破解。
* 应当按以下方式限速：

  1. 每个用户名+IP 的连续失败尝试次数
  2. 一段时间窗口内每个 IP 的失败尝试次数

不安全模式：

* 登录尝试次数不限。

检测提示：

* 识别所有认证端点并检查是否有速率限制/节流。
* 搜索 `rate-limiter-flexible`、`express-rate-limit` 或网关策略。

修复：

* 实施速率限制/节流（应用层或边缘层）。Express 文档将 `rate-limiter-flexible` 指向为实现此方法的一种工具。（[Express][1]）

备注：

* OWASP Node.js 速查表也建议防范暴力破解。（[OWASP Cheat Sheet Series][8]）

---

### EXPRESS-DEPS-001：依赖与补丁卫生（Express + Node + 关键中间件）

严重性：中 / 低

注意：`npm audit` 经常会返回大量无足轻重的“漏洞”，这些漏洞实际上并不重要。应只关注 Express 或其他极为关键的包，忽略开发工具、打包器等中列出的包。

未经用户同意不要升级包。这可能会以意外方式破坏现有代码。相反，应告知他们过时的包。

要求：

* 必须让 Express 保持在受维护的版本线（避免 EOL 主版本）。
* 可以在 CI 和维护工作中使用 `npm audit`。
* 应当通过锁文件固定依赖，并仔细审查主版本升级。

不安全模式：

* 运行已 EOL 的 Express 版本（例如非常旧的主版本线）。
* 未经分诊就忽略 `npm audit` 发现。
* 未固定的依赖范围自动升级到不安全版本。

检测提示：

* 检查 `package.json` 和锁文件中的 `express` 版本及其他关键中间件版本。
* 检查 CI 流水线中是否有 `npm audit`/SCA 步骤。

修复：

* 升级到最新的稳定版 Express 并应用补丁。
* 添加自动化依赖扫描和升级流程。

备注：

* Express 生产安全指引强调依赖漏洞可能危及应用，并推荐 `npm audit`。（[Express][1]）
* 跟踪影响 Express 版本的安全问题（包括已知的开放重定向相关 CVE）。（[NVD][9]）

---

### EXPRESS-DOS-001：配置 DoS 防护（超时、限制、反向代理）

严重性：低

注意：根据所提供的应用上下文，可能很难判断应用是否运行在反向代理之后。可以告知用户或建议使用反向代理，但不要在他们主动提出之前尝试配置。这高度依赖部署环境。

要求：

* 在可行时应当使用反向代理提供缓存、负载均衡和过滤控制。
* 可以配置服务器/代理超时和连接限制，以减少 Slowloris 及类似 DoS 模式的暴露。
* 必须处理服务器/套接字错误，使畸形连接不会导致进程崩溃。（Express 应处理异常，但存在边界情况）

不安全模式：

* 公共 Node 服务器前没有反向代理，且全部使用默认值。
* 服务器/套接字对象上缺少错误处理器。
* 极为宽松的超时和无限制的请求体大小。

检测提示：

* 检查服务器创建（`http.createServer`、`https.createServer`）以及是否设置了超时。
* 检查代理/网关配置中的超时和最大请求体大小。

修复：

* 说明如何配置反向代理和超时、设置请求大小限制
* 添加健壮的错误处理中间件

备注：

* Node 的 HTTP DoS 安全指引讨论了使用反向代理和正确配置服务器超时。（[Node.js][15]）

---

### EXPRESS-NODE-INSPECT-001：不要在生产环境暴露 Node inspector

严重性：严重

注意：确保该检测对象确实位于生产路径中，而不仅仅是用于本地调试。

要求：

* 生产环境不得使用 `--inspect` 运行 Node（尤其不能绑定到非回环地址）。
* 必须确保 `NODE_OPTIONS` 或启动脚本不会在生产环境启用 inspector。
* 应当仅在本地进行防火墙/调试。

不安全模式：

* 生产环境中使用 `node --inspect=0.0.0.0:9229 app.js`。
* 容器/PM2/systemd 配置启用了 inspector。

检测提示：

* 在 Dockerfile、Procfiles、systemd 单元、PM2 配置、npm 脚本中搜索 `--inspect`。
* 检查 `NODE_OPTIONS`。

修复：

* 从生产启动命令中移除 inspector 标志；限制仅在本地开发使用。

备注：

* Node 安全指引讨论了 inspector 暴露风险（例如 DNS 重绑定），并建议不要在生产环境运行 inspector。（[Node.js][15]）

---

### EXPRESS-NODE-HTTP-001：不要在生产环境启用不安全的 HTTP 解析

严重性：高

注意：确保该检测对象确实位于生产路径中，而不仅仅是用于本地开发。

要求：

* 生产环境不得使用 Node 的 `insecureHTTPParser`。
* 可以建议配置前端代理规范化有歧义的请求，以降低请求走私风险。

不安全模式：

* 使用 `{ insecureHTTPParser: true }` 创建 HTTP 服务器。

检测提示：

* 在服务器创建代码中搜索 `insecureHTTPParser`。

修复：

* 移除不安全解析；依赖符合规范的解析并在边缘层规范化。

备注：

* Node 安全指引明确建议不要使用 `insecureHTTPParser`。（[Node.js][15]）

---

## 5) 实用扫描启发式（如何“排查”）

主动扫描 Express 代码库时，以下模式是高信号：

* TLS / 传输：

  * `app.listen(80` 且未提及反向代理；缺少 `helmet`；cookie 缺少 `secure`（[Express][1]）（注意这仅适用于面向 Web 的应用，内部应用很可能没有 TLS）
* 代理信任：

  * `app.set('trust proxy', true)`；使用 `req.ip`/`req.protocol`/`req.hostname` 的逻辑（[Express][2]）
* 安全头 / 指纹暴露：

  * 缺少 `helmet(`；缺少 `app.disable('x-powered-by')`（[Express][1]）
* Cookie / 会话：

  * `express-session` 缺少 `store`（MemoryStore 风险）、硬编码 `secret:`、缺少 `cookie: { secure/httpOnly/sameSite }`（[Express][1]）
  * `cookie-session` 存储大型对象或密钥（[Express][1]）
* 请求体解析限制：

  * 无 `limit`/`parameterLimit`/`depth` 的 `express.json()` 或 `express.urlencoded()`（[Express][5]）
* CSRF：

  * 使用 cookie 认证且无 CSRF 令牌/来源检查的 POST/PUT/PATCH/DELETE 路由（[OWASP Cheat Sheet Series][3]）
* 开放重定向：

  * `res.redirect(req.query.next)` 或类似代码（[Express][1]）
* XSS / HTML 输出：

  * 使用用户输入构建 HTML 的 `res.send(`；模板“安全”标志；`res.locals` 中的不受信任值（[Express][5]）
* 文件处理：

  * 路径源自请求的 `res.sendFile(` / `res.download(`；`express.static('uploads')`（[Express][5]）
* 注入：

  * 进入数据库调用的 SQL 字符串 + 模板字面量（[OWASP Cheat Sheet Series][6]）
  * `child_process.exec` / `execSync` / `shell: true`（[OWASP Cheat Sheet Series][14]）
* SSRF：

  * 向用户提供的 URL 发起出站 `fetch/axios/got`（[OWASP Cheat Sheet Series][7]）
* 暴力破解 / 滥用：

  * 缺少节流的认证端点；没有速率限制中间件（[Express][1]）
* 供应链：

  * 过时的 Express 版本；没有锁文件；没有 `npm audit` 工作流（[Express][1]）
* Node 运行时风险：

  * 生产脚本中的 `--inspect`；`insecureHTTPParser` 使用（[Node.js][15]）

始终尝试确认：

* 数据来源（不受信任 vs 受信任）
* 汇点类型（HTML/模板、SQL/NoSQL、子进程、文件系统、重定向、出站 HTTP）
* 存在的防护控制（验证、白名单、中间件、代理配置、头策略）
* 防护位于边缘层还是在应用代码中

---

## 6) 来源（访问于 2026-01-27）

主要 Express 文档：

* Express：生产最佳实践——安全：`https://expressjs.com/en/advanced/best-practice-security.html`（[Express][1]）
* Express：Behind Proxies（`trust proxy`）：`https://expressjs.com/en/guide/behind-proxies.html`（[Express][2]）
* Express 5.x API 参考（解析器、static、sendFile、redirect、cookies）：`https://expressjs.com/en/5x/api.html`（[Express][5]）
* Express：错误处理：`https://expressjs.com/en/guide/error-handling.html`（[Express][11]）

会话中间件文档：

* express-session 文档（cookie 标志、密钥轮换、会话固定缓解、MemoryStore 警告）：`https://expressjs.com/en/resources/middleware/session.html`（[Express][1]）

Node.js 和 npm 官方参考：

* Node.js——安全最佳实践（DoS、代理指引、inspector 风险、请求走私说明）：`https://nodejs.org/en/learn/getting-started/security-best-practices`（[Node.js][15]）
* npm 文档——`npm audit`：`https://docs.npmjs.com/cli/v9/commands/npm-audit/`（[npm Docs][16]）

OWASP Cheat Sheet Series：

* 会话管理：`https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][12]）
* CSRF 防护：`https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][3]）
* XSS 防护：`https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][4]）
* 输入验证：`https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][17]）
* SQL 注入防护：`https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][6]）
* 操作系统命令注入防御：`https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][14]）
* SSRF 防护：`https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][7]）
* 文件上传：`https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][13]）
* 未验证重定向：`https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][18]）
* HTTP 头：`https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][10]）

版本 / 漏洞公告：

* Express 包版本（npm）：`https://www.npmjs.com/package/express`
* Express 开放重定向公告（CVE）：`https://nvd.nist.gov/vuln/detail/CVE-2024-29041`（[NVD][9]）

[1]: https://expressjs.com/en/advanced/best-practice-security.html "Security Best Practices for Express in Production"
[2]: https://expressjs.com/en/guide/behind-proxies.html "Express behind proxies"
[3]: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html "Cross-Site Request Forgery Prevention - OWASP Cheat Sheet Series"
[4]: https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html "Cross Site Scripting Prevention - OWASP Cheat Sheet Series"
[5]: https://expressjs.com/en/5x/api.html "Express 5.x - API Reference"
[6]: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html "SQL Injection Prevention - OWASP Cheat Sheet Series"
[7]: https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html "Server Side Request Forgery Prevention - OWASP Cheat Sheet Series"
[8]: https://cheatsheetseries.owasp.org/cheatsheets/Nodejs_Security_Cheat_Sheet.html "Nodejs Security - OWASP Cheat Sheet Series"
[9]: https://nvd.nist.gov/vuln/detail/cve-2024-29041?utm_source=chatgpt.com "CVE-2024-29041 Detail - NVD"
[10]: https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html "HTTP Headers - OWASP Cheat Sheet Series"
[11]: https://expressjs.com/en/guide/error-handling.html "Express error handling"
[12]: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html "Session Management - OWASP Cheat Sheet Series"
[13]: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html "File Upload - OWASP Cheat Sheet Series"
[14]: https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html "OS Command Injection Defense - OWASP Cheat Sheet Series"
[15]: https://nodejs.org/en/learn/getting-started/security-best-practices "Node.js — Security Best Practices"
[16]: https://docs.npmjs.com/cli/v9/commands/npm-audit/ "npm-audit | npm Docs"
[17]: https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html "Input Validation - OWASP Cheat Sheet Series"
[18]: https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html "Unvalidated Redirects and Forwards - OWASP Cheat Sheet Series"
