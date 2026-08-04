#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const TOKEN = process.env.TELEGRAM_BOT_TOKEN || '';
const API = TOKEN ? `https://api.telegram.org/bot${TOKEN}` : '';
const POLL_MS = Number(process.env.TELEGRAM_POLL_INTERVAL_MS || 3000);
const WORKSPACE = process.cwd();
const OUTPUT_DIR = process.env.PLAN_B_OUTPUT_DIR || path.join(WORKSPACE, 'plan-b', 'output');
const TEMPLATE_DOCX = process.env.PLAN_B_TEMPLATE_DOCX || path.join(WORKSPACE, 'plan-b', 'originals', 'talent_individual_original.docx');
const STATE_FILE = path.join(WORKSPACE, '.state', 'telegram-planb-bot.json');
const MANAGEMENT_CHAT_ID = String(process.env.TELEGRAM_MANAGEMENT_CHAT_ID || '');
const CONTRACT_CHAT_ID = String(process.env.TELEGRAM_CONTRACT_CHAT_ID || '');
const PLAN_C_TMP_DIR = path.join(WORKSPACE, '.state', 'plan-c');
const PLAN_C_MODE = 'eid';

function ensureDir(dir) { fs.mkdirSync(dir, { recursive: true }); }
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
function loadState() {
  try { return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8')); }
  catch { return { offset: 0, sessions: {} }; }
}
function saveState(s) { ensureDir(path.dirname(STATE_FILE)); fs.writeFileSync(STATE_FILE, JSON.stringify(s, null, 2)); }

async function tg(method, payload) {
  const res = await fetch(`${API}/${method}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload || {}),
  });
  const json = await res.json();
  if (!json.ok) throw new Error(`${method} failed: ${JSON.stringify(json)}`);
  return json.result;
}

async function sendMessage(chatId, text, replyToMessageId) {
  return tg('sendMessage', { chat_id: chatId, text, reply_to_message_id: replyToMessageId });
}

async function sendDocument(chatId, filePath, caption, replyToMessageId) {
  const form = new FormData();
  form.append('chat_id', String(chatId));
  if (caption) form.append('caption', caption);
  if (replyToMessageId) form.append('reply_to_message_id', String(replyToMessageId));
  form.append('document', new Blob([fs.readFileSync(filePath)]), path.basename(filePath));
  const res = await fetch(`${API}/sendDocument`, { method: 'POST', body: form });
  const json = await res.json();
  if (!json.ok) throw new Error(`sendDocument failed: ${JSON.stringify(json)}`);
  return json.result;
}

async function getFile(fileId) {
  return tg('getFile', { file_id: fileId });
}

async function downloadTelegramFile(fileId, destPath) {
  const info = await getFile(fileId);
  const res = await fetch(`https://api.telegram.org/file/bot${TOKEN}/${info.file_path}`);
  if (!res.ok) throw new Error(`download file failed: ${res.status}`);
  const buf = Buffer.from(await res.arrayBuffer());
  ensureDir(path.dirname(destPath));
  fs.writeFileSync(destPath, buf);
  return destPath;
}

function looksLikeContractInput(text) {
  const mustHave = ['TEN:', 'NGAY_SINH:', 'CCCD:', 'DU_AN:', 'CONG_VIEC:', 'SO_TIEN:'];
  const upper = String(text || '').toUpperCase();
  return mustHave.every(k => upper.includes(k));
}

function runCommand(cmd, args) {
  return execFileSync(cmd, args, { cwd: WORKSPACE, encoding: 'utf8' });
}

function sessionKey(chatId, userId) {
  return `${chatId}:${userId}`;
}

function getSession(state, chatId, userId) {
  return state.sessions?.[sessionKey(chatId, userId)] || null;
}

function setSession(state, chatId, userId, session) {
  state.sessions = state.sessions || {};
  state.sessions[sessionKey(chatId, userId)] = session;
}

function clearSession(state, chatId, userId) {
  if (state.sessions) delete state.sessions[sessionKey(chatId, userId)];
}

function isPhotoMessage(msg) {
  return Array.isArray(msg.photo) && msg.photo.length > 0;
}

function getBestPhotoFileId(msg) {
  if (!isPhotoMessage(msg)) return null;
  const sorted = [...msg.photo].sort((a, b) => (b.file_size || 0) - (a.file_size || 0));
  return sorted[0]?.file_id || null;
}

function runJsonCommand(cmd, args) {
  const out = execFileSync(cmd, args, { cwd: WORKSPACE, encoding: 'utf8' });
  return JSON.parse(out);
}

function buildCccdDraftBlock() {
  return `TEN:
NGAY_SINH:
CCCD:
NGAY_CAP:
NOI_CAP: CTCCS QLHC VTTXH
THUONG_TRU:
CHO_O_HIEN_TAI:
DIEN_THOAI:
EMAIL:
STK:
NGAN_HANG:
DU_AN:
CONG_VIEC:
TU_NGAY:
DEN_NGAY:
SO_TIEN:
SO_TIEN_CHU:
THANH_TOAN:`;
}

function scoreFrontBack(text) {
  const t = String(text || '');
  const squashed = t.replace(/\s+/g, '');
  let front = 0;
  let back = 0;

  // Front-side indicators user explicitly confirmed
  if (/Số\/?No\.?|So\/?No\.?|\bNo\.?\b/i.test(t)) front += 2;
  if (/Họ và tên|Ho va ten|Full name/i.test(t)) front += 4;
  if (/Ngày sinh|Ngay sinh|Date of birth/i.test(t)) front += 4;
  if (/Quê quán|Que quan|Place of origin/i.test(t)) front += 3;
  if (/Nơi thường trú|Noi thuong tru|Place of residence/i.test(t)) front += 3;
  if (/Có giá trị đến|Co gia tri den|Date of expiry/i.test(t)) front += 4;
  if (/\b\d{2}\/\d{2}\/\d{2,4}\b/.test(t)) front += 1;
  if (/\b\d{12}\b/.test(squashed)) front += 4;
  if (/^[A-ZÀ-ỸĐ\s]{6,40}$/m.test(t)) front += 1; // uppercase full-name style line

  // Ignore sex/nationality as extraction targets, but presence still hints front layout slightly
  if (/Giới tính|Gioi tinh|Sex|Quốc tịch|Quoc tich|Nationality/i.test(t)) front += 1;

  // Back-side indicators
  if (/Nơi cấp|Noi cap|Place of issue/i.test(t)) back += 4;
  if (/Ngày cấp|Ngay cap|Date of issue/i.test(t)) back += 4;
  if (/Đặc điểm nhận dạng|Dac diem nhan dang|Personal identification/i.test(t)) back += 3;
  if (/IDVNM|<</i.test(t)) back += 5;
  if (/MRZ/i.test(t)) back += 2;

  return { front, back };
}

async function runSingleOcr(imagePath) {
  const jsonPath = `${imagePath}.ocr.json`;
  fs.writeFileSync(jsonPath, execFileSync('swift', ['plan-c-ocr.swift', imagePath], { cwd: WORKSPACE, encoding: 'utf8' }));
  const data = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
  return { data, jsonPath };
}

function buildOcrDebugText(ocrData) {
  const lines = (ocrData.lines || []).map((x, i) => `${i + 1}. ${x.text} [${Number(x.confidence || 0).toFixed(2)}]`);
  const joined = lines.join('\n');
  return joined.length > 3500 ? joined.slice(0, 3500) + '\n...[truncated]' : joined;
}

async function runEidOcr(imagePath) {
  const result = await runSingleOcr(imagePath);
  const parsed = runJsonCommand('node', ['plan-c-eid-parse.js', result.jsonPath]);
  return { parsed, rawOcr: result.data, artifacts: [result.jsonPath] };
}

async function handleContractFlow(msg, state) {
  const chatId = msg.chat.id;
  const userId = msg.from?.id;
  const text = (msg.text || '').trim();
  const messageId = msg.message_id;
  const normalizedCommand = text.split(/\s+/)[0].split('@')[0];
  const session = getSession(state, chatId, userId);

  if (normalizedCommand === '/cancel') {
    clearSession(state, chatId, userId);
    saveState(state);
    await sendMessage(chatId, 'Đã hủy phiên hiện tại.', messageId);
    return;
  }

  if (normalizedCommand === '/status') {
    if (!session) {
      await sendMessage(chatId, 'Hiện không có session nào đang chạy.', messageId);
      return;
    }
    await sendMessage(chatId, `Trạng thái hiện tại: ${session.state}`, messageId);
    return;
  }

  if (normalizedCommand === '/mauhopdong') {
    const template = fs.readFileSync(path.join(WORKSPACE, 'plan-b-telegram-template.txt'), 'utf8');
    await sendMessage(chatId, template, messageId);
    return;
  }

  if (normalizedCommand === '/cccd' || normalizedCommand === '/cccd_debug') {
    setSession(state, chatId, userId, {
      state: 'WAITING_EID_IMAGE',
      startedAt: new Date().toISOString(),
      eidReceived: false,
      debugOcr: normalizedCommand === '/cccd_debug',
    });
    saveState(state);
    await sendMessage(chatId,
`Bắt đầu quy trình đọc CCCD điện tử.

Hãy gửi 1 ảnh chụp màn hình CCCD điện tử rõ nét từ app.

Sau khi nhận ảnh, mình sẽ OCR và trả block thông tin để bạn xác nhận trước khi tạo hợp đồng.${normalizedCommand === '/cccd_debug' ? '\n\nChế độ debug đang bật: mình sẽ trả thêm raw OCR text.' : ''}`,
    messageId);
    return;
  }

  if (session && session.state === 'WAITING_EID_IMAGE') {
    if (!isPhotoMessage(msg)) {
      await sendMessage(chatId, 'Hiện tại mình đang chờ 1 ảnh chụp màn hình CCCD điện tử từ app.', messageId);
      return;
    }

    const fileId = getBestPhotoFileId(msg);
    if (!fileId) {
      await sendMessage(chatId, 'Mình không lấy được file ảnh từ Telegram. Hãy thử gửi lại ảnh.', messageId);
      return;
    }

    const eidPath = path.join(PLAN_C_TMP_DIR, `${chatId}_${userId}_eid_${Date.now()}.jpg`);
    await downloadTelegramFile(fileId, eidPath);
    session.state = 'OCR_PROCESSING';
    session.eidReceived = true;
    session.eidPath = eidPath;
    setSession(state, chatId, userId, session);
    saveState(state);
    await sendMessage(chatId, 'Đã nhận ảnh CCCD điện tử. Mình đang đọc thông tin...', messageId);

    try {
      const { parsed, rawOcr } = await runEidOcr(session.eidPath);
      session.state = 'WAITING_USER_CONFIRMATION';
      session.ocrResult = parsed.fields;
      setSession(state, chatId, userId, session);
      saveState(state);
      const block = parsed.block || buildCccdDraftBlock();
      await sendMessage(chatId,
`Mình đã bóc được thông tin từ ảnh CCCD điện tử. Hãy kiểm tra, bổ sung các trường còn thiếu, rồi gửi lại nguyên block này để mình tạo hợp đồng:\n\n${block}`,
      messageId);
      if (session.debugOcr) {
        await sendMessage(chatId, `OCR RAW DEBUG:\n${buildOcrDebugText(rawOcr)}`, messageId);
      }
    } catch (err) {
      session.state = 'ERROR';
      session.lastError = String(err.message || err);
      setSession(state, chatId, userId, session);
      saveState(state);
      await sendMessage(chatId, 'Mình chưa OCR được rõ từ ảnh CCCD điện tử. Hãy thử gửi lại ảnh rõ hơn.', messageId);
    }
    return;
  }

  if (session && session.state === 'WAITING_USER_CONFIRMATION') {
    if (!looksLikeContractInput(text)) {
      await sendMessage(chatId, 'Mình đang chờ block xác nhận thông tin hợp đồng theo mẫu. Nếu muốn hủy, gửi /cancel.', messageId);
      return;
    }

    const tempInput = path.join(OUTPUT_DIR, `.telegram-input-${Date.now()}.txt`);
    fs.writeFileSync(tempInput, text, 'utf8');
    try {
      const raw = runCommand('node', ['plan-b-telegram-to-docx.js', tempInput, OUTPUT_DIR, TEMPLATE_DOCX]);
      const result = JSON.parse(raw);
      clearSession(state, chatId, userId);
      saveState(state);
      await sendDocument(chatId, path.resolve(WORKSPACE, result.generated), 'Đã tạo hợp đồng .docx xong.', messageId);
    } catch (err) {
      const output = String(err.stdout || '') || String(err.message || err);
      await sendMessage(chatId, `Không tạo được hợp đồng. Chi tiết:\n${output.slice(0, 3000)}`, messageId);
    } finally {
      try { fs.unlinkSync(tempInput); } catch {}
    }
    return;
  }

  if (!looksLikeContractInput(text)) {
    await sendMessage(chatId, 'Mình chưa nhận ra đây là block input hợp đồng. Gửi /mauhopdong để lấy mẫu chuẩn hoặc /cccd để bắt đầu luồng CCCD.', messageId);
    return;
  }

  const tempInput = path.join(OUTPUT_DIR, `.telegram-input-${Date.now()}.txt`);
  fs.writeFileSync(tempInput, text, 'utf8');
  try {
    const raw = runCommand('node', ['plan-b-telegram-to-docx.js', tempInput, OUTPUT_DIR, TEMPLATE_DOCX]);
    const result = JSON.parse(raw);
    await sendDocument(chatId, path.resolve(WORKSPACE, result.generated), 'Đã tạo hợp đồng .docx xong.', messageId);
  } catch (err) {
    const output = String(err.stdout || '') || String(err.message || err);
    await sendMessage(chatId, `Không tạo được hợp đồng. Chi tiết:\n${output.slice(0, 3000)}`, messageId);
  } finally {
    try { fs.unlinkSync(tempInput); } catch {}
  }
}

async function handleMessage(msg, state) {
  const chatId = msg.chat.id;
  const chatIdStr = String(chatId);
  const text = (msg.text || '').trim();
  const messageId = msg.message_id;
  const chatTitle = msg.chat.title || msg.chat.username || msg.chat.first_name || 'unknown';
  const normalizedCommand = text.split(/\s+/)[0].split('@')[0];
  const isManagement = MANAGEMENT_CHAT_ID && chatIdStr === MANAGEMENT_CHAT_ID;
  const isContract = CONTRACT_CHAT_ID && chatIdStr === CONTRACT_CHAT_ID;

  if (normalizedCommand === '/start') {
    let intro = 'FlexClawBot đã sẵn sàng.';
    if (isManagement) intro += '\n\nGroup này được map cho Plan A (management/employee reminders).';
    else if (isContract) intro += '\n\nGroup này được map cho Plan B/Plan C (hợp đồng + CCCD).';
    intro += '\n\nLệnh hỗ trợ:\n/id - xem chat_id hiện tại';
    if (isContract) intro += '\n/mauhopdong - lấy mẫu input hợp đồng\n/cccd - bắt đầu luồng CCCD\n/cccd_debug - OCR + trả raw debug text\n/status - xem trạng thái hiện tại\n/cancel - hủy phiên';
    await sendMessage(chatId, intro, messageId);
    return;
  }

  if (normalizedCommand === '/id') {
    await sendMessage(chatId, `chat_id: ${chatId}\ntitle: ${chatTitle}\ntype: ${msg.chat.type}`, messageId);
    return;
  }

  if (isManagement) {
    if (normalizedCommand === '/mauhopdong' || normalizedCommand === '/cccd') {
      await sendMessage(chatId, 'Group này dành cho Plan A (management). Chức năng hợp đồng/CCCD chỉ dùng ở group automatic contract.', messageId);
      return;
    }
    await sendMessage(chatId, 'Group này đã được map cho Plan A. Hiện group này dùng để nhận báo cáo management/employee.', messageId);
    return;
  }

  if (isContract) {
    await handleContractFlow(msg, state);
    return;
  }

  await sendMessage(chatId, 'Chat này chưa được map chức năng. Hiện bot chỉ hỗ trợ 2 group nội bộ đã cấu hình.', messageId);
}

async function main() {
  if (!TOKEN) throw new Error('Thiếu TELEGRAM_BOT_TOKEN');
  ensureDir(OUTPUT_DIR);
  const state = loadState();
  while (true) {
    try {
      const updates = await tg('getUpdates', { offset: state.offset + 1, timeout: 20 });
      for (const u of updates) {
        state.offset = u.update_id;
        if (u.message && (u.message.text || isPhotoMessage(u.message))) {
          await handleMessage(u.message, state);
        }
      }
      saveState(state);
    } catch (err) {
      console.error(err.message || err);
      await sleep(POLL_MS);
    }
  }
}

main().catch(err => {
  console.error(err.message || err);
  process.exit(1);
});
