# Flask（Python）Web 安全规范（Flask 3.1.x，Python 3.x）

本文档定位为一份**安全规范**，用于支撑：
1) 新 Flask 代码的**安全默认代码生成**。
2) 现有 Flask 代码的**安全审查 / 漏洞搜寻**（被动"工作时留意问题"和主动"扫描代码库并报告发现"）。

它有意写成一组**规范性要求**（"MUST/SHOULD/MAY"）加上**审计规则**（不良模式长什么样、如何检测、如何修复/缓解）。

--------------------------------------------------------------------

## 0）安全、边界和反滥用约束（必须遵守）

- 不得请求、输出、记录或提交机密（API 密钥、密码、私钥、会话 Cookie、SECRET_KEY）。
- 不得通过禁用保护来"修复"安全问题（例如关闭 CSRF、放宽 CORS、禁用转义、禁用认证检查）。
- 审计时必须提供**基于证据的发现**：引用支持该主张的文件路径、代码片段和配置值。
- 必须诚实对待不确定性：如果某项保护可能存在于基础设施层（反向代理、WAF、CDN），应报告为"应用代码中不可见；请在运行时/配置处验证"。

--------------------------------------------------------------------

## 1）运行模式

### 1.1 生成模式（默认）
当被要求编写新 Flask 代码或修改现有代码时：
- 必须遵循本规范中的每一项 **MUST** 要求。
- 除非用户明确另有说明，应遵循每一项 **SHOULD** 要求。
- 必须优先选择安全默认的 API 和经过验证的库，而非自定义安全代码。
- 必须避免引入新的危险汇点（从字符串渲染模板、shell 执行、动态导入、不安全重定向、将用户文件作为 HTML 提供等）。

### 1.2 被动审查模式（编辑期间始终开启）
在 Flask 代码库的任何位置工作时（即使用户未要求安全扫描）：
- 必须"留意"所接触/附近代码中对本规范的违反。
- 应在问题出现时提及，并附简要说明 + 安全修复建议。

### 1.3 主动审计模式（明确扫描请求）
当用户要求"扫描""审计"或"搜寻漏洞"时：
- 必须系统性地搜索代码库中违反本规范之处。
- 必须以结构化格式输出发现（见 §2.3）。

建议的审计顺序：
1) 应用入口点 / 部署脚本 / Dockerfile / Procfile。
2) Flask 配置和环境处理。
3) 认证 + 会话 + Cookie。
4) CSRF 防护和状态变更路由。
5) 模板渲染和 XSS/SSTI。
6) 文件处理（上传 + 下载）和路径遍历。
7) 注入类别（SQL、命令执行、不安全反序列化）。
8) 出站请求（SSRF）。
9) 重定向处理（开放重定向）。
10) CORS 和安全响应头。

--------------------------------------------------------------------

## 2）定义与审查指引

### 2.1 不受信任的输入（除非证明相反，否则视为攻击者控制）
示例包括：
- `request.args`、`request.form`、`request.values`
- `request.get_json()`、`request.json`、`request.data`
- `request.headers`、`request.cookies`
- URL 路径参数（例如 `/user/<id>`）
- 来自外部系统的任何数据（Webhook、第三方 API、消息队列）
- 源自用户的任何持久化用户内容（数据库行）

### 2.2 状态变更请求
如果请求可以创建/更新/删除数据、改变认证/会话状态、触发副作用（购买、发送邮件、发送 Webhook）或发起特权操作，则该请求为状态变更请求。

### 2.3 要求的审计发现格式
对发现的每个问题，输出：

- 规则 ID：
- 严重性：严重 / 高 / 中 / 低
- 位置：文件路径 + 函数/路由名称 + 行号
- 证据：确切的代码/配置片段
- 影响：可能出什么问题、谁可以利用
- 修复：安全变更（优先最小差异）
- 缓解：如立即修复困难时的纵深防御
- 误报说明：不确定时应核实什么

--------------------------------------------------------------------

## 3）安全基线：最低生产配置（生产环境中的 MUST）

这是防止常见 Flask 错误配置的最小"生产基线"。

### 3.1 应用初始化模式（SHOULD）
应使用应用工厂（app factory）和基于环境的配置，使生产配置不被硬编码。

示例骨架（示意性；请根据项目调整）：
- 从环境 / 密钥存储加载配置。
- 生产环境中缺少关键设置时采取安全失败（fail closed）模式。

关键基线配置目标：
- `SECRET_KEY` 已设置且未被提交
- `SESSION_COOKIE_SECURE=True`（使用 HTTPS 时）重要说明：仅在配置了 TLS 的生产环境中设置 `Secure` 属性。当通过 HTTP 在本地开发环境中运行时，不要在 Cookie 上设置 `Secure` 属性。应根据应用是否在生产模式下运行来条件性设置。还应包含类似 `SESSION_COOKIE_SECURE` 的属性，以便在通过 HTTP 测试时禁用 `Secure` Cookie。
- `SESSION_COOKIE_HTTPONLY=True`
- `SESSION_COOKIE_SAMESITE='Lax'`（如兼容则为 `'Strict'`）
- 生产环境设置 `TRUSTED_HOSTS`
- 在应用或边缘层设置安全响应头（CSP 等）

--------------------------------------------------------------------

## 4）规则（生成 + 审计）

每条规则包含：要求做法、不安全模式、检测提示和补救措施。

### FLASK-DEPLOY-001：不得在生产环境中使用 Flask 的开发服务器
严重性：高（如用于生产环境）

要求：
- 不得将内置开发服务器部署为生产服务器。
- 必须在生产级 WSGI 服务器或托管平台（例如 gunicorn）之后运行。

不安全模式：
- 生产入口点中使用 `app.run(...)`。
- 生产环境中使用 `flask run` 的部署文档/脚本。

检测提示：
- 搜索 `app.run(`、`flask run`、`--debug`、`FLASK_DEBUG`、`FLASK_ENV=development`。
- 检查 Docker CMD/ENTRYPOINT、Procfile、systemd 单元、shell 脚本。

修复：
- 使用生产 WSGI 服务器（并将 Flask 保留为应用对象）。
- 确保开发服务器仅用于本地开发。

注意：
- 这些常在开发模式或本地测试中使用。这是允许的。只有明确用于生产入口点时才标记。

---

### FLASK-DEPLOY-002：生产环境必须禁用调试模式
严重性：严重

要求：
- 生产环境不得启用调试模式。
- 如交互式调试器暴露，必须将其等同于远程代码执行。

不安全模式：
- `app.run(debug=True)`
- 生产环境中使用 `flask run --debug`。
- 生产环境中通过环境变量/配置设置 `DEBUG=True`。

检测提示：
- 查找 `debug=True`、`FLASK_DEBUG=1`、`DEBUG = True`、`app.debug = True`。
- 查找非测试上下文中启用的 `TRAP_HTTP_EXCEPTIONS`/调试器设置。

修复：
- 确保调试仅在本地开发/测试中启用。
- 优先使用基于环境的开关和安全默认值。

注意：
- 这些常在开发模式或本地测试中使用。这是允许的。只有明确用于生产入口点时才标记。

---

### FLASK-CONFIG-001：SECRET_KEY 必须强随机、保密并安全轮换
严重性：高（生产环境中缺失且使用会话或签名时为严重）

要求：
- 生产环境必须设置强随机 `SECRET_KEY`。
- 必须将 `SECRET_KEY` 排除在源代码控制之外、排除在日志之外。
- 可以定期轮换密钥；可以使用 `SECRET_KEY_FALLBACKS` 支持轮换而不立即使现有会话失效，然后在轮换窗口结束后移除旧密钥。对于较小应用可能不需要，但对较大应用是良好实践。由于这可能使部署复杂化，建议由用户选择实施而非默认实施。

不安全模式：
- 生产环境缺少 `SECRET_KEY`。
- 仓库中硬编码 `SECRET_KEY`（包括测试密钥被误用于生产）。
- 记录或打印 `SECRET_KEY`。

检测提示：
- 搜索 `SECRET_KEY =`、`app.secret_key =`、`SECRET_KEY_FALLBACKS =`。
- 检查提交到仓库的 `.env` 文件。
- 检查配置模块中的常量。

修复：
- 从密钥管理器或环境变量加载。
- 添加轮换流程：
  - 设置新 `SECRET_KEY`
  - 暂时将旧密钥保留在 `SECRET_KEY_FALLBACKS` 中
  - 安全窗口结束后移除旧密钥。

备注：
- 如果应用使用 Flask 会话（默认基于 Cookie），`SECRET_KEY` 直接具有安全关键性。

---

### FLASK-SESS-001：生产环境中的会话 Cookie 必须使用安全属性
严重性：中

要求（生产环境、HTTPS）：
- 必须设置 `SESSION_COOKIE_SECURE=True`（Cookie 仅通过 HTTPS 传输）。注意：仅在配置了 TLS 的生产环境中设置 `Secure` 属性。当通过 HTTP 在本地开发环境中运行时，不要在 Cookie 上设置 `Secure` 属性。应根据应用是否在生产模式下运行来条件性设置。还应包含类似 `SESSION_COOKIE_SECURE` 的属性，以便在通过 HTTP 测试时禁用 `Secure` Cookie。
- 必须确保 `SESSION_COOKIE_HTTPONLY=True`（防止 JS 访问）。
- 应设置 `SESSION_COOKIE_SAMESITE='Lax'`（推荐）或与用户体验兼容的 `'Strict'`。
- 除非明确需要全子域 Cookie，应保持 `SESSION_COOKIE_DOMAIN=None`。
- 如需嵌入式/iframe 第三方使用，可考虑 `SESSION_COOKIE_PARTITIONED=True`（要求 HTTPS）。

不安全模式：
- 生产环境 `SESSION_COOKIE_SECURE=False`。
- `SESSION_COOKIE_HTTPONLY=False`。
- 基于 Cookie 认证的状态变更端点使用 `SESSION_COOKIE_SAMESITE=None`（CSRF 风险更高）。

检测提示：
- 检查 `app.config.update(...)` 块和配置类。
- 也查找非会话 Cookie 上的 `set_cookie(..., secure=..., httponly=..., samesite=...)` 用法。

修复：
- 在生产配置中显式设置这些配置值。

备注：
- SameSite 是纵深防御；不要将其视为 CSRF 令牌的完全替代。

---

### FLASK-SESS-002：会话必须有界并抵抗固定/重放攻击
严重性：中

要求：
- 应设置与应用相匹配的有界会话生命周期。
- 仅当你有意设置持久会话时，应设置 `session.permanent = True`，并将 `PERMANENT_SESSION_LIFETIME` 设置为合理的值。
- 应在登录和权限变更时清除会话，以降低会话固定风险。
- 不得在默认 Flask 会话 Cookie 中存储敏感机密。默认会话是签名的，不是加密的。

不安全模式：
- 特权会话生命周期过长或无限制。
- 登录时不清除会话。
- 使用默认 Cookie 会话时，将机密（密码、访问令牌、PII）直接存储在 `session[...]` 中。

检测提示：
- 搜索 `PERMANENT_SESSION_LIFETIME`、`session.permanent`、`session[...] =`。
- 识别是否使用服务端会话存储；如未使用，假定为默认 Cookie 会话。

修复：
- 设置适当的生命周期。
- 登录时清除/轮换会话。
- 敏感数据存储在服务端；会话 Cookie 中仅存储标识符。

---

### FLASK-CSRF-001：使用 Cookie 认证的状态变更请求必须受 CSRF 保护
严重性：高

- 重要说明：如果 Cookie 不用于认证（即通过 Authentication 头或其他传递的令牌认证），则不存在 CSRF 风险。

要求：
- 必须保护所有依赖 Cookie 进行认证的状态变更端点（POST/PUT/PATCH/DELETE）。
- 可以使用经过充分测试的 CSRF 库/集成（表单框架或中间件），而非自行实现。
- 可以使用额外防御（Origin/Referer 检查、SameSite Cookie、Fetch Metadata 响应头、AJAX/API 的自定义响应头），但令牌仍是基于 Cookie 认证应用的主要防御。
如果令牌不切实际，或对于小型应用：
* 必须至少要求设置自定义响应头，并将会话 Cookie 设置为 SESSION_COOKIE_SAMESITE=lax，因为这是除要求表单令牌之外最强的方法，而且可能更容易实现。

不安全模式：
- 无 CSRF 保护且改变状态的 Cookie 认证端点。
- 对状态变更操作使用 GET（放大 CSRF 风险）。

检测提示：
- 枚举非 GET 方法的路由并识别认证机制。
- 查找 CSRF 集成（例如 Flask-WTF、全局 CSRF 中间件）。如不存在，视为可疑。
- 也要检查 JSON API 端点，不仅是 HTML 表单。

修复：
- 为所有状态变更请求添加 CSRF 保护。
- 如果应用是纯 API 并使用 Authorization 头（不记名令牌）而非 Cookie，请记录该选择并确保 Cookie 不用于认证。如果 Cookie 不用于认证，则不存在 CSRF 风险。

备注：
- XSS 可以击破 CSRF 防护；CSRF 防御不能替代 XSS 预防。

---

### FLASK-XSS-001：防止模板和 HTML 生成中的反射型/存储型 XSS
严重性：高

要求：
- 必须依赖 Jinja 自动转义进行 HTML 模板渲染。
- 不得将不受信任内容标记为安全：
  - 避免对用户数据使用 `Markup(...)`。
  - 避免对用户控制内容使用 Jinja `|safe`。
- 必须对包含 Jinja 表达式的 HTML 属性加引号（`value="{{ x }}"` 而非 `value={{ x }}`）。
- 不得将上传的 HTML 作为活动 HTML 提供；应作为下载提供（`Content-Disposition: attachment`）或转换为安全格式。注意：仅当可能上传 html、js、css 等文档内容时才相关。如果纯粹是图片文件，则无此问题。
- 应部署内容安全策略（CSP）以缓解各类 XSS（包括 `href` 中的 `javascript:`）。

不安全模式：
- `Markup(request.args.get(...))`
- 模板过滤器：`{{ user_html|safe }}`
- 模板中未加引号的属性
- 直接以 `text/html` 或内联渲染方式提供用户上传内容

检测提示：
- 搜索 `Markup(` 并调查数据来源。
- 在模板文件中搜索 `|safe`、`|tojson` 误用以及未加引号的属性。
- 审查可能在没有 `as_attachment=True` 的情况下返回用户上传内容的文件提供路由。注意：仅当可能上传 html、js、css 等文档内容时才相关。如果纯粹是图片文件，则无此问题。

修复：
- 移除不安全标记；仅在严格必要时使用可信 HTML 净化器净化。
- 始终为属性加引号。
- 添加 CSP 并减少内联脚本。

---

### FLASK-SSTI-001：绝不渲染不受信任的模板（服务端模板注入）
严重性：严重

要求：
- 不得渲染包含用户控制模板语法的模板。
- 如果模板字符串受不受信任输入影响，必须将 `render_template_string` 和 `Environment.from_string(...).render(...)` 视为危险。
- 不得对用户控制的字符串使用 `.format()`。
- 如绝对需要不受信任模板，应将其视为特殊的高风险设计：
  - 必须使用沙箱化模板方法并限制能力。
  - 必须保持 Jinja 更新，并假定沙箱逃逸可能发生；进一步隔离。

不安全模式：
- `render_template_string(request.args["tmpl"], ...)`
- 将用户模板存储在数据库中，并用常规 Jinja 环境渲染。
- `request.args["tmpl"].format(...)`

检测提示：
- 搜索 `render_template_string`、`from_string`、带动态字符串的 `.render(`。
- 追溯模板字符串的来源（数据库、请求、上传、管理面板）。

修复：
- 替换为不执行代码的安全模板替代方案（例如 string.Template、str.replace）。
- 如果模板必须由用户定义，使用沙箱加严格白名单和重度隔离。

---

### FLASK-HEADERS-001：设置基本安全响应头（在应用或边缘层）
严重性：中

要求（典型 Web 应用）：
- 应设置：
  - CSP（`Content-Security-Policy`）
  - `X-Content-Type-Options: nosniff`
  - 点击劫持防护（`X-Frame-Options: SAMEORIGIN` 和/或 CSP `frame-ancestors`）（可能存在用户希望在其他地方 iframe 其网站的情况。如属此类情况，请与其合作以安全地允许）
- 应根据应用考虑额外加固响应头（Referrer-Policy、Permissions-Policy）。
- 必须确保 Cookie 以安全属性设置（见 FLASK-SESS-001）。

注意：安全响应头可能通过代理或其他云服务商设置。请检查是否有相关证据。

不安全模式：
- 任何位置（应用或边缘）都没有安全响应头。
- 显示不受信任内容的应用缺少 CSP。

检测提示：
- 搜索 `after_request` 钩子、Flask-Talisman 用法、反向代理配置。
- 如应用代码中不可见，标记为"在边缘层验证"。

修复：
- 集中设置响应头（中间件 / after_request）或通过反向代理/CDN。
- 保持 CSP 现实可行且兼容；尽可能避免 `unsafe-inline`。

---

### FLASK-LIMITS-001：请求大小和表单解析限制必须适当设置
严重性：低（如可能存在文件上传/大请求体则为中）

要求：
- 应设置并说明理由：
  - `MAX_CONTENT_LENGTH`（全局最大请求字节数）
  - `MAX_FORM_MEMORY_SIZE`（multipart 中每个非文件表单字段的最大值）
  - `MAX_FORM_PARTS`（multipart 字段的最大数量）
- 必须在可行处于反向代理 / WSGI / 平台层面强制额外限制。

不安全模式：
- 处理上传或用户内容时无限制的请求体大小。
- 接受任意大的 multipart 表单或大量字段。

检测提示：
- 检查 Flask 配置中是否存在这些键。
- 检查上传路由和接受大型 JSON 的 API。

修复：
- 设置保守默认值，仅在需要时按路由覆盖。
- 确保大型上传使用专门的上传机制。

---

### FLASK-HOST-001：生产环境中必须验证 Host 响应头
严重性：低（取决于应用对外部 URL 的使用）

要求：
- 生产环境必须设置 `TRUSTED_HOSTS` 以限制接受的 Host 值。
- 不得依赖 `SERVER_NAME` 作为主机限制机制。

不安全模式：
- 生产环境未设置 `TRUSTED_HOSTS`。
- 生成邮件/密码重置外部 URL 的代码未进行主机验证。

检测提示：
- 查找 `TRUSTED_HOSTS` 配置用法。
- 查找 `url_for(..., _external=True)` 并检查主机如何确定。

修复：
- 将 `TRUSTED_HOSTS` 设置为你预期的域名（以及所需的子域名）。
- 确保外部 URL 生成使用可信主机/协议。

---

### FLASK-PROXY-001：反向代理信任必须正确配置
严重性：中（如依赖 IP 进行认证则为高）

要求：
- 如果在反向代理之后，必须配置 Flask/Werkzeug，使其仅信任来自预期代理的转发响应头。
- 不得盲目信任来自开放互联网的 `X-Forwarded-*` 响应头。

不安全模式：
- 以过于宽泛的信任设置应用 `ProxyFix`，或在不了解前面有几个代理的情况下应用。
- 依赖未经验证的转发响应头来确定协议/主机。

检测提示：
- 搜索 `ProxyFix`。
- 搜索安全敏感逻辑中对 `request.remote_addr`、`request.scheme`、`request.host` 的使用。

修复：
- 以正确的跳数配置 `ProxyFix`（或平台特定设置）。
- 即使在代理之后也保持 `TRUSTED_HOSTS`。

---

### FLASK-PATH-001：防止路径遍历和不安全的文件提供
严重性：高

要求：
- 不得将用户控制的文件路径传给 `send_file` 或直接文件 I/O。
- 必须使用安全的文件提供模式：
  - 对受信任基目录下的用户指定路径使用 `send_from_directory`
  - 将受信任基目录与不受信任路径组件拼接时使用 `safe_join`
  - 对上传文件名使用 `secure_filename`（并仍然生成你自己的唯一存储名称）
- 必须确保用户上传内容不作为可执行/活动内容提供（尤其是 HTML）。
- 对于几乎所有文件系统路径计算，通常应使用 `safe_join` 而非 `os.path.join`。

不安全模式：
- `send_file(request.args["path"])`
- `open(os.path.join(base_dir, user_path))`，其中 `user_path` 不受信任
- 在静态 Web 根目录内无限制地提供上传内容

检测提示：
- 在文件路由中搜索 `send_file(`、`open(`、`os.path.join(`、`pathlib.Path(...)/...`。
- 识别文件名来源（请求参数、数据库、响应头）。

修复：
- 仅从非用户控制的目录基址提供服务。
- 将上传存储在静态根目录之外；通过受控路由提供服务。
- 始终验证并规范化文件标识符。

注意：`safe_join` 从 `werkzeug.security` 导入

---

### FLASK-UPLOAD-001：文件上传必须经过验证、安全存储和安全提供
严重性：高

要求：
- 必须强制执行上传大小限制（应用 + 边缘层）。
- 必须使用白名单和内容检查验证文件类型（不仅是扩展名）。
- 在可能情况下，必须将上传存储在可执行/静态根目录之外。
- 应生成服务端文件名（随机 ID），避免信任原始名称。
- 必须安全地提供潜在活动格式（下载附件），除非明确有意内联提供。

不安全模式：
- 接受任意文件类型并内联返回。
- 使用用户提供的文件名作为存储路径。
- 缺少大小/类型验证。

检测提示：
- 查找 `request.files[...]` 处理程序。
- 检查 `secure_filename` 用法（以及是否与唯一性结合）。
- 检查文件存储位置和提供方式。

修复：
- 实施白名单验证 + 安全存储 + 安全提供。
- 如适用，添加扫描/隔离。

---

### FLASK-INJECT-001：防止 SQL 注入（使用参数化查询 / ORM）
严重性：高

要求：
- 必须使用参数化查询或在底层参数化的 ORM。
- 不得通过字符串拼接 / f-string 与不受信任输入构建 SQL。

不安全模式：
- `f"SELECT ... WHERE id={request.args['id']}"`
- `"... WHERE name = '%s'" % user_input`

检测提示：
- 在 Python 代码中搜索 `SELECT`、`INSERT`、`UPDATE`、`DELETE` 字符串。
- 追踪不受信任数据进入数据库 execute 调用。

修复：
- 替换为参数化查询或 ORM 查询 API。
- 在查询前验证类型（例如整数 ID）。

---

### FLASK-INJECT-002：防止操作系统命令注入
严重性：严重至高（取决于暴露程度）

要求：
- 必须避免使用不受信任输入执行 shell 命令。
- 如必须使用 subprocess：
  - 必须以列表形式传递参数（而非字符串）
  - 不得对受攻击者影响的字符串使用 `shell=True`
  - 应对任何可变部分使用严格白名单
- 如可能，使用纯 Python 或 Python 库，而非 subprocess 或系统命令
- 即使使用 `shell=False`，也不要假定传给命令的参数天然安全。命令可能错误地将这些参数作为命令行标志或其他可信值处理。

不安全模式：
- `os.system(user_input)`
- `subprocess.run(f"cmd {user}", shell=True)`
- 将用户字符串传入 `bash -c`、`sh -c`、PowerShell 等。

检测提示：
- 搜索 `os.system`、`subprocess`、`Popen`、`shell=True`。
- 追踪从请求/数据库进入这些调用的数据。

修复：
- 使用库 API 而非 shell 命令。
- 如不可避免，硬编码命令并对验证过的参数使用白名单。如子命令支持，尽量将用户值放在 `--` 之后，防止其被当作命令行标志处理。

---

### FLASK-SSRF-001：防止出站 HTTP 中的服务端请求伪造（SSRF）
严重性：中

- 注意：对于小型独立项目，这不太重要。在部署到 LAN 或与其他服务监听同一服务器时最为重要。

要求：
- 必须将对用户提供 URL 的出站请求视为高风险。
- 应对任何受用户影响的 URL 抓取进行验证并限制目的地（主机/域名白名单）。
- 应阻止访问：
  - localhost / 私有 IP 范围 / 链路本地地址
  - 云元数据端点
- 不得允许非 http/https 协议（即 file: 等）
- 应设置超时并限制重定向。



不安全模式：
- `requests.get(request.args["url"])`
- 接受任意 URL 的 Webhook/预览/抓取端点。

检测提示：
- 搜索使用不受信任 URL 来源的 `requests.get/post`、`httpx`、`urllib`、`aiohttp`。
- 识别 URL 抓取功能（预览、导入、webhook 测试器）。

修复：
- 确保 URL 是 http 或 https（不允许 file: 或其他协议）
- 强制执行白名单和网络出站控制。
- 添加严格解析和 IP 解析检查；设置超时；如不需要则禁用重定向。

---

### FLASK-REDIRECT-001：防止开放重定向
严重性：低

要求：
- 必须验证源自不受信任输入（例如 `next`、`redirect`、`return_to`）的重定向目标。
- 应使用内部路径或已知域名的白名单。
- 应优先只重定向到同站相对路径。

不安全模式：
- `redirect(request.args.get("next"))` 且无验证。

检测提示：
- 搜索 `redirect(` 并检查 `location` 的来源。

修复：
- 只允许相对路径或白名单域名。
- 验证失败时回退到安全默认值。

---

### FLASK-HTTP-001：安全使用 HTTP 方法；不要通过 GET 改变状态；避免 URL 中的机密
严重性：中

要求：
- 不得通过 GET 执行状态变更操作。
- 不得在 URL 中放置机密（查询字符串常被记录并通过 referrer 泄露）。
- 应要求状态变更使用 POST/PUT/PATCH/DELETE，并在基于 Cookie 认证时应用 CSRF 防护。

不安全模式：
- `/delete?id=...` 以 GET 实现
- 密码重置令牌或 API 密钥放在查询参数中

检测提示：
- 枚举 GET 路由并检查它们是否改变状态。
- 查找名为 `token`、`key`、`secret`、`password` 等的 URL 参数。

修复：
- 将状态变更移至非 GET 方法。
- 将敏感值移至安全通道（POST 请求体、响应头）并加以保护。

---

### FLASK-CORS-001：CORS 必须明确且最小权限
严重性：中（与凭据一起错误配置时为高）

要求：
- 如不需要 CORS，必须保持禁用。
- 如需要 CORS：
  - 必须对可信来源使用白名单（不要反射任意来源）。
  - 必须谨慎对待带凭据的请求；不要将宽泛来源与 Cookie 结合。
  - 应限制允许的方法和响应头。

不安全模式：
- `Access-Control-Allow-Origin: *` 与带凭据 Cookie 或过于宽泛的访问结合。
- 未经验证反射 `Origin`。
- `flask_cors.CORS(app)` 使用宽松默认值。

检测提示：
- 搜索 `flask_cors`、`CORS(`、`Access-Control-Allow-Origin`。
- 检查 `supports_credentials=True` 和通配符来源。

修复：
- 使用严格来源白名单和最少的允许方法/响应头。
- 除非必要，确保基于 Cookie 认证的端点不跨源暴露。

---

### FLASK-SUPPLY-001：依赖与补丁卫生（重点关注安全相关依赖）
严重性：低

要求：
- 应固定并定期更新安全关键依赖（Flask、Werkzeug、Jinja2、itsdangerous）。
- 必须及时响应已知安全公告。

审计重点示例：
- 如在 Windows 上运行并使用不受信任路径提供文件，确保 Werkzeug 的 `safe_join` 行为不会受 Windows 设备名边缘情况影响。

检测提示：
- 检查 `requirements.txt`、锁文件和运行时环境。
- 识别安全辅助函数（safe_join、send_from_directory）的使用位置。

修复：
- 升级到已修补版本，并为受影响行为添加回归测试。

--------------------------------------------------------------------

## 5）实用扫描启发式方法（如何"搜寻"）

主动扫描时，使用这些高信号模式：

- 开发服务器 / 调试：
  - `app.run(`、`flask run`、`--debug`、`DEBUG=True`、`FLASK_DEBUG`
- 机密：
  - `SECRET_KEY`、`secret_key`、已提交的 `.env`、`print(config)`
- Cookie / 会话：
  - `SESSION_COOKIE_SECURE`、`SESSION_COOKIE_HTTPONLY`、`SESSION_COOKIE_SAMESITE`
  - 带敏感值的 `session[...] =`
- CSRF：
  - 基于 Cookie 认证的应用中无 CSRF 检查的 POST/PUT/PATCH/DELETE 处理程序
- XSS/SSTI：
  - `Markup(`、`|safe`、未加引号的属性、`render_template_string`
- 文件：
  - 带用户控制路径的 `send_file(`；对用户路径的 `open(`；带不受信任输入的 `os.path.join`
  - 使用用户文件名作为路径的上传处理程序
- 注入：
  - SQL 字符串 + 字符串格式化进入 `.execute(...)`
  - `subprocess.*`、`shell=True`、`os.system`
- SSRF：
  - URL 来自请求/数据库的 `requests.get/post` 或 `httpx`
- 重定向：
  - `redirect(request.args.get("next"))`
- CORS：
  - `flask_cors.CORS` 宽松配置；带凭据的通配符来源

始终尝试确认：
- 数据来源（不受信任 vs 可信）
- 汇点类型（模板/SQL/subprocess/文件/重定向/http）
- 存在的防护控制（验证、白名单、中间件）

--------------------------------------------------------------------

## 6）来源（访问于 2026-01-26）

主要框架文档：
- Flask 文档：部署到生产环境——https://flask.palletsprojects.com/en/stable/deploying/
- Flask 文档：调试应用错误——https://flask.palletsprojects.com/en/stable/debugging/
- Flask 文档：配置处理——https://flask.palletsprojects.com/en/stable/config/
- Flask 文档：安全注意事项——https://flask.palletsprojects.com/en/stable/web-security/
- Flask 文档：告诉 Flask 它在代理之后——https://flask.palletsprojects.com/en/stable/deploying/proxy_fix/
- Flask API 文档：会话——https://flask.palletsprojects.com/en/stable/api/#sessions

Werkzeug 文档与公告：
- Werkzeug 文档：工具（send_file / send_from_directory / safe_join / secure_filename / 密码哈希）——https://werkzeug.palletsprojects.com/en/stable/utils/
- GitHub 公告：CVE-2025-66221（Werkzeug safe_join Windows 设备名）——https://github.com/advisories/GHSA-hgf8-39gv-g3f2

OWASP Cheat Sheet Series：
- 会话管理——https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- CSRF 预防——https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
- XSS 预防——https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
- 输入验证——https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html
- SQL 注入预防——https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
- 注入预防——https://cheatsheetseries.owasp.org/cheatsheets/Injection_Prevention_Cheat_Sheet.html
- OS 命令注入防御——https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html
- SSRF 预防——https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
- 文件上传——https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
- 未验证的重定向——https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html
- HTTP 响应头——https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html

模板安全参考：
- Jinja：沙箱（渲染不受信任模板）——https://jinja.palletsprojects.com/en/stable/sandbox/
- OWASP WSTG：服务端模板注入测试——https://owasp.org/www-project-web-security-testing-guide/v41/4-Web_Application_Security_Testing/07-Input_Validation_Testing/18-Testing_for_Server_Side_Template_Injection
- PortSwigger Web Security Academy：服务端模板注入——https://portswigger.net/web-security/server-side-template-injection

HTTP 语义：
- RFC 9110：HTTP 语义（安全方法）——https://www.rfc-editor.org/rfc/rfc9110
