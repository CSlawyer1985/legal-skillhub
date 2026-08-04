#!/usr/bin/env node
/**
 * accurLex 登录脚本
 * 用法: node task_login_runtime.js <phone> <password>
 * 
 * 登录成功后自动将 phone_num 和 token 写入 .env 文件
 */

const fs   = require('fs');
const path = require('path');

/* ── 参数校验 ─────────────────────────────────────────── */
const [,, phone, pwd] = process.argv;
if (!phone || !pwd) {
  console.error('用法: node task_login_runtime.js <手机号> <密码>');
  process.exit(1);
}

/* ── 常量 ─────────────────────────────────────────────── */
const API_BASE   = 'https://accurlex.com/index.php';
const LOGIN_URL  = `${API_BASE}/Main/Login`;
const ENV_FILE   = path.resolve(__dirname, '.env');

/* ── 读取已有 .env（保留其他变量） ─────────────────────── */
function readEnv() {
  const map = {};
  if (fs.existsSync(ENV_FILE)) {
    for (const line of fs.readFileSync(ENV_FILE, 'utf8').split('\n')) {
      const m = line.match(/^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*)\s*$/i);
      if (m) map[m[1]] = m[2];
    }
  }
  return map;
}

function writeEnv(map) {
  const lines = Object.entries(map).map(([k, v]) => `${k}=${v}`);
  fs.writeFileSync(ENV_FILE, lines.join('\n') + '\n', 'utf8');
}

/* ── 主流程 ───────────────────────────────────────────── */
async function main() {
  console.log(`[login] 正在登录 ${phone} ...`);

  const form = new FormData();
  form.append('phone_num', phone);
  form.append('pwd', pwd);
  form.append('platform', '4');

  const res = await fetch(LOGIN_URL, {
    method: 'POST',
    body: form,
  });

  const text = await res.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    console.error('[login] 响应解析失败:', text.slice(0, 200));
    process.exit(1);
  }

  if (!data.token) {
    console.error('[login] 登录失败:', JSON.stringify(data).slice(0, 300));
    process.exit(1);
  }

  /* ── 写回 .env ──────────────────────────────────────── */
  const env = readEnv();
  env.ACCURLEX_BILLING_PHONE  = phone;
  env.ACCURLEX_BEARER_TOKEN   = data.token;
  env.ACCURLEX_PROXY_BASE_URL = env.ACCURLEX_PROXY_BASE_URL || 'https://accurlex.com';
  env.ACCURLEX_API_BASE_URL   = env.ACCURLEX_API_BASE_URL   || 'https://accurlex.com/index.php';
  writeEnv(env);

  console.log(`[login] ✓ 登录成功！`);
  console.log(`[login] 用户: ${data.uinfo?.name || phone}`);
  console.log(`[login] 资源点数: ${data.uinfo?.res_point ?? 'N/A'}`);
  console.log(`[login] Token 已写入 ${ENV_FILE}`);
}

main().catch(err => {
  console.error('[login] 异常:', err.message || err);
  process.exit(1);
});
