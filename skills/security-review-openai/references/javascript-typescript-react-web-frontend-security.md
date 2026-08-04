# React（JavaScript/TypeScript）Web 安全规范（React 19.x，TypeScript 5.x）

本文档定位为一份**安全规范**，用于支撑：

1. 新 React 代码的**安全默认代码生成**。
2. 现有 React 代码的**安全审查 / 漏洞搜寻**（被动"工作时留意问题"和主动"扫描代码库并报告发现"）。

它有意写成一组**规范性要求**（"MUST/SHOULD/MAY"）加上**审计规则**（不良模式长什么样、如何检测、如何修复/缓解）。

---

## 0）安全、边界和反滥用约束（必须遵守）

* 不得请求、输出、记录或提交机密（API 密钥、OAuth 客户端机密、私钥、会话 Cookie、JWT、签名密钥）。

  * 前端注意事项：任何发送到浏览器的内容，最终用户和攻击者都可以观察到（查看源代码、开发者工具、代理）；切勿将客户端代码或"打包中的环境变量"视为机密。（[create-react-app.dev][1]）
* 不得通过禁用保护来"修复"安全问题（例如为"让它工作"而关闭 CSP、在无文档化且受限的计划下添加 `unsafe-inline`/`unsafe-eval`、使用 Cookie 时禁用 CSRF 防护、放宽 CORS、跳过净化，或"临时"绕过却随产品发布）。（[OWASP Cheat Sheet Series][2]）
* 审计时必须提供**基于证据的发现**：引用支持该主张的文件路径、代码片段和配置值。
* 必须诚实对待不确定性：如果某项保护可能存在于基础设施层（CDN/WAF/反向代理），应报告为"应用代码中不可见；请通过运行时响应头/边缘配置验证"。
* 必须假定任何跨越信任边界的数据（URL、存储、网络、postMessage、第三方脚本）都可能受攻击者影响，除非证明相反（见 §2.1）。

---

## 1）运行模式

### 1.1 生成模式（默认）

当被要求编写新 React 代码或修改现有代码时：

* 必须遵循本规范中的每一项 **MUST** 要求。
* 除非用户明确另有说明，应遵循每一项 **SHOULD** 要求。
* 必须优先选择安全默认的 API 和经过验证的库，而非自定义安全代码。
* 必须避免引入新的危险汇点（原始 HTML 插入、`innerHTML` 等直接 DOM 汇点、动态代码执行、不受信任的重定向/导航、第三方脚本注入、不安全的令牌存储等）。（[MDN Web Docs][3]）

### 1.2 被动审查模式（编辑期间始终开启）

在 React 代码库的任何位置工作时（即使用户未要求安全扫描）：

* 必须"留意"所接触/附近代码中对本规范的违反。
* 应在问题出现时提及，并附简要说明 + 安全修复建议。

### 1.3 主动审计模式（明确扫描请求）

当用户要求"扫描""审计"或"搜寻漏洞"时：

* 必须系统性地搜索代码库中违反本规范之处。
* 必须以结构化格式输出发现（见 §2.3）。

建议的审计顺序：

1. 应用入口点、构建工具（Vite/Webpack/CRA/Next）、部署配置、CDN/静态托管配置。
2. 机密与配置暴露（环境变量、运行时配置注入、源映射）。
3. 不受信任数据的渲染（XSS/DOM XSS），尤其是 `dangerouslySetInnerHTML`、markdown/HTML 渲染器、URL 属性。
4. 直接 DOM 使用和危险的 JS 执行（`innerHTML`、`eval`、`new Function`、`document.write` 等）。
5. 认证与会话模式（令牌存储、Cookie、CSRF 交互、OAuth 流程）。
6. 网络层（axios/fetch 封装、动态 base URL、携带凭据的请求、数据外泄风险）。
7. 导航与重定向处理（开放重定向、`window.location`、`target=_blank`、`window.open`）。
8. 第三方脚本/标签/分析及完整性控制（CSP、SRI）。
9. Service Worker/PWA 行为（HTTPS、缓存规则、更新策略）。
10. 应用或边缘层安全响应头态势（CSP、点击劫持、nosniff、引用者策略）。（[OWASP Cheat Sheet Series][2]）

---

## 2）定义与审查指引

### 2.1 不受信任的输入（除非证明相反，否则视为攻击者控制）

示例包括：

* 来自 URL 的数据：`window.location`、查询参数、哈希片段、路由参数。
* 来自浏览器存储的任何数据：`localStorage`、`sessionStorage`、`IndexedDB`（包括应用先前写入的数据——因为 XSS 或扩展可篡改它们）。（[OWASP Cheat Sheet Series][4]）
* 来自跨窗口消息的任何数据：`window.postMessage` 载荷。（[OWASP Cheat Sheet Series][4]）
* 来自远程 API、代理到客户端的 Webhook、GraphQL 响应、CMS 内容、功能开关服务的任何数据。
* 在界面中渲染的任何持久化用户内容（个人资料、评论、富文本、markdown）。
* 第三方脚本或标签管理器产生的任何数据（除非受到严格管控，否则视为不受信任）。（[OWASP Cheat Sheet Series][5]）

### 2.2 状态变更请求（前端视角）

如果请求可以创建/更新/删除数据、改变认证/会话状态、触发副作用（购买、发送邮件、Webhook）或发起特权操作，则该请求为状态变更请求。

前端特别说明：

* 状态变更通常由 `fetch/axios` 调用或表单提交触发。如果认证基于 Cookie，这些调用可能与 CSRF 相关（§4 REACT-CSRF-001）。（[OWASP Cheat Sheet Series][6]）

### 2.3 要求的审计发现格式

对发现的每个问题，输出：

* 规则 ID：
* 严重性：严重 / 高 / 中 / 低
* 位置：文件路径 + 组件/函数 + 行号
* 证据：确切的代码/配置片段
* 影响：可能出什么问题、谁可以利用
* 修复：安全变更（优先最小差异）
* 缓解：如立即修复困难时的纵深防御
* 误报说明：不确定时应核实什么

---

## 3）安全基线：最低生产配置（生产环境中的 MUST）

这是防止常见 React 前端错误配置的最小"生产基线"。

### 3.1 生产构建与配置卫生（MUST）

* 必须发布生产构建（压缩、无仅开发环境的浮层/工具、正确的模式标志）。
* 必须确保构建时配置不会将机密嵌入已发布的 JS/HTML/CSS。构建时的"环境变量"不是机密；应视为公开。（[create-react-app.dev][1]）
* 应将源映射视为敏感的运维工件：

  * 要么不公开发布，要么仅在预期位置发布（例如在认证之后，或提供给错误报告服务商），因为它们会暴露代码结构和内部 URL。

### 3.2 浏览器强制保护（SHOULD，但为现代应用基线预期）

* 应部署 CSP 作为针对 XSS 的纵深防御，并保持与 React 构建兼容（除非严格必要并有记录，否则避免 `unsafe-inline` 和 `unsafe-eval`）。（[OWASP Cheat Sheet Series][2]）
* 应对从 CDN 加载的任何第三方脚本/样式使用子资源完整性（SRI）（或改为自托管）。（[MDN Web Docs][7]）
* 应通过 `frame-ancestors`（CSP）和/或 `X-Frame-Options` 启用点击劫持防御，除非嵌入是明确的产品需求。（[MDN Web Docs][8]）

### 3.3 高风险功能基线（如使用则为 MUST）

* 如渲染任何用户提供的 HTML/markdown/富文本：

  * 必须在插入前净化，并避免原始 DOM 汇点。（[OWASP Cheat Sheet Series][9]）
* 如使用 Service Worker / PWA：

  * 必须通过 HTTPS 提供服务，并实施安全的缓存/更新策略（Service Worker 是强大的请求/响应代理）。（[MDN Web Docs][10]）

---

## 4）规则（生成 + 审计）

每条规则包含：要求做法、不安全模式、检测提示和补救措施。

### REACT-CONFIG-001：切勿在客户端捆绑包中嵌入机密（环境变量是公开的）

严重性：严重（如果机密暴露）

要求：

* 不得将机密放入 React 代码、`public/` 资产或供客户端消费的构建时环境变量中。
* 必须假定 React 应用在运行时可得任何值，攻击者都能提取。

不安全模式：

* 使用构建时环境变量存放机密：

  * 包含私钥或凭据的 `process.env.REACT_APP_*`。
  * 包含机密的 `import.meta.env.VITE_*`。
* 在 JS/TS 中硬编码机密、提交 `.env`，或在面向所有用户的 `public/config.json` 中放置机密。

检测提示：

* 搜索：

  * `REACT_APP_`、`VITE_`、`NEXT_PUBLIC_`、`process.env.`、`import.meta.env.`
  * `apiKey`、`secret`、`token`、`private`、`password`、`client_secret`
* 检查 `public/` 中是否有运行时配置 JSON。

修复：

* 将机密移至服务端（API、BFF、无服务器函数）。
* 如浏览器需要调用第三方 API，使用后端铸造短期、有作用域的令牌。

备注：

* CRA 明确警告不要存储机密，并指出环境变量会嵌入构建产物，任何检查文件的人都能看到。（[create-react-app.dev][1]）
* Vite 明确指出，暴露给客户端代码的变量最终会进入客户端捆绑包，不应包含敏感信息。（[vitejs][11]）

---

### REACT-XSS-001：不要对不受信任的内容使用 `dangerouslySetInnerHTML`（净化或避免）

严重性：高（仅当你能证明攻击者控制的 HTML 到达该处）

要求：

* 除非绝对必要，必须避免 `dangerouslySetInnerHTML`。
* 如果必须使用：

  * 必须使用经过验证的净化器（例如 DOMPurify）并以白名单导向配置净化不受信任的 HTML。
  * 必须将净化逻辑集中放置并接受严格审查。
  * 应添加 CSP 并考虑 Trusted Types（见 REACT-TT-001）。

不安全模式：

* `<div dangerouslySetInnerHTML={{ __html: userHtml }} />`，其中 `userHtml` 来自 API/URL/存储。
* 用正则、临时剔除或不完整的白名单做"净化"。

检测提示：

* 搜索：`dangerouslySetInnerHTML`、`__html:`
* 追溯 HTML 字符串的来源（API/CMS/URL/localStorage）。

修复：

* 改为安全渲染：

  * 将结构化数据渲染为 React 元素/组件，而非 HTML 字符串。
  * 如需富文本，用 DOMPurify（或同等工具）净化并渲染净化后的输出。
* 添加 CSP；尽可能移除危险汇点。

备注：

* React 明确警告 `dangerouslySetInnerHTML` 是危险的，误用可能引入 XSS。（[React][12]）
* OWASP 明确将 React 未净化的 `dangerouslySetInnerHTML` 列为常见框架"逃生舱"陷阱。（[OWASP Cheat Sheet Series][9]）
* DOMPurify 自称是面向 HTML/SVG/MathML 的 XSS 净化器。（[GitHub][13]）

---

### REACT-XSS-002：依赖 React 的默认转义行为；不要绕过它

严重性：高（被绕过时）

要求：

* 必须通过常规 JSX 插值（`{value}`）和 React props 渲染不受信任的字符串，它们默认会被转义。
* 不得从不信任数据构建 HTML 字符串，再以任何方式将其注入 DOM。
* 应将任何"逃生舱"视为高风险并要求审查。

不安全模式：

* 将不受信任的文本转换为 HTML 并注入：

  * `element.innerHTML = userValue`
  * `document.write(userValue)`
  * `insertAdjacentHTML(..., userValue)`

检测提示：

* 搜索 DOM 汇点：`innerHTML`、`outerHTML`、`insertAdjacentHTML`、`document.write`、`DOMParser`、`createContextualFragment`。

修复：

* 通过 React（JSX）渲染文本内容，使其被转义。
* 如果确实需要 HTML，先净化，再应用 REACT-XSS-001 + REACT-TT-001。

备注：

* React 文档（JSX）指出，React DOM 在渲染前会转义嵌入 JSX 的值，以帮助防止注入攻击。（[React][14]）

---

### REACT-DOM-001：避免 React 代码中的 DOM XSS 注入汇点（使用安全替代方案）

严重性：高

要求：

* 必须避免直接 DOM 注入汇点，即使在 React 渲染之外，除非受到严格管控。
* 如果必须使用 DOM 汇点：

  * 必须确保输入可信/经过验证/已净化。
  * 应强制执行 Trusted Types（REACT-TT-001）。

不安全模式：

* `someEl.innerHTML = untrusted`
* `document.write(untrusted)`
* `new DOMParser().parseFromString(untrusted, 'text/html')` 后接插入

检测提示：

* 搜索：`innerHTML`、`outerHTML`、`document.write`、`DOMParser`、`Range().createContextualFragment`、`insertAdjacentHTML`

修复：

* 优先使用：

  * `textContent` 用于文本插入。
  * React 渲染而非手工 DOM 操作。
  * 任何必需的 HTML 解析使用经过审查的净化器。

备注：

* Trusted Types 文档将 `Element.innerHTML` 和 `document.write()` 等 HTML 汇点定义为注入汇点，在输入受攻击者控制时可执行脚本。（[MDN Web Docs][3]）
* OWASP HTML5 指南建议为不受信任数据的赋值使用 `textContent` 而非 `innerHTML`。（[OWASP Cheat Sheet Series][4]）

---

### REACT-URL-001：验证并约束用于 `href`、`src`、导航和重定向的不受信任 URL

严重性：高，仅当你能证明它们受攻击者控制

要求：

* 必须将任何源自不受信任输入的 URL 视为危险。
* 必须对协议（如适用时还包括主机）使用白名单：

  * 通常只允许 `https:`（以及用于 localhost/开发环境的 `http:`）和应用内导航的相对 URL。
  * 必须明确阻止 `javascript:` 和危险的 `data:` 用法，除非有专门的验证和明确用例。
* 应优先使用同站相对路径（例如 `/settings`）而非绝对 URL。
* 必须验证"returnTo/next/redirect"参数（见 REACT-REDIRECT-001）。

不安全模式：

* `<img src={userProvidedUrl}>...`（可用于跟踪 / 数据外泄；用于脚本/iframe 时也有风险）
* `window.location = next`
* `navigate(next)`，其中 `next` 来自未经验证的查询参数

检测提示：

* 搜索：

  * `href={`、`src={`、`window.location`、`location.href`、`window.open`、`navigate(`、`redirectTo`、`returnTo`、`next=`
* 追踪该值是否源自 URL/查询参数/存储/API。

修复：

* 实现共享的 `safeUrl()` 工具：

  * 用 `new URL(value, base)` 解析
  * 强制执行协议白名单和主机白名单（或强制同源）
  * 对重定向：仅允许相对路径（以 `/` 开头）或绝对源的严格白名单。
* 验证失败时回退到安全默认值。

备注：

* OWASP 明确提到 React 的 `dangerouslySetInnerHTML` 风险，并指出没有专门验证，React 无法安全处理 `javascript:` 或 `data:` URL。（[OWASP Cheat Sheet Series][9]）

---

### REACT-MARKUP-001：Markdown / 富文本渲染必须安全配置

严重性：中

要求：

* 如果 markdown/富文本来自用户或 CMS，必须假定其可能受攻击者控制。
* 必须确保未净化前不渲染原始 HTML。
* 应优先选择满足以下条件的 markdown 渲染器：

  * 默认不允许原始 HTML，或
  * 可配置为不允许原始 HTML，或
  * 在渲染前净化 HTML 输出。

不安全模式：

* 启用"原始 HTML 直通"的 Markdown 渲染（例如允许 HTML 的选项/插件）。
* 未经净化即内联渲染用户提供的 SVG/MathML/HTML。

检测提示：

* 搜索常见库和危险选项：

  * `marked`、`markdown-it`、`react-markdown`、`rehype-raw`、`sanitize: false`、`allowDangerousHtml` 等。
* 查找与"markdown 输出"配合使用的 `dangerouslySetInnerHTML`。

修复：

* 禁用原始 HTML 直通。
* 渲染前用经过验证的净化器（例如 DOMPurify）净化输出。

备注：

* OWASP XSS 指南强调，框架逃生舱需要输出编码和/或 HTML 净化。（[OWASP Cheat Sheet Series][9]）

---

### REACT-TT-001：在可行处使用 Trusted Types（配合 CSP）加固 DOM XSS 汇点

严重性：低

要求：

* 应首先考虑以仅报告模式启用 Trusted Types，待违规解决后再强制执行。
* 应将 Trusted Types 策略集中管理，并将其视为需要审查的高风险代码。
* 不得创建仅"直通"不受信任字符串的宽松策略。

不安全模式：

* 对 HTML 汇点返回未经净化的原始字符串的 Trusted Types 策略。
* 代码库中大量分散的策略（难以审计）。

检测提示：

* 搜索：

  * `trustedTypes.createPolicy`
  * CSP 指令：`require-trusted-types-for`、`trusted-types`
* 搜索残留的 DOM 汇点（REACT-DOM-001）。

修复：

* 实施少量严格限定范围的策略：

  * HTML 策略使用净化器（DOMPurify 或同等工具）。
  * 脚本 URL 策略使用严格白名单。
* 以仅报告模式运行，修复违规后强制执行。

备注：

* MDN 将 Trusted Types 描述为一种确保输入在传给注入汇点之前经过转换（通常是净化）的方式，并重点指出 HTML 汇点（`innerHTML`、`document.write`）和 JS URL 汇点（`script.src`）。（[MDN Web Docs][3]）
* W3C Trusted Types 规范将其定位为：通过将汇点锁定为由经过审查的策略创建的带类型值来降低 DOM XSS 风险。（[W3C][15]）

---

### REACT-CSP-001：部署并维护 CSP 作为纵深防御（尤其是渲染不受信任内容时）

严重性：中至高

要求：

* 应在生产环境部署 CSP；对于渲染不受信任内容或集成第三方脚本的应用必须部署。
* 应尽可能避免 `unsafe-inline` 和 `unsafe-eval`。
* 如需要，应对内联脚本使用 CSP nonce/哈希，并保持策略现实可行。
* 应在适当处使用 CSP 要求/鼓励 SRI。

不安全模式：

* 应用外壳（SPA 入口 HTML）上完全没有 CSP。
* 依赖广泛使用 `unsafe-inline`/`unsafe-eval` 且无正当理由的 CSP。
* `script-src *` 或过于宽泛的来源。

检测提示：

* 查找 CSP 配置：

  * 服务器/CDN 配置、`index.html` 响应中的响应头，或框架配置。
* 如仓库中不存在，标记为"在边缘层验证"。

修复：

* 通过 HTTP 响应头添加 CSP（首选）。
* 从仅报告模式开始以减少破坏，然后强制执行。

备注：

* OWASP 将 CSP 描述为针对 XSS 的"纵深防御"，并指出即使在静态站点上它也能帮助强制执行 SRI，但不应是唯一的防御手段。（[OWASP Cheat Sheet Series][2]）

---

### REACT-SRI-001：对第三方脚本和样式使用子资源完整性（SRI）（或自托管）

严重性：低

要求：

* 必须将第三方 JS 等同于在你的源中运行任意代码。
* 如果从 CDN 或第三方加载：

  * 应在适用处使用 SRI（`integrity=...`）和 `crossorigin`。
  * 应固定确切版本（避免"latest" URL）。
  * 对关键代码应优先自托管。

不安全模式：

* `<script src="https://cdn.example.com/lib/latest.js"></script>` 且无完整性校验。
* 无治理地动态加载任意脚本的标签管理器。

检测提示：

* 在 `public/index.html`、模板或 SSR 包装中搜索：

  * `<script src=`、`<link rel="stylesheet" href=`
  * 标签管理器代码片段（GTM、Segment 等）
* 识别运行时 JS 中动态加载的脚本。

修复：

* 为稳定的第三方资产添加 SRI 哈希或自托管。
* 对标签管理器应用治理控制（见 REACT-3P-001）。

备注：

* MDN 将 SRI 描述为一项安全功能，使浏览器能够通过校验密码哈希来验证所获取资源（例如来自 CDN）未被篡改。（[MDN Web Docs][7]）
* OWASP CSP 指南指出，CSP 可以强制执行 SRI，即使在静态站点上也有用。（[OWASP Cheat Sheet Series][2]）

---

### REACT-3P-001：第三方 JavaScript 和标签管理器必须最小化并受治理

严重性：高

要求：

* 必须最小化第三方脚本，并将每一个都视为供应链风险。
* 必须确切知道你的源中执行哪些第三方 JS 以及原因。
* 应实施治理：

  * 审查并固定版本（或在内部镜像）。
  * 限制数据访问（数据层方法）。
  * 使用 SRI 和 CSP；在可行处考虑将不受信任的界面沙箱化到 iframe 中。

不安全模式：

* 未经审查的分析/广告脚本以对 DOM、Cookie、存储和用户数据的完全访问权限运行。
* 可由非工程角色在无变更控制的情况下修改的标签管理器。

检测提示：

* 在 HTML/JS 中搜索常见供应商代码片段：

  * GTM、Segment、Hotjar、FullStory 等。
* 查找动态脚本插入：

  * `document.createElement('script')`、`.src = ...`、`.appendChild(script)`

修复：

* 只保留必要供应商。
* 在可行处：

  * 自托管或镜像脚本。
  * 使用 SRI。
  * 通过受控数据层限制数据暴露。

备注：

* OWASP 指出，第三方 JS 服务器被攻破可注入恶意 JS，并强调任意代码执行以及向第三方披露敏感信息等风险。（[OWASP Cheat Sheet Series][5]）

---

### REACT-AUTH-001：令牌和会话处理必须对 XSS 有弹性（避免在 Web 存储中存放敏感内容）

严重性：中

要求：

* 应避免在 `localStorage`（以及一般的 Web 存储）中存储会话标识符或长期令牌，因为 XSS 可以将其外泄。
* 如果令牌必须存在于客户端：

  * 应优先使用短生命周期并带刷新机制的内存存储。
  * 必须限定令牌的作用域并轮换令牌；避免在持久存储中存放长期不记名令牌。
* 如可能，会话令牌应优先使用 HTTPOnly Cookie（需要 CSRF 策略：见 REACT-CSRF-001）。

不安全模式：

* 用 `localStorage.setItem('token', ...)` / `sessionStorage.setItem('token', ...)` 存储认证令牌。
* 在 `localStorage` 中持久化刷新令牌。
* 将来自 Web 存储的数据视为可信。

检测提示：

* 搜索：`localStorage.`、`sessionStorage.`、`setItem(`、`getItem(`、`token`、`jwt`、`refresh`
* 在认证代码中搜索持久化存储令牌的"记住我"。

修复：

* 改用 HTTPOnly Cookie（服务器端变更）+ CSRF 防护，或使用短期内存令牌。
* 缩小令牌作用域并缩短生命周期。

备注：

* OWASP HTML5 指南建议避免在本地存储中存放敏感信息和会话标识符，并警告一次 XSS 即可窃取 Web 存储中的所有数据。（[OWASP Cheat Sheet Series][4]）
* 面向浏览器的 OAuth 应用指南讨论了存储在 localStorage 等持久浏览器存储中的令牌可能被恶意 JS（例如通过 XSS）访问。（[IETF Datatracker][16]）

---

### REACT-CSRF-001：基于 Cookie 认证的状态变更请求必须受 CSRF 保护

严重性：高

注意：如果应用不使用基于 Cookie 的认证（例如使用 Authentication 头），则 CSRF 不构成问题。

要求：

* 如果应用依赖 Cookie 进行认证：

  * 必须保护状态变更请求（POST/PUT/PATCH/DELETE）免受 CSRF。
  * 应包含 CSRF 令牌机制（同步器令牌或双重提交 Cookie）或适合后端架构的其他稳健模式。
  * 应将 SameSite Cookie 用作纵深防御，而非唯一防线。

不安全模式：

* `fetch('/api/transfer', { method: 'POST', credentials: 'include' })` 且无 CSRF 令牌/头，仅依赖 Cookie。
* 对状态变更操作使用 GET。

检测提示：

* 枚举状态变更网络调用并检查：

  * 是否使用了 `credentials: 'include'` 或 `withCredentials: true`？
  * 是否包含 CSRF 令牌头（例如 `X-CSRF-Token`）？
* 搜索"csrf"工具；如不存在，视为可疑。

修复：

* 添加 CSRF 令牌流程：

  * 从安全端点获取令牌并附加到状态变更请求。
  * 在服务端验证。
* 保留 SameSite Cookie 和 Origin/Referer 验证作为纵深防御。

备注：

* OWASP CSRF 指南将 SameSite 行为（Lax/Strict/None）解释为纵深防御技术，并说明为何 Lax 通常是可用性/安全性的平衡点，但它不能完全替代 CSRF 防护。（[OWASP Cheat Sheet Series][6]）

---

### REACT-AUTHZ-001：不要依赖仅前端的授权

严重性：高（仅当用作主要保护时）

要求：

* 必须将所有前端授权检查视为仅用户体验。
* 必须对任何受保护资源或操作在服务器上强制执行授权。

不安全模式：

* 界面中隐藏的"受保护"操作，但无需服务器检查即可通过 API 调用。
* `if (user.isAdmin) { showAdminPanel(); }` 之类的客户端检查，且无服务端强制。

检测提示：

* 查找敏感操作周围的界面门禁，并验证服务器端点强制执行授权。
* 在仅前端审计中，报告为"客户端检查不是安全；请验证后端"。

修复：

* 添加/确认服务端授权检查。
* 仅将前端门禁保留为便利措施。

备注：

* 这是通用 Web 应用安全属性；React 本身无法保护服务器资源。

---

### REACT-NET-001：防止通过动态出站请求发生数据外泄和凭据泄露

严重性：中至高

要求：

* 必须避免向攻击者控制的源发起带认证的请求。
* 应避免允许用户输入控制请求目的地（协议/主机/端口）。
* 应集中网络客户端（fetch/axios），并配以：

  * 固定的 `baseURL`（或严格白名单），
  * 严格的重定向处理，
  * 明确的 `credentials` 用法。

不安全模式：

* `fetch(userProvidedUrl, { credentials: 'include' })`
* `axios.create({ baseURL: userProvidedBase })`
* 客户端中携带敏感响应头访问任意域名的"URL 抓取/预览"功能。

检测提示：

* 搜索 `fetch(` / `axios(`，其中第一个参数或 `baseURL` 源自：

  * 查询参数、localStorage、API 响应、postMessage
* 搜索 `credentials: 'include'`、`withCredentials: true`。

修复：

* 强制执行目的地白名单；除非明确要求，禁止跨源请求。
* 对任何非白名单目的地剥离凭据/Authorization 头。

备注：

* 即使浏览器限制部分跨源行为，向不受信任端点泄露令牌/响应头仍是常见故障模式。

---

### REACT-REDIRECT-001：防止开放重定向和不受信任的导航

严重性：中

要求：

* 必须验证源自不受信任输入（`next`、`returnTo`、`redirect`）的重定向/导航目标。
* 应只允许同站相对路径，或对绝对 URL 使用受信任源的严格白名单。

不安全模式：

* `window.location.href = new URLSearchParams(location.search).get('next')`
* `navigate(next)`，其中 `next` 来自查询参数。

检测提示：

* 搜索：`next`、`returnTo`、`redirect`、`window.location`、`navigate(`
* 追溯重定向目标的来源。

修复：

* 只允许相对路径（`/^\/[^\s]*$/`）或白名单源。
* 无效时回退到安全默认值（例如 `/`）。

备注：

* 开放重定向常被用于网络钓鱼，并可能破坏 SSO/OAuth 流程。

---

### REACT-SW-001：Service Worker 是特权级组件；要求 HTTPS 和安全的缓存/更新规则

严重性：中

要求：

* 必须通过 HTTPS 提供服务工作者（`localhost` 开发环境除外），并且只在安全上下文中部署。
* 必须避免缓存敏感的带认证 API 响应，除非经过专门设计和威胁建模。
* 应实施安全的更新策略（提示刷新、版本化缓存、激活时移除旧缓存）。

不安全模式：

* 为带认证的应用注册 Service Worker，并不加区分地"缓存一切"。
* 包含 PII 或用户特定内容的长期缓存跨账户共享。

检测提示：

* 搜索：

  * `navigator.serviceWorker.register`
  * `workbox`、`precacheAndRoute`、自定义 `fetch` 处理程序
* 检查缓存模式（`caches.open`、`cache.put`、`respondWith`）。

修复：

* 将缓存限制为仅静态资产（JS/CSS/图片），除非你设计了离线模型。
* 如果必须缓存用户特定数据，确保缓存键按用户隔离。
* 提供清晰的更新机制。

备注：

* MDN 指出 Service Worker 出于安全原因要求 HTTPS，并像请求/响应代理一样工作。（[MDN Web Docs][10]）
* "安全上下文"的存在是为了防止中间人攻击者访问强大 API；Service Worker 就是此类强大功能的一个例子。（[MDN Web Docs][18]）

---

### REACT-HEADERS-001：确保为 React 应用外壳设置必要安全响应头（应用层或边缘层）

严重性：中

要求（从某个源提供服务的典型 SPA）：

* 应设置：

  * CSP（`Content-Security-Policy`）
  * `X-Content-Type-Options: nosniff`
  * 点击劫持防护（CSP 中的 `frame-ancestors` 和/或 `X-Frame-Options`）
  * `Referrer-Policy`
  * 酌情使用 `Permissions-Policy`
* 必须确保这些响应头在某个位置（CDN/边缘/服务器）设置，即使不在仓库中。

不安全模式：

* 任何位置（应用或边缘）都没有安全响应头。
* 渲染不受信任内容或使用第三方脚本的应用缺少 CSP。

检测提示：

* 检查仓库中的服务器/CDN 配置（nginx、Cloudflare、Vercel 配置等）。
* 如缺失，标记为"在运行时/边缘层验证"。

修复：

* 在边缘层集中设置响应头。
* 保持 CSP 现实可行并迭代推进（仅报告 → 强制执行）。

备注：

* MDN 点击劫持指南讨论了包括 `X-Frame-Options` 和 CSP `frame-ancestors` 在内的防御措施。（[MDN Web Docs][8]）
* OWASP CSP 指南解释了通过响应头交付的方式，并建议响应头为首选机制。（[OWASP Cheat Sheet Series][2]）

---

### REACT-POSTMSG-001：`postMessage` 必须验证来源并将载荷视为不受信任数据

严重性：中至高（取决于消息能做什么）

要求：

* 发送消息时必须指定确切的 `targetOrigin`（而非 `*`），除非有严格理由。
* 接收时必须验证 `event.origin` 并验证消息形状。
* 不得将消息数据作为代码执行或作为 HTML 插入 DOM。

不安全模式：

* 向未知目标发送 `window.postMessage(data, '*')`。
* 接收：

  * `window.addEventListener('message', (e) => { eval(e.data) })`
  * `element.innerHTML = e.data`

检测提示：

* 搜索：`postMessage(`、`addEventListener('message'`
* 检查是否存在来源检查和安全的处理方式。

修复：

* 添加严格的来源白名单和模式验证（例如 zod）。
* 严格将消息载荷视为数据；通过 React 安全渲染。

备注：

* OWASP HTML5 指南建议为 `postMessage` 指定预期来源、检查发送者来源、验证数据，并避免对消息内容使用 eval/innerHTML。（[OWASP Cheat Sheet Series][4]）

---

### REACT-FILE-001：文件上传和预览不得制造客户端活动内容漏洞

严重性：中（如可能发生存储型 XSS 则为高）

要求：

* 必须将用户上传的文件和预览视为潜在恶意。
* 除非已净化且明确要求，不得内联渲染上传的 HTML/SVG/其他活动内容。
* 应仅出于用户体验目的在客户端验证文件类型，但必须依赖服务端验证保证安全。

不安全模式：

* 将用户上传的 HTML 作为内容渲染。
* 通过 `dangerouslySetInnerHTML` 或 `<iframe srcdoc=...>` 未经净化即内联渲染不受信任的 SVG/HTML。

检测提示：

* 搜索上传组件和预览逻辑：

  * `input type="file"`、`FileReader`、`URL.createObjectURL`、`<iframe>`、`<object>`、`<embed>`。
* 追踪上传内容后续在何处显示。

修复：

* 限制接受的类型，在需要处净化，并优先为危险类型采用下载/附件流程。
* 确保服务器强制执行真实策略（类型检查、重命名、扫描、存储在 Web 根目录之外）。

备注：

* OWASP 文件上传指南强调对扩展名白名单、验证文件类型、生成文件名、限制大小、存储在 Web 根目录之外，并在文件可公开获取时考虑"客户端活动内容（XSS、CSRF 等）"。（[OWASP Cheat Sheet Series][19]）

---

### REACT-SUPPLY-001：依赖与供应链卫生（前端 + 构建工具）

严重性：低

要求：

* 必须使用锁文件并在 CI 中强制执行可复现安装。
* 应定期审计依赖并快速响应下列项目的安全公告：

  * React、react-dom、路由库、构建工具（Vite/Webpack）、净化器、认证库等。
* 应减少安装时脚本攻击和仿冒包（typosquatting）风险的暴露。

审计重点：

* CI 应使用 `npm ci`（或 Yarn 冻结锁文件 / pnpm 等效命令）以防止漂移。
* 使用漏洞扫描（`npm audit`、GitHub Dependabot/警报等）。

不安全模式：

* 无锁文件或 CI 忽略锁文件。
* CI 中使用 `npm install` 产生不可复现的构建。
* 未固定或未经审查的高风险依赖；未经审查的突然大版本升级。
* 盲目运行第三方包的安装脚本。

检测提示：

* 检查锁文件：`package-lock.json`、`yarn.lock`、`pnpm-lock.yaml`。
* 检查 CI 脚本中用的是 `npm install` 还是 `npm ci`。
* 搜索 `postinstall` 脚本和可疑的构建步骤。

修复：

* 使用锁文件并在 CI 中强制执行（例如 `npm ci`）。
* 定期运行审计；负责任地固定/升级。
* 在可行处考虑限制安装脚本。

备注：

* npm 文档将 `npm audit` 描述为将项目依赖树提交给注册表以获得已知漏洞报告，并（可选）通过 `npm audit fix` 应用修复，同时指出部分漏洞需要人工审查。（[npm Docs][20]）
* npm 文档将 `npm ci` 描述为面向自动化/CI 环境，要求已有锁文件，并在 `package.json` 与锁文件不一致时失败。（[npm Docs][21]）
* OWASP NPM 安全指南建议强制执行锁文件，并明确推荐 `npm ci` / `yarn install --frozen-lockfile` 以在不一致时中止，同时强调安装时脚本的风险以及使用 `--ignore-scripts` 降低攻击面的选项。（[OWASP Cheat Sheet Series][22]）

---

## 5）实用扫描启发式方法（如何"搜寻"）

主动扫描时，使用这些高信号模式：

* 原始 HTML / XSS 逃生舱：

  * `dangerouslySetInnerHTML`、`__html:`
  * Markdown HTML 直通标志：`rehype-raw`、`allowDangerousHtml`、`sanitize: false`
* DOM XSS 汇点：

  * `innerHTML`、`outerHTML`、`insertAdjacentHTML`、`document.write`、`DOMParser`、`createContextualFragment`
* 危险的 JS 执行：

  * `eval(`、`new Function(`、`setTimeout("`、`setInterval("`
* 不受信任的 URL 注入 / 导航：

  * 带不受信任值的 `href={` / `src={`
  * `window.location`、`location.href`、`window.open`、`navigate(`
  * 查询参数：`next`、`returnTo`、`redirect`
* 令牌/会话风险：

  * `localStorage.setItem`、`sessionStorage.setItem`、与 `token`、`jwt`、`refresh` 一起使用的 `getItem(`
* Cookie/CSRF 耦合：

  * 无 CSRF 响应头的状态变更请求上的 `credentials: 'include'`、`withCredentials: true`
* 第三方脚本：

  * `public/index.html` 中的 `<script src=...>`
  * 标签管理器代码片段和动态脚本插入
* Service Worker：

  * `navigator.serviceWorker.register`、Workbox 使用、自定义 `fetch` 处理程序
* postMessage：

  * 带 `*` 的 `postMessage(`、缺少 `event.origin` 检查
* 供应链：

  * 锁文件缺失、CI 使用 `npm install`、无审计步骤、危险的 postinstall 脚本

始终尝试确认：

* 数据来源（不受信任 vs 可信）
* 汇点类型（React 逃生舱 vs DOM 汇点 vs 导航 vs 存储）
* 存在的防护控制（净化、白名单、CSP/Trusted Types、CSRF 令牌、响应头、治理）

---

## 6）来源（访问于 2026-01-26）

主要 React 文档：

* React 19 稳定版公告——`https://react.dev/blog/2024/12/05/react-19`（[React][23]）
* React DOM 文档：`dangerouslySetInnerHTML` 警告——`https://react.dev/reference/react-dom/components/common#dangerouslysetting-the-inner-html`（[React][12]）
* React（旧版）JSX 转义声明——`https://legacy.reactjs.org/docs/introducing-jsx.html`（[React][14]）

OWASP Cheat Sheet Series：

* 跨站脚本预防（框架逃生舱；React `dangerouslySetInnerHTML`；URL 验证说明）——`https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][9]）
* 内容安全策略——`https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][2]）
* 跨站请求伪造预防——`https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][6]）
* HTML5 安全（Web 存储、postMessage、tabnabbing、沙箱化框架）——`https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][4]）
* 第三方 JavaScript 管理——`https://cheatsheetseries.owasp.org/cheatsheets/Third_Party_Javascript_Management_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][5]）
* 文件上传——`https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][19]）
* NPM 安全最佳实践——`https://cheatsheetseries.owasp.org/cheatsheets/NPM_Security_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][22]）

浏览器/平台参考（MDN、W3C）：

* Trusted Types API——`https://developer.mozilla.org/en-US/docs/Web/API/Trusted_Types_API`（[MDN Web Docs][3]）
* W3C Trusted Types 规范——`https://www.w3.org/TR/trusted-types/`（[W3C][15]）
* 子资源完整性——`https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity`（[MDN Web Docs][7]）
* 点击劫持防御概述——`https://developer.mozilla.org/en-US/docs/Web/Security/Attacks/Clickjacking`（[MDN Web Docs][8]）
* 使用 Service Workers（HTTPS 要求；类代理行为）——`https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers`（[MDN Web Docs][10]）
* 安全上下文（强大 API 仅限 HTTPS）——`https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Secure_Contexts`（[MDN Web Docs][18]）
* 链接 `rel` 值（noopener/noreferrer）——`https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/rel`（[MDN Web Docs][17]）

构建工具 / 环境暴露参考：

* Create React App 环境变量警告——`https://create-react-app.dev/docs/adding-custom-environment-variables/`（[create-react-app.dev][1]）
* Vite 环境变量安全说明——`https://vite.dev/guide/env-and-mode`（[vitejs][11]）

认证/令牌存储指南：

* 面向浏览器的应用的 OAuth 2.0（令牌存储讨论）——`https://datatracker.ietf.org/doc/html/draft-ietf-oauth-browser-based-apps`（[IETF Datatracker][16]）

依赖工具参考：

* npm audit 文档——`https://docs.npmjs.com/cli/v10/commands/npm-audit/`（[npm Docs][20]）
* npm ci 文档——`https://docs.npmjs.com/cli/v10/commands/npm-ci/`（[npm Docs][21]）

净化器参考：

* DOMPurify——`https://github.com/cure53/DOMPurify`（[GitHub][13]）

[1]: https://create-react-app.dev/docs/adding-custom-environment-variables/ "添加自定义环境变量 | Create React App"
[2]: https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html "内容安全策略 - OWASP Cheat Sheet Series"
[3]: https://developer.mozilla.org/en-US/docs/Web/API/Trusted_Types_API "Trusted Types API - Web APIs | MDN"
[4]: https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html "HTML5 安全 - OWASP Cheat Sheet Series"
[5]: https://cheatsheetseries.owasp.org/cheatsheets/Third_Party_Javascript_Management_Cheat_Sheet.html "第三方 JavaScript 管理 - OWASP Cheat Sheet Series"
[6]: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html "跨站请求伪造预防 - OWASP Cheat Sheet Series"
[7]: https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Subresource_Integrity "子资源完整性 - 安全 | MDN"
[8]: https://developer.mozilla.org/en-US/docs/Web/Security/Attacks/Clickjacking "点击劫持 - 安全 | MDN"
[9]: https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html "跨站脚本预防 - OWASP Cheat Sheet Series"
[10]: https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers "使用 Service Workers - Web APIs | MDN"
[11]: https://vite.dev/guide/env-and-mode "环境变量与模式 | Vite"
[12]: https://react.dev/reference/react-dom/components/common "通用组件（例如 <div>）——React"
[13]: https://github.com/cure53/DOMPurify "GitHub - cure53/DOMPurify：DOMPurify——一个纯 DOM、超快、超容错的 HTML、MathML 和 SVG XSS 净化器。DOMPurify 以安全默认工作，但提供大量可配置性和钩子。演示："
[14]: https://legacy.reactjs.org/docs/introducing-jsx.html "介绍 JSX——React"
[15]: https://www.w3.org/TR/trusted-types/ "Trusted Types"
[16]: https://datatracker.ietf.org/doc/html/draft-ietf-oauth-browser-based-apps "

                draft-ietf-oauth-browser-based-apps-26

        "
[17]: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel "HTML 属性：rel - HTML | MDN"
[18]: https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Secure_Contexts "安全上下文 - 安全 | MDN"
[19]: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html "文件上传 - OWASP Cheat Sheet Series"
[20]: https://docs.npmjs.com/cli/v10/commands/npm-audit "npm-audit | npm Docs"
[21]: https://docs.npmjs.com/cli/v10/commands/npm-ci "npm-ci | npm Docs"
[22]: https://cheatsheetseries.owasp.org/cheatsheets/NPM_Security_Cheat_Sheet.html "NPM 安全 - OWASP Cheat Sheet Series"
[23]: https://react.dev/blog/2024/12/05/react-19 "React v19——React"
