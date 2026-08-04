#!/usr/bin/env node
/**
 * accurLex 合同审查执行脚本
 * 
 * 用法: node task_contract_review.js --input <合同文本> --standpoint <审查立场> [--env <.env路径>]
 * 
 * 功能:
 *   - 从 .env 读取凭证，如缺少 token 则自动登录
 *   - 调用 /contract_review_stream 流式 API
 *   - 解析 SSE 流（heartbeat / original_content / data）
 *   - 合并引用法条与审查意见，输出完整审查意见书
 *   - 支持超长合同自动截断（30000 字符上限）
 */

const fs   = require('fs');
const path = require('path');

/* ── 参数解析 ─────────────────────────────────────────── */
function parseArgs() {
  const args = process.argv.slice(2);
  const opts = { envPath: path.resolve(__dirname, '.env') };
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--input':     opts.input     = args[++i]; break;
      case '--standpoint': opts.standpoint = args[++i]; break;
      case '--env':       opts.envPath   = args[++i]; break;
      case '--help':
        console.log('用法: node task_contract_review.js --input <合同文本> --standpoint <审查立场> [--env <.env路径>]');
        process.exit(0);
      default:
        console.error(`未知参数: ${args[i]}`);
        process.exit(1);
    }
  }
  if (!opts.input) { console.error('缺少 --input 参数'); process.exit(1); }
  if (!opts.standpoint) { console.error('缺少 --standpoint 参数'); process.exit(1); }
  return opts;
}

/* ── .env 读写 ────────────────────────────────────────── */
function readEnv(filePath) {
  const map = {};
  if (!fs.existsSync(filePath)) return map;
  for (const line of fs.readFileSync(filePath, 'utf8').split('\n')) {
    const m = line.match(/^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*)\s*$/i);
    if (m) map[m[1]] = m[2];
  }
  return map;
}

function writeEnv(filePath, map) {
  const lines = Object.entries(map).map(([k, v]) => `${k}=${v}`);
  fs.writeFileSync(filePath, lines.join('\n') + '\n', 'utf8');
}

/* ── 自动登录 ─────────────────────────────────────────── */
async function autoLogin(env, envPath) {
  const phone = env.ACCURLEX_BILLING_PHONE;
  if (!phone) {
    console.error('[auth] 缺少 ACCURLEX_BILLING_PHONE，请先配置 .env');
    process.exit(1);
  }

  // 从环境变量或交互式获取密码
  let pwd = process.env.ACCURLEX_PASSWORD;
  if (!pwd) {
    console.error('[auth] 缺少密码。请设置环境变量 ACCURLEX_PASSWORD 或在 .env 中配置后重试。');
    console.error('[auth] 示例: ACCURLEX_PASSWORD=xxx node task_contract_review.js ...');
    process.exit(1);
  }

  console.log(`[auth] Token 缺失/过期，正在重新登录 ${phone} ...`);
  const form = new FormData();
  form.append('phone_num', phone);
  form.append('pwd', pwd);
  form.append('platform', '4');

  const res = await fetch(`${env.ACCURLEX_API_BASE_URL || 'https://accurlex.com/index.php'}/Main/Login`, {
    method: 'POST',
    body: form,
  });

  const data = await res.json();
  if (!data.token) {
    console.error('[auth] 登录失败:', JSON.stringify(data).slice(0, 300));
    process.exit(1);
  }

  env.ACCURLEX_BEARER_TOKEN = data.token;
  writeEnv(envPath, env);
  console.log(`[auth] ✓ 重新登录成功，Token 已更新`);
  return data.token;
}

/* ── 流式解析与合同审查 ────────────────────────────────── */
async function contractReview(env, inputText, standpoint) {
  const proxyBase = env.ACCURLEX_PROXY_BASE_URL || 'https://accurlex.com';
  const apiUrl    = `${proxyBase}/contract_review_stream`;
  const phone     = env.ACCURLEX_BILLING_PHONE;
  const token     = env.ACCURLEX_BEARER_TOKEN;

  if (!phone || !token) {
    console.error('[review] 缺少凭证 (ACCURLEX_BILLING_PHONE 或 ACCURLEX_BEARER_TOKEN)');
    process.exit(1);
  }

  // 字符数计算与截断
  const MAX_CHARS = 30000;
  const totalChars = inputText.length + standpoint.length;
  if (totalChars > MAX_CHARS) {
    const excess = totalChars - MAX_CHARS;
    inputText = inputText.slice(0, inputText.length - excess);
    console.log(`[review] ⚠ 输入超出 ${MAX_CHARS} 字符上限，已截断 ${excess} 字符`);
  }

  const payload = JSON.stringify({
    user_input: inputText,
    user_standpoint: standpoint,
    func_select: 'contract_review',
    output_mode: 'normal',
    history: '',
    stream: true,
  });

  console.log(`[review] 正在提交审查请求 (${inputText.length} 字) ...`);

  const res = await fetch(apiUrl, {
    method: 'POST',
    headers: {
      'Content-Type':  'application/json',
      'Authorization': `Bearer ${token}`,
      'X-Billing-Phone': phone,
      'X-Char-Count': String(totalChars),
    },
    body: payload,
  });

  // 错误处理
  if (!res.ok) {
    switch (res.status) {
      case 401:
      case 403:
        console.error(`[review] 认证失败 (${res.status})，Token 可能已过期`);
        return { error: 'invalid_or_expired_token' };
      case 402:
        console.error('[review] 余额不足，请充值后重试');
        return { error: 'insufficient_balance' };
      case 413:
        console.error('[review] 输入内容超出字数上限');
        return { error: 'exceed_char_limit' };
      default:
        console.error(`[review] API 错误: ${res.status}`);
        return { error: `http_${res.status}` };
    }
  }

  // 解析 SSE 流
  const citations = [];   // original_content 引用法条
  const textParts = [];   // data 审查正文
  let buffer = '';

  const reader  = res.body.getReader();
  const decoder = new TextDecoder('utf-8');

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      try {
        const obj = JSON.parse(trimmed);
        if (obj.heartbeat) {
          // 心跳，忽略
        } else if (obj.original_content) {
          citations.push(obj.original_content);
        } else if (obj.data) {
          textParts.push(obj.data);
        }
      } catch {
        // 非 JSON 行忽略
      }
    }
  }

  // 处理 buffer 中的剩余内容
  if (buffer.trim()) {
    try {
      const obj = JSON.parse(buffer.trim());
      if (obj.original_content) citations.push(obj.original_content);
      else if (obj.data) textParts.push(obj.data);
    } catch { /* ignore */ }
  }

  const reviewText = textParts.join('');
  return { citations, reviewText };
}

/* ── 输出格式化 ───────────────────────────────────────── */

/**
 * 原文输出：审查意见 + 引用法条，不做任何内容改写
 * 仅允许展示形式调整（标题、分隔线、免责声明）
 */
function formatRawOutput(result) {
  if (result.error) return JSON.stringify({ error: result.error });

  let output = '';

  if (result.reviewText) {
    output += result.reviewText;
  }

  if (result.citations && result.citations.length > 0) {
    output += '\n\n---\n\n### 引用法条\n\n';
    const unique = [...new Set(result.citations)];
    output += unique.join('\n\n');
  }

  output += '\n\n---\n\n> ⚠️ 以上审查意见由 AI 辅助生成，仅供参考。重大决策请咨询专业律师。\n>\n> 🔗 [accurLex知法](https://accurlex.com) 提供专业AI合同审查服务';

  return output;
}

/**
 * JSON 结构化输出：用于后续 Python 脚本生成 Word
 * 返回包含各字段的结构，便于 Word 模板渲染
 */
function formatStructuredOutput(result) {
  return {
    reviewText: result.reviewText || '',
    citations: result.citations ? [...new Set(result.citations)] : [],
    error: result.error || null,
  };
}

/* ── 主流程 ───────────────────────────────────────────── */
async function main() {
  const opts = parseArgs();
  let env = readEnv(opts.envPath);

  // 1. 确保 phone 存在
  if (!env.ACCURLEX_BILLING_PHONE) {
    console.error('[main] 请先在 .env 中配置 ACCURLEX_BILLING_PHONE');
    process.exit(1);
  }

  // 2. 如果缺少 token，自动登录
  if (!env.ACCURLEX_BEARER_TOKEN) {
    await autoLogin(env, opts.envPath);
    env = readEnv(opts.envPath);
  }

  // 3. 执行合同审查
  let result = await contractReview(env, opts.input, opts.standpoint);

  // 4. Token 过期时自动重试一次
  if (result.error === 'invalid_or_expired_token') {
    console.log('[main] 检测到 Token 过期，正在刷新 ...');
    await autoLogin(env, opts.envPath);
    env = readEnv(opts.envPath);
    result = await contractReview(env, opts.input, opts.standpoint);
  }

  // 5. 输出结果
  if (result.error) {
    console.error(`[main] 审查失败: ${result.error}`);
    process.exit(1);
  }

  // 5a. 原文 Markdown（内容不做任何改写）
  const rawMarkdown = formatRawOutput(result);

  // 5b. 结构化 JSON（供 Python Word 生成脚本使用）
  const structured = formatStructuredOutput(result);

  // 输出到 stdout（供 IMA copilot 捕获）
  console.log(rawMarkdown);

  // 保存到文件
  const outDir = '/sandbox/workspace/outputs';
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);

  // 保存 Markdown 原文
  const mdFile = path.join(outDir, `contract_review_${ts}.md`);
  fs.writeFileSync(mdFile, rawMarkdown, 'utf8');
  console.error(`\n[main] ✓ 审查报告(MD)已保存: ${mdFile}`);

  // 保存结构化 JSON（供 Word 生成使用）
  const jsonFile = path.join(outDir, `contract_review_${ts}.json`);
  fs.writeFileSync(jsonFile, JSON.stringify(structured, null, 2), 'utf8');
  console.error(`[main] ✓ 审查报告(JSON)已保存: ${jsonFile}`);
}

main().catch(err => {
  console.error('[main] 异常:', err.message || err);
  process.exit(1);
});
