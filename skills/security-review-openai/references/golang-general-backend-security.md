# Go（Golang）安全规范（Go 1.25.x、标准库、net/http）

本文档作为一份**安全规范**设计，用于支持：
1) 面向新 Go 代码的**默认安全的代码生成**。
2) 对既有 Go 代码的**安全审查/漏洞排查**（被动式“在工作中留意问题”和主动式“扫描仓库并报告发现”）。

本文件有意写成一组**规范性要求**（“MUST/SHOULD/MAY”）加上**审计规则**（不良模式长什么样、如何检测、如何修复/缓解）。

--------------------------------------------------------------------

## 0) 安全、边界与防滥用约束（必须遵守）

- 不得请求、输出、记录或提交机密（API 密钥、密码、私钥、会话 Cookie、JWT、含凭据的数据库 URL、签名密钥、客户端机密）。
- 不得通过禁用保护机制来“修复”安全问题（例如 `InsecureSkipVerify`、对公共模块设置 `GOSUMDB=off`、通配 CORS 加凭据、移除认证检查、禁用基于 Cookie 认证应用上的 CSRF 防御）。
- 审计时必须提供**基于证据的发现**：引用支撑该主张的文件路径、代码片段、构建/部署配置和具体值。
- 必须诚实对待不确定性：如果某项控制可能存在于基础设施中（反向代理、WAF、服务网格、平台配置），应报告为“应用代码中不可见；请在运行时/配置中核实”。
- 必须保持修复最小化、正确且生产安全；未经警示不得引入破坏性变更（尤其涉及认证/会话流程和代理）。

--------------------------------------------------------------------

## 1) 工作模式

### 1.1 生成模式（默认）
当被要求编写新的 Go 代码或修改既有代码时：
- 必须遵循本规范中的每一条 **MUST** 要求。
- 除非用户明确另有说明，否则应遵循每一条 **SHOULD** 要求。
- 必须优先使用默认安全的 API 和经过验证的库，而非自行编写安全代码。
- 必须避免引入新的危险汇点（shell 执行、动态模板执行、以 HTML 形式提供用户文件、不安全重定向、弱加密、无界解析等）。

### 1.2 被动审查模式（编辑时始终开启）
在 Go 仓库的任何位置工作时（即使用户未要求安全扫描）：
- 必须在所触及/邻近的代码中“留意”对本规范的违反。
- 应随问题出现提出，附简要说明和安全修复建议。

### 1.3 主动审计模式（明确扫描请求）
当用户要求“扫描”“审计”或“排查漏洞”时：
- 必须系统性地搜索代码库中违反本规范之处。
- 必须以结构化格式输出发现（见第 2.3 节）。

建议的审计顺序：
1) 构建/部署入口点：`main.go`、`cmd/*`、Dockerfile、Kubernetes 清单、systemd 单元、CI 工作流。
2) Go 工具链与依赖策略：Go 版本、模块、`go.mod/go.sum`、代理/sumdb 设置、govulncheck 使用。
3) 机密管理与配置加载（环境变量、文件、机密存储）+ 日志记录模式。
4) HTTP 服务器配置（超时、请求体限制、代理信任、安全响应头）。
5) 认证/授权边界、会话/Cookie 设置、令牌验证。
6) 基于 Cookie 认证的状态变更端点的 CSRF 防护。
7) 模板使用与输出编码（XSS），以及任何“从字符串渲染模板”的行为（SSTI）。
8) 文件处理（上传/下载/路径遍历/临时文件）、静态文件服务。
9) 注入汇点：SQL、操作系统命令执行、SSRF/出站请求、开放重定向。
10) 并发/资源耗尽（无界 goroutine/队列、缺少超时/上下文）。
11) 在安全敏感路径中使用 `unsafe`/`cgo`/`reflect`。
12) 调试/诊断端点（pprof/expvar/metrics）暴露。
13) 密码学使用（随机性、密码哈希）。

--------------------------------------------------------------------

## 2) 定义与审查指引

### 2.1 不可信输入（除非证明相反，否则视为攻击者可控）
示例包括：
- `*http.Request` 字段：`r.URL.Path`、`r.URL.RawQuery`、`r.Form`、`r.PostForm`、请求头、Cookie、`r.Body`
- 来自路由器的路径参数（包括从 URL 路径中提取的值）
- JSON/XML/YAML 请求体、multipart 表单部分、上传的文件
- 来自外部系统的任何数据（webhook、第三方 API、消息队列）
- 源自用户的任何持久化用户内容（数据库行）
- 在某些部署中可能受攻击者影响的配置值（上游代理设置的请求头、多租户系统中的环境变量）

### 2.2 状态变更请求
如果请求能够创建/更新/删除数据、改变认证/会话状态、触发副作用（购买、发送邮件、发送 webhook）或启动特权操作，则该请求属于状态变更请求。

### 2.3 必需的审计发现格式
对每个发现的问题，输出：

- 规则编号（Rule ID）：
- 严重性（Severity）：严重 / 高 / 中 / 低
- 位置（Location）：文件路径 + 函数/处理器名称 + 行号
- 证据（Evidence）：确切的代码/配置片段
- 影响（Impact）：可能出什么问题、谁能利用
- 修复（Fix）：安全变更（优先最小差异）
- 缓解（Mitigation）：如果立即修复困难时的纵深防御
- 误报说明（False positive notes）：不确定时应核实什么（边界配置、代理行为、认证假设）

--------------------------------------------------------------------

## 3) 安全基线：最低生产配置（生产环境必须遵守）

这是防止常见 Go 配置错误的最简“生产基线”。

### 3.1 工具链、补丁与依赖卫生（必须）
- 必须运行受支持的 Go 主版本并保持最新补丁版本。
- 必须将 Go 标准库补丁版本视为与安全相关（许多安全修复落在 `net/http`、`crypto/*`、解析包等标准库组件中）。
- 必须使用带已提交 `go.mod` 和 `go.sum` 的 Go 模块。
- 不得为公共模块禁用模块真实性机制（校验和数据库），除非你有受控的、有文档记录的替代方案。
- 必须在 CI 中运行 `govulncheck`（源码扫描和/或二进制扫描）并处理其发现。

### 3.2 HTTP 服务器基线（面向网络的服务必须）
如果程序提供 HTTP 服务（直接或通过基于 `net/http` 的框架）：
- 必须配置带显式超时和请求头限制的 `http.Server`。
- 必须设置请求体大小限制（按需全局和各路由）。
- 必须避免公开暴露诊断端点（pprof/expvar）。
- 应设置一组一致的响应安全头（或核实已在边缘设置）。
- 必须为签发的任何 Cookie 设置安全属性。
- 应对认证和高开销端点实现速率限制和滥用控制。

示意性基线骨架（根据你的项目调整）：
- 创建专用 mux（除非有意管理，否则避免隐式全局默认值）。
- 用以下内容包装处理器：panic 安全错误处理、请求 ID、日志记录、认证和限制。

--------------------------------------------------------------------

## 4) 规则（生成 + 审计）

每条规则包含：必需实践、不安全模式、检测提示和修复建议。

### GO-DEPLOY-001：保持 Go 工具链和标准库更新（安全版本）
严重性：中

注意：升级依赖和 Go 核心版本可能以不可预期的方式破坏项目。只关注安全关键的依赖；如注意到问题，告知用户而非自动升级。

要求：
- 必须运行受支持的 Go 主版本并及时应用补丁版本。
- 应把补丁版本视为与安全相关，即使你的应用代码没有变化。

不安全模式：
- 生产构建固定在无补丁流程的旧 Go 版本上。
- `golang:1.xx` 等 Docker 镜像或自定义基础镜像未定期更新。
- CI 流水线有意抑制 Go 更新。

检测提示：
- 检查 CI（`.github/workflows`、`gitlab-ci.yml` 等）中的 `go-version:` 或工具链设置。
- 检查 Dockerfile 中的 `FROM golang:` 标签。
- 检查 `go.mod` 的 `go` 指令及任何工具链固定设置。

修复：
- 升级到受支持 Go 版本的最新补丁。
- 添加自动检查（CI），当 Go 低于批准的最低版本时使构建失败。

说明：
- Go 定期发布包含跨标准库包安全修复的次版本。

---

### GO-SUPPLY-001：不得为公共依赖禁用 Go 模块真实性校验
严重性：高

要求：
- 必须对公共模块保持模块校验和验证启用。
- 应提交 `go.sum` 并将其变更视为安全敏感。
- 不得对公共模块使用不安全的模块获取设置。
- 可以为私有仓库使用 `GOPRIVATE`/`GONOSUMDB` 配置私有模块行为，但必须做到范围狭窄且有意为之。

不安全模式：
- 在 CI 或生产构建环境中对公共模块设置 `GOSUMDB=off`。
- `GONOSUMDB=*` 或实际上禁用验证的过宽模式。
- 对公共模块使用 `GOINSECURE=*` 或过宽的 `GOINSECURE` 模式。
- 无明确策略地到处使用 `GOPROXY=direct`。

检测提示：
- 在构建配置中搜索 `GOSUMDB`、`GONOSUMDB`、`GOINSECURE`、`GOPROXY`、`GOPRIVATE`。
- 查找推荐“为了让构建通过”而禁用校验和数据库的文档/脚本。

修复：
- 恢复公共模块验证的默认设置。
- 对于私有模块：
  - 设置 `GOPRIVATE=your.private.domain/*`
  - 配置内部代理或直接获取，并将 `GONOSUMDB` 限制为仅私有模式。

说明：
- 禁用校验和验证会移除针对定向攻击或受污染上游交付的重要完整性层级。

---

### GO-CONFIG-001：机密必须外部化，绝不记录或提交
严重性：高（若凭据被提交则为严重）

要求：
- 必须从环境变量、机密管理器或权限受限的安全配置文件加载机密。
- 不得在 Go 源码、可能进入生产的测试夹具或构建参数中硬编码机密。
- 不得记录机密或含凭据的完整连接字符串。
- 生产环境中必需机密缺失时应默认安全失败（fail closed）。

不安全模式：
- 包含令牌/密钥/密码的字符串常量。
- `.env` 文件或含机密且已提交到仓库的配置文件。
- 记录 `os.Environ()`、转储完整配置或打印 DSN。

检测提示：
- 搜索可疑字面量（`API_KEY`、`SECRET`、`PASSWORD`、`Authorization:`）。
- 检查配置加载器和日志记录语句。
- 检查 CI 日志或调试打印路径。

修复：
- 将机密移至机密存储/环境变量。
- 在日志中脱敏敏感字段。
- 在 CI 和 pre-commit 中添加机密扫描。

---

### GO-HTTP-001：HTTP 服务器必须设置超时和 MaxHeaderBytes
严重性：高（DoS 风险）

要求：
- 必须设置 `ReadHeaderTimeout`，并应根据服务情况设置 `ReadTimeout`、`WriteTimeout`、`IdleTimeout`。
- 必须将 `MaxHeaderBytes` 设置为适合你应用的合理限制。
- 生产环境中的互联网面向服务器不得依赖超时为零值的默认值。

不安全模式：
- 使用默认 `http.Server`（无显式超时）的 `http.ListenAndServe(":8080", handler)`。
- `&http.Server{}` 超时全部为零。
- 缺少 `MaxHeaderBytes`。

检测提示：
- 搜索 `http.ListenAndServe(`、`ListenAndServeTLS(`、`Server{` 并检查所配置的字段。
- 检查反向代理；即使有代理，应用层超时仍然重要。

修复：
- 使用 `http.Server{ReadHeaderTimeout: ..., ReadTimeout: ..., WriteTimeout: ..., IdleTimeout: ..., MaxHeaderBytes: ...}`。
- 按端点类型校准超时（流式与 JSON API）。

说明：
- net/http 文档说明这些超时存在，零值/负值表示“无超时”；生产服务应选择显式值。

---

### GO-HTTP-002：请求体和 multipart 解析必须限制大小
严重性：中（DoS 风险；上传密集型应用可为高）

要求：
- 必须对接受请求体的端点强制全局最大请求体大小。
- 必须强制严格的 multipart 上传限制，避免无界表单解析。
- 当某些端点合法需要更大请求体时，应强制按路由限制。
- 应将上游（代理）限制作为纵深防御设置。

不安全模式：
- 在无大小上限的情况下用 `io.ReadAll(r.Body)` 读取 `r.Body`。
- 以过大限制（或忘记大小控制）调用 `r.ParseMultipartForm(...)`。
- 接受无文件大小、部件数量或总请求体大小限制的文件上传。

检测提示：
- 搜索 `io.ReadAll(r.Body)`、`json.NewDecoder(r.Body)`、`ParseMultipartForm`、`FormFile`、`multipart`。
- 查找缺少 `http.MaxBytesReader` 或等效的逐处理器限制。
- 查找“上传”端点并检查限制。

修复：
- 在解析前用 `http.MaxBytesReader(w, r.Body, maxBytes)` 包装请求体。
- 对于 multipart，设置保守限制并显式校验文件大小/部件数量。
- 除应用限制外，设置代理限制（例如在入口处）。

说明：
- 存在与 multipart/form 解析中过度资源消耗相关的已知漏洞类别和建议；将无界解析视为安全问题。

---

### GO-DEPLOY-002：诊断端点（pprof/expvar/metrics）不得公开暴露
严重性：高

注意：此规则仅适用于生产配置。这些端点常用于调试或开发端点。如发现，确认其是否可从实际生产部署到达。

要求：
- 不得在无强访问控制的公共互联网面向监听器上暴露 `net/http/pprof` 处理器。
- 应在单独的、仅内部使用的监听器（回环/VPC 专用）上运行诊断并需要认证。
- 必须审查诊断端点会揭示什么（堆栈跟踪、内存、命令行、环境变量、内部 URL）。

不安全模式：
- 在带公共 mux 的服务器二进制中副作用导入 `import _ "net/http/pprof"`。
- `/debug/pprof/*` 无需认证即可访问。
- `/debug/vars`（expvar）无需认证即可访问。

检测提示：
- 搜索 `net/http/pprof` 导入（包括空白导入）。
- 搜索路由前缀 `/debug/pprof`、`/debug/vars`。
- 检查是否使用 `http.DefaultServeMux` 以及是否有调试处理器全局注册。

修复：
- 从生产构建中移除诊断，或将其绑定到仅内部监听的监听器。
- 添加强认证/授权（并理想情况下添加网络级限制）。

说明：
- pprof 通常因其在 `/debug/pprof/` 下注册 HTTP 处理器的副作用而被导入。

---

### GO-HTTP-003：反向代理与转发请求头信任必须显式化
严重性：高（认证、URL 生成、日志/审计正确性）

要求：
- 如果在反向代理后面，必须定义哪个代理受信任以及客户端 IP/协议/主机如何推导。
- 不得信任来自开放互联网的 `X-Forwarded-For`、`X-Forwarded-Proto`、`Forwarded` 或类似请求头。
- 必须确保“安全 Cookie”逻辑、重定向和绝对 URL 生成不依赖可伪造的请求头。

不安全模式：
- 未验证代理边界就使用 `r.Header.Get("X-Forwarded-For")` 作为客户端 IP。
- 未确认来自受信任代理就从 `X-Forwarded-Proto` 推导“是否为 HTTPS”。
- 未做白名单就使用转发的 `Host` 值生成密码重置链接。

检测提示：
- 搜索 `X-Forwarded-For`、`X-Forwarded-Proto`、`Forwarded`、`Real-IP` 及任何自定义“客户端 IP”辅助函数。
- 检查入口/代理配置；如不可见，标记为“在边缘核实”。

修复：
- 在边缘和应用中强制代理信任：
  - 仅接受来自已知代理 IP 段的转发请求头。
  - 在可用时优先使用平台提供的机制。
- 生成外部链接时，使用配置的、经白名单允许的规范源（而非请求的 Host 请求头）。

---

### GO-HTTP-004：应设置安全响应头（在应用中或边缘处）
严重性：中

要求（面向浏览器的典型 Web 应用）：
- 应设置：
  - 适合应用的 `Content-Security-Policy`（CSP）。注意：最重要的是设置 CSP 的 script-src。所有其他指令没有那么重要，为开发便利通常可以省略。
  - `X-Content-Type-Options: nosniff`
  - 点击劫持防护（`X-Frame-Options` 和/或 CSP 的 `frame-ancestors`）
  - 适当时的 `Referrer-Policy` 和 `Permissions-Policy`
- 必须确保 Cookie 具有安全属性（见 GO-HTTP-005）。

注意：
- 这些响应头可通过反向代理/CDN 设置；如果在应用代码中不可见，报告为“在边缘核实”。

不安全模式：
- 面向浏览器的应用在任何地方（应用或边缘）都没有安全响应头。
- 渲染不可信内容的应用缺少 CSP。

检测提示：
- 搜索设置响应头的中间件：`w.Header().Set("Content-Security-Policy", ...)` 等。
- 搜索设置响应头的反向代理配置。

修复：
- 在 Go 中添加集中式响应头中间件，或在边缘配置。
- 保持 CSP 现实可行；尽量避免 `unsafe-inline`。

---

### GO-HTTP-005：生产环境中 Cookie 必须使用安全属性
严重性：中

要求（生产环境、HTTPS）：
- 必须对携带认证/会话状态的 Cookie 设置 `Secure`。重要说明：仅在配置了 TLS 的生产环境中设置 `Secure`。在本地开发环境通过 HTTP 运行时，不要对 Cookie 设置 `Secure` 属性。应根据应用是否以生产模式运行来条件性地执行此操作。还应包含一个类似 `SESSION_COOKIE_SECURE` 的属性，可在通过 HTTP 测试时禁用安全 Cookie。
- 必须对认证/会话 Cookie 设置 `HttpOnly`。
- 应默认设置 `SameSite=Lax`（如兼容则为 `Strict`），仅在必要时使用 `None`（且仅与 `Secure` 搭配）。
- 应设置适合应用的有界生存期（`Max-Age`/`Expires`）。

不安全模式：
- 在 HTTPS 部署中设置不带 `Secure` 的认证/会话 Cookie。
- 会话标识符的 Cookie 不带 `HttpOnly`。
- 基于 Cookie 认证的应用使用 `SameSite=None` 而无强 CSRF 策略。

检测提示：
- 搜索 `http.SetCookie`、`&http.Cookie{`、`Set-Cookie`。
- 检查认证/会话代码中的 Cookie 标志。

修复：
- 在 `http.Cookie` 上设置正确的字段并集中化 Cookie 创建。

说明：
- SameSite 是纵深防御，不能替代基于 Cookie 认证应用的 CSRF 防护。

---

### GO-HTTP-006：基于 Cookie 认证的状态变更端点必须受 CSRF 保护
严重性：高

- 重要说明：如果认证不使用 Cookie（例如纯 Authorization 请求头中的 Bearer 令牌且无环境 Cookie），这些端点不存在 CSRF 风险。

要求：
- 必须保护所有依赖 Cookie 认证的状态变更端点（POST/PUT/PATCH/DELETE）。
- 应使用经过充分测试的 CSRF 库/中间件，而非自行实现。
- 可以使用额外防御（Origin/Referer 检查、Fetch Metadata、SameSite Cookie），但对基于 Cookie 认证的应用，令牌仍是主要防御。
如果令牌不切实际，或对于小型应用：
* 至少必须要求设置一个自定义请求头并将会话 Cookie 设置为 SESSION_COOKIE_SAMESITE=lax，因为这是除要求表单令牌之外最强的方法，且可能更容易实现。

不安全模式：
- 变更状态且无 CSRF 检查的基于 Cookie 认证的 JSON 端点。
- 使用 GET 执行状态变更操作。

检测提示：
- 枚举所有非 GET 路由并识别认证机制。
- 查找 CSRF 中间件使用情况；如缺失，在面向浏览器的应用中视为可疑。

修复：
- 添加 CSRF 中间件并确保其覆盖所有状态变更路由。
- 如果服务是面向非浏览器客户端的 API，避免 Cookie 认证；使用 Authorization 请求头。

---

### GO-HTTP-007：CORS 必须显式且最小权限
严重性：中（与凭据搭配配置错误时为高）

要求：
- 如果不需要 CORS，必须保持其禁用。
- 如果需要 CORS：
  - 必须将可信来源列入白名单（不反射任意来源）
  - 必须谨慎处理带凭据的请求；不得将宽泛来源与 Cookie 组合
  - 应限制允许的方法/请求头

不安全模式：
- `Access-Control-Allow-Origin: *` 与 Cookie（`Access-Control-Allow-Credentials: true`）搭配。
- 未经验证地反射 `Origin`。

检测提示：
- 搜索 `Access-Control-Allow-` 响应头设置。
- 搜索 CORS 中间件配置。

修复：
- 实现严格的来源白名单和最小的方法/请求头。
- 确保除非必要，基于 Cookie 认证的端点不跨源暴露。

---

### GO-XSS-001：使用 html/template，避免用不可信数据绕过自动转义
严重性：高

要求：
- 必须使用 `html/template` 进行 HTML 渲染（而非 `text/template`）。
- 不得将不可信数据转换为“受信任”的模板类型（`template.HTML`、`template.JS`、`template.URL` 等）。
- 应保持模板静态且由开发人员控制；将动态模板视为高风险。
- 除非明确有意且经过安全沙箱隔离，不得将用户上传的 HTML/JS 作为活动内容提供。

不安全模式：
- 使用 `text/template` 生成 HTML。
- 使用 `template.HTML(userInput)` 或类似的类型包装器。
- 将未转义的用户内容直接写入 HTML 响应。

检测提示：
- 搜索 `text/template`、`template.New(...).Parse(...)` 及 `template.HTML(` 等类型包装器。
- 检查以字符串拼接返回 HTML 的处理器。

修复：
- 使用 `html/template` 并将不可信数据作为数据（而非标记）传递。
- 如果必须允许受限 HTML，使用经审查的 HTML 消毒器，并仍对属性/URL 保持谨慎。

---

### GO-SSTI-001：绝不解析/执行来自不可信输入的模板（SSTI）
严重性：严重

要求：
- 不得对受不可信输入影响的模板文本调用 `template.Parse`/`template.ParseFiles`/`template.New(...).Parse(...)`。
- 必须将“用户自定义模板”视为特殊的高风险设计：
  - 必须使用重度沙箱和严格白名单
  - 如确实需要，必须隔离执行（进程/容器边界）

不安全模式：
- `tmpl := template.Must(template.New("x").Parse(r.FormValue("tmpl")))`
- 从上传/数据库条目中读取模板并在与服务器代码相同的信任域中执行。

检测提示：
- 搜索 `.Parse(` 并追踪模板字符串的来源。
- 查找“自定义邮件模板”“用户主题模板”等。

修复：
- 替换为安全的替换机制（无代码执行）。
- 如果模板必须由用户控制，积极进行隔离和沙箱。

---

### GO-PATH-001：防止路径遍历和不安全的文件服务
严重性：高

要求：
- 未经严格验证和基础目录强制，不得将用户控制的路径传给 `os.Open`、`os.ReadFile`、`http.ServeFile` 或 `http.FileServer`。
- 必须将 `..`、绝对路径和操作系统特定的路径技巧视为恶意输入。
- 应将用户上传存储在任意静态 Web 根目录之外；通过受控处理器提供。
- 必须避免敏感文件树的目录列表。

不安全模式：
- `http.ServeFile(w, r, r.URL.Query().Get("path"))`
- 未检查结果是否保持在 `baseDir` 下的 `os.Open(filepath.Join(baseDir, userPath))`
- 提供项目根目录或用户可写目录的 `http.FileServer(http.Dir("."))`

检测提示：
- 搜索 `ServeFile(`、`FileServer(`、`http.Dir(`、`os.Open(`、`ReadFile(`、`filepath.Join(`。
- 追踪路径组件是否来自请求/数据库。

修复：
- 使用映射到服务器端路径的文件标识符（例如数据库 ID）白名单。
- 在清理和拼接后强制执行基础目录包含关系。
- 除非明确有意，以下载方式提供活动格式（`Content-Disposition: attachment`）。

---

### GO-UPLOAD-001：文件上传必须验证、安全存储、安全提供
严重性：高

要求：
- 必须强制上传大小限制（应用 + 边缘）。
- 必须使用白名单和内容检查验证文件类型（而非仅扩展名）。
- 应尽可能将上传存储在可执行/静态根目录之外。
- 应生成服务器端文件名（随机 ID），不信任原始名称。
- 除非明确有意，必须以安全方式提供潜在活动格式（下载附件）。

不安全模式：
- 接受任意文件类型并内联返回。
- 使用用户提供的文件名作为存储路径。
- 缺少大小/类型验证。

检测提示：
- 搜索 `multipart`、`FormFile`、`ParseMultipartForm`、`io.Copy` 到磁盘。
- 检查文件的存储位置及提供方式。

修复：
- 实现白名单验证 + 安全存储 + 安全提供。
- 在适用时添加扫描/隔离工作流。

---

### GO-INJECT-001：防止 SQL 注入（参数化查询 / ORM）
严重性：高

要求：
- 必须使用参数化查询或在底层参数化的 ORM。
- 不得通过字符串拼接 / `fmt.Sprintf` / 字符串插值用不可信输入构建 SQL。

不安全模式：
- `fmt.Sprintf("SELECT ... WHERE id=%s", r.URL.Query().Get("id"))`
- `query := "UPDATE users SET role='" + role + "' WHERE id=" + id`

检测提示：
- 搜索 `SELECT`、`INSERT`、`UPDATE`、`DELETE` 并检查查询字符串的构建方式。
- 追踪不可信数据进入 `db.Query`、`db.Exec`、`QueryRow` 等。

修复：
- 替换为占位符（`?`、`$1` 等）并单独传递参数。
- 在使用前验证并类型检查 ID。

---

### GO-INJECT-002：防止操作系统命令注入；避免用不可信输入调用 shell
严重性：严重到高（取决于暴露面）

要求：
- 必须避免使用攻击者控制的字符串执行外部命令。
- 如果必须使用子进程：
  - 必须使用带参数列表的 `exec.CommandContext`（而非 `sh -c`）。
  - 不得将不可信输入传给 shell（`bash -c`、`sh -c`、PowerShell）。
  - 应对任何可变部分（子命令、标志、文件名）使用严格白名单。
- 必须假设 CLI 工具可能将攻击者控制的参数解释为标志或特殊值。

不安全模式：
- `exec.Command("sh", "-c", userString)`
- `exec.Command("bash", "-c", fmt.Sprintf("tool %s", user))`
- 为获取用户提供 glob 的 glob 展开而调用 shell。

检测提示：
- 搜索 `os/exec`、`exec.Command(`、`CommandContext(`、`"sh"`、`"bash"`、`"-c"`。
- 追踪不可信输入进入命令名/参数。

修复：
- 使用库 API 而非子进程。
- 硬编码命令并对参数进行白名单/验证。
- 如果无法避免 shell，进行稳健转义并视为高风险（优先避免）。

说明：
- Go 的 `os/exec` 包有意不调用 shell；引入 `sh -c` 会重新引入 shell 注入风险。

---

### GO-SSRF-001：防止出站 HTTP 请求中的 SSRF
严重性：中（云/局域网环境中为高）

- 注意：对于小型独立项目，这一点不那么重要。在部署到局域网或与其他服务监听同一服务器时最重要。

要求：
- 必须将发往用户提供 URL 的出站请求视为高风险。
- 应对任何受用户影响的 URL 获取进行主机/域名白名单。
- 应阻止访问 localhost/私有 IP 段/链路本地地址和云元数据端点。
- 必须将协议限制为 `http`/`https`（不允许 `file:`、`gopher:` 等）。
- 必须设置客户端超时并限制重定向。

不安全模式：
- `http.Get(r.URL.Query().Get("url"))`
- 获取任意 URL 的“URL 预览”/“webhook 测试”端点。

检测提示：
- 搜索 `http.Get`、`client.Do` 以及从请求/数据库派生的 URL 值。
- 识别获取远程资源的功能。

修复：
- 严格解析 URL；强制协议和白名单主机名。
- 解析 DNS 并强制执行 IP 段限制（注意 DNS 重绑定）。
- 设置超时，除非需要否则禁用重定向，并限制响应大小。

---

### GO-HTTPCLIENT-001：出站 HTTP 客户端必须设置超时并关闭请求体
严重性：高（DoS 和资源耗尽）

要求：
- 必须在 `http.Client` 使用上设置整体超时（或通过上下文 + 传输层超时设置等效的按请求截止时间）。
- 必须确保所有成功请求都调用 `resp.Body.Close()`（通常在错误检查后立即 `defer resp.Body.Close()`）。
- 应限制响应体读取（不对无界响应执行 `io.ReadAll`）。
- 应对安全敏感获取（SSRF、认证流程）限制重定向。

不安全模式：
- 对受用户影响的目标使用无超时策略的 `http.DefaultClient`/`http.Get`。
- 缺少 `defer resp.Body.Close()` 导致资源泄漏。
- 无限制的 `io.ReadAll(resp.Body)`。

检测提示：
- 搜索 `http.Get(`、`http.Post(`、无 `Timeout` 的 `client := &http.Client{}`、`client.Do(` 及缺失的关闭。
- 搜索 `io.ReadAll(resp.Body)`。

修复：
- 使用带超时的已配置客户端。
- 始终关闭响应体。
- 对大型/不可信响应使用有界读取器（`io.LimitReader`）。

说明：
- net/http 包将 `DefaultClient` 暴露为零值 `http.Client`，除非配置，否则很容易导致“无超时”行为。

---

### GO-REDIRECT-001：防止开放重定向
严重性：中（涉及认证流程时可为高）

要求：
- 必须验证从不可信输入派生的重定向目标（`next`、`redirect`、`return_to`）。
- 应只优先使用同站相对路径。
- 验证失败时应回退到安全默认值。

不安全模式：
- 无验证的 `http.Redirect(w, r, r.URL.Query().Get("next"), http.StatusFound)`。

检测提示：
- 搜索 `http.Redirect(` 并检查 location 的来源。

修复：
- 对内部路径或已知域名进行白名单。
- 除非明确需要且已列入白名单，否则拒绝绝对 URL。

---

### GO-CRYPTO-001：密码学随机性必须来自 crypto/rand
严重性：高（用于认证/会话令牌或密钥时为严重）

要求：
- 必须对以下内容使用 `crypto/rand`：
  - 会话 ID、密码重置令牌、API 密钥、CSRF 令牌、nonce
  - 加密密钥、签名密钥、需要时的盐
- 不得将 `math/rand` 用于任何安全敏感值。
- 应使用在可用时能生成足够强度令牌的内置辅助函数。

不安全模式：
- `math/rand.Seed(time.Now().UnixNano())` 后跟用于认证或会话的令牌生成。
- 使用基于 `math/rand` 构建的类 UUIDv4 构造。

检测提示：
- 在涉及认证/会话/令牌流程的代码中搜索 `math/rand`、`rand.Seed`、`rand.Intn`。
- 搜索自定义令牌生成器。

修复：
- 切换到 `crypto/rand`（`rand.Reader`、`rand.Read` 或安全令牌辅助函数）。
- 确保足够的熵并使用 URL 安全编码。

说明：
- crypto/rand 包提供安全随机性 API 和令牌生成辅助函数。

---

### GO-AUTH-001：密码存储必须使用自适应哈希（bcrypt/argon2id）和安全比较
严重性：高

要求：
- 必须使用自适应密码哈希函数（bcrypt 或 argon2id）对密码进行哈希。
- 不得存储明文密码或密码的可逆加密。
- 在相关时必须以恒定时间比较机密（令牌、MAC、API 密钥），以减少时序泄漏。
- 应确保密码策略不超过算法约束（例如 bcrypt 有输入长度限制；妥善处理长密码短语）。

不安全模式：
- 将 `sha256(password)` 存储为密码哈希。
- 明文密码存储。
- 在时序敏感场景中用 `==` 比较机密。

检测提示：
- 搜索对密码使用 `sha1`、`sha256`、`md5`。
- 搜索 `bcrypt`/`argon2` 使用情况；如缺失，予以怀疑。
- 搜索对令牌/API 密钥的 `==` 比较。

修复：
- 使用 `bcrypt.GenerateFromPassword`/`CompareHashAndPassword` 或带推荐参数的 argon2id。
- 比较 MAC/令牌时使用恒定时间比较辅助函数。

说明：
- Go 在 `golang.org/x/crypto/bcrypt` 中提供 bcrypt，在 `crypto/subtle` 中提供恒定时间比较。

---

### GO-CONC-001：数据竞争和并发危险必须视为与安全相关
严重性：中到高（取决于竞争影响什么）

要求：
- 必须对安全敏感服务在 CI 中使用竞态检测器运行测试（`go test -race`）。
- 必须修复检测到的竞争；未经深入论证不得抑制。
- 应将处理器中的共享可变状态视为高风险；强制同步或避免共享可变性。

不安全模式：
- 无互斥锁保护的、被多个 goroutine 变更的全局 map/slice。
- 存储在无并发保护的全局变量中的缓存或认证/会话状态。
- 对授权状态的竞争性访问（可导致绕过或不一致的执行）。

检测提示：
- 搜索处理器中使用的 `var someMap = map[...]...`。
- 查找缺失的 `sync.Mutex`、`sync.Map`、channel 或其他同步机制。
- 确保 CI 包含 `-race` 并运行相关测试。

修复：
- 添加适当的同步或重新设计以避免共享可变状态。
- 添加竞态测试并持续运行。

说明：
- Go 竞态检测器只能发现已执行代码路径中发生的竞争；改进测试覆盖率并在可行时使用 `-race` 运行真实负载。

---

### GO-UNSAFE-001：unsafe/cgo 的使用必须最小化并像内存不安全代码一样审计
严重性：高（高风险代码路径中为严重）

要求：
- 除非绝对必要，应避免在应用代码中导入 `unsafe`。
- 如果使用 `unsafe`，必须将其视为“手动内存安全”，需要仔细审查和测试覆盖。
- 如果使用 `cgo`，必须将 C/C++ 边界视为内存不安全；在 C 侧应用安全编码实践并尽可能隔离。

不安全模式：
- 在解析、序列化、认证或网络代码中广泛使用 `unsafe.Pointer` 转换。
- 未经沙箱即将 `cgo` 用于解析或安全边界。

检测提示：
- 搜索 `import "unsafe"`、`unsafe.Pointer`、`// #cgo`、`import "C"`。
- 优先审查 unsafe 触及不可信输入之处。

修复：
- 尽可能用安全的标准库替代方案替换 unsafe/cgo 使用。
- 将不安全代码隔离在小型、经过充分测试的模块中，并带模糊/竞态测试。

说明：
- unsafe 包明确提供绕过 Go 类型安全保证的操作。

--------------------------------------------------------------------

## 5) 实用扫描启发式（如何“排查”）

主动扫描时，使用这些高信号模式：

工具链与依赖：
- `FROM golang:`（Dockerfile）、`go-version:`（CI）、`toolchain go`（go.mod）、固定的旧版本
- `GOSUMDB=off`、`GOINSECURE`、`GONOSUMDB`、`GOPROXY=direct`
- `go.mod` 中指向 fork/路径的 `replace` 指令
- CI 中缺少 `govulncheck`

HTTP 服务器加固：
- 缺少超时的 `http.ListenAndServe(`、`ListenAndServeTLS(`、`&http.Server{`
- `ReadHeaderTimeout: 0`、`ReadTimeout: 0`、`WriteTimeout: 0`、`IdleTimeout: 0`、缺少 `MaxHeaderBytes`

请求体解析 / DoS：
- 无大小上限的 `io.ReadAll(r.Body)`、`json.NewDecoder(r.Body)`
- 无显式限制的 `ParseMultipartForm`、`FormFile`、`multipart.NewReader`
- 缺少 `http.MaxBytesReader`

调试暴露：
- `import _ "net/http/pprof"`
- `/debug/pprof`、`/debug/vars`

模板 / XSS / SSTI：
- 用于 HTML 输出的 `text/template`
- 带用户控制数据的 `template.HTML(`、`template.JS(`、`template.URL(`
- 对用户控制字符串的 `.Parse(`

文件：
- 带用户路径的 `http.ServeFile(`
- 指向仓库根目录或上传目录的 `http.FileServer(http.Dir(`
- 无包含关系检查的 `os.Open(filepath.Join(base, user))`

注入：
- 用 `fmt.Sprintf`、`db.Query/Exec` 附近的字符串拼接构建 SQL
- `exec.Command("sh","-c", ...)`、`exec.Command("bash","-c", ...)`

SSRF / 出站 HTTP：
- URL 来自请求/数据库的 `http.Get(userURL)`、`client.Do(req)`
- 缺少客户端超时、缺少 `resp.Body.Close()`、无界的 `io.ReadAll(resp.Body)`

密码学：
- 令牌/会话生成中的 `math/rand`
- `InsecureSkipVerify: true`
- 用 `sha256`/`md5` 而非 bcrypt/argon2 进行密码哈希

并发：
- 无锁的处理器对共享 map/slice 的变更
- CI 缺少 `go test -race`

始终尝试确认：
- 数据来源（不可信与可信）
- 汇点类型（模板/SQL/子进程/文件/http）
- 存在的防护控制（限制、验证、白名单、中间件、网络控制）

--------------------------------------------------------------------

## 6) 来源（访问于 2026-01-28）

主要 Go 文档：
- Go 安全政策 — https://go.dev/doc/security/policy
- Go 版本历史（补丁版本中的安全修复）— https://go.dev/doc/devel/release
- Go 1.25 发布说明 — https://go.dev/doc/go1.25
- net/http（服务器超时、MaxHeaderBytes、DefaultClient）— https://pkg.go.dev/net/http
- html/template（自动转义和受信任模板假设）— https://pkg.go.dev/html/template
- crypto/tls（MinVersion 默认值、InsecureSkipVerify 警告）— https://pkg.go.dev/crypto/tls
- crypto/rand（安全随机性、令牌辅助函数）— https://pkg.go.dev/crypto/rand
- crypto/subtle（恒定时间比较）— https://pkg.go.dev/crypto/subtle
- os/exec（默认不调用 shell；命令执行指引）— https://pkg.go.dev/os/exec
- unsafe（绕过类型安全）— https://go.dev/src/unsafe/unsafe.go
- net/http/pprof（调试端点）— https://pkg.go.dev/net/http/pprof
- cmd/go（通过 go.sum/校验和数据库的模块认证；GOINSECURE 等环境变量）— https://pkg.go.dev/cmd/go
- 模块镜像与校验和数据库发布（Go 博客）— https://go.dev/blog/module-mirror-launch
- govulncheck 文档 — https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck
- Go 竞态检测器文档 — https://go.dev/doc/articles/race_detector
- bcrypt（密码哈希）— https://pkg.go.dev/golang.org/x/crypto/bcrypt
- Go 漏洞条目示例（multipart 资源消耗）— https://pkg.go.dev/vuln/GO-2023-1569

OWASP 速查表系列（通用 Web 安全）：
- 会话管理 — https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- CSRF 防护 — https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
- SSRF 防护 — https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
- XSS 防护 — https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
- HTTP 安全响应头 — https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html
