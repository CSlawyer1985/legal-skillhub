# jQuery 前端安全规范（jQuery 4.0.x，现代浏览器）

本文档设计为一份**安全规范**，用于支持：

1. 为基于 jQuery 的新前端代码**默认安全地生成代码**。
2. 对现有基于 jQuery 的代码进行**安全审查/漏洞挖掘**（被动"在处理代码时注意问题"和主动"扫描仓库并报告发现"）。

本文档有意以一组**规范性要求**（"必须/应当/可以"MUST/SHOULD/MAY）+ **审计规则**（不良模式长什么样、如何检测、如何修复/缓解）的形式编写。

---

## 0) 安全、边界与反滥用约束（必须遵循 MUST FOLLOW）

* 不得请求、输出、记录或提交机密（API 密钥、密码、私钥、会话令牌、刷新令牌、CSRF 令牌、会话 Cookie）。
* 必须将浏览器视为攻击者可控的环境：

  * 前端检查（UI 门控、"禁用按钮"、隐藏字段、客户端验证）不得被视为授权或安全边界。
  * 即使前端"正确"，也必须存在服务端授权和验证。
* 不得通过禁用保护来"修复"安全问题（例如放宽 CSP 以允许 `unsafe-inline`、启用 JSONP"因为它能用"、添加宽松的 CORS、禁用净化、压制安全检查）。
* 审计时必须提供基于证据的发现：引用文件路径、代码片段和相关配置值。
* 必须诚实地对待不确定性：如果某种保护可能存在于边缘层（CDN/WAF/反向代理头，如 CSP），报告为"仓库中不可见；需在运行时/配置中验证"。

---

## 1) 运行模式

### 1.1 生成模式（默认）

当被要求编写新的 jQuery 代码或修改现有 jQuery 代码时：

* 必须遵循本规范中的每一项**必须**要求。
* 应当遵循每一项**应当**要求，除非用户明确另有说明。
* 必须优先采用默认安全的模式：文本插入、DOM 节点构建、白名单和经过验证的净化库，而非自定义转义。
* 必须避免引入新的高风险汇点（sink）（HTML 字符串构建、动态脚本加载、JSONP、内联脚本/事件处理属性、不安全的 URL 赋值、不安全的对象合并）。

### 1.2 被动审查模式（编辑时始终开启）

在使用 jQuery 的仓库的任何位置工作时（即使用户未要求安全扫描）：

* 必须"注意"所触及/附近代码中违反本规范的情况。
* 应当在问题出现时提及，附简要说明 + 安全修复方案。

### 1.3 主动审计模式（明确的扫描请求）

当用户要求"扫描"、"审计"或"挖掘漏洞"时：

* 必须系统地搜索代码库中违反本规范的情况。
* 必须以结构化格式输出发现（见 §2.3）。

建议的审计顺序：

1. jQuery 来源、版本和依赖卫生（脚本标签、锁文件、CDN 使用、SRI）。
2. CSP / Trusted Types / 安全头配置（在仓库中，如可观察则在运行时）。
3. DOM XSS：不受信任的来源 → jQuery 汇点（`.html`、`.append`、`$("<…>")`、`.load` 等）。
4. 脚本执行汇点：JSONP、`dataType:"script"`、`$.getScript`、动态 `<script>` 插入。
5. URL/属性赋值（`href`、`src`、`style`、`on*` 属性）。
6. 原型污染/不安全对象合并（`$.extend` 模式）。
7. AJAX 认证模式 + 基于 Cookie 会话的 CSRF。
8. 第三方插件和不受信任内容渲染路径（评论、所见即所得编辑器、markdown 转 HTML）。

---

## 2) 定义与审查指引

### 2.1 不受信任的输入（除非证明相反，否则视为攻击者可控）

示例包括：

* 服务器上来自用户的任何数据（用户资料、评论、"显示名"、富文本、文件名）。
* 来自第三方 API 或服务的数据。
* 浏览器可控的来源：

  * `location.href`、`location.search`、`location.hash`
  * `document.URL`、`document.baseURI`、`document.referrer`
  * `window.name`
  * `localStorage` / `sessionStorage`
  * `postMessage` 事件数据（除非存在严格来源和模式验证）
  * 任何可能已被先前注入的 DOM 内容（存储型 XSS）

### 2.2 jQuery 语境中的高风险"汇点"（sink）

汇点是指不受信任的输入可能被解释为可执行代码或 HTML 的代码路径。

关键的 jQuery 汇点类别：

* HTML 插入/解析：

  * 接受 HTML 字符串的 DOM 操作方法，如 `.html()`、`.append()` 及相关方法（见下文 CVE 说明）。（[NVD][1]）
  * `$(htmlString)`（当参数可能被解释为 HTML 标记时）。
  * `jQuery.parseHTML(html, …, keepScripts)`，尤其是 `keepScripts=true` 时。（[jQuery API][2]）
  * `.load(url)`（将 HTML 加载到 DOM 中；具有特殊的脚本执行行为）。（[jQuery API][3]）
* 脚本执行/动态代码加载：

  * `$.getScript()` / `$.ajax({ dataType: "script" })`（执行获取的 JavaScript）。（[jQuery API][4]）
  * JSONP（`dataType: "jsonp"` 或隐式 JSONP 行为）（将远程 JavaScript 作为响应执行）。（[jQuery API][5]）
  * `eval`、`new Function`、`setTimeout("…")`、`setInterval("…")`、`$.globalEval`（如存在）
* 危险的属性赋值：

  * 将不受信任的字符串赋给 `href`、`src`、`srcdoc`、`style` 或事件处理属性（`onload`、`onclick` 等）
  * `javascript:` URL 尤其危险，不鼓励使用。（[MDN Web Docs][6]）

### 2.3 要求的审计发现格式

对发现的每个问题，输出：

* 规则 ID：
* 严重程度：严重 / 高 / 中 / 低
* 位置：文件路径 + 函数/组件 + 行号
* 证据：精确的代码/配置片段
* 影响：可能出什么问题，谁可以利用它
* 修复：安全变更（优先最小差异）
* 缓解：如无法立即修复，采用纵深防御
* 误报说明：不确定时要验证什么

---

## 3) 安全基线：最低生产配置（生产环境中必须 MUST）

这是防止常见 jQuery 相关安全故障的最小"生产基线"。

### 3.1 使用受支持、已打补丁的 jQuery 版本（必须 MUST）

* 必须使用受支持的 jQuery 主版本并保持更新。
* 截至 2026-01-27，jQuery 项目将 jQuery 4.0.0 作为最新的主版本发布。（[blog.jquery.com][7]）
* 如果必须支持非常旧的浏览器（特别是 IE < 11），jQuery 4 不支持它们，可能需停留在 jQuery 3.x；请将其视为更高风险状态并积极打补丁。（[blog.jquery.com][7]）

### 3.2 安全加载 jQuery（必须 MUST）

* 必须仅从以下来源加载 jQuery：

  * 自己的构建管线（通过 npm/yarn + 锁文件打包），或
  * 官方 jQuery CDN / 启用了子资源完整性（SRI）的可信 CDN。
* 如果从 CDN 加载，应当使用 SRI（`integrity`）和正确的 `crossorigin` 设置；jQuery 项目明确支持并推荐在其 CDN 上使用 SRI。（取自 [jquery.com][8]）

### 3.3 CSP + Trusted Types（应当 SHOULD；在可用/政策要求时须 MUST）

* 应当部署内容安全策略（CSP）以降低 XSS 影响（尤其是 `script-src` 限制和避免 `unsafe-inline`）。如果未通过 HTTP 服务器完成，可通过 `<meta http-equiv="Content-Security-Policy" content="...">` 标签完成。（[OWASP Cheat Sheet Series][9]）注意：设置 CSP 的 script-src 最为重要。所有其他指令都不那么重要，为便于开发通常可以省略。
* 应当将 Trusted Types 视为对抗 DOM XSS 的强纵深防御。（[W3C][10]）
* 如果部署了 CSP 指令 `require-trusted-types-for`，代码必须通过 Trusted Types 策略路由 DOM 注入。（[MDN Web Docs][11]）
* 注意：jQuery 4.0 明确添加了 Trusted Types 支持，因此 TrustedHTML 可以用于 jQuery 操作方法而不会违反 `require-trusted-types-for`。（[blog.jquery.com][7]）

### 3.4 安全头和 Cookie 状态（纵深防御；应当 SHOULD）

虽然这些通常由服务端设置，但它们能实质性缩小 jQuery 相关错误的爆炸半径。但如果上下文只是前端 Web 应用，则无法对这些采取措施。

* 应当设置常见安全头（CSP、`X-Content-Type-Options: nosniff`、通过 `frame-ancestors` / `X-Frame-Options` 进行点击劫持防护、`Referrer-Policy`）。（[OWASP Cheat Sheet Series][12]）
* 应当避免将长期有效的机密/令牌存储在 JavaScript 可访问的位置（如 `localStorage`），除非威胁模型明确接受"XSS == 账户接管"。这不是 jQuery 特有的，但大量依赖 jQuery 的 DOM 操作会增加 DOM XSS 回归的概率；请降低其价值。

---

## 4) 规则（生成 + 审计）

每条规则包含：要求做法、不安全模式、检测提示和补救措施。

### JQ-SUPPLY-001：jQuery 必须打补丁；不得运行已知存在漏洞的版本

严重程度：中（如果应用面向互联网且版本已知存在漏洞，则为高）

注意：执行升级前，须征得用户同意并尝试了解其是否有保留旧版本的理由。升级可能以意想不到的方式破坏应用。请报告并建议升级，而非直接执行升级。

要求：

* 在存在已打补丁版本时，不得使用已知存在高影响漏洞的 jQuery 版本。
* 必须升级越过：

  * CVE-2019-11358（jQuery 3.4.0 之前的原型污染）。（[NVD][13]）
  * CVE-2020-11022 / CVE-2020-11023（处理不受信任 HTML 时 DOM 操作方法中的 XSS 风险；已在 3.5.0 中修复）。（[NVD][1]）

不安全模式：

* 引用旧 jQuery 的脚本标签或包清单（如 `jquery-1.*`、`jquery-2.*`、`jquery-3.3.*`、`jquery-3.4.*`、`jquery-3.4.1` 等）。
* 包含旧压缩版 jQuery 且无升级路径的捆绑供应商目录。

检测提示：

* 在 HTML/模板中搜索 `jquery-` 并解析版本字符串。
* 检查 `package.json`、`package-lock.json`、`yarn.lock`、`pnpm-lock.yaml`。
* 检查 `vendor/`、`public/`、`static/`、`assets/`、`wwwroot/` 中的 `jquery*.js`。

修复：

* 升级到当前 jQuery（优先最新稳定主版本；截至 2026-01-27，4.0.0 为当前版本）。（[blog.jquery.com][7]）
* 如果升级受限，至少升级越过 CVE 阈值，并添加补偿控制（强 CSP、严格净化、移除 JSONP 等高风险 API、移除对不受信任对象的深层扩展）。

说明：

* 如果产品需求强制使用旧版本，报告为"须以补偿控制接受的已接受风险"。

---

### JQ-SUPPLY-002：第三方脚本加载应当使用完整性校验和可信来源

严重程度：高

要求：

* 必须仅从可信来源加载 jQuery 和插件。
* 如果从 CDN 加载，应当使用 SRI（`integrity`）和正确的 `crossorigin` 处理。（[jquery.com][8]）

不安全模式：

* 无 `integrity` 的 `<script src="https://…/jquery.min.js"></script>`。
* 未经明确信任决策而从随机第三方 CDN 加载 jQuery。

检测提示：

* 扫描 HTML 中的 `<script src=`，检查是否有 `integrity=` + `crossorigin=`。
* 识别使用不受信任 URL 的动态脚本插入（见 JQ-EXEC-001）。

修复：

* 优先通过 npm + 锁文件打包。
* 如果使用 CDN，复制官方脚本标签（jQuery CDN 支持 SRI）。（[jquery.com][8]）

注意：如果无法获得正确的 SRI 标签，跳过此步骤但告知用户。如果最终使用了错误的标签，应用将无法运行。在这种情况下移除它并告知用户。

---

### JQ-XSS-001：不受信任的数据不得通过 jQuery DOM 操作方法作为 HTML 插入

严重程度：高（如果攻击者控制的内容到达这些汇点）

要求：

* 必须将任何 HTML 字符串插入视为代码执行边界。
* 对不受信任的文本必须使用安全替代方案：

  * `.text(untrusted)`（文本，而非 HTML）。（[jQuery API][14]）
  * 表单字段使用 `.val(untrusted)`。（[jQuery API][15]）
  * 安全地创建元素并设置文本/属性，而不是拼接 HTML 字符串。

不安全模式（示例）：

* `$(selector).html(untrusted)`
* `$(selector).append(untrusted)`
* `$(selector).before(untrusted)` / `.after(untrusted)` / `.replaceWith(untrusted)` / `.wrap(untrusted)`（及类似方法）
* 构建标记："`<div>" + untrusted + "</div>`"然后传递给 jQuery

检测提示：

* 搜索：`.html(`、`.append(`、`.prepend(`、`.before(`、`.after(`、`.replaceWith(`、`.wrap(`、`.wrapAll(`、`.wrapInner(`
* 从 §2.1 中的来源追踪进入这些调用的数据流。

修复：

* 替换为 `.text()` / `.val()` 或节点构建：

  * `const $el = $("<span>").text(untrusted); container.append($el);`
* 如果输出必须包含有限标记，见 JQ-XSS-002（净化）。

说明：

* 较旧的 jQuery 版本即使在尝试净化时也有额外边缘情况；已在 3.5.0+ 中修复。但仍然：永远不要仅依赖"字符串净化"——优先结构化创建或经过验证的净化器。（[GitHub][16]）

---

### JQ-XSS-002：如果必须渲染用户控制的 HTML，必须使用经过验证的 HTML 净化器进行净化

严重程度：中（如果富 HTML 由攻击者控制且净化器较弱/配置不当，则为高）

要求：

* 不得用正则表达式"自研"HTML 净化器。
* 如果必须显示用户控制的 HTML（如富文本评论），必须使用维护良好的 HTML 净化器和严格的允许列表进行净化。

  * DOMPurify 是常见选择；使用保守配置并保持更新。（[GitHub][17]）
  * 在可用的情况下，可以考虑浏览器 HTML Sanitizer API（注意：浏览器支持有限）。（[MDN Web Docs][18]）
* 应当将净化与 CSP 配对，并在可行时与 Trusted Types 配对，以实现纵深防御。（[OWASP Cheat Sheet Series][9]）

不安全模式：

* 基于正则的"去除 `<script>`"或"转义 `<`"尝试，随后进行 `.html()` 插入。
* 配置为允许过宽标签/属性的 DOMPurify（或类似工具），或未经审查的配置。

检测提示：

* 搜索"净化"辅助函数、替换 `<`/`>` 模式的正则，或"允许所有标签"配置。
* 识别渲染用户生成"富文本"或"自定义 HTML"的功能。
* 检查净化结果是否通过 `.html()` 或等效汇点插入。

修复：

* 引入带严格允许列表的净化器。
* 将"净化后注入"模式集中到单个经审查的模块中。
* 添加覆盖代表性恶意输入的回归测试（不要将载荷存入日志或遥测）。

误报说明：

* 如果内容保证可信（例如你随附的编译模板），记录信任边界以及为什么它不受攻击者控制。

---

### JQ-XSS-003：`$(untrustedString)` 和 `jQuery.parseHTML` 不得处理攻击者控制的标记

严重程度：高（如果由攻击者控制）

要求：

* 不得将攻击者控制的字符串传给 `$()`——如果它们可能被解释为 HTML。
* 必须将 `jQuery.parseHTML(html, …, keepScripts)` 视为高风险原语；对任何不受信任的输入，keepScripts 必须为 `false`。（[jQuery API][2]）

不安全模式：

* `const $node = $(untrusted);`
* `$.parseHTML(untrusted, /* context */, true)`（保留脚本）

检测提示：

* 搜索 `$(` 调用，其中参数不是静态选择器或静态标记。
* 搜索 `$.parseHTML(` 并检查 `keepScripts` 参数。

修复：

* 使用常量标签名的 DOM 创建和 `.text()` 处理不受信任的值。
* 如果必须解析 HTML，先净化（JQ-XSS-002）并保持脚本禁用。

---

### JQ-XSS-004：`.load()` 必须被视为 HTML+脚本注入面

严重程度：中（如果 URL/内容由攻击者控制，则为高）

要求：

* 不得对攻击者控制的 URL 或攻击者控制的 HTML 片段使用 `.load()`。
* 必须理解 jQuery `.load()` 的脚本行为：

  * URL 中没有选择器时，内容在脚本被移除之前传递给 `.html()`，这可以执行脚本。（[jQuery API][3]）
* 应当优先使用 `fetch()`/XHR 检索数据，然后用安全的 DOM 创建渲染，或显式净化。

不安全模式：

* `$("#target").load(untrustedUrl)`
* `$("#target").load("/path?param=" + untrusted)`

检测提示：

* 在 JS/TS 文件中搜索 `.load(`。
* 识别 URL 后是否附加了选择器（行为不同）。（[jQuery API][3]）
* 追踪 URL 是否可受用户输入影响。

修复：

* 将 `.load()` 替换为：

  * 用 `fetch()` 检索 JSON，然后通过 `.text()` / 节点构建渲染，或
  * 用 `fetch()` 检索 HTML，净化后再注入。
* 如果必须保留 `.load()`，确保 URL 是常量或严格白名单，且返回内容可信。

---

### JQ-EXEC-001：动态脚本执行和脚本获取不得可从不受信任的输入触达

严重程度：高

要求：

* 不得从不受信任或受用户影响的 URL 获取并执行脚本。
* 必须将以下内容视为代码执行原语：

  * `$.getScript(url)` 在全局上下文中执行获取的脚本。（[jQuery API][4]）
  * `$.ajax({ dataType: "script" })` 及其他执行响应的脚本类型请求。
* 应当移除这些模式，除非存在强有力的、经审查的理由。

不安全模式：

* `$.getScript(untrustedUrl)`
* `$.ajax({ url: untrustedUrl, dataType: "script" })`
* 动态 `<script src=...>` 注入，其中 `src` 来源于不受信任的输入。

检测提示：

* 搜索 `getScript(`、`dataType: "script"`、`globalEval`、`eval`、`new Function`。
* 寻找接受 URL 的"插件加载器"或"主题加载器"功能。

修复：

* 在构建时打包脚本。
* 如果必须运行时加载，限制为白名单、带版本、经完整性校验的资产（理想情况下仍然避免运行时代码加载）。

---

### JQ-AJAX-001：除非端点完全可信，否则必须禁用 JSONP（即使如此，也要避免）

严重程度：中（如果攻击者能影响 URL/端点，则为高）

要求：

* 不得对不受信任的端点使用 JSONP，因为它会执行 JavaScript 响应。
* 使用 `$.ajax` 时，对非完全可信目标必须显式禁用 JSONP；jQuery 自己的文档建议，如果你不信任目标，设置 `jsonp: false`"出于安全原因"。（[jQuery API][5]）
* 应当优先使用带 JSON 的 CORS（`dataType: "json"`）和服务端显式来源白名单。

不安全模式：

* `dataType: "jsonp"`
* 包含 `callback=?` 或触发 JSONP 行为的模式的 URL。callback 参数历来是 XSS 向量。
* 未固定 `dataType` 且未禁用 JSONP 的 `$.get(untrustedUrl)`（风险取决于选项和 jQuery 行为）

检测提示：

* 搜索 `jsonp`、`dataType: "jsonp"`、`callback=?`。
* 搜索 URL 非硬编码或非白名单的跨域 AJAX。

修复：

* 使用 HTTPS 上的 JSON，并在服务端配置 CORS。
* 设置：

  * `dataType: "json"`
  * `jsonp: false`（当 URL 可能模糊时作为纵深防御）（[jQuery API][5]）

---

### JQ-AJAX-002：使用 Cookie 认证的状态变更 AJAX 请求必须受 CSRF 保护

严重程度：高

注意：这仅在基于 Cookie 的认证时有意义。如果请求使用 Authorization 头，则不存在 CSRF 可能。

要求：

* 如果认证使用 Cookie，必须保护状态变更请求（POST/PUT/PATCH/DELETE）免受 CSRF。
* 应当使用服务器验证的 CSRF 令牌；对于 AJAX 调用，令牌通常通过自定义头发送。（[OWASP Cheat Sheet Series][19]）
* 不得仅将"它是 AJAX 请求"视为 CSRF 保护。

不安全模式：

* 使用 Cookie 认证且无 CSRF 令牌/头的 `$.post("/transfer", {...})` 或 `$.ajax({ method: "POST", ... })`。
* 仅检查 `X-Requested-With` 的"CSRF 保护"（仅纵深防御，非主要手段）。

检测提示：

* 枚举状态变更 AJAX 调用，确定其是否包含 CSRF 令牌。
* 识别服务器期望的 CSRF 验证方式（meta 标签、cookie-to-header 双重提交、同步器令牌等）。

修复：

* 在集中位置添加 CSRF 令牌包含逻辑，例如 `$.ajaxSetup({ headers: { "X-CSRF-Token": token } })`，并确保服务器验证。
* 遵循 OWASP 关于令牌属性和验证的 CSRF 指引。（[OWASP Cheat Sheet Series][19]）

误报说明：

* 如果认证不是基于 Cookie 的（例如 Authorization 头承载令牌），CSRF 风险不同；请验证实际认证机制。

---

### JQ-ATTR-001：未经验证/白名单，不得将不受信任的值写入危险属性

严重程度：低（对 onclick 等事件为高）

要求：

* 必须验证/白名单写入 `href`、`src`、`action` 等的 URL。
* 必须阻止危险协议；`javascript:` URL 不受鼓励，因为它们可以执行代码。（[MDN Web Docs][6]）
* 不得从字符串设置事件处理属性（`onclick`、`onerror` 等）。
* 应当避免将不受信任的字符串写入 `style` 属性；优先切换预定义的 CSS 类。

不安全模式：

* `$("a").attr("href", untrustedUrl)`
* `$("img").attr("src", untrustedUrl)`
* `$(el).attr("style", untrustedCss)`
* `$(el).attr("onclick", untrustedJs)`

检测提示：

* 搜索 `.attr("href"`、`.attr("src"`、`.attr("style"`、`.prop("href"`、`.prop("src"`。
* 追踪输入是否来自 URL 参数、服务器 JSON、DOM 或存储。

修复：

* 使用 `new URL(value, location.origin)` 解析和验证 URL，并在需要时白名单协议（`https:` 等）和主机名。
* 对于导航目标，优先使用自己构造的相对路径而非完整 URL。
* 用 `addClass/removeClass` 和预定义类名替换 `style` 字符串。

---

### JQ-SELECTOR-001：用户控制的选择器片段必须使用 `jQuery.escapeSelector` 转义

严重程度：中（如果它导致安全相关 UI 中选择错误元素，则可变为高）

要求：

* 如果必须按可能包含特殊 CSS 字符的 ID/类进行选择，应当使用 `jQuery.escapeSelector()`（jQuery 3.0+ 可用）。（[jQuery API][20]）
* 不得将原始攻击者控制的字符串拼接进选择器表达式。

不安全模式：

* `$("#" + untrustedId)`
* `$("[data-id='" + untrusted + "']")`（尤其是没有严格引号/转义时）

检测提示：

* 搜索 `"#" +`、`". " +` 或 `$(` 选择器内使用的模板字符串。
* 寻找"按用户提供的 id 选择"。

修复：

* `$("#" + $.escapeSelector(untrustedId))`（[jQuery API][20]）
* 优先使用稳定的内部 ID 而非用户派生的选择器。

说明：

* 这往往是"健壮性"问题，但如果错误的选择导致 UI 显示/修改错误数据或跳过安全相关提示，则可能变得与安全相关。

---

### JQ-PROTOTYPE-001：不要深度合并不受信任的对象；防止原型污染

严重程度：中

要求：

* 不得将攻击者控制的对象深合并（`$.extend(true, …)`）到应用对象中，除非过滤危险键。
* 必须确保 jQuery >= 3.4.0，以避免 CVE-2019-11358 原型污染行为。（[NVD][13]）

不安全模式：

* `$.extend(true, target, untrustedObj)`
* `$.extend(true, {}, defaults, untrustedObj)`，其中 untrustedObj 来自 URL/JSON/存储

检测提示：

* 搜索 `$.extend(true` 并检查被合并对象的来源。
* 搜索使用不受信任 JSON 的"合并选项"/"应用配置"模式。

修复：

* 优先采用：

  * 带白名单键集的浅合并，或
  * 显式拒绝 `__proto__`、`prototype`、`constructor` 及其嵌套出现的安全合并辅助函数。
* 保持 jQuery 已打补丁。

---

### JQ-CSP-001：应当使用 CSP 和 Trusted Types 使 DOM XSS 更难以引入和利用

严重程度：中

要求：

* 应当部署 CSP 作为对抗 XSS 的纵深防御。（[OWASP Cheat Sheet Series][9]）
* 如果启用 Trusted Types（`require-trusted-types-for`），必须确保 DOM 注入通过 Trusted Types 策略。（[MDN Web Docs][11]）
* 使用 jQuery 4 时，应当利用其 Trusted Types 支持（TrustedHTML 输入）。（[blog.jquery.com][7]）

不安全模式：

* 通过削弱 CSP（`script-src 'unsafe-inline'` / `'unsafe-eval'`）"修复"jQuery 功能，而无补偿计划。
* 渲染用户内容或大量操作 DOM 的应用无 CSP。

检测提示：

* 寻找 CSP 头（服务器配置、框架中间件、meta 标签）。
* 如果在仓库中不可见，标记为"在边缘/运行时验证"。

修复：

* 增量添加 CSP；首先消除内联脚本和内联事件处理程序，然后收紧 `script-src`。
* 在支持且可行的地方添加 Trusted Types。

---

## 5) 实用扫描启发式（如何"狩猎"）

主动扫描时，使用这些高信号模式：

* jQuery 版本 / 来源：

  * `vendor/` 或 `static/` 中的 `jquery-*.js`
  * `package.json` 中固定到旧版本的 `jquery` 依赖
  * 缺少 `integrity`/`crossorigin` 的 CDN 脚本标签（[jquery.com][8]）
* HTML 注入汇点（DOM XSS）：

  * `.html(`、`.append(`、`.prepend(`、`.before(`、`.after(`、`.replaceWith(`、`.wrap(`
  * `$(` 参数可能是 HTML / 模板字符串
  * `$.parseHTML(`，尤其是 `keepScripts=true` 时（[jQuery API][2]）
  * `.load(`（以及是否附加了选择器；脚本行为不同）（[jQuery API][3]）
* 脚本执行 / 动态代码：

  * `$.getScript(`、`dataType: "script"`（[jQuery API][4]）
  * `dataType: "jsonp"` 或 `jsonp:` 使用；`callback=?` 模式（[jQuery API][5]）
  * `eval`、`new Function`、`setTimeout("…")`、`$.globalEval`
* 危险属性写入：

  * `.attr("href", …)`、`.attr("src", …)`、`.attr("style", …)`
  * 任何 `javascript:` 类协议方案或可疑 URL 构建的赋值（[MDN Web Docs][6]）
* 选择器构建：

  * `$("#" + user)` 及类似；通过 `$.escapeSelector` 修复（[jQuery API][20]）
* 原型污染：

  * `$.extend(true, …, userObj)`；确保 jQuery >= 3.4.0 并过滤危险键（[NVD][13]）
* AJAX 的 CSRF 状态：

  * 使用 Cookie 且无 CSRF 令牌/头的 `$.post(` / `$.ajax({ method: ... })`（[OWASP Cheat Sheet Series][19]）
* 纵深防御：

  * 配置中缺少 CSP/安全头（或不可见；需要运行时验证）（[OWASP Cheat Sheet Series][12]）

始终尝试确认：

* 数据来源（不受信任 vs 可信）
* 汇点类型（HTML 插入 / 脚本执行 / 属性 / 选择器 / 对象合并）
* 存在的保护控制（净化器、白名单、CSP、Trusted Types、CSRF 验证）

---

## 6) 来源（访问于 2026-01-27）

jQuery 项目主要文档与发布说明：

* jQuery 4.0.0 发布说明（Trusted Types/CSP 变更；版本信息）：`https://blog.jquery.com/2026/01/17/jquery-4-0-0/`。（[blog.jquery.com][7]）
* 下载 jQuery（最新版本信息；CDN + SRI 指引）：`https://jquery.com/download/`。（[jquery.com][8]）
* jQuery API：`.html()`：`https://api.jquery.com/html/`。（[jQuery API][21]）
* jQuery API：`.text()`：`https://api.jquery.com/text/`。（[jQuery API][14]）
* jQuery API：`.append()`：`https://api.jquery.com/append/`。（[jQuery API][22]）
* jQuery API：`.load()`（脚本执行行为）：`https://api.jquery.com/load/`。（[jQuery API][3]）
* jQuery API：`jQuery.parseHTML(…, keepScripts)`：`https://api.jquery.com/jQuery.parseHTML/`。（[jQuery API][2]）
* jQuery API：`$.ajax()`（`jsonp: false` 安全说明）：`https://api.jquery.com/jQuery.ajax/`。（[jQuery API][5]）
* jQuery API：`$.getScript()`（执行脚本）：`https://api.jquery.com/jQuery.getScript/`。（[jQuery API][4]）
* jQuery API：`jQuery.escapeSelector()`：`https://api.jquery.com/jQuery.escapeSelector/`。（[jQuery API][20]）

jQuery 漏洞 / 公告：

* NVD CVE-2019-11358（原型污染；jQuery < 3.4.0）：`https://nvd.nist.gov/vuln/detail/CVE-2019-11358`。（[NVD][13]）
* NVD CVE-2020-11022（DOM 操作方法中的 XSS 风险；已在 3.5.0 中修复）：`https://nvd.nist.gov/vuln/detail/CVE-2020-11022`。（[NVD][1]）
* NVD CVE-2020-11023（涉及 `<option>` 的 XSS 风险；已在 3.5.0 中修复）：`https://nvd.nist.gov/vuln/detail/CVE-2020-11023`。（[NVD][23]）
* GitHub 安全公告 GHSA-gxr4-xjj5-5px2（jQuery htmlPrefilter XSS；已在 3.5.0 中修复）：`https://github.com/jquery/jquery/security/advisories/GHSA-gxr4-xjj5-5px2`。（[GitHub][16]）

OWASP Cheat Sheet Series（与 jQuery 使用相关的 Web 应用安全基础）：

* XSS 防护：`https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html`。（[OWASP Cheat Sheet Series][24]）
* 基于 DOM 的 XSS 防护：`https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html`。（[OWASP Cheat Sheet Series][25]）
* CSRF 防护：`https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html`。（[OWASP Cheat Sheet Series][19]）
* HTTP 安全头：`https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html`。（[OWASP Cheat Sheet Series][12]）
* 内容安全策略速查表：`https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html`。（[OWASP Cheat Sheet Series][9]）

浏览器/平台参考（SRI、CSP、Trusted Types 和危险 URL 协议）：

* MDN：子资源完整性（SRI）：`https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Subresource_Integrity`。（[MDN Web Docs][26]）
* W3C：SRI 规范：`https://www.w3.org/TR/sri-2/`。（[W3C][27]）
* MDN：CSP 指南：`https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP`。（[MDN Web Docs][28]）
* MDN：`require-trusted-types-for` 指令：`https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/require-trusted-types-for`。（[MDN Web Docs][11]）
* MDN：Trusted Types API：`https://developer.mozilla.org/en-US/docs/Web/API/Trusted_Types_API`。（[MDN Web Docs][29]）
* W3C：Trusted Types 规范：`https://www.w3.org/TR/trusted-types/`。（[W3C][10]）
* MDN：`javascript:` URL 协议警告：`https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Schemes/javascript`。（[MDN Web Docs][6]）
* DOMPurify 项目文档：`https://github.com/cure53/DOMPurify`。（[GitHub][17]）

[1]: https://nvd.nist.gov/vuln/detail/cve-2020-11022?utm_source=chatgpt.com "CVE-2020-11022 Detail - NVD"
[2]: https://api.jquery.com/jQuery.parseHTML/?utm_source=chatgpt.com "jQuery.parseHTML()"
[3]: https://api.jquery.com/load/?utm_source=chatgpt.com ".load() | jQuery API Documentation"
[4]: https://api.jquery.com/jQuery.getScript/?utm_source=chatgpt.com "jQuery.getScript()"
[5]: https://api.jquery.com/jQuery.ajax/?utm_source=chatgpt.com "jQuery.ajax()"
[6]: https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Schemes/javascript?utm_source=chatgpt.com "javascript: URLs - URIs - MDN Web Docs"
[7]: https://blog.jquery.com/2026/01/17/jquery-4-0-0/ "jQuery 4.0.0 | Official jQuery Blog"
[8]: https://jquery.com/download/ "Download jQuery | jQuery"
[9]: https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html?utm_source=chatgpt.com "Content Security Policy - OWASP Cheat Sheet Series"
[10]: https://www.w3.org/TR/trusted-types/?utm_source=chatgpt.com "Trusted Types"
[11]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/require-trusted-types-for?utm_source=chatgpt.com "Content-Security-Policy: require-trusted-types-for directive"
[12]: https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html?utm_source=chatgpt.com "HTTP Security Response Headers Cheat Sheet"
[13]: https://nvd.nist.gov/vuln/detail/cve-2019-11358?utm_source=chatgpt.com "CVE-2019-11358 Detail - NVD"
[14]: https://api.jquery.com/text/?utm_source=chatgpt.com ".text() | jQuery API Documentation"
[15]: https://api.jquery.com/val/?utm_source=chatgpt.com ".val() | jQuery API Documentation"
[16]: https://github.com/jquery/jquery/security/advisories/GHSA-gxr4-xjj5-5px2 "Potential XSS vulnerability in jQuery.htmlPrefilter and related methods · Advisory · jquery/jquery · GitHub"
[17]: https://github.com/cure53/DOMPurify?utm_source=chatgpt.com "DOMPurify - a DOM-only, super-fast, uber-tolerant XSS ..."
[18]: https://developer.mozilla.org/en-US/docs/Web/API/HTML_Sanitizer_API?utm_source=chatgpt.com "HTML Sanitizer API - MDN Web Docs"
[19]: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html?utm_source=chatgpt.com "Cross-Site Request Forgery Prevention Cheat Sheet"
[20]: https://api.jquery.com/jQuery.escapeSelector/?utm_source=chatgpt.com "jQuery.escapeSelector()"
[21]: https://api.jquery.com/html/?utm_source=chatgpt.com ".html() | jQuery API Documentation"
[22]: https://api.jquery.com/append/?utm_source=chatgpt.com ".append() | jQuery API Documentation"
[23]: https://nvd.nist.gov/vuln/detail/cve-2020-11023?utm_source=chatgpt.com "CVE-2020-11023 Detail - NVD"
[24]: https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html?utm_source=chatgpt.com "Cross Site Scripting Prevention - OWASP Cheat Sheet Series"
[25]: https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html?utm_source=chatgpt.com "DOM based XSS Prevention Cheat Sheet"
[26]: https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Subresource_Integrity?utm_source=chatgpt.com "Subresource Integrity - Security - MDN Web Docs"
[27]: https://www.w3.org/TR/sri-2/?utm_source=chatgpt.com "Subresource Integrity"
[28]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP?utm_source=chatgpt.com "Content Security Policy (CSP) - HTTP - MDN Web Docs"
[29]: https://developer.mozilla.org/en-US/docs/Web/API/Trusted_Types_API?utm_source=chatgpt.com "Trusted Types API - MDN Web Docs"
