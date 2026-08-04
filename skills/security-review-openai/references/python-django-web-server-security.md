# Django（Python）Web 安全规范（Django 6.0.x，Python 3.x）

本文档设计为一份**安全规范**，用于支持：

1. 为新的 Django 代码进行**默认安全的代码生成**。
2. 对现有 Django 代码进行**安全审查/漏洞搜寻**（被动式"工作时发现问题"与主动式"扫描仓库并报告发现"）。

本文档特意以一组**规范性要求**（"MUST/SHOULD/MAY"，必须/应当/可以）加**审计规则**（不良模式长什么样、如何检测、如何修复/缓解）的形式编写。

---

## 0) 安全、边界与反滥用约束（必须遵守 MUST FOLLOW）

* 不得（MUST NOT）请求、输出、记录或提交密钥（API 密钥、密码、私钥、会话 Cookie、`SECRET_KEY`、`SECRET_KEY_FALLBACKS`、数据库密码）。
* 不得（MUST NOT）通过禁用保护来"修复"安全问题（例如移除 `CsrfViewMiddleware`、到处加 `@csrf_exempt`、将 `ALLOWED_HOSTS` 放宽为 `['*']`、禁用 `SecurityMiddleware`、禁用模板自动转义、禁用权限检查）。
* 审计时必须提供**基于证据的发现**：引用证明每项主张的文件路径、代码片段和具体配置值。
* 必须（MUST）诚实地对待不确定性：如果某项保护可能存在于基础设施层（反向代理、WAF、CDN、入口控制器），应报告为"在应用代码中不可见；需在运行时/边缘配置中验证"。
* 必须（MUST）保持修复与 Django 的设计安全模型兼容：尽可能优先使用 Django 内置组件（中间件、认证、表单、ORM）而非自定义安全逻辑。Django 的部署检查清单和系统检查属于该预期模型的一部分。（[Django Project][1]）

---

## 1) 运行模式

### 1.1 生成模式（默认）

当被要求编写新的 Django 代码或修改现有代码时：

* 必须（MUST）遵守本规范中的每一项 **MUST** 要求。
* 应当（SHOULD）遵守每一项 **SHOULD** 要求，除非用户明确另有指示。
* 必须（MUST）优先选择默认安全的 Django API 和成熟的库，而非自定义安全代码。
* 必须（MUST）避免引入新的高风险汇点（sink）（从不受信任的字符串动态渲染模板、不安全的重定向、不安全的文件提供、shell 执行、原始 SQL 字符串格式化、基于不受信任输入发起 SSRF 能力的 URL 抓取）。

### 1.2 被动审查模式（编辑时始终开启）

在 Django 代码仓库的任何位置工作时（即使用户未要求安全扫描）：

* 必须（MUST）"注意"被触碰/附近代码中违反本规范之处。
* 应当（SHOULD）在问题出现时提及，附带简要说明与安全修复方案。

### 1.3 主动审计模式（明确请求扫描）

当用户要求"扫描""审计"或"搜寻漏洞"时：

* 必须（MUST）系统地搜索代码库中违反本规范之处。
* 必须（MUST）以结构化格式输出发现（见第 2.3 节）。

推荐的审计顺序：

1. 部署入口（ASGI/WSGI）、Dockerfile、Procfile、systemd 单元、平台清单。
2. `settings.py` 与环境特定的设置模块。
3. 中间件顺序与已启用的保护。
4. 认证/授权（登录、会话管理、权限、admin）。
5. CSRF 防护与改变状态（state-changing）的端点。
6. 模板与 XSS。
7. 文件处理（上传/下载/static/media）与路径遍历。
8. 注入类别（SQL、命令执行、不安全的反序列化）。
9. 出站请求（SSRF）。
10. 重定向处理（开放重定向）+ CORS + 安全响应头（CSP、HSTS 等）。
11. 依赖/版本固定与修补姿态。

---

## 2) 定义与审查指引

### 2.1 不受信任的输入（除非证明可信，否则视为攻击者可控）

示例包括：

* `request.GET`、`request.POST`、`request.FILES`
* `request.body`、JSON 请求体（如 `json.loads(request.body)`）、DRF `request.data`
* URL 路径参数（如 `<int:id>`、`<slug:...>`）
* `request.headers` / `request.META`（包括 `HTTP_HOST`、`HTTP_ORIGIN`、`HTTP_REFERER`、`HTTP_X_FORWARDED_*`）
* `request.COOKIES`
* 来自外部系统的任何数据（Webhook、第三方 API、消息队列）
* 源自用户的任何持久化内容（数据库行、缓存内容、文件上传）

Django 明确强调"永远不要信任用户控制的数据"，并推荐使用表单/验证。（[Django Project][2]）

### 2.2 改变状态的请求（state-changing request）

如果请求能够创建/更新/删除数据、改变认证/会话状态、触发副作用（购买、发送邮件、发送 Webhook）或发起特权操作，则该请求属于改变状态的请求。

### 2.3 必需的审计发现格式

对发现的每个问题，输出：

* 规则 ID：
* 严重程度：严重（Critical）/ 高（High）/ 中（Medium）/ 低（Low）
* 位置：文件路径 + 函数/类/视图名称 + 行号
* 证据：精确的代码/配置片段
* 影响：可能出什么问题、谁可以利用
* 修复：安全的变更（优先最小差异）
* 缓解：如果立即修复困难时的纵深防御
* 误报说明：不确定时需要验证什么

---

## 3) 安全基线：最低生产配置（生产环境必须遵守）

这是防止常见 Django 错误配置的最小"生产基线"。Django 提供了"部署检查清单"（Deployment checklist），并建议针对生产设置运行 `manage.py check --deploy`。（[Django Project][1]）

### 3.1 设置管理模式（应当）

* 应当（SHOULD）使用基于环境的配置（或密钥管理器），使生产设置不硬编码。
* 必须（MUST）将敏感设置视为机密（如 `SECRET_KEY`、数据库密码），并使其不进入源代码管理。Django 的检查清单明确建议从环境变量或文件加载 `SECRET_KEY`，而非硬编码。（[Django Project][1]）
* 应当（SHOULD）分离开发与生产设置模块，并为生产环境提供安全默认值（关键设置缺失时默认拒绝，fail closed）。（[Django Project][1]）

### 3.2 最低基线目标（生产环境）

* 必须（MUST NOT）将 `manage.py runserver` 作为生产入口；使用生产级 WSGI 或 ASGI 服务器。（[Django Project][1]）
* 必须（MUST）在生产环境中设置 `DEBUG = False`。（[Django Project][1]）
* 必须（MUST）设置强随机的 `SECRET_KEY` 并保持其秘密；可以（MAY）使用 `SECRET_KEY_FALLBACKS` 进行安全轮换。（[Django Project][1]）
* 必须（MUST）将 `ALLOWED_HOSTS` 设置为预期主机（无通配符，除非你自己做主机验证）。（[Django Project][1]）
* 必须（MUST）对认证区域强制 HTTPS（理想情况下对任何可登录的应用全站启用），并在使用 HTTPS 时设置 `CSRF_COOKIE_SECURE=True` 与 `SESSION_COOKIE_SECURE=True`。（[Django Project][1]）
* 应当（SHOULD）启用关键 `SecurityMiddleware` 响应头/设置：HSTS、Referrer-Policy、COOP、nosniff、SSL 重定向（配合正确的代理配置）。（[Django Project][3]）
* 必须（MUST）将用户上传视为不受信任；确保 Web 服务器永远不会将其解释为可执行内容；保持 `MEDIA_ROOT` 与 `STATIC_ROOT` 分离。（[Django Project][1]）

---

## 4) 规则（生成 + 审计）

每条规则包含：必需做法、不安全模式、检测提示与修复方法。

### DJANGO-DEPLOY-001：不得在生产环境使用 Django 的开发服务器

严重程度：高（如处于生产环境）

必需：

* 必须（MUST NOT）将 `manage.py runserver` 部署为生产服务器。
* 必须（MUST）在生产级 WSGI 或 ASGI 服务器之后运行。（[Django Project][1]）

不安全模式：

* 生产文档/脚本使用 `python manage.py runserver 0.0.0.0:8000`。
* Docker `CMD`/入口点使用 `runserver`。
* Kubernetes/Procfile/systemd 单元调用 `runserver`。

检测提示：

* 搜索 `manage.py runserver`、`runserver 0.0.0.0`、`--insecure`。
* 检查 Docker `CMD/ENTRYPOINT`、Procfile、systemd 单元文件、Helm 图表。

修复：

* 按照 Django 部署检查清单的推荐使用生产服务器（WSGI/ASGI）。（[Django Project][1]）

说明：

* `runserver` 适合本地开发。仅当其被用作生产入口时才标记。

---

### DJANGO-DEPLOY-002：`DEBUG` 必须（MUST）在生产环境禁用

严重程度：高

必需：

* 必须（MUST）在生产环境中设置 `DEBUG = False`。
* 必须（MUST）将任何向不受信任用户暴露调试页面/堆栈跟踪的机制视为严重的信息泄露风险。Django 的检查清单明确警告 `DEBUG=True` 会泄露源码摘录、局部变量、设置等。（[Django Project][1]）

不安全模式：

* 生产设置中 `DEBUG = True`。
* 环境默认 `DEBUG=True`，除非显式覆盖。

检测提示：

* 搜索 `DEBUG = True`、`DEBUG=os.environ.get(..., True)`、`DJANGO_DEBUG`、`.env` 文件。
* 查找从开发默认值导入的"生产"设置模块。

修复：

* 在生产设置中设置 `DEBUG=False`；使用显式环境配置。
* 确保错误报告通过安全的日志/监控实现，而非调试页面。（[Django Project][1]）

---

### DJANGO-CONFIG-001：`SECRET_KEY` 必须强随机、保密并安全轮换

严重程度：高（生产环境中缺失且使用签名/会话时为严重）

必需：

* 必须（MUST）在生产环境中设置大随机的 `SECRET_KEY` 并保持其秘密。（[Django Project][1]）
* 必须（MUST NOT）将其提交到源代码管理或打印/记录。（[Django Project][1]）
* 应当（SHOULD）从环境变量或文件/密钥存储加载（而非硬编码）。（[Django Project][1]）
* 可以（MAY）使用 `SECRET_KEY_FALLBACKS` 轮换密钥，以避免立即使所有签名数据失效；必须（MUST）及时从回退列表中移除旧密钥。（[Django Project][1]）

不安全模式：

* 仓库中为生产环境硬编码 `SECRET_KEY = "..."`。
* `SECRET_KEY` 跨环境复用。
* `SECRET_KEY_FALLBACKS` 长期保留已过期的密钥。

检测提示：

* 搜索 `SECRET_KEY =`、`SECRET_KEY_FALLBACKS`、提交的 `.env` 文件、`print(settings.SECRET_KEY)`。

修复：

* 从密钥管理器/环境变量加载。
* 如轮换：

  * 设置新的 `SECRET_KEY`
  * 暂时将旧密钥保留在 `SECRET_KEY_FALLBACKS`
  * 在轮换窗口期后移除旧密钥。（[Django Project][1]）

---

### DJANGO-HOST-001：Host 请求头必须经过验证（`ALLOWED_HOSTS` 必须严格）

严重程度：中

必需：

* 必须（MUST）在生产环境将 `ALLOWED_HOSTS` 设置为预期的域名/主机。（[Django Project][1]）
* 必须（MUST NOT）在生产环境设置 `ALLOWED_HOSTS = ['*']`，除非你也实施自己的健壮 `Host` 验证（Django 警告通配符需要自己的验证以避免 CSRF 类攻击）。（[Django Project][1]）
* 应当（SHOULD）配置前端的 Web 服务器尽早拒绝未知主机（纵深防御）。（[Django Project][1]）

不安全模式：

* 生产环境中 `ALLOWED_HOSTS = ['*']`（或环境变量展开为 `*`）。
* `DEBUG=False` 时 `ALLOWED_HOSTS = []`（站点无法运行，或配置错误的部署试图变通）。

检测提示：

* 搜索 `ALLOWED_HOSTS`。
* 检查覆盖 `ALLOWED_HOSTS` 的平台环境设置。

修复：

* 为生产环境设置 `ALLOWED_HOSTS = ['example.com', 'www.example.com', ...]`。
* 将开发主机分开。

说明：

* Django 使用 Host 请求头构造 URL；伪造的 Host 值可能导致 CSRF、缓存投毒和被投毒的邮件链接（Django 安全文档特别指出了这一点）。（[Django Project][2]）

---

### DJANGO-HTTPS-001：如使用 TLS，Cookie 传输必须得到保护

严重程度：高（启用认证的应用为严重）

说明：仅在启用 TLS 时强制执行此项，因为这会破坏非 TLS 应用。

如果使用 TLS：
* 必须（MUST）设置：

  * `CSRF_COOKIE_SECURE = True`（[Django Project][1]）
  * `SESSION_COOKIE_SECURE = True`（[Django Project][1]）
* 应当（SHOULD）考虑启用：

  * `SECURE_SSL_REDIRECT = True`（配合正确的代理配置）（[Django Project][3]）
  * 通过 `SECURE_HSTS_SECONDS` 启用 HSTS（+ 适当时 includeSubDomains/preload）。（[Django Project][3]）

不安全模式：

* 通过 HTTP 的登录页面，或同一会话 Cookie 混用 HTTP/HTTPS。
* 生产环境 HTTPS 下 `CSRF_COOKIE_SECURE=False` 或 `SESSION_COOKIE_SECURE=False`。
* HSTS 配置错误（可能在配置期间内破坏站点）。

检测提示：

* 检查 `settings.py` 中的 `CSRF_COOKIE_SECURE`、`SESSION_COOKIE_SECURE`、`SECURE_SSL_REDIRECT`、`SECURE_HSTS_SECONDS`。
* 检查代理/入口配置中的 HTTP->HTTPS 重定向行为。

修复：

* 启用 HTTPS 重定向和安全 Cookie。
* 谨慎添加 HSTS（从小值开始，验证后再增加）。Django 警告配置错误可能在 HSTS 期间破坏站点。（[Django Project][3]）

---

### DJANGO-PROXY-001：反向代理信任必须正确配置（`SECURE_PROXY_SSL_HEADER`）

严重程度：中（在 TLS 代理之后时）

必需：

* 如果位于终止 TLS 的反向代理之后，必须（MUST）配置 Django，使 `request.is_secure()` 反映*外部*协议，否则 CSRF 和其他逻辑可能失效。Django 记录了使用 `SECURE_PROXY_SSL_HEADER` 实现这一点。（[Django Project][3]）
* 仅当你控制代理（或有保证）且其剥离入站伪造请求头时，才必须（MUST）设置 `SECURE_PROXY_SSL_HEADER`。Django 明确警告配置错误可能危及安全，并列出了必要条件。（[Django Project][3]）

不安全模式：

* 在代理不剥离用户提供的 `X-Forwarded-Proto` 的环境中设置 `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`。
* 设置 `SECURE_SSL_REDIRECT=True` 后出现无限重定向循环（通常表明代理的 HTTPS 检测错误）。（[Django Project][3]）

检测提示：

* 搜索 `SECURE_PROXY_SSL_HEADER`、`SECURE_SSL_REDIRECT`。
* 检查入口/代理剥离转发请求头的行为。

修复：

* 仅当代理正确剥离并设置该请求头时（按照 Django 记录的先决条件）才设置 `SECURE_PROXY_SSL_HEADER`。（[Django Project][3]）

---

### DJANGO-SESS-001：生产环境中会话 Cookie 必须使用安全属性

严重程度：中（仅在启用 TLS 时）

必需（生产环境，HTTPS）：

* 必须（MUST）设置 `SESSION_COOKIE_SECURE=True`（仅通过 HTTPS 传输）。（[Django Project][3]）
* 必须（MUST）保持 `SESSION_COOKIE_HTTPONLY=True`（Django 默认值为 `True`）。（[Django Project][3]）
* 应当（SHOULD）保持 `SESSION_COOKIE_SAMESITE='Lax'`（Django 默认值为 `Lax`），除非有正当理由的跨站流程要求 `None`。（[Django Project][3]）
* 应当（SHOULD）避免设置 `SESSION_COOKIE_DOMAIN`，除非确实需要跨子域 Cookie（子域级 Cookie 扩大攻击面）。

不安全模式：

* 生产环境 HTTPS 下 `SESSION_COOKIE_SECURE=False`。

重要说明：仅在配置了 TLS 的生产环境中设置 `Secure`。在通过 HTTP 运行的本地开发环境中，不要在 Cookie 上设置 `Secure` 属性。应根据应用是否处于生产模式进行条件设置。还应包含类似 `SESSION_COOKIE_SECURE` 的属性，用于在通过 HTTP 测试时禁用 `Secure` Cookie。

* `SESSION_COOKIE_HTTPONLY=False`。
* `SESSION_COOKIE_SAMESITE=None` 搭配以 Cookie 认证的改变状态端点（CSRF 风险更高）。

检测提示：

* 搜索 `SESSION_COOKIE_` 设置、`response.set_cookie(..., httponly=..., secure=..., samesite=...)`。

修复：

* 在生产设置中显式设置上述项。
* 验证与你的认证流程的兼容性。（[Django Project][3]）

---

### DJANGO-SESS-002：CSRF Cookie 设置必须审慎（HttpOnly 有权衡）

严重程度：中

必需：

* 使用 HTTPS/TLS 时应当（SHOULD）设置 `CSRF_COOKIE_SECURE=True`。（[Django Project][3]）
* 应当（SHOULD）保持 `CSRF_COOKIE_SAMESITE='Lax'`，除非有跨站需求。Django 默认值为 `Lax`。（[Django Project][3]）
* 如果你的前端不需要读取 CSRF Cookie，可以（MAY）设置 `CSRF_COOKIE_HTTPONLY=True`（默认值为 `False`）。如果启用它，你的 JS 必须改为从 DOM 读取 CSRF 令牌（Django 记录了这一点）。（[Django Project][3]）

不安全模式：

* 生产环境 HTTPS/TLS 下 `CSRF_COOKIE_SECURE=False`。
* 设置 `CSRF_COOKIE_HTTPONLY=True` 但仍依赖"在 JS 中读取 csrftoken Cookie"的模式（破坏 AJAX 的 CSRF）。
* 无明确理由的 `CSRF_COOKIE_SAMESITE=None`。

检测提示：

* 搜索 `CSRF_COOKIE_` 设置。
* 搜索 JS 中通过 `document.cookie` 获取 `csrftoken` 的使用。

修复：

* 按照 Django 的描述，使 Cookie 设置与你的 CSRF 令牌获取方式（Cookie vs DOM）保持一致。（[Django Project][4]）

---

### DJANGO-CSRF-001：以 Cookie 认证的改变状态请求必须受 CSRF 保护

严重程度：高

必需：

* 必须（MUST）保持 `django.middleware.csrf.CsrfViewMiddleware` 启用（默认激活）。（[Django Project][4]）
* 必须（MUST）在内部 POST 表单中包含 `{% csrf_token %}`；不得（MUST NOT）在向外部 URL 提交的表单中包含它（Django 警告这会泄露令牌）。（[Django Project][4]）
* 必须（MUST）保护所有依赖 Cookie 进行认证的改变状态端点（POST/PUT/PATCH/DELETE）。
* 对于 AJAX/SPA 调用，必须（MUST）按文档所述通过 `X-CSRFToken` 请求头（或配置的请求头名称）发送 CSRF 令牌。（[Django Project][4]）
* 必须（MUST）非常谨慎地使用 `@csrf_exempt`，仅在绝对必要时使用；如果使用，必须（MUST）用适当的替代控制（如 Webhook 的请求签名）替代 CSRF。Django 明确警告 `csrf_exempt` 的风险。（[Django Project][2]）

不安全模式：

* `MIDDLEWARE` 中缺少 `CsrfViewMiddleware`。
* 通用认证视图上的 `@csrf_exempt`。
* 带会话认证且无 CSRF 令牌的 POST/PUT/PATCH/DELETE 端点。
* 使用 GET 进行改变状态的操作（放大 CSRF 风险）。

检测提示：

* 检查 `settings.py` 的 `MIDDLEWARE` 中是否有 `CsrfViewMiddleware` 及其顺序（Django 指出它应位于假定 CSRF 已处理的中间件之前）。（[Django Project][4]）
* 搜索 `csrf_exempt`、`csrf_protect`、`ensure_csrf_cookie`。
* 枚举非 GET 方法的 URL 模式；确认 CSRF 覆盖。

修复：

* 重新启用 `CsrfViewMiddleware`，在表单中添加 CSRF 令牌，并添加 AJAX 请求头处理。
* 对于缓存装饰器：如果你缓存需要 CSRF 令牌的视图，按 Django 文档所述应用 `@csrf_protect`，避免缓存无 CSRF Cookie/Vary 响应头的响应。（[Django Project][4]）

说明：

* 使用 HTTPS 部署时，Django 的 CSRF 中间件还会检查 Referer 请求头是否为同源（Django 安全文档提到了这一点）。（[Django Project][2]）

---

### DJANGO-XSS-001：防止模板和 HTML 生成中的反射型/存储型 XSS

严重程度：高

必需：

* 必须（MUST）依赖 Django 模板自动转义（默认安全）进行 HTML 模板渲染。Django 安全文档强调 Django 模板会转义危险字符，但存在局限性。（[Django Project][2]）
* 必须（MUST NOT）广泛禁用自动转义（`{% autoescape off %}`），除非内容受信任或已被安全净化。（[Django Project][5]）
* 必须（MUST NOT）将不受信任的内容标记为安全：

  * 避免对用户数据使用 `mark_safe(...)`
  * 避免对用户控制的内容使用 `|safe`
* 必须（MUST）注意 HTML 上下文陷阱（如未加引号的属性）；Django 明确展示了一个转义无法保护未加引号属性上下文的示例。（[Django Project][2]）
* 应当（SHOULD）优先使用安全的 HTML 构造辅助函数（如 `format_html`），而非可能漏掉转义的手工拼接。（[Django Project][6]）

不安全模式：

* `{% autoescape off %}{{ user_input }}{% endautoescape %}`
* `{{ user_input|safe }}`
* `mark_safe(request.GET["q"])`
* 未加引号的属性注入：`<style class={{ var }}>...`（Django 自己的示例）。（[Django Project][2]）

检测提示：

* 搜索模板中的 `|safe`、`autoescape off`、`safeseq`。
* 搜索 Python 中的 `mark_safe`、`SafeString`，或带有请求/数据库值的直接 HTML 拼接。
* 审查任何返回 `HttpResponse(user_value)` 且 `user_value` 包含 HTML 的代码。

修复：

* 移除不安全标记；仅在严格必要时净化（使用基于白名单的 HTML 净化器）。
* 给属性加引号，避免将不受信任的值放入危险上下文。
* 添加 CSP 作为纵深防御（见 DJANGO-CSP-001）。（[Django Project][2]）

---

### DJANGO-TEMPLATE-001：绝不渲染不受信任的模板源字符串

严重程度：高至 严重（取决于上下文与暴露面）

必需：

* 必须（MUST NOT）渲染模板源字符串受不受信任输入影响（请求、用户内容、可由不受信任用户编辑的数据库行）的模板。
* 必须（MUST）将"从字符串渲染模板"的模式视为危险，即使 Django 模板比其他某些引擎更受约束：它们仍可能从上下文中泄露数据、绕过转义，并造成 XSS 或内容注入。

不安全模式：

* `Template(request.GET["tmpl"]).render(Context(...))`
* 将用户模板保存在数据库中，并以正常权限/上下文渲染。

检测提示：

* 搜索 `django.template.Template(`、`Engine.from_string`、使用非常量字符串的 `.render(Context(`。
* 追踪模板字符串的来源（管理面板、数据库、上传、请求）。

修复：

* 替换为不执行的格式化（如 `string.Template`、显式占位符）或严格白名单的渲染模型。
* 如果*必须*支持用户定义模板，则重度隔离（独立服务/租户上下文、严格白名单，并假设绕过是可能的）。

---

### DJANGO-SQL-001：防止 SQL 注入（使用 ORM 或参数化原始 SQL）

严重程度：高

必需：

* 必须（MUST）对常规数据库访问使用 Django ORM/查询集；Django 指出查询集已参数化，在典型使用下可防止 SQL 注入。（[Django Project][2]）
* 必须（MUST）非常谨慎地使用原始 SQL；如果使用 `raw()`、`cursor.execute()`、`extra()` 或 `RawSQL`，必须（MUST）单独传递参数（如 `params=`），且必须（MUST NOT）将不受信任的输入字符串插值进 SQL。Django 的原始 SQL 文档警告使用 `params` 转义用户控制的参数。（[Django Project][7]）
* 必须（MUST NOT）在 SQL 模板中引用占位符（Django 文档明确警告引用 `%s` 占位符会使其不安全）。（[Django Project][8]）
* 应当（SHOULD）除非必要，避免 `extra()` 和 `RawSQL`；Django 安全文档要求谨慎。（[Django Project][2]）

不安全模式：

* `cursor.execute(f"SELECT ... WHERE id={request.GET['id']}")`
* `Model.objects.raw("... %s" % user_input)`（字符串格式化）
* `extra(where=[f"headline='{q}'"])`
* 引用占位符：`WHERE othercol = '%s'`（文档明确列为不安全）。（[Django Project][8]）

检测提示：

* 搜索 `.raw(`、`.extra(`、`RawSQL(`、`connection.cursor()`、`.execute(`。
* 搜索 Python 字符串中的 SQL 关键字（`SELECT`、`UPDATE`、`DELETE`、`INSERT`）。
* 追踪不受信任的输入进入这些调用点。

修复：

* 优先使用 ORM 查询。
* 如果原始 SQL 不可避免，使用参数（`params`、DB-API 参数绑定）且不引用占位符。（[Django Project][7]）

---

### DJANGO-CMD-001：防止操作系统命令注入

严重程度：严重至 高（取决于暴露面）

必需：

* 必须（MUST）避免使用受攻击者影响的输入执行系统命令。
* 如果必须使用子进程：

  * 必须（MUST）以列表形式传递参数（而非 shell 字符串）。
  * 必须（MUST NOT）对受攻击者影响的内容使用 `shell=True`。
  * 应当（SHOULD）对可变组件使用严格白名单。
* 应当（SHOULD）优先使用纯 Python 库而非调用 shell。

不安全模式：

* `os.system(request.GET["cmd"])`
* 当 `path` 为用户控制时使用 `subprocess.run(f"convert {path}", shell=True)`。

检测提示：

* 搜索 `os.system`、`subprocess`、`Popen`、`shell=True`。
* 追踪请求/数据库输入进入这些调用。

修复：

* 替换为库 API；如果不可避免，硬编码可执行文件并白名单验证过的参数。

---

### DJANGO-UPLOAD-001：文件上传必须经过验证、安全存储、安全提供

严重程度：高

必需：

* 必须（MUST）将所有用户上传视为不受信任。Django 明确警告"媒体文件是用户上传的。它们不受信任！"（[Django Project][1]）
* 必须（MUST）确保 Web 服务器永远不将用户上传解释为可执行代码（例如，不允许上传的 `.php` 或 HTML 作为活动内容执行/内联）。（[Django Project][1]）
* 必须（MUST）强制大小限制（至少在网络服务器层面；Django 安全文档建议在服务器端限制上传大小以防止 DoS）。（[Django Project][2]）
* 应当（SHOULD）使用白名单和内容检查验证文件类型（不仅仅是扩展名）。
* 应当（SHOULD）将上传存储于应用代码目录之外以及任何静态根目录之外。
* 应当（SHOULD）考虑从单独的顶级/二级域名提供上传，以降低同源影响；Django 安全文档推荐使用独立域名，并指出子域名可能不足以提供某些保护。（[Django Project][2]）
* 必须（MUST）了解多语言文件（polyglot）上传风险：Django 记录了一个案例，HTML 可以通过使用有效的 PNG 文件头"作为图片"上传（并可能根据 Web 服务器配置作为 HTML 提供）。（[Django Project][2]）

不安全模式：

* 以 `text/html` 内联提供上传，或不强制对可能活动的格式进行下载。
* 仅基于扩展名的上传白名单。
* 上传存储于静态根目录或代码根目录内。

检测提示：

* 搜索 `request.FILES`、`FileField`、`ImageField`、上传表单/视图。
* 检查上传提供路径和 Nginx/Apache 配置（媒体处理器）。
* 检查 `MEDIA_URL`、`MEDIA_ROOT` 和静态配置。

修复：

* 配置 Web 服务器以惰性字节（无执行）形式提供上传，并考虑对风险类型强制 `Content-Disposition: attachment`。
* 在适当时为用户内容使用独立域名。（[Django Project][2]）

---

### DJANGO-PATH-001：防止路径遍历与不安全的文件提供（static/media 分离）

严重程度：高

必需：

* 必须（MUST NOT）将用户输入作为读取/写入/提供的文件系统路径。
* 必须（MUST）保持 `MEDIA_ROOT` 与 `STATIC_ROOT` 不同；Django 设置文档明确警告两者必须具有不同值，以避免安全影响。（[Django Project][3]）
* 应当（SHOULD）优先使用按服务端标识符索引的 Django 存储 API，而非接受用户提供的任意相对路径。

不安全模式：

* `open(os.path.join(MEDIA_ROOT, request.GET["path"]))`
* 接受 `?file=../../...` 样式参数的下载端点。
* 配置错误的 `MEDIA_ROOT == STATIC_ROOT`。

检测提示：

* 搜索与请求值一起使用的 `open(`、`Path(`、`os.path.join(`。
* 检查设置中的 `MEDIA_ROOT`、`STATIC_ROOT`。（[Django Project][3]）

修复：

* 使用映射到已知文件的服务端 ID。
* 保持静态与媒体分离，并确保 Web 服务器将媒体视为不受信任。（[Django Project][3]）

---

### DJANGO-REDIRECT-001：防止开放重定向（`next`、`return_to`、`redirect`）

严重程度：中（与认证流程组合时为高）

必需：

* 必须（MUST）验证源自不受信任输入的跳转目标（如 `next`、`return_to`）。
* 应当（SHOULD）限制为同站相对路径或白名单主机/协议。
* 应当（SHOULD）使用 Django 的安全 URL 辅助函数（如 `django.utils.http.url_has_allowed_host_and_scheme`），而非自定义解析。

不安全模式：

* `return redirect(request.GET.get("next"))` 无验证。
* 用朴素字符串检查实施的重定向白名单。

检测提示：

* 搜索 `redirect(` 并追踪目标来源。
* 搜索名为 `next`、`return_to`、`redirect`、`url` 的参数。

修复：

* 用白名单验证，验证失败时默认返回安全的内部路径。
* 确保通过 `ALLOWED_HOSTS` 的主机验证保持严格（见 DJANGO-HOST-001）。（[Django Project][3]）

---

### DJANGO-HEADERS-001：启用基本安全响应头（SecurityMiddleware + 点击劫持保护）

严重程度：中至 高

必需：

* 应当（SHOULD）使用 `django.middleware.security.SecurityMiddleware` 并适当配置（生产环境），用于：

  * `X-Content-Type-Options: nosniff`（Django 设置 `SECURE_CONTENT_TYPE_NOSNIFF`，默认 `True`）。（[Django Project][3]）
  * `Referrer-Policy`（Django 设置 `SECURE_REFERRER_POLICY`，默认 `'same-origin'`）。（[Django Project][3]）
  * COOP（Django 设置 `SECURE_CROSS_ORIGIN_OPENER_POLICY`，默认 `'same-origin'`）。（[Django Project][3]）
  * 适当时的 HTTPS 重定向与 HSTS（见 DJANGO-HTTPS-001）。（[Django Project][3]）
* 应当（SHOULD）通过 X-Frame-Options 中间件启用点击劫持保护；Django 安全文档强烈推荐不需要第三方嵌入的站点使用。（[Django Project][2]）

不安全模式：

* 缺少 SecurityMiddleware。
* 缺少点击劫持保护（或全局禁用）而无明确的嵌入需求。
* 对敏感端点过宽的嵌入允许。

检测提示：

* 检查 `MIDDLEWARE` 中是否有 SecurityMiddleware 和 XFrameOptionsMiddleware。
* 搜索按视图禁用嵌入/CSRF 保护的情况。

修复：

* 添加/启用中间件并有意配置相关设置。（[Django Project][3]）

说明：

* 某些响应头可能在边缘层（CDN/反向代理）设置。如果在应用代码中不可见，标记为"在边缘层验证"。

---

### DJANGO-CSP-001：部署内容安全策略（CSP）作为纵深防御

严重程度：中（渲染不受信任内容的应用为高）

说明：最重要的是设置 CSP 的 script-src。其他指令不那么重要，为了便于开发通常可以省略。

必需：

* 应当（SHOULD）部署 CSP 以缓解 XSS 和内容注入类别；Django 的安全文档推荐 CSP，并指出这是 Django 6.0 中的新功能。（[Django Project][2]）
* 必须（MUST）理解 CSP 的局限性：

  * 避免将路由排除在 CSP 覆盖之外；Django 警告由于同源策略，未受保护的页面可能削弱受保护页面的防护。（[Django Project][2]）
* 可以（MAY）从 `SECURE_CSP_REPORT_ONLY` 开始安全迭代（Django 提供仅报告模式支持）。（[Django Project][3]）

不安全模式：

* 渲染用户控制内容的应用无 CSP。
* CSP 排除"只有几个页面"（削弱整体保护），尤其是任何有注入面的页面。（[Django Project][2]）
* CSP 使用过于宽松的指令（如广泛使用 `unsafe-inline`）而无正当理由。

检测提示：

* 搜索 `SECURE_CSP`、`SECURE_CSP_REPORT_ONLY` 和 CSP 中间件配置。
* 检查反向代理/CDN 配置中的 CSP 响应头。

修复：

* 实施切实可行的 CSP，理想情况下先仅报告，再强制执行。（[Django Project][3]）

---

### DJANGO-AUTH-001：密码存储必须使用 Django 的安全哈希器；密码策略必须配置

严重程度：高

必需：

* 必须（MUST）使用 Django 内置的密码哈希（绝不存储明文或可逆加密的密码）。
* 应当（SHOULD）优先使用现代哈希器并保持默认值更新；Django 记录了 `PASSWORD_HASHERS`，并包含现代选项（Argon2、bcrypt、scrypt、PBKDF2 变体）。（[Django Project][3]）
* 应当（SHOULD）为生产密码策略配置 `AUTH_PASSWORD_VALIDATORS`（默认为空）。（[Django Project][3]）

不安全模式：

* 自定义密码存储或哈希。
* 数据库字段中存储明文密码。
* 面向消费者的应用无密码验证。

检测提示：

* 搜索 `.set_password(` 的使用 vs 手动哈希。
* 检查设置中的 `PASSWORD_HASHERS` 和 `AUTH_PASSWORD_VALIDATORS`。（[Django Project][3]）

修复：

* 使用 Django 认证用户模型 API。
* 启用与产品风险状况相称的密码验证器。（[Django Project][3]）

---

### DJANGO-AUTHZ-001：授权必须显式且一致

严重程度：高

必需：

* 必须（MUST）在每个特权操作（查看、修改、类似 admin 的操作）上强制执行授权检查。
* 必须（MUST NOT）在没有服务端权限检查的情况下仅依赖 UI 层限制（如隐藏按钮）。
* 应当（SHOULD）在适用时使用 Django 的权限/组和按对象授权模式。

不安全模式：

* 假定"用户已登录"即"用户可以执行操作"的视图。
* 更新/删除端点缺少授权检查。

检测提示：

* 枚举改变状态的视图；确保其验证所有权/权限。
* 查找仅使用 `is_authenticated` 或仅使用 `is_staff` 而不检查对象级访问的情况。

修复：

* 添加显式权限检查，并测试未授权访问。

---

### DJANGO-ADMIN-001：Django admin 必须被视为高价值目标

严重程度：高

必需：

* 必须（MUST）确保 admin 受强认证和仅 HTTPS 传输保护（见 DJANGO-HTTPS-001）。（[Django Project][1]）
* 应当（SHOULD）在可能时限制 admin 的暴露（网络白名单、VPN、SSO 或额外认证控制）。
* 应当（SHOULD）审计已安装的 admin 扩展和第三方应用是否存在 XSS/CSRF 暴露。

不安全模式：

* admin 以弱认证暴露于互联网。
* admin 通过 HTTP 提供。

检测提示：

* 搜索 `urlpatterns` 中的 `admin.site.urls`。
* 检查部署配置中的 IP 白名单或认证网关。

修复：

* 添加网络控制并强制 HTTPS。

---

### DJANGO-LOG-001：日志与错误报告不得泄露密钥

严重程度：中至 高

必需：

* 必须（MUST NOT）记录密钥（包括 `SECRET_KEY`、会话 Cookie、认证请求头、密码重置令牌）。
* 必须（MUST）审慎配置生产日志；Django 的部署检查清单明确要求在进入生产前审查日志配置。（[Django Project][1]）
* 必须（MUST）确保生产环境 `DEBUG=False`，以免异常以敏感上下文渲染。（[Django Project][1]）

不安全模式：

* 在生产环境记录完整请求头或 Cookie。
* 打印设置字典。
* 调试错误页面。

检测提示：

* 检查 `LOGGING` 配置；搜索记录请求头/Cookie 的中间件。
* 搜索 `print(settings` / `logging.info(request.META)` 模式。

修复：

* 脱敏敏感值；记录 ID 而非密钥。
* 使用结构化日志和安全错误监控工具。（[Django Project][1]）

---

### DJANGO-SUPPLY-001：依赖与修补卫生（Django + 安全关键依赖）

严重程度：中（已知漏洞版本为高）

必需：

* 应当（SHOULD）固定并定期更新 Django 和安全关键依赖。
* 必须（MUST）及时响应 Django 安全发布。

检测提示：

* 检查 `requirements.txt`、锁文件、构建镜像。
* 识别 Django 版本；与最新受支持版本比较（Django 的下载页面发布当前稳定和受支持分支）。（[Django Project][9]）

修复：

* 升级到已修补版本；为之前易受攻击的类别添加回归测试。

---

## 5) 实用扫描启发式（如何"搜寻"）

主动扫描时，使用这些高信号模式：

* 部署/开发服务器：

  * `manage.py runserver`、`runserver 0.0.0.0`、`--insecure`（[Django Project][1]）
* 调试/设置：

  * `DEBUG = True`（[Django Project][1]）
  * `SECRET_KEY =`、`SECRET_KEY_FALLBACKS`（[Django Project][1]）
* 主机验证：

  * `ALLOWED_HOSTS = ['*']`（[Django Project][3]）
* HTTPS 与代理：

  * `SECURE_SSL_REDIRECT`、`SECURE_HSTS_SECONDS`、`SECURE_PROXY_SSL_HEADER`（[Django Project][3]）
* Cookie / 会话：

  * `SESSION_COOKIE_SECURE`、`SESSION_COOKIE_HTTPONLY`、`SESSION_COOKIE_SAMESITE`（[Django Project][3]）
  * `CSRF_COOKIE_SECURE`、`CSRF_COOKIE_HTTPONLY`、`CSRF_COOKIE_SAMESITE`（[Django Project][3]）
* CSRF 绕过：

  * `csrf_exempt`、缺少 `CsrfViewMiddleware`、无 `{% csrf_token %}` 的 POST 表单（[Django Project][4]）
* XSS：

  * `|safe`、`autoescape off`、`mark_safe(`、HTML 字符串拼接（[Django Project][5]）
* SQL 注入：

  * `.raw(`、`.extra(`、`RawSQL(`、带格式化 SQL 字符串的 `cursor.execute(`（[Django Project][7]）
* 用户上传 / 媒体：

  * `request.FILES`、`MEDIA_ROOT`、`MEDIA_URL`、内联提供媒体；`MEDIA_ROOT == STATIC_ROOT`（[Django Project][1]）
* 重定向：

  * `redirect(request.GET.get("next"))` 模式；缺少白名单验证
* 安全响应头与 CSP：

  * 缺少 `SecurityMiddleware`、缺少 X-Frame-Options 保护、未采用 `SECURE_CSP`（在适当时）（[Django Project][2]）

始终尝试确认：

* 数据来源（不受信任 vs 受信任）
* 汇点类型（模板/SQL/子进程/文件/重定向/http）
* 存在的防护控制（中间件、验证、白名单、授权检查）
* 安全响应头/控制是在应用中设置还是在边缘层设置

---

## 6) 来源（访问于 2026-01-27）

主要 Django 文档：

```text
- Django Downloads (current stable & supported branches): https://www.djangoproject.com/download/
- Django 6.0 Release Notes: https://docs.djangoproject.com/en/6.0/releases/6.0/
- Django: Deployment checklist (incl. check --deploy, runserver warning, HTTPS/cookies guidance): https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/
- Django: Settings reference (SecurityMiddleware settings, cookies, SECRET_KEY_FALLBACKS, CSP settings): https://docs.djangoproject.com/en/6.0/ref/settings/
- Django: Security in Django (XSS/CSRF/SQLi/clickjacking/HTTPS/host header validation/uploads/CSP): https://docs.djangoproject.com/en/6.0/topics/security/
- Django: CSRF how-to (middleware, csrf_token usage, AJAX header patterns, csrf_exempt cautions): https://docs.djangoproject.com/en/6.0/howto/csrf/
- Django: Performing raw SQL queries (parameterization guidance): https://docs.djangoproject.com/en/6.0/topics/db/sql/
- Django: QuerySet API reference (extra() cautions; "do not quote placeholders" guidance): https://docs.djangoproject.com/en/6.0/ref/models/querysets/
- Django: Template built-ins (autoescape tag): https://docs.djangoproject.com/en/6.0/ref/templates/builtins/
- Django: Template language reference (turning off autoescape & risks): https://docs.djangoproject.com/en/6.0/ref/templates/language/
- Django: Utilities reference (e.g., format_html): https://docs.djangoproject.com/en/6.0/ref/utils/
```

OWASP：

```text
- OWASP Cheat Sheet Series: Django Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Django_Security_Cheat_Sheet.html
```

[1]: https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/ "https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/"
[2]: https://docs.djangoproject.com/en/6.0/topics/security/ "Security in Django | Django documentation | Django"
[3]: https://docs.djangoproject.com/en/6.0/ref/settings/ "Settings | Django documentation | Django"
[4]: https://docs.djangoproject.com/en/6.0/howto/csrf/ "How to use Django's CSRF protection | Django documentation | Django"
[5]: https://docs.djangoproject.com/en/6.0/ref/templates/builtins/ "https://docs.djangoproject.com/en/6.0/ref/templates/builtins/"
[6]: https://docs.djangoproject.com/en/6.0/ref/utils/ "https://docs.djangoproject.com/en/6.0/ref/utils/"
[7]: https://docs.djangoproject.com/en/6.0/topics/db/sql/ "https://docs.djangoproject.com/en/6.0/topics/db/sql/"
[8]: https://docs.djangoproject.com/en/6.0/ref/models/querysets/ "https://docs.djangoproject.com/en/6.0/ref/models/querysets/"
[9]: https://www.djangoproject.com/download/ "Download Django | Django"
