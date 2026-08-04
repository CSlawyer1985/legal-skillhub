#!/usr/bin/env node
/**
 * accurLex 法律问答执行脚本
 *
 * 用法: node task_qa_ask.js --prompt <法律问题> [--mode deep|expert] [--history <历史对话>] [--env <.env路径>]
 *
 * 功能:
 *   - 从 .env 读取凭证（手机号 + Bearer Token）
 *   - 如缺少 Token 则自动登录获取
 *   - 调用 /ask_free_stream（深度模式，免费）或 /ask_stream（专家模式，计费）
 *   - 解析 SSE 流（heartbeat / original_content / data / error）
 *   - 合并引用法条与回答正文，输出完整问答
 *   - 支持超长输入自动截断（深度 10000 字 / 专家 30000 字上限）
 */

const fs   = require('fs');
const path = require('path');

/* ── 参数解析 ─────────────────────────────────────────── */
function parseArgs() {
  const args = process.argv.slice(2);
  const opts = { envPath: path.resolve(__dirname, '.env'), mode: 'deep', history: '' };
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--prompt':   opts.prompt   = args[++i]; break;
      case '--mode':     opts.mode     = args[++i]; break;
      case '--history':  opts.history  = args[++i]; break;
      case '--env':      opts.envPath  = args[++i]; break;
      case '--help':
        console.log('用法: node task_qa_ask.js --prompt <法律问题> [--mode deep|expert] [--history <历史对话>] [--env <.env路径>]');
        console.log('  --mode deep    深度模式（默认，免费，上限 1 万字）');
        console.log('  --mode expert  专家模式（计费 5 点/次，上限 3 万字）');
        process.exit(0);
      default:
        console.error(`未知参数: ${args[i]}`);
        process.exit(1);
    }
  }
  if (!opts.prompt) { console.error('缺少 --prompt 参数（法律问题）'); process.exit(1); }
  if (opts.mode !== 'deep' && opts.mode !== 'expert') {
    console.error(`无效的 --mode 值: ${opts.mode}（仅支持 deep 或 expert）`);
    process.exit(1);
  }
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

/**
 * 确保 .env 文件存在且包含基本字段。
 * 如果 .env 不存在，则自动创建带默认值的模板。
 * 返回读取到的 env map。
 */
function ensureEnv(envPath) {
  if (!fs.existsSync(envPath)) {
    console.log('[env] .env 文件不存在，正在自动创建模板 ...');
    const defaultEnv = {
      ACCURLEX_PROXY_BASE_URL: 'https://accurlex.com',
      ACCURLEX_API_BASE_URL: 'https://accurlex.com/index.php',
      ACCURLEX_BILLING_PHONE: '',
      ACCURLEX_BEARER_TOKEN: '',
    };
    writeEnv(envPath, defaultEnv);
    console.error(`[env] ✓ 已创建 .env 模板: ${envPath}`);
    console.error('[env] 请在 .env 中填写 ACCURLEX_BILLING_PHONE 后重试');
    return defaultEnv;
  }
  return readEnv(envPath);
}

/* ── 自动登录 ─────────────────────────────────────────── */
async function autoLogin(env, envPath) {
  const phone = env.ACCURLEX_BILLING_PHONE;
  if (!phone) {
    console.error('[auth] 缺少 ACCURLEX_BILLING_PHONE，请先在 .env 中配置手机号');
    process.exit(1);
  }

  // 从环境变量获取密码
  let pwd = process.env.ACCURLEX_PASSWORD;
  if (!pwd) {
    console.error('[auth] 缺少密码。请设置环境变量 ACCURLEX_PASSWORD 后重试。');
    console.error('[auth] 示例: ACCURLEX_PASSWORD=xxx node task_qa_ask.js ...');
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

/* ── 法律问答（Ask Stream API）───────────────────────── */
async function qaAsk(env, prompt, mode, history) {
  const proxyBase = env.ACCURLEX_PROXY_BASE_URL || 'https://accurlex.com';
  // 深度模式（免费）→ /ask_free_stream ；专家模式（计费）→ /ask_stream
  const route     = mode === 'expert' ? '/ask_stream' : '/ask_free_stream';
  const apiUrl    = `${proxyBase}${route}`;
  const phone     = env.ACCURLEX_BILLING_PHONE;
  const token     = env.ACCURLEX_BEARER_TOKEN;

  if (!phone) {
    console.error('[qa] 缺少凭证 (ACCURLEX_BILLING_PHONE)');
    process.exit(1);
  }

  if (!token) {
    console.error('[qa] 缺少凭证 (ACCURLEX_BEARER_TOKEN)，需要先登录');
    return { error: 'invalid_or_expired_token' };
  }

  // 字符数上限：深度 10000 / 专家 30000
  const MAX_CHARS = mode === 'expert' ? 30000 : 10000;
  const totalChars = prompt.length + history.length;
  if (totalChars > MAX_CHARS) {
    const excess = totalChars - MAX_CHARS;
    // 优先截断历史对话，再截断问题
    if (history.length > excess) {
      history = history.slice(history.length - (history.length - excess));
      console.log(`[qa] ⚠ 历史对话超出上限，已截断 ${excess} 字符`);
    } else {
      let remaining = excess - history.length;
      history = '';
      prompt = prompt.slice(0, prompt.length - remaining);
      console.log(`[qa] ⚠ 输入超出 ${MAX_CHARS} 字符上限，已截断`);
    }
  }

  const payload = JSON.stringify({
    prompt: prompt,
    func_select: 'query_law',
    history: history,
    stream: true,
  });

  const modeLabel = mode === 'expert' ? '专家模式（计费）' : '深度模式（免费）';
  console.log(`[qa] 正在提交法律问答请求 [${modeLabel}] (${prompt.length} 字问题) ...`);

  const res = await fetch(apiUrl, {
    method: 'POST',
    headers: {
      'Content-Type':    'application/json',
      'Authorization':   `Bearer ${token}`,
      'X-Billing-Phone': phone,
      'X-Char-Count':    String(totalChars),
    },
    body: payload,
  });

  // 错误处理
  if (!res.ok) {
    switch (res.status) {
      case 401:
      case 403:
        console.error(`[qa] 认证失败 (${res.status})，Token 可能已过期`);
        return { error: 'invalid_or_expired_token' };
      case 402:
        console.error('[qa] 余额不足，请充值后重试');
        return { error: 'insufficient_balance' };
      case 413:
        console.error('[qa] 输入内容超出字数上限');
        return { error: 'exceed_char_limit' };
      default:
        console.error(`[qa] API 错误: ${res.status}`);
        return { error: `http_${res.status}` };
    }
  }

  // 解析 SSE 流
  const citations = [];   // original_content 引用法条
  const textParts = [];   // data 回答正文
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
        if ('error' in obj) {
          if (obj.error) {
            console.error(`[qa] API 返回错误: ${obj.error}`);
            return { error: 'api_rejected', errorMessage: obj.error };
          }
        } else if (obj.heartbeat) {
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
      if ('error' in obj && obj.error) {
        return { error: 'api_rejected', errorMessage: obj.error };
      } else if (obj.original_content) citations.push(obj.original_content);
      else if (obj.data) textParts.push(obj.data);
    } catch { /* ignore */ }
  }

  const answerText = textParts.join('');

  if (!answerText.trim() && !citations.length) {
    return { error: 'no_result', errorMessage: '未能检索到相关法条或生成回答' };
  }

  return { citations, answerText, mode };
}

/* ── 输出格式化 ───────────────────────────────────────── */

/**
 * 原文输出：回答正文 + 引用法条，不做任何内容改写
 * 仅允许展示形式调整（标题、分隔线、免责声明）
 */
function formatRawOutput(result) {
  if (result.error) {
    if (result.errorMessage) return result.errorMessage;
    return JSON.stringify({ error: result.error });
  }

  let output = '';

  if (result.answerText) {
    output += result.answerText;
  }

  if (result.citations && result.citations.length > 0) {
    output += '\n\n---\n\n### 引用法条\n\n';
    const unique = [...new Set(result.citations)];
    output += unique.join('\n\n');
  }

  output += '\n\n---\n\n> ⚠️ 以上法律分析内容由 AI 辅助生成，仅供参考。重大法律事务请咨询专业律师。\n>\n> 🔗 [accurLex知法](https://accurlex.com) 提供专业AI法律问答服务';

  return output;
}

/**
 * JSON 结构化输出：用于后续处理
 */
function formatStructuredOutput(result) {
  return {
    answerText: result.answerText || '',
    citations: result.citations ? [...new Set(result.citations)] : [],
    mode: result.mode || 'deep',
    error: result.error || null,
    errorMessage: result.errorMessage || null,
  };
}

/* ── 主流程 ───────────────────────────────────────────── */
async function main() {
  const opts = parseArgs();

  // 1. 确保 .env 存在（不存在则自动创建模板）
  let env = ensureEnv(opts.envPath);

  // 2. 检查手机号
  if (!env.ACCURLEX_BILLING_PHONE) {
    console.error('[main] 请先在 .env 中填写 ACCURLEX_BILLING_PHONE（知法注册手机号）');
    console.error(`[main] .env 路径: ${opts.envPath}`);
    process.exit(1);
  }

  // 3. 如果缺少 Token，自动登录获取
  if (!env.ACCURLEX_BEARER_TOKEN) {
    await autoLogin(env, opts.envPath);
    env = readEnv(opts.envPath);
  }

  // 4. 执行法律问答
  let result = await qaAsk(env, opts.prompt, opts.mode, opts.history);

  // 5. Token 过期时自动重试一次
  if (result.error === 'invalid_or_expired_token') {
    console.log('[main] 检测到 Token 过期，正在刷新 ...');
    await autoLogin(env, opts.envPath);
    env = readEnv(opts.envPath);
    result = await qaAsk(env, opts.prompt, opts.mode, opts.history);
  }

  // 6. 输出结果
  if (result.error) {
    console.error(`[main] 法律问答失败: ${result.error}`);
    if (result.errorMessage) {
      // 将错误信息也输出到 stdout，供 AI 助手展示
      console.log(result.errorMessage);
    }
    process.exit(1);
  }

  // 6a. 原文 Markdown（内容不做任何改写）
  const rawMarkdown = formatRawOutput(result);

  // 6b. 结构化 JSON
  const structured = formatStructuredOutput(result);

  // 输出到 stdout（供 AI 助手捕获）
  console.log(rawMarkdown);

  // 保存到文件（输出到 skill 目录下的 outputs 子目录）
  const outDir = path.join(__dirname, 'outputs');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);

  // 保存 Markdown 原文
  const mdFile = path.join(outDir, `qa_ask_${ts}.md`);
  fs.writeFileSync(mdFile, rawMarkdown, 'utf8');
  console.error(`\n[main] ✓ 问答(MD)已保存: ${mdFile}`);

  // 保存结构化 JSON
  const jsonFile = path.join(outDir, `qa_ask_${ts}.json`);
  fs.writeFileSync(jsonFile, JSON.stringify(structured, null, 2), 'utf8');
  console.error(`[main] ✓ 问答(JSON)已保存: ${jsonFile}`);
}

main().catch(err => {
  console.error('[main] 异常:', err.message || err);
  process.exit(1);
});
