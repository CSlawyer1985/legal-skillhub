#!/usr/bin/env node
/**
 * 专利 SSE 流生成 + 解析一体化脚本
 *
 * 用法:
 *   node assemble.js <documentId> [输出md文件] [输出模式]
 *
 * 输出模式: file (写文件，默认) | stdout (输出到标准输出)
 *
 * 流程:
 *   1. 自动生成 chatId
 *   2. 调用 curl.exe 请求 SSE 流（子进程，绕开 PowerShell 管道编码问题）
 *   3. 实时解析 SSE：progress/error → stdout（带百分比），message.delta → 拼接全文
 *   4. 结束后根据输出模式写入文件或输出到 stdout
 *
 * 进度输出到 stdout 而非 stderr，避免 PowerShell 将 stderr 当作错误流。
 */
const { spawn } = require("child_process");
const fs = require("fs");
const readline = require("readline");

const API_BASE = "https://www.cndeeptest.com/patent_draft/api";

const documentId = process.argv[2];
const outPath = process.argv[3];
const outputMode = process.argv[4] || "file"; // "file" 或 "stdout"

if (!documentId) {
  console.error("用法: node assemble.js <documentId> [输出md文件] [输出模式]");
  console.error("  输出模式: file (写文件，默认) | stdout (输出到标准输出)");
  process.exit(1);
}

if (outputMode === "file" && !outPath) {
  console.error("错误: 输出模式为 file 时必须指定输出文件路径");
  process.exit(1);
}

const chatId = "patent-" + Date.now();
const body = JSON.stringify({ chatId, documentFileId: documentId });

// 调用 curl.exe，绕开 PowerShell 管道编码问题
const curl = spawn("curl.exe", [
  "-sN",
  "-X", "POST",
  `${API_BASE}/patent/generate`,
  "-H", "Content-Type: application/json",
  "-d", body,
  "--max-time", "900",
], {
  stdio: ["ignore", "pipe", "pipe"],
});

let event = null;
let dataLines = [];
const full = [];

// 百分比进度映射：step → 预估完成百分比（与进度汇报规则保持一致）
const STEP_PERCENT = {
  STEP_1: 5,           // 校验交底材料中
  STEP_1_PASS: 8,     // 校验合格，开始生成
  STEP_1_FAIL: 8,     // 校验不合格，终止流程
  STEP_2: 15,         // 生成初稿中
  STEP_2_DONE: 50,    // 初稿已完成
  STEP_3: 55,         // 质检进行中
  STEP_3_DONE: 70,    // 质检完成
  STEP_4: 75,         // 修复终稿中
  COMPLETE: 100,      // 全部完成
};

function dispatch() {
  if (dataLines.length === 0) { event = null; dataLines = []; return; }
  const raw = dataLines.join("\n");
  if (event === "message") {
    try { full.push(JSON.parse(raw).delta || ""); } catch {}
  } else if (event === "progress") {
    try {
      const d = JSON.parse(raw);
      const pct = STEP_PERCENT[d.step];
      if (pct !== undefined) {
        console.log("[进度 %d%%] %s: %s", pct, d.step, d.message);
      } else {
        console.log("[进度] %s: %s", d.step, d.message);
      }
    } catch {}
  } else if (event === "error") {
    try { const d = JSON.parse(raw); console.log("[错误] %s: %s", d.step, d.message); } catch {}
  }
  event = null;
  dataLines = [];
}

function processLine(line) {
  if (line === "") { dispatch(); return; }
  if (line.startsWith("event:")) event = line.slice("event:".length).trim();
  else if (line.startsWith("data:")) dataLines.push(line.slice("data:".length).replace(/^ /, ""));
}

function finish() {
  dispatch();
  const text = full.join("");

  if (outputMode === "stdout") {
    // 输出到 stdout（JSON 格式，不含进度消息）
    console.log(JSON.stringify({ content: text, charCount: text.length }));
  } else {
    // 写入文件（原行为）
    fs.writeFileSync(outPath, text, "utf8");
    console.log("[完成] 已写入 %s，共 %d 字", outPath, text.length);
  }
}

// 实时逐行解析 curl 的 stdout
const rl = readline.createInterface({ input: curl.stdout });
rl.on("line", processLine);
rl.on("close", finish);

// curl stderr 只保留网络错误等，转发到 stderr（不影响进度显示）
curl.stderr.on("data", (d) => process.stderr.write(d));

curl.on("close", (code) => {
  if (code !== 0) {
    console.log("[警告] curl 退出码: %d", code);
  }
});
