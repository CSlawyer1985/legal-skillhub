# 前端 JavaScript/TypeScript Web 安全规范（原生浏览器 JS/TS、现代浏览器）

本文档定位为一份**安全规范**，用于支持：

1. 为新前端 JavaScript/TypeScript 代码提供**默认安全**的代码生成（不假定特定框架）。
2. 对现有前端代码进行**安全审查／漏洞排查**（被动式“工作中发现即提示”和主动式“扫描代码库并报告发现”）。

本文刻意以一组**规范性要求**（“MUST／SHOULD／MAY”）加**审计规则**（不良模式长什么样、如何检测、如何修复／缓解）的形式写成。

---

## 0）安全、边界与反滥用约束（必须遵守）

- 不得请求、输出、记录、硬编码或提交机密信息（意图保密的 API 密钥、私钥、密码、OAuth 刷新令牌、会话令牌、Cookie）。
  说明：

  - 前端代码天然对最终用户可见。如果一个值必须保持机密，就不能出现在交付给浏览器的代码中。
  - 如果项目使用“公开”密钥（例如可发布的统计密钥），必须将其视为非机密并相应限定范围。

- 不得通过禁用保护来“修复”安全问题（例如无正当理由地用 `unsafe-inline`／`unsafe-eval` 削弱 CSP、移除 `postMessage` 的来源检查、为方便改用 `innerHTML`、接受任意跳转／URL，或关闭净化）。

- 审计时必须提供**基于证据的发现**：引用能够佐证结论的文件路径、代码片段以及相关的 HTML／CSP／配置值。

- 必须诚实地处理不确定性：

  - 安全响应头（CSP、frame-ancestors 等）可能由服务器／边缘层／CDN 设置，而非在仓库代码中。如不可见，报告为“此处不可见；需在运行时／边缘配置中验证”。（另请注意，`<meta http-equiv=...>` 只能模拟一部分响应头；不要因为存在 meta 标签就假定其他安全响应头也存在。）（[MDN Web Docs][1]）

---

## 1）运行模式

### 1.1 生成模式（默认）

当被要求编写新的前端 JS/TS 代码或修改现有代码时：

- 必须遵守本规范中的每一项**MUST**要求。
- 应当遵守每一项**SHOULD**要求，除非用户明确另有要求。
- 必须优先选用默认安全的浏览器 API 和经过验证的库，而不是自行编写安全代码（尤其是 HTML 净化）。
- 必须避免引入新的高风险汇点（`innerHTML` 等 DOM XSS 注入汇点、跳转到 `javascript:` URL、通过 `eval`／`Function` 动态执行代码、不安全的 `postMessage`、不安全的第三方脚本加载等）。（[OWASP Cheat Sheet Series][2]）

### 1.2 被动审查模式（编辑期间始终开启）

在前端代码库中任何位置工作时（即使用户没有要求安全扫描）：

- 必须“留意”所触及或附近代码中对本规范的违反。
- 应当及时指出问题，附简要说明和安全修复建议。

### 1.3 主动审计模式（明确要求扫描）

当用户要求“扫描”“审计”或“排查漏洞”时：

- 必须系统性地搜索代码库中违反本规范之处。
- 必须以结构化格式输出发现（见 §2.3）。

建议的审计顺序：

1. HTML 入口点（`index.html`、服务端渲染模板）、脚本／样式引入，以及 CSP 的交付方式（响应头 vs meta）。（[W3C][3]）
2. DOM XSS 汇点（`innerHTML`、`document.write`、`insertAdjacentHTML`、事件处理器属性）及其数据来源（URL 参数／hash、存储、postMessage、API 响应）。（[OWASP Cheat Sheet Series][2]）
3. 导航／跳转处理（`window.location*`、链接目标、URL 白名单），包括 `javascript:` URL 危害。（[MDN Web Docs][4]）
4. 跨源通信（`postMessage`、iframe 嵌入模式、沙箱化）。（[MDN Web Docs][5]）
5. 敏感数据的存储（localStorage／sessionStorage）及对信任的假设。（[OWASP Cheat Sheet Series][6]）
6. 第三方脚本／标签管理器／CDN，以及完整性控制（SRI）和策略控制（CSP）。（[OWASP Cheat Sheet Series][7]）
7. DOM clobbering 小工具及对 `window`／`document` 命名属性的不安全依赖。（[OWASP Cheat Sheet Series][8]）

---

## 2）定义与审查指引

### 2.1 不可信输入（除非证明可信，否则视为攻击者可控）

示例包括：

- URL 派生数据：`location.href`、`location.search`、`location.hash`、`document.baseURI`、`new URLSearchParams(location.search)`、路由片段。（[OWASP Cheat Sheet Series][2]）
- 可能包含用户可控标记的 DOM 内容（评论、个人资料、CMS 内容、markdown 转 HTML 的输出等），尤其是动态插入时。（[OWASP Cheat Sheet Series][2]）
- 来自其他窗口／框架的 `postMessage` 事件数据（`event.data`）和元数据（`event.origin`）。（[MDN Web Docs][5]）
- 浏览器存储：`localStorage`、`sessionStorage`、IndexedDB（其内容可能通过 XSS 或本机访问被攻击者影响；绝不视为“可信”）。（[OWASP Cheat Sheet Series][6]）
- 任何来自网络调用的数据（即使来自“你的 API”），因为它可能包含存储的攻击者内容，只有插入 DOM 后才变得危险。（[OWASP Cheat Sheet Series][2]）

### 2.2 危险汇点（DOM XSS／代码执行汇点）

汇点是指任何能够以安全敏感方式执行脚本或将攻击者可控字符串解释为 HTML／JS／URL 的 API／操作。高信号汇点包括：

- HTML 解析／插入：`innerHTML`、`outerHTML`、`insertAdjacentHTML`、`document.write`、`document.writeln`。（[OWASP Cheat Sheet Series][2]）
- 动态代码执行：`eval`、`new Function`、`setTimeout("...")`、`setInterval("...")`。（[MDN Web Docs][10]）
- 通过 `Location.href`／`window.location` 等 setter 跳转到可执行脚本的 URL（例如 `javascript:`）（以及攻击者可控的链接 `href`）。（[MDN Web Docs][4]）
- 从字符串设置事件处理器属性，例如 `setAttribute("onclick", "...")`。（[OWASP Cheat Sheet Series][2]）

### 2.3 审计发现的规定输出格式

对发现的每个问题，输出：

- 规则 ID：
- 严重级别：严重／高／中／低
- 位置：文件路径＋函数／类／模块＋行号
- 证据：确切的代码／配置片段
- 影响：可能出什么问题、谁能利用
- 修复：安全的变更（优先最小 diff）
- 缓解：若无法立即修复时的纵深防御
- 误报说明：不确定时应核验什么

---

## 3）安全基线：最低生产配置（生产环境必须满足）

这是防止常见前端 JS/TS 安全配置错误的最简基线。有些项“在仓库内”（HTML／JS），有些可能位于服务器／边缘层。

### 3.1 内容安全策略（CSP）基线（应当；高风险应用必须）

- 应当尽可能通过 HTTP 响应头交付 CSP。
- 无法设置响应头时（例如纯静态托管的限制），可以通过 HTML 的 `<meta http-equiv="Content-Security-Policy" ...>` 标签交付 CSP。（[MDN Web Docs][1]）
- 如通过 `<meta http-equiv>` 使用 CSP，必须了解其限制：

  - 该策略只适用于 meta 元素之后的内容（因此必须尽早出现，先于任何你想约束的脚本／资源）。（[W3C][3]）
  - 以下指令在 meta 交付的策略中**不受支持**且会被忽略：`report-uri`、`frame-ancestors` 和 `sandbox`。（[W3C][3]）
  - 无法通过 meta 元素设置“仅报告”CSP。（[W3C][3]）

实用基线目标：

- 避免脚本源使用 `unsafe-inline` 和 `unsafe-eval`（它们会显著削弱 CSP 对抗 XSS 的价值）。（[MDN Web Docs][10]）
- 如需内联脚本，优先采用 nonce 或 hash 策略。（[MDN Web Docs][10]）
- 在可行处考虑启用 Trusted Types 强制。（[MDN Web Docs][11]）

### 3.2 第三方脚本基线（应当）

- 应当尽量减少第三方脚本执行，并将其视为与第一方 JS 同等权限（它以你来源的权限运行）。（[OWASP Cheat Sheet Series][7]）
- 对从 CDN 加载的第三方脚本／样式，应当使用子资源完整性（SRI）。（[MDN Web Docs][12]）

### 3.3 跨窗口通信基线（应当）

- 应当将 `postMessage` 通信限制为显式来源，并同时校验来源和消息形态。（[MDN Web Docs][5]）

---

## 4）规则（生成＋审计）

每条规则包含：要求做法、不安全模式、检测提示、补救措施。

### JS-XSS-001：不要将不可信 HTML 注入 DOM（避免 `innerHTML` 及其同类）

严重级别：如能证明攻击者可控输入可到达这些 API 则为严重；否则为中


要求：

- 当 `innerHTML`、`outerHTML` 和 `insertAdjacentHTML` 的输入可能包含不可信数据时，必须将其视为危险汇点。（[OWASP Cheat Sheet Series][2]）
- 必须优先使用不解析 HTML 的安全 DOM API：

  - 纯文本使用 `textContent`。（[OWASP Cheat Sheet Series][2]）
  - 非事件处理器属性使用 `document.createElement`、`appendChild`、`setAttribute`。（[OWASP Cheat Sheet Series][2]）
- 如果确实需要插入 HTML，应当使用经过充分审查的 HTML 净化器进行净化，并强烈考虑启用 Trusted Types 强制，将此类用法限制在经审计的代码路径中。（[MDN Web Docs][11]）

不安全模式：

- `el.innerHTML = userInput`
- `el.insertAdjacentHTML('beforeend', userInput)`
- `el.outerHTML = userInput`

检测提示：

- 搜索：`.innerHTML`、`.outerHTML`、`insertAdjacentHTML(`。
- 追踪所插入字符串的来源：URL 参数／hash、postMessage、存储、API 响应、DOM 属性。（[OWASP Cheat Sheet Series][2]）

修复：

- 纯文本改用 `textContent`。（[OWASP Cheat Sheet Series][2]）
- 结构化 UI 显式构建 DOM 节点。
- 对“富文本”需求：

  - 使用基于白名单的净化器进行净化。
  - 优先返回安全的“组件”而非任意 HTML 字符串。
  - 在支持处使用 Trusted Types 强制，确保只有 `TrustedHTML` 能到达汇点。（[MDN Web Docs][11]）

缓解：

- 部署严格的 CSP，并考虑启用 Trusted Types 强制（`require-trusted-types-for 'script'`）。（[MDN Web Docs][10]）

误报说明：

- 如果字符串可证明是常量或完全由可信常量生成，则可能安全。但仍应优先使用更安全的 API。

---

### JS-XSS-002：避免 `document.write`／`document.writeln`（XSS＋文档 clobbering 危害）

严重级别：如能证明攻击者可控输入可到达这些 API 则为严重；否则为中

要求：

- 生产代码必须避免使用 `document.write()` 和 `document.writeln()`（它们是 XSS 向量，即使某些浏览器在某些情况下会阻止注入的 `<script>`，仍可被精心构造的 HTML 滥用）。（[MDN Web Docs][13]）
- 如无法避免遗留用法，必须确保没有不可信输入到达这些 API，并应当在支持处启用 Trusted Types（`TrustedHTML`）。（[MDN Web Docs][14]）

不安全模式：

- `document.write(userInput)`
- `document.writeln(getParam('q'))`

检测提示：

- 搜索 `document.write(`、`document.writeln(`。（[OWASP Cheat Sheet Series][2]）

修复：

- 改用 DOM 操作（`createElement`、`appendChild`）或安全文本插入（`textContent`）。（[OWASP Cheat Sheet Series][2]）

缓解：

- 严格的 CSP＋Trusted Types 强制可缩小残留汇点的爆炸半径。（[MDN Web Docs][10]）

---

### JS-XSS-003：不要使用字符串到代码的执行（`eval`、`new Function`、字符串定时器）

严重级别：如能证明攻击者可控输入可到达这些 API 则为严重；否则为中

要求：

- 不得将不可信数据传给：

  - `eval()`
  - `new Function(...)`
  - 带字符串参数的 `setTimeout("...")`／`setInterval("...")`（[MDN Web Docs][10]）
- 在现代前端代码中应当完全避免这些 API；重构为无 eval 的逻辑。（[MDN Web Docs][10]）
- 除非有经过记录和审查的理由及补偿性控制，不得通过添加 `unsafe-eval` 来“修复 CSP 破坏”。（[MDN Web Docs][10]）

不安全模式：

- `eval(userInput)`
- `new Function("return " + userInput)()`
- `setTimeout(userInput, 0)`（其中 userInput 是字符串）

检测提示：

- 搜索 `eval(`、`new Function`、`setTimeout("`、`setInterval("`。
- 也搜索后续使用的代码字符串构造。

修复：

- 将动态代码替换为：

  - 结构化数据＋显式分支／处理器，
  - 对 JSON 使用 `JSON.parse` 而非 `eval`。（[OWASP Cheat Sheet Series][2]）

缓解：

- 默认阻止 `eval()` 类 API 的 CSP，并避免 `unsafe-eval`。（[MDN Web Docs][10]）
- 对受控场景可考虑 Trusted Types，但应将其视为加固层，而非保留 eval 模式的许可。（[MDN Web Docs][10]）

---

### JS-XSS-004：不要从字符串设置事件处理器属性（例如 `setAttribute("onclick", "...")`）

严重级别：高

要求：

- 不得对不可信数据使用 `setAttribute("on…", string)` 或类似模式；这会将字符串强制转换为事件处理器上下文中的可执行代码。（[OWASP Cheat Sheet Series][2]）
- 应当优先使用带函数引用的 `addEventListener`。

不安全模式：

- `el.setAttribute("onclick", userInput)`
- `el.onclick = userControlledString`（字符串赋值）

检测提示：

- 搜索 `.setAttribute("on`、`.onclick =`、`.onmouseover =` 等。
- 追踪右侧是否可受 URL／hash／存储／postMessage 影响。（[OWASP Cheat Sheet Series][2]）

修复：

- 改用 `addEventListener("click", () => { ... })`。
- 如需动态分发，使用从标识符到函数的白名单映射（不做字符串 eval）。（[OWASP Cheat Sheet Series][2]）

---

### JS-URL-001：导航前净化并白名单 URL（尤其是 `window.location`／`location.replace`）

严重级别：低（如能证明攻击者可完全控制 URL 则为高）

重要提示：这会产生大量误报。请进行额外分析，判断 URL 是否完全由攻击者控制。若并非完全受攻击者控制，则最多只能算提示性信息。

注意：能够跳转到任意 URL 可能是重要功能。如果这是该功能的目的，那么至少应确保检查 schema，即使允许任意来源。

要求：

- 必须将对导航目标的任何赋值视为安全敏感：

  - `window.location = ...`
  - `location.href = ...`
  - `location.assign(...)`
  - `location.replace(...)`（[MDN Web Docs][4]）
- 必须防止跳转到 `javascript:` URL（以及一般的其他可执行脚本／活动 scheme），尤其是当输入源自 URL 参数、存储或消息时。（[MDN Web Docs][4]）。只允许 `http:` 和 `https:`。
- 应当校验／白名单目标。安全基线是：

  - 只允许同源相对路径，或
  - 只允许严格的来源和协议白名单（通常为 `https:`，本地开发可选 `http:`）。（[OWASP Cheat Sheet Series][8]）

不安全模式：

- `location.replace(getParam("next"))`
- `window.location = userSuppliedUrl`
- `location.assign(window.redirectTo || "/")`，其中 `redirectTo` 可被 clobber 或由攻击者设置（[OWASP Cheat Sheet Series][8]）

检测提示：

- 搜索 `window.location`、`location.href`、`location.assign`、`location.replace`。
- 搜索常见跳转参数：`next`、`returnTo`、`redirect`、`url`、`continue`。
- 搜索 `javascript:` 字面量。（[MDN Web Docs][4]）

修复：

- 用 `new URL(value, location.origin)` 解析并校验，然后强制执行：

  - `url.protocol` 属于 `{ "https:" }`（仅将 `http:` 保留在显式的仅开发代码路径中），
  - 内部跳转时 `url.origin` 等于 `location.origin`，外部跳转时在严格白名单内，
  - 可选地只允许特定路径前缀。（[MDN Web Docs][4]）
- 校验失败时，跳转到安全默认页（首页／仪表盘）。

缓解：

- 部署严格的 CSP 和 Trusted Types 强制以缩小 DOM XSS 汇点的影响，但注意 Trusted Types 本身并不能防止所有可能的不安全导航场景。（[W3C][15]）

误报说明：

重要提示：这会产生大量误报。请进行额外分析，判断 URL 是否完全由攻击者控制。若并非完全受攻击者控制，则最多只能算提示性信息。

- 某些应用有意支持外部跳转（SSO、支付流程）。这些必须白名单化并记录。

---

### JS-URL-002：在将 URL 插入 DOM 的 URL 上下文（`href`、`src` 等）之前净化 URL

严重级别：低（如能证明攻击者可完全控制 URL 则为高）

重要提示：这会产生大量误报。请进行额外分析，判断 URL 是否完全由攻击者控制。若并非完全受攻击者控制，则最多只能算提示性信息。

要求：

- 必须将设置承载 URL 的 DOM 属性／特性视为安全敏感，尤其是：

  - `a.href`、`img.src`、`script.src`、`iframe.src`、`form.action`、`link.href`。
- 当值可能受攻击者影响时，必须防止可执行脚本的 scheme（`javascript:` 及其他活动 scheme）。（[MDN Web Docs][4]）
- 应当优先在解析和校验后设置属性（例如 `a.href = url.toString()`），而不是字符串拼接。

不安全模式：

- `link.href = getParam("u")`
- 未经验证的 `el.setAttribute("href", userInput)`
- 用不可信片段拼接 URL

检测提示：

- 搜索 `.href =`、`.src =`、`.action =`、`setAttribute("href"`、`setAttribute("src"`。
- 搜索 URL 中的 `javascript:`／`data:` 用法。（[MDN Web Docs][4]）

重要提示：这会产生大量误报。请进行额外分析，判断 URL 是否完全由攻击者控制。若并非完全受攻击者控制，则最多只能算提示性信息。

修复：

- 使用 `new URL(...)` 并校验：

  - 协议白名单
  - 完全避免将用户提供的值传入 `<script src>`（视为代码执行）。（[OWASP Cheat Sheet Series][8]）

---

### JS-CSP-001：使用 CSP；允许 meta 交付

严重级别：中至高（取决于威胁模型；处理不可信内容时为高）

注意：设置 CSP 的 script-src 最为重要。其他指令没有那么重要，为便于开发通常可以省略。

要求：

- 应当部署 CSP 作为对抗 XSS 的主要纵深防御。（[MDN Web Docs][10]）
- 无法设置响应头时，可以通过 `<meta http-equiv="Content-Security-Policy" ...>` 提供 CSP。（[MDN Web Docs][1]）
- 如果通过 meta 交付 CSP，必须：

  - 将其放在早期（先于你想约束的脚本／资源），并且
  - 不依赖 meta 策略中不支持的指令（`report-uri`、`frame-ancestors`、`sandbox`）。（[W3C][3]）
- 除非明确需要并经审查，不得将添加 `unsafe-inline` 作为 CSP 问题的“快速修复”（它会破坏 CSP 的大部分目的）。（[MDN Web Docs][10]）
- 除非明确需要并经审查，不得添加 `unsafe-eval`（它允许经常被滥用的 eval 类 API）。（[MDN Web Docs][10]）

不安全模式：

- 渲染不可信内容的应用在任何位置（仓库 HTML 或服务器／边缘层）都没有 CSP。
- CSP 包含 `script-src 'unsafe-inline'` 和／或 `script-src 'unsafe-eval'` 且无有力理由。（[MDN Web Docs][10]）
- CSP 通过 meta 交付但包含 `frame-ancestors`（在 meta 中会被忽略）。（[W3C][3]）

检测提示：

- 在 HTML 中搜索 `<meta http-equiv="Content-Security-Policy"`。
- 在服务器／边缘配置中搜索 `Content-Security-Policy` 响应头。
- 如果 CSP 仅在 meta 中，检查它是否出现在任何你想约束的 `<script>` 标签之前。（[W3C][3]）

修复：

- 优先在服务器／边缘层以响应头交付 CSP。
- 如受限于 meta，保持强白名单 CSP 并记录其限制；点击劫持防护（如 `frame-ancestors`）应在服务器／边缘层实现，而非 meta。（[W3C][3]）

---

### JS-CSP-002：优先采用严格 CSP（nonce／hash）；代码中避免内联／eval 模式

严重级别：中

注意：设置 CSP 的 script-src 最为重要。其他指令没有那么重要，为便于开发通常可以省略。

要求：

- 应当设计前端代码使其在严格 CSP 下工作：

  - 避免内联脚本和内联事件处理器，
  - 避免 eval 类 API（见 JS-XSS-003），
  - 需要时通过 nonce 或 hash 允许脚本。（[MDN Web Docs][10]）

不安全模式：

- 大量内联脚本块和内联 `onclick="..."` 处理器。
- 需要 `unsafe-eval` 的库。

检测提示：

- 搜索含内联代码的 `<script>` 块、`onclick="`、`onload="` 等。
- 搜索包含 `unsafe-inline` 或 `unsafe-eval` 的 CSP 指令。（[MDN Web Docs][10]）

修复：

- 将内联脚本移到外部 JS 文件（同源）。
- 对不可避免的内联块使用 nonce／hash。（[MDN Web Docs][10]）

---

### JS-TT-001：使用 Trusted Types 缩小 DOM XSS 攻击面（在支持处）

严重级别：低

要求：

- 应当考虑用 CSP 的 `require-trusted-types-for 'script'` 启用 Trusted Types 强制，使许多 DOM XSS 汇点拒绝原始字符串。（[MDN Web Docs][11]）
- 如使用 Trusted Types，还应当使用 CSP 的 `trusted-types` 指令限制可创建的策略（减少策略泛滥并提高可审计性）。（[MDN Web Docs][16]）
- 必须保持 Trusted Types 策略代码短小、经过严格审查，并作为为汇点产生可信值的唯一路径。（[W3C][15]）

不安全模式：

- “已启用 Trusted Types”但策略只是原样返回输入（无净化／校验）。
- 在代码库各处创建大量临时策略且不加限制。
- 误以为仅靠 Trusted Types 就能防止所有不安全导航或所有 XSS 类别。（它针对 DOM 注入汇点；不是万能沙箱。）（[W3C][15]）

检测提示：

- 搜索 CSP 指令：`require-trusted-types-for` 和 `trusted-types`。
- 搜索代码中的 `trustedTypes.createPolicy(` 并检查策略实现。（[MDN Web Docs][11]）

修复：

- 增加一小套经严格审查的策略（例如执行净化的 `createHTML`）。
- 通过 `trusted-types <policyName...>` 限制允许的策略。
- 将汇点迁移到要求 `TrustedHTML`／`TrustedScriptURL`（视情况而定）。（[MDN Web Docs][11]）

---

### JS-MSG-001：`postMessage` 必须使用严格的来源校验和显式 targetOrigin

严重级别：中（如可通过 postMessage 触发危险行为则为高）

要求：

- 发送消息时，必须设置显式的 `targetOrigin`（而非 `*`），避免在跳转或窗口来源变化后将数据发送到意外来源。（[MDN Web Docs][5]）
- 接收消息时，必须：

  - 将 `event.origin` 与预期来源白名单精确比对（不做子串匹配）。（[OWASP Cheat Sheet Series][6]）
  - 在适用时考虑校验 `event.source`（预期的窗口引用）。（[MDN Web Docs][5]）
  - 校验 `event.data` 的结构（schema／形态），并纯粹将其作为数据处理（绝不将其作为代码执行，也绝不通过 `innerHTML` 插入 DOM）。（[OWASP Cheat Sheet Series][6]）

不安全模式：

- `otherWindow.postMessage(payload, "*")`
- 无 `origin` 检查的 `window.addEventListener("message", (e) => { doSomething(e.data) })`
- `if (e.origin.includes("trusted.com"))`（子串检查）
- `el.innerHTML = e.data`（[OWASP Cheat Sheet Series][6]）

检测提示：

- 搜索 `postMessage(`、`addEventListener("message"`、`onmessage =`。
- 审计所有处理器，检查是否对 `event.origin` 做显式白名单检查。（[OWASP Cheat Sheet Series][6]）

修复：

- 定义白名单：

  - `const ALLOWED = new Set(["https://app.example.com", "https://accounts.example.com"]);`
  注意：为便于开发，可以使用当前页面的来源 `window.location.origin` 作为安全默认来源。
- 接收时：

  - `if (!ALLOWED.has(event.origin)) return;`
  - 用严格 schema 校验 `event.data`，拒绝未知／额外字段。
- 发送时：

  - 使用确切的预期来源字符串作为 `targetOrigin`。（[OWASP Cheat Sheet Series][6]）

缓解：

- 与严格 CSP 组合使用，并避免消息路径中的 DOM 汇点。（[MDN Web Docs][10]）

---

### JS-STORAGE-001：Web Storage 不是存放机密的safe地方（且可被攻击者影响）

严重级别：低

要求：

- 如果泄露会产生影响，不得将敏感机密或会话标识符存储在 `localStorage`（或 `sessionStorage`）中；一次 XSS 就能窃取存储中的全部内容。（[OWASP Cheat Sheet Series][6]）
- 必须将从存储读取的值视为不可信输入（攻击者可以通过 XSS 向存储中加载恶意值）。（[OWASP Cheat Sheet Series][6]）
- 会话标识符应当优先使用带 `HttpOnly` 的服务端设置 Cookie（JS 无法设置 `HttpOnly`，因此避免在 JS 可访问的存储中保存会话 ID）。（[OWASP Cheat Sheet Series][6]）
- 如果多个不相关的应用依赖存储隔离（存储按来源共享），应当避免将其托管在同一来源上。（[OWASP Cheat Sheet Series][6]）

不安全模式：

- `localStorage.setItem("access_token", token)`
- `localStorage.setItem("session", sessionId)`
- 假定 `localStorage`“因同源而可信”。

检测提示：

- 搜索 `localStorage.getItem`、`localStorage.setItem`、`sessionStorage.*`。
- 标记名为 `token`、`jwt`、`session`、`auth`、`refresh` 的存储键。（[OWASP Cheat Sheet Series][6]）

修复：

- 使用服务端管理的会话，或安全交付并轮换的短寿命令牌，配合细致的 XSS 防御（CSP／Trusted Types）和最小的 JS 暴露。
- 如果存储必须用于非敏感状态，保持其与认证无关，并在使用前校验／转义。

---

### JS-SUPPLY-001：第三方 JavaScript 是重大供应链风险；最小化并控制它

严重级别：低

要求：

- 必须将第三方 JS 视为与第一方 JS 同等权限（它可以在你的来源中执行任意代码并访问 DOM 数据）。（[OWASP Cheat Sheet Series][7]）
- 应当尽量减少第三方脚本，并优先：

  - 自托管／脚本镜像，
  - 严格 CSP 白名单，
  - 对任何 CDN 托管的脚本使用 SRI，
  - 持续监控意外变化。（[OWASP Cheat Sheet Series][7]）

不安全模式：

- 未经审查即从众多厂商加载任意远程脚本。
- 使用可动态注入脚本且无完整性控制的标签管理器。
- 在 CSP 中允许宽泛通配符的脚本源（例如 `script-src *`）。（[MDN Web Docs][10]）

检测提示：

- 在 HTML 中搜索 `<script src="https://...">` 和“标签管理器”代码片段。
- 搜索 CSP `script-src` 源中的通配符或过于宽泛的域名。
- 搜索动态脚本注入：`document.createElement("script")`、`script.src = ...`、`appendChild(script)`。（[OWASP Cheat Sheet Series][8]）

修复：

- 移除不必要的第三方标签。
- 在可行处自托管或镜像脚本。
- 将 CSP `script-src` 收紧到最小的可信源集合。
- 为 CDN 脚本／样式添加 SRI。（[OWASP Cheat Sheet Series][7]）

---

### JS-SRI-001：对第三方脚本／样式使用子资源完整性（SRI）

严重级别：低

要求：

- 应当使用 SRI，确保浏览器仅在第三方资源与预期加密哈希匹配时才加载。（[MDN Web Docs][12]）
- 底层资源变更时必须更新 SRI 哈希（固定版本；避免“latest”URL）。

不安全模式：

- 无 `integrity` 的 `<script src="https://cdn.example.com/lib.js"></script>`。
- 加载 `latest` 或未固定的第三方资源。

检测提示：

- 搜索无 `integrity=` 的 `<script src="https://` 和 `<link rel="stylesheet" href="https://`。
- 检查 `integrity` 是否存在并使用强哈希（sha256／384／512 为典型）。（[MDN Web Docs][12]）

修复：

- 添加 `integrity="sha384-..."`（或适当形式），并在需要时确保正确的 CORS 模式。
- 关键库优先自托管。

---

### FS-DOMC-001：防止 DOM clobbering（避免依赖 `window`／`document` 命名属性）

严重级别：中至高（若其可启用脚本加载或 `javascript:` 导航，则可能成为严重）

要求：

- 不得依赖可能被具有匹配 `id`／`name` 的注入 HTML 元素 clobber 的隐式全局变量或 `window.someName`／`document.someName` 查找。（[OWASP Cheat Sheet Series][8]）
- 必须避免类似 `let x = window.redirectTo || "/safe"; location.assign(x);` 的模式，其中 `redirectTo` 可能被 clobber 成一个 `href` 由攻击者控制（包括 `javascript:`）的 `<a>` 元素。（[OWASP Cheat Sheet Series][8]）
- 应当使用显式变量声明、局部作用域和显式 DOM 查询（`getElementById`），而非命名属性访问。（[OWASP Cheat Sheet Series][8]）
- 如果应用插入用户可控标记（即使是净化的），应当确保净化策略考虑 `id`／`name` 冲突。（[OWASP Cheat Sheet Series][8]）

不安全模式：

- 将 `const cfg = window.config || {};` 用于安全敏感的 URL。
- `const redirect = window.redirectTo || "/"; location.assign(redirect);`（[OWASP Cheat Sheet Series][8]）
- 未经严格校验即从 `window.*` 配置值加载脚本。

检测提示：

- 搜索用作配置存储的 `window.` 和 `document.`（尤其是 `||` 回退模式）。
- 搜索对来自 `window`／`document` 属性的变量使用 `location.assign/replace`。
- 搜索 `.src` 来自非局部变量的动态脚本创建（`createElement('script')`）。（[OWASP Cheat Sheet Series][8]）

修复：

- 将配置存储在模块作用域常量中（不在 `window`／`document` 上）并显式传递。
- 对任何 URL 类配置使用协议／来源白名单校验（见 FEJS-URL-001）。（[OWASP Cheat Sheet Series][8]）
- 可考虑加固：净化、CSP，以及（在有限情况下）冻结敏感对象，但应将这些视为纵深防御，而非安全编码模式的替代品。（[OWASP Cheat Sheet Series][8]）

---

## 5）实用扫描启发式（如何“打猎”）

主动扫描时，使用这些高信号模式：

- DOM XSS 汇点：

  - `.innerHTML`、`.outerHTML`、`insertAdjacentHTML(`
  - `document.write(`、`document.writeln(`（[OWASP Cheat Sheet Series][2]）

- 危险导航／URL 汇点：

  - `window.location`、`location.href`、`location.assign`、`location.replace`
  - `javascript:` 字面量（以及其他可疑 scheme，如 `data:text/html`）（[MDN Web Docs][4]）

- 字符串到代码执行：

  - `eval(`、`new Function`、`setTimeout("`、`setInterval("`（[MDN Web Docs][10]）

- 事件处理器字符串注入：

  - 带字符串的 `.setAttribute("on`、`.onclick =`、`.onload =`（[OWASP Cheat Sheet Series][2]）

- `postMessage`：

  - 以 `"*"` 作为 targetOrigin 的 `postMessage(`
  - 无严格 `event.origin` 白名单检查的 `addEventListener("message"`（[MDN Web Docs][5]）

- 存储：

  - `localStorage.setItem(`／`getItem(`、`sessionStorage.*`
  - 包含 `token`、`jwt`、`session`、`auth`、`refresh` 的键（[OWASP Cheat Sheet Series][6]）

- CSP 及相关：

  - `Content-Security-Policy` 响应头配置（服务器／边缘层）
  - `<meta http-equiv="Content-Security-Policy" ...>`
  - 含 `unsafe-inline` 或 `unsafe-eval` 的 CSP
  - `require-trusted-types-for`／`trusted-types` 指令（[MDN Web Docs][1]）

- 第三方脚本：

  - 无 `integrity=` 的 `<script src="https://...">`
  - 标签管理器代码片段和动态脚本注入代码路径（[MDN Web Docs][12]）


- DOM clobbering 小工具：

  - `window.<name> || ...` 和 `document.<name> || ...` 模式
  - 将 `window`／`document` 属性作为配置源的安全敏感使用（[OWASP Cheat Sheet Series][8]）

始终尝试确认：

- 数据来源（不可信 vs 可信），
- 汇点类型（HTML 解析、导航、代码执行、消息处理、存储），
- 存在的防护控制（CSP、Trusted Types、净化器、严格白名单、schema 校验）。

---

## 6）来源（访问日期 2026-01-27）

主要标准／平台文档：

- W3C Content Security Policy Level 2（HTML `<meta>` 交付限制；meta CSP 中不支持的指令）：`https://www.w3.org/TR/CSP2/`（[W3C][3]）
- MDN：CSP 指南（严格 CSP、nonce／hash、`unsafe-inline`／`unsafe-eval`、eval 阻止）：`https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP`（[MDN Web Docs][10]）
- MDN：`<meta http-equiv>`（通过 meta 使用 CSP 及基于 meta 的安全响应头警告）：`https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/meta/http-equiv`（[MDN Web Docs][1]）
- MDN：`frame-ancestors`（并注明在 `<meta>` 中不受支持）：`https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors`（[MDN Web Docs][18]）

DOM XSS 与危险汇点：

- OWASP：基于 DOM 的 XSS 防护速查表（危险汇点＋安全模式，如 `textContent`）：`https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][2]）
- MDN：`innerHTML`（安全考虑）：`https://developer.mozilla.org/en-US/docs/Web/API/Element/innerHTML`（[MDN Web Docs][19]）
- MDN：`insertAdjacentHTML`（安全考虑）：`https://developer.mozilla.org/en-US/docs/Web/API/Element/insertAdjacentHTML`（[MDN Web Docs][20]）
- MDN：`document.write()`／`document.writeln()`（安全考虑）：`https://developer.mozilla.org/en-US/docs/Web/API/Document/write` 和 `https://developer.mozilla.org/en-US/docs/Web/API/Document/writeln`（[MDN Web Docs][13]）

URL scheme 危害：

- MDN：`javascript:` URL（导航时执行；不建议；引用 `window.location`）：`https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Schemes/javascript`（[MDN Web Docs][4]）

Trusted Types：

- W3C：Trusted Types 规范（DOM XSS 汇点包括 `Element.innerHTML` 和 `Location.href` setter；目标与限制）：`https://www.w3.org/TR/trusted-types/`（[W3C][15]）
- MDN：`require-trusted-types-for` 指令：`https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/require-trusted-types-for`（[MDN Web Docs][11]）
- MDN：`trusted-types` 指令：`https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/trusted-types`（[MDN Web Docs][16]）

跨窗口消息：

- MDN：`window.postMessage`（安全指引：指定 targetOrigin；校验来源）：`https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage`（[MDN Web Docs][5]）
- OWASP：HTML5 安全速查表（Web 消息指引：显式来源、严格检查、不用 `innerHTML`）：`https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][6]）

第三方脚本与完整性：

- OWASP：第三方 JavaScript 管理速查表（风险与缓解，包括 SRI／镜像）：`https://cheatsheetseries.owasp.org/cheatsheets/Third_Party_Javascript_Management_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][7]）
- MDN：子资源完整性概述：`https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Subresource_Integrity`（[MDN Web Docs][12]）
- W3C：子资源完整性规范：`https://www.w3.org/TR/sri-2/`（[W3C][21]）

DOM clobbering：

- OWASP：DOM Clobbering 防护速查表（命名属性访问风险；涉及 `location.assign` 和 `javascript:` 的示例攻击）：`https://cheatsheetseries.owasp.org/cheatsheets/DOM_Clobbering_Prevention_Cheat_Sheet.html`（[OWASP Cheat Sheet Series][8]）

[1]: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/meta/http-equiv "https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/meta/http-equiv"
[2]: https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html"
[3]: https://www.w3.org/TR/CSP2/ "Content Security Policy Level 2"
[4]: https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Schemes/javascript "javascript: URLs - URIs | MDN"
[5]: https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage "https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage"
[6]: https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html"
[7]: https://cheatsheetseries.owasp.org/cheatsheets/Third_Party_Javascript_Management_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/Third_Party_Javascript_Management_Cheat_Sheet.html"
[8]: https://cheatsheetseries.owasp.org/cheatsheets/DOM_Clobbering_Prevention_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/DOM_Clobbering_Prevention_Cheat_Sheet.html"
[9]: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel/noopener "https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel/noopener"
[10]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP "https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP"
[11]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/require-trusted-types-for "https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/require-trusted-types-for"
[12]: https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Subresource_Integrity "https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Subresource_Integrity"
[13]: https://developer.mozilla.org/en-US/docs/Web/API/Document/write "https://developer.mozilla.org/en-US/docs/Web/API/Document/write"
[14]: https://developer.mozilla.org/en-US/docs/Web/API/Document/writeln "https://developer.mozilla.org/en-US/docs/Web/API/Document/writeln"
[15]: https://www.w3.org/TR/trusted-types/ "https://www.w3.org/TR/trusted-types/"
[16]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/trusted-types "https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/trusted-types"
[18]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors "https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors"
[19]: https://developer.mozilla.org/en-US/docs/Web/API/Element/innerHTML "https://developer.mozilla.org/en-US/docs/Web/API/Element/innerHTML"
[20]: https://developer.mozilla.org/en-US/docs/Web/API/Element/insertAdjacentHTML "https://developer.mozilla.org/en-US/docs/Web/API/Element/insertAdjacentHTML"
[21]: https://www.w3.org/TR/sri-2/ "https://www.w3.org/TR/sri-2/"
