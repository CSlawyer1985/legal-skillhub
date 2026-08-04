# Vue.js 网络安全规范（Vue 3.x、TypeScript/JavaScript、常用工具链：Vite）

本文档设计为一份**安全规范**，用于支持：

1. 新 Vue 代码的**安全默认代码生成**。
2. 现有 Vue 代码中的**安全审查/漏洞排查**（被动"工作途中发现问题"与主动"扫描代码库并报告发现"）。

本文档有意写成一组**规范性要求**（"必须/应当/可以"，MUST/SHOULD/MAY）外加**审计规则**（不良模式是什么样、如何检测、如何修复/缓解）。

---

## 0) 安全、边界与反滥用约束（必须遵守）

* 不得请求、输出、记录或提交机密信息（API 密钥、密码、私钥、会话 cookie、认证令牌）。
* 不得通过禁用保护来"修复"安全问题（例如削弱 CSP、开启不安全的模板编译、将 `v-html` 当作捷径、绕过后端认证，或"直接把令牌存进 localStorage"）。
* 审计期间必须提供**基于证据的发现**：引用证明该主张的文件路径、代码片段和配置值。
* 必须诚实地对待不确定性：如果某项保护可能存在于边界处（CDN、反向代理、WAF、服务器响应头），应报告为"代码库中不可见；请核实运行时/基础设施配置"。
* 必须牢记前端信任模型：**任何交付到浏览器的代码，攻击者都能读取和修改**。机密信息和"安全强制执行"不能依赖纯前端逻辑。

---

## 1) 工作模式

### 1.1 生成模式（默认）

当被要求编写新的 Vue 代码或修改现有代码时：

* 必须遵循本规范中的每一项**必须**要求。
* 应当遵循每一项**应当**要求，除非用户明确另有说明。
* 必须优先使用默认安全的框架特性和经检验的库，而非自研安全代码。
* 必须避免引入新的风险入口（运行时模板编译、`v-html` / `innerHTML`、不安全的 URL 导航、动态脚本注入等）。（[Vue.js][1]）

### 1.2 被动审查模式（编辑期间始终开启）

在 Vue 代码库的任何位置工作时（即使用户没有要求安全扫描）：

* 必须"注意"所触及/附近代码中对本规范的违反。
* 应当随手指出问题，附简要说明和安全修复方案。

### 1.3 主动审计模式（明确的扫描请求）

当用户要求"扫描""审计"或"排查漏洞"时：

* 必须系统化地搜索代码库中违反本规范的行为。
* 必须按结构化格式输出发现（见 §2.3）。

推荐的审计顺序：

1. 构建/部署入口点和托管配置（Docker、CI、静态托管、SSR 服务器）。
2. 机密信息暴露（环境变量使用、`.env*`、硬编码密钥）。（[vitejs][2]）
3. XSS 面：模板、`v-html` / `innerHTML`、URL/样式注入、DOM API。（[Vue.js][1]）
4. 浏览器中的认证/会话处理（令牌存储、带凭据的请求、CSRF 集成）。（[Vue.js][1]）
5. 路由/导航（开放重定向、"return_to/next"、不安全的站外导航）。（[Vue.js][1]）
6. 第三方脚本和内容（CDN 资源、分析工具、小部件、iframe）。（[Vue.js][1]）
7. 安全响应头和浏览器加固预期（CSP、点击劫持）。（[Vue.js][1]）
8. SSR 特定问题（状态序列化、模板边界），如适用。（[Vue.js][1]）

---

## 2) 定义与审查指引

### 2.1 不可信输入（除非证明安全，否则视为攻击者可控）

在 Vue 应用中，不可信输入包括（非穷尽）：

* 来自 API 的任何内容：`fetch`、`axios`、GraphQL 响应、webhook、第三方 SDK。
* 路由器控制的数据：`route.params`、`route.query`、`route.hash`，以及任何源自 `window.location` 的数据。
* 用户控制的持久化内容：在界面中显示、以数据库为后端的內容（评论、个人资料、CMS 内容）。
* 浏览器控制的存储：`localStorage`、`sessionStorage`、`IndexedDB`。
* 跨窗口消息：`postMessage` 输入。
* 任何可通过 DOM 污染（DOM clobbering）或注入 HTML 而受攻击者影响的內容（尤其是当 Vue 挂载到非无菌 DOM 上时）。（[Vue.js][1]）

### 2.2 状态变更操作（前端视角）

如果一项操作能够：

* 通过 API 调用创建/更新/删除数据。
* 更改认证/会话状态（登录、登出、刷新令牌）。
* 触发特权操作（支付、管理员操作）。
* 产生副作用（发送电子邮件、触发 webhook、更改账户设置）。

则该操作即为状态变更操作。

### 2.3 必需审计发现格式

对发现的每个问题，输出：

* 规则 ID：
* 严重程度：严重 / 高 / 中 / 低
* 位置：文件路径 + 组件/函数 + 行号
* 证据：确切的代码/配置片段
* 影响：可能出什么问题、谁可以利用
* 修复：安全的更改（优先最小 diff）
* 缓解：如果立即修复有困难，采用纵深防御
* 误报说明：不确定时应核实什么

---

## 3) 安全基线：最低生产配置（生产环境必须）

这是防止常见 Vue/前端错误配置的最简"生产基线"。

* 必须发布**生产构建**（而非开发构建或开发服务器）。（[Vue.js][3]）
* 不得在前端包中附带机密信息；将所有暴露给客户端的环境变量视为公开信息。（[vitejs][2]）
* 不得渲染非可信模板或允许用户提供的 Vue 模板（等同于任意 JavaScript 执行）。（[Vue.js][1]）
* 应当避免原始 HTML 注入（`v-html`、`innerHTML`），除非内容可信或经过强沙箱隔离。（[Vue.js][1]）
* 应当在服务器/CDN 层部署基线安全响应头（尤其是 CSP 和点击劫持防御）。（[OWASP Cheat Sheet Series][4]）
* 应当使用安全的认证模式（会话令牌优先使用 HttpOnly cookie；与后端协调 CSRF 方案）。（[Vue.js][1]）

---

## 4) 规则（生成 + 审计）

每条规则包含：要求实践、不安全模式、检测提示和修复方法。

### VUE-DEPLOY-001：不得在生产环境运行开发/预览服务器

严重程度：高

要求：

* 不得将 Vite/Vue 开发服务器（`vite`、`npm run dev`、HMR）作为生产服务器部署。
* 不得将 `vite preview` 作为生产服务器。（[vitejs][5]）
* 必须构建（`vite build`）并使用生产级静态服务器/CDN 提供构建产物服务，若采用 SSR 则使用生产级 SSR 服务器。（[vitejs][6]）

不安全模式：

* Docker/Procfile/systemd 将 `vite`、`npm run dev` 或 `vite preview` 作为生产入口运行。
* 公开暴露的 HMR 端点。

检测提示：

* 搜索：`vite`、`npm run dev`、`pnpm dev`、`yarn dev`、`vite preview`、`vue-cli-service serve`。
* 检查 Docker `CMD`、`ENTRYPOINT`、CI 部署脚本、平台配置。

修复：

* 用 `vite build` 构建产物。
* 用加固后的托管（CDN/静态服务器）提供 `dist/` 服务，或作为静态资源集成到后端服务器中。

备注：

* 本地使用开发/预览服务器没有问题；只有将其作为生产入口时才需要标记。

---

### VUE-DEPLOY-002：使用 Vue 生产构建，并在生产环境关闭 devtools

严重程度：中（若生产环境启用了 devtools/调试钩子则为高）

要求：

* 如果未经打包器而从 CDN/自托管加载 Vue，生产环境必须使用 `.prod.js` 构建。（[Vue.js][3]）
* 应当确保生产包不在生产构建中启用 Vue devtools，并且不应故意启用生产 devtools 标志。（[Vue.js][7]）

不安全模式：

* 生产环境中包含开发构建产物。
* 明确启用生产 devtools/诊断钩子。

检测提示：

* 搜索 HTML 中的 `vue.global.js` / 非 `.prod.js` 变体（使用 CDN 构建时）。
* 搜索构建配置中的 Vue 特性标志，如 `__VUE_PROD_DEVTOOLS__`。（[Vue.js][7]）

修复：

* 切换为生产构建产物，并确保编译时标志按生产环境配置。

---

### VUE-SECRETS-001：切勿在前端代码或环境变量中附带机密信息

严重程度：高（若真实凭据暴露则为严重）

要求：

* 必须将所有前端代码和配置视为公开信息。
* 不得在以下位置嵌入机密信息：

  * 源代码
  * 提交到代码库的 `.env` 文件
  * 包含在包中的 `import.meta.env.*` 变量
* 必须假定任何最终进入客户端包的 env 变量都是攻击者可读取的。（[vitejs][2]）

不安全模式：

* 包含真正机密（而非仅公开标识符）的 `VITE_API_KEY=...`。
* 在 JS/TS 中硬编码 API 密钥、私有令牌、服务凭据、签名密钥。

检测提示：

* 搜索：`VITE_`、`import.meta.env`、`.env`、`.env.production`、`.env.*.local`。
* 用 grep 搜索 `API_KEY`、`SECRET`、`TOKEN`、`PRIVATE_KEY`、`BEGIN`、`sk-`、`AKIA` 等。

修复：

* 将机密信息移至后端/边缘函数。
* 需要时使用后端签发的短期令牌供浏览器使用。

备注：

* Vite 特别警告 `.env.*.local` 应加入 gitignore，且 `VITE_*` 变量会进入客户端包，因此不得包含敏感信息。（[vitejs][2]）

---

### VUE-SECRETS-002：不得扩大 Vite 环境变量暴露范围

严重程度：高

要求：

* 不得将 Vite 配置为向客户端暴露所有环境变量。
* 应当保持 `envPrefix` 严格且明确。

不安全模式：

* 将 `envPrefix` 设置为过于宽泛的值（或 `''`）以"让 env 变量生效"。
* 在构建时将服务器机密注入 HTML 全局变量的自定义脚本。

检测提示：

* 检查 `vite.config.*` 中的 `envPrefix`。
* 查找 `define: { 'process.env': ... }` 或手动注入 `window.__CONFIG__` 的情况。

修复：

* 将机密信息保留在服务器端。
* 只暴露有意设计为公开的非敏感值。

备注：

* Vite 文档说明只有带前缀的变量会被暴露，且被暴露的变量会进入客户端包。（[vitejs][2]）

---

### VUE-XSS-001：优先使用 Vue 的默认转义；避免原始 HTML 注入

严重程度：高

要求：

* 在可能的情况下，必须依赖 Vue 对文本插值和属性绑定的自动转义。（[Vue.js][1]）
* 不得通过以下方式渲染用户提供的 HTML：

  * `v-html`
  * 渲染函数 / JSX 中的 `innerHTML`
  * 直接 DOM API（`element.innerHTML`、`insertAdjacentHTML`）

  除非该 HTML 可信或经过稳健的净化处理，且该风险已被明确接受。（[Vue.js][1]）

不安全模式：

* `<div v-html="userProvidedHtml"></div>`
* `h('div', { innerHTML: userProvidedHtml })`
* `<div innerHTML={userProvidedHtml}></div>`
* `el.innerHTML = untrusted`

检测提示：

* 搜索：`v-html`、`innerHTML`、`insertAdjacentHTML`、`DOMParser`、`document.write`。

修复：

* 将不可信内容作为文本渲染（插值）。
* 如果必须渲染 HTML（如 Markdown），使用维护良好的 HTML 净化器进行净化，并应用纵深防御（CSP、Trusted Types）。（[Vue.js][1]）

备注：

* Vue 文档明确警告，用户提供的 HTML 除非经过沙箱隔离或严格仅限自暴露，否则绝不"100% 安全"。（[Vue.js][1]）

---

### VUE-XSS-002：切勿使用非可信模板（客户端模板/代码注入）

严重程度：严重

要求：

* 不得将非可信内容用作 Vue 组件模板。
* 必须将"用户可以编写 Vue 模板"视为"用户可以在你的应用中执行任意 JavaScript"，在 SSR 情境中也可能如此。（[Vue.js][1]）
* 应当优先使用仅运行时构建（模板在构建时编译），除非有经审查核实的需要，否则避免附带运行时编译器。

不安全模式：

* `createApp({ template: '<div>' + userProvidedString + '</div>' }).mount(...)`
* 将模板存储在数据库中并在浏览器中编译/渲染。
* 允许输入 Vue 模板语法的管理后台/CMS 功能。

检测提示：

* 搜索：值为非静态字符串的 `template:`。
* 搜索：`@vue/compiler-dom`、`compile(`、"运行时编译器"构建选择、动态 SFC 编译。
* 搜索"模板编辑器""自定义模板""主题 HTML"等功能。

修复：

* 将模板视为代码：保持由开发人员控制。
* 如果需要最终用户自定义，使用安全格式（受限 Markdown 子集）并通过净化器渲染，或隔离在沙箱 iframe 中。

---

### VUE-XSS-003：不得将 Vue 挂载到可能包含用户提供的服务器渲染 HTML 的 DOM 上

严重程度：中

要求：

* 不得将 Vue 挂载到可能包含服务器渲染且用户提供内容的节点上（因为"作为 HTML 安全"的攻击者控制 HTML 可能作为 Vue 模板变得不安全）。（[Vue.js][1]）
* 应当将 Vue 挂载到"无菌"根元素上，并让 Vue 控制的模板/组件渲染应用的 DOM。

不安全模式：

* 服务器将用户内容渲染进 `#app`，然后 Vue 挂载到 `#app` 上并将该 DOM 当作模板编译/解释。
* 在包含用户生成内容的大型服务器渲染页面上"点缀式"使用 Vue。

检测提示：

* 检查服务器模板（如 Rails/Django/Express 模板）中 Vue 挂载根内插入的用户 HTML。
* 查找 `mount('#app')` 且 `#app` 包含服务器渲染的 UGC 的情况。

修复：

* 将用户渲染的 HTML 移出 Vue 挂载根，或以安全方式（文本/净化后 HTML）从 Vue 组件渲染。

---

### VUE-XSS-004：防止绑定和导航中的 URL 注入

严重程度：高

要求：

* 在绑定到导航入口（`href`、`src`、`action`、`window.location`、`window.open`、路由站外导航）之前，必须验证/净化任何受用户影响的 URL。
* 必须特别防止 `<a :href="userProvidedUrl">` 等绑定中的 `javascript:` URL 执行。（[Vue.js][1]）
* 应当验证协议和目标（将 `https:` 和预期主机列入白名单；仅在有意图时允许 `mailto:`/`tel:`）。

不安全模式：

* `<iframe :src="userProvidedUrl">`
* `window.location = route.query.next`
* `window.open(userProvidedUrl)`

检测提示：

* 搜索：使用不可信输入的 `:href=`、`:src=`、`window.location`、`location.href`、`window.open`、`router.push(`。
* 查找 `next`、`return_to`、`redirect` 查询参数。

修复：

* 优先通过你控制的路由名称/路径进行内部导航。
* 对外部 URL：用 `new URL(...)` 解析，将协议/主机列入白名单，拒绝 `javascript:` 和其他危险协议。
* 在存储用户 URL 之前，在后端进行净化和验证（Vue 文档明确建议后端净化）。（[Vue.js][1]）

---

### VUE-XSS-005：防止样式/CSS 注入和界面欺骗（UI redress）

严重程度：低

要求：

* 不得大范围绑定攻击者控制的 CSS 字符串（如 `:style="userProvidedStyles"`）。
* 应当使用 Vue 的样式对象语法，如果允许用户自定义，只允许安全、特定的属性。（[Vue.js][1]）
* 应当将"用户可控制布局/CSS"的功能隔离在沙箱 iframe 中。

不安全模式：

* 样式受攻击者控制的 `:style="userProvidedStyles"`。
* 渲染用户提供的 `<style>` 内容（即使 Vue 阻止某些模式，也不要试图绕过它）。

检测提示：

* 搜索：绑定到源自 API/用户内容的非常量变量的 `:style="`。
* 搜索"自定义 CSS""主题编辑器""个人资料 CSS"。

修复：

* 将属性和值列入白名单；避免原始样式字符串。
* 对丰富的用户自定义使用沙箱 iframe。

---

### VUE-XSS-006：切勿将用户提供的 JavaScript 绑定到事件处理程序属性中

严重程度：严重

要求：

* 不得将攻击者提供的字符串绑定到事件处理程序属性（如 `onclick`、`onfocus` 等）中。
* 必须将"用户提供的 JS"视为不安全，除非经过沙箱隔离且保证仅限自暴露。（[Vue.js][1]）

不安全模式：

* `<div :onclick="userProvidedString">`
* `<a :onmouseenter="userProvidedString">`

检测提示：

* 搜索：后接事件属性名的 `:on`（`:onclick`、`:onload` 等）。
* 搜索 `setAttribute('on` 模式。

修复：

* 使用带有开发者控制处理程序的真实事件监听器。
* 如果确实需要用户脚本，将其隔离（沙箱 iframe + 严格边界）。

---

### VUE-ROUTER-001：不得将客户端路由守卫视为授权

严重程度：高

要求：

* 不得依赖 Vue Router 守卫、界面隐藏或客户端检查来强制执行授权。
* 必须对每个特权操作和敏感数据响应在后端强制执行授权。（[OWASP Cheat Sheet Series][8]）

不安全模式：

* "管理路由受保护，因为 `beforeEach` 检查 `user.isAdmin`"。
* 假定"前端未经允许不会调用此接口"的敏感 API 端点。

检测提示：

* 搜索 `router.beforeEach` 中的基于角色的门禁，并检查后端是否也执行了该门禁。
* 查找无服务器佐证的"按路由元数据实现安全"模式（`meta.requiresAdmin`）。

修复：

* 将路由守卫仅保留为 UX 用途（减少意外访问），但真实检查在服务端执行。

---

### VUE-ROUTER-002：防止开放重定向和不安全的"return_to/next"处理

严重程度：低

要求：

* 必须验证源自不可信输入的跳转目标（`next`、`return_to`、`redirect`）。
* 应当只允许同站点相对路径或明确的目标白名单。
* 不得允许非 `http` / `https` 协议（如 `javascript:`）。

不安全模式：

* `router.push(route.query.next as string)`
* `window.location.href = route.query.redirect`

检测提示：

* 搜索 `route.query.next`、`route.query.redirect`、`return_to`、`continue`、`callback`。
* 跟踪该值进入路由器/window 导航入口的情况。

修复：

* 只允许以 `/` 开头的相对路径（并拒绝 `//host`、`javascript:` 等）。
* 优先跳转到你控制的命名路由。

备注：

* 连 Vue 文档都指出，净化后的 URL 仍可能无法保证目标安全。（[Vue.js][1]）

---

### VUE-AUTH-001：令牌存储必须假定 XSS 可能发生

严重程度：低

要求：

* 必须假定任何 JavaScript 可访问的令牌都可能被 XSS 窃取。
* 应当优先使用（后端设置的）HttpOnly cookie 存储会话令牌，并在相关场合配合 CSRF 防护。（[Vue.js][1]）
* 应当避免在 `localStorage`/`sessionStorage` 中存储长期令牌（尤其是刷新令牌）。

不安全模式：

* 为长期持有的 bearer 令牌使用 `localStorage.setItem('token', ...)`。
* 将刷新令牌存储在 JS 可访问的存储中。

检测提示：

* 搜索：`localStorage`、`sessionStorage`、`indexedDB`、`persist`、`pinia-plugin-persistedstate`。
* 识别存储的值是否为认证/会话材料。

修复：

* 优先通过 HttpOnly cookie 使用后端管理的会话。
* 如果 bearer 令牌不可避免，保持短期有效、存储在内存中并频繁轮换；配合强 XSS 缓解措施（CSP、Trusted Types、严格净化）。（[OWASP Cheat Sheet Series][4]）

---

### VUE-CSRF-001：使用 cookie 时与后端协调 CSRF 方案

严重程度：高（针对 cookie 认证的状态变更请求）

注意：如果应用不使用基于 cookie 的认证（例如通过 Authorization 头传递），则 CSRF 不是问题。

要求：

* 如果 API 请求包含 cookie（`credentials: 'include'` / `withCredentials: true`）且 cookie 用于用户认证，必须包含与后端协调的 CSRF 防护（令牌/响应头模式、Origin 检查、SameSite cookie 作为纵深防御）。（[Vue.js][1]）
* 不得通过禁用后端保护或在前端使用 `mode: 'no-cors'` 来"解决 CORS/CSRF 错误"。

不安全模式：

* 任何地方都不使用 CSRF 令牌/响应头的 `fetch(url, { credentials: 'include', method: 'POST', body: ... })`。
* 没有严格来源白名单（后端侧）就启用跨源带凭据请求。

检测提示：

* 搜索：`credentials: 'include'`、`withCredentials`、`xsrf`、`csrf`、`X-CSRF-Token`、`X-XSRF-TOKEN`。
* 查看 API 封装模块中的响应头和 cookie 设置。

修复：

* 实现后端签发的 CSRF 令牌，并要求状态变更请求携带。
* 在兼容的情况下保持 cookie 为 `SameSite=Lax/Strict`，并在适当处（后端驱动）验证 Origin/Referer。（[OWASP Cheat Sheet Series][9]）

备注：

* Vue 文档明确指出 CSRF 主要由后端解决，但建议在 CSRF 令牌提交上进行协调。（[Vue.js][1]）

---

### VUE-HTTP-001：不要将机密信息放入 URL；避免在导航/日志中泄露敏感数据

严重程度：中

要求：

* 不得将令牌/机密信息放入查询字符串或片段中（它们会通过日志、referrer、浏览器历史泄露）。
* 应当避免在生产环境向控制台记录敏感值。

不安全模式：

* 超出短期 OAuth 交接范围使用的 `/?token=...`、`/#access_token=...`。
* 包含令牌/PII 的 `console.log(userSession)`。

检测提示：

* 搜索路由解析、认证回调处理程序和埋点日志中的 `token=`。
* 搜索认证代码周围的 `console.log(`。

修复：

* 使用 Authorization 头或 HttpOnly cookie。
* 清理日志；将调试日志限制在仅开发环境检查之后。

---

### VUE-HEADERS-001：在部署层要求安全响应头

严重程度：中

要求：

* 应当为你的 Vue 应用部署合适的 CSP（`Content-Security-Policy`）。
* 应当部署点击劫持防御（CSP `frame-ancestors` 和/或 `X-Frame-Options`），除非有意允许嵌入。
* 应当部署 `X-Content-Type-Options: nosniff`，以及按需的其他响应头（Referrer-Policy、Permissions-Policy）。（[OWASP Cheat Sheet Series][4]）

不安全模式：

* 对于包含 UGC 或丰富 HTML 渲染的应用，服务器/CDN 配置中没有响应头的迹象。
* 没有充分理由就在 CSP 中包含 `unsafe-inline`/`unsafe-eval`。

检测提示：

* 查找托管配置：nginx、Netlify/Vercel 响应头配置、CloudFront/Cloudflare 规则。
* 如果代码库中没有，标记为"需在边缘层核实"。

修复：

* 在边缘层或服务器中设置响应头。从保守的 CSP 开始，再逐步收紧。

---

### VUE-CSP-001：可行时使用 Trusted Types 和 DOM XSS 加固

严重程度：低

要求：

* 对于 DOM 注入面较大的应用（富文本、插件、`v-html`），应当考虑启用 Trusted Types 以降低 DOM XSS 风险。（[web.dev][10]）
* 应当将 Trusted Types 视为纵深防御，而非净化处理的替代。

不安全模式：

* 频繁使用未经净化或未经 CSP 加固的 `innerHTML`/`v-html`。

检测提示：

* 搜索：`v-html`、`innerHTML`、`insertAdjacentHTML`。
* 检查 CSP 中是否使用 `require-trusted-types-for 'script'`（如果响应头在代码库中）。

修复：

* 减少/集中 HTML 注入点，净化输入，并在适当处添加 Trusted Types 策略。

---

### VUE-THIRDPARTY-001：避免动态第三方脚本注入；优先静态、经审查的加载方式

严重程度：低

要求：

* 不得注入 URL 由用户控制的 `<script src="...">`。
* 应当将第三方小部件/埋点视为供应链风险；只从经审查、固定版本的来源加载。

不安全模式：

* `const s=document.createElement('script'); s.src = userProvidedUrl; ...`
* 加载任意远程脚本的"插件市场"。

检测提示：

* 搜索：`createElement('script')`、`.src =`、`appendChild(script)`。
* 搜索 "loadExternalScript"、"injectScript"、"cdnUrl"。

修复：

* 打包依赖，或将严格来源列入白名单并强制完整性检查（见 SRI 规则）。
* 对不可信的第三方界面考虑使用沙箱 iframe。

---

### VUE-SRI-001：对 CDN 托管的脚本/样式使用子资源完整性（SRI）

严重程度：低

要求：

* 如果从 CDN 加载脚本/样式，应当使用子资源完整性（`integrity` 属性）并配置合适的 `crossorigin`。（[MDN Web Docs][11]）
* 对于安全关键代码，应当优先自托管或打包，而非运行时 CDN 依赖。

不安全模式：

* 无 `integrity` 的 `<script src="https://cdn.example/...">`。
* 未固定版本、内容可能变化的远程脚本 URL。

检测提示：

* 搜索 `index.html` 和服务器模板中的 `https://` 脚本/样式标签。
* 检查是否存在 `integrity=`。

修复：

* 添加 SRI 哈希（并固定版本），或随构建打包资源。

---

### VUE-SUPPLY-001：依赖与补丁卫生是强制要求

严重程度：低

要求：

* 应当保持 Vue 及官方配套库更新；Vue 明确建议使用最新版本以尽可能保持安全。（[Vue.js][1]）
* 必须及时响应安全公告。
* 应当固定依赖版本并提交锁文件（以减少生产产物的漂移）。

不安全模式：

* 存在已知 CVE 的过时主要版本。
* 代码库中没有锁文件；关键依赖使用宽泛的 semver 范围。
* 忽视模板/渲染/编译器包的安全公告。

检测提示：

* 检查 `package.json`、锁文件、CI 安装命令。
* 搜索被禁用的 `npm audit`、"ignore vulnerabilities" 脚本。

修复：

* 升级依赖，并围绕受影响行为添加回归测试。
* 在 CI 中添加依赖扫描。

---

### VUE-SSR-001：SSR 增加了额外的信任边界；将状态注入视为 XSS 敏感

严重程度：中

要求：

* 使用 SSR 时，必须将注入 HTML 文档的任何内容（初始状态、序列化数据、内联脚本）视为 XSS 敏感。
* 必须更加严格执行"仅可信模板"规则，因为不安全的模板可能导致渲染期间的服务器端执行。（[Vue.js][1]）
* 应当遵循 Vue SSR 文档和 SSR 安全最佳实践。（[Vue.js][1]）

不安全模式：

* 将不可信字符串拼接进 SSR 模板。
* 在没有稳健转义/序列化控制的情况下将 JSON 注入 `<script>` 块。

检测提示：

* 搜索服务器代码中的 `__INITIAL_STATE__`、`window.__*STATE__`、模板拼接和 SSR 渲染管线。
* 将不可信数据跟踪到这些入口。

修复：

* 使用 SSR 技术栈推荐的序列化安全模式。
* 避免渲染不可信 HTML；进行净化或隔离。

---

## 5) 实用扫描启发式方法（如何进行"排查"）

主动扫描时，使用这些高信号模式：

* 生产环境中的开发/预览服务器：

  * `npm run dev`、`vite`、`vite preview`、`vue-cli-service serve` （[vitejs][5]）
* 机密信息暴露：

  * `.env`、`.env.production`、`.env.*.local`、`VITE_`、`import.meta.env`、硬编码的 `API_KEY` / `SECRET` （[vitejs][2]）
* XSS 入口：

  * `v-html`、`innerHTML`、`insertAdjacentHTML`、`DOMParser`、`document.write` （[Vue.js][1]）
* 客户端模板注入：

  * `template:` 拼接、`compile(`、运行时编译器使用、挂载到非无菌 DOM （[Vue.js][1]）
* URL 注入 / 开放重定向：

  * 来自用户数据的 `:href="..."` / `:src="..."`
  * `javascript:` 出现处
  * 流入 `router.push` 或 `window.location` 的 `route.query.next` / `redirect` / `return_to` （[Vue.js][1]）
* 样式注入：

  * `:style="userProvidedStyles"` 或用户驱动的主题 CSS （[Vue.js][1]）
* 令牌存储：

  * `localStorage.setItem('token'...)`、持久化认证存储、存储在 JS 可访问存储中的刷新令牌
* CSRF 集成危险信号：

  * 无任何 CSRF 响应头/令牌处理的 `credentials: 'include'` / `withCredentials: true` （[Vue.js][1]）
* 第三方脚本：

  * 动态脚本注入（`createElement('script')`）、无 SRI 的 CDN 脚本 （[MDN Web Docs][11]）
* 外部链接安全：

  * 无 `rel="noopener"`/`noreferrer` 的 `target="_blank"`（为兼容旧版和明确性仍建议添加）（[MDN Web Docs][12]）

始终尝试确认：

* 数据来源（不可信与可信）
* 入口类型（HTML/DOM 插入、模板编译、URL 导航、样式注入、脚本注入）
* 现有的防护控制（净化、白名单、CSP/Trusted Types、后端验证）

---

## 6) 资料来源（访问于 2026-01-27）

Vue 主要文档：

* Vue 文档：安全——`https://vuejs.org/guide/best-practices/security` （[Vue.js][1]）
* Vue 文档：模板语法（关于 DOM 内模板的安全警告）——`https://vuejs.org/guide/essentials/template-syntax` （[Vue.js][13]）
* Vue 文档：生产部署——`https://vuejs.org/guide/best-practices/production-deployment` （[Vue.js][3]）
* Vue 文档：特性标志——`https://link.vuejs.org/feature-flags` （[Vue.js][7]）

Vite 文档（常见 Vue 工具链）：

* Vite 文档：环境变量与模式（VITE_* 暴露 + 安全说明）——`https://vite.dev/guide/env-and-mode` （[vitejs][2]）
* Vite 文档：CLI（`vite preview` 并非为生产而设计）——`https://vite.dev/guide/cli` （[vitejs][5]）
* Vite 文档：服务器选项（`server.host` 可以监听公共地址）——`https://vite.dev/config/server-options` （[vitejs][14]）

OWASP 与 Web 平台加固参考：

* OWASP Cheat Sheet Series：XSS 防御——`https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html` （[Vue.js][1]）
* OWASP Cheat Sheet Series：CSRF 防御——`https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html` （[OWASP Cheat Sheet Series][9]）
* OWASP Cheat Sheet Series：授权——`https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html` （[OWASP Cheat Sheet Series][8]）
* OWASP Cheat Sheet Series：HTTP 响应头——`https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html` （[OWASP Cheat Sheet Series][4]）
* HTML5 安全速查表（Vue 引用）——`https://html5sec.org/` （[Vue.js][1]）

浏览器/平台参考：

* MDN：`rel="noopener"`——`https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel/noopener` （[MDN Web Docs][12]）
* MDN：子资源完整性——`https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity` （[MDN Web Docs][11]）
* web.dev：Trusted Types——`https://web.dev/trusted-types/` （[web.dev][10]）

[1]: https://vuejs.org/guide/best-practices/security "https://vuejs.org/guide/best-practices/security"
[2]: https://vite.dev/guide/env-and-mode "https://vite.dev/guide/env-and-mode"
[3]: https://vuejs.org/guide/best-practices/production-deployment "https://vuejs.org/guide/best-practices/production-deployment"
[4]: https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html"
[5]: https://vite.dev/guide/cli "https://vite.dev/guide/cli"
[6]: https://vite.dev/guide/build "https://vite.dev/guide/build"
[7]: https://vuejs.org/guide/best-practices/production-deployment?utm_source=chatgpt.com "Production Deployment"
[8]: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html"
[9]: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html "https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html"
[10]: https://web.dev/articles/trusted-types "https://web.dev/articles/trusted-types"
[11]: https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Subresource_Integrity?utm_source=chatgpt.com "Subresource Integrity - Security - MDN Web Docs"
[12]: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel/noopener "https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel/noopener"
[13]: https://vuejs.org/guide/essentials/template-syntax "Template Syntax | Vue.js"
[14]: https://vite.dev/config/server-options "https://vite.dev/config/server-options"
