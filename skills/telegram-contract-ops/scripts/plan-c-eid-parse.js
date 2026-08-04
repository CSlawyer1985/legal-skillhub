#!/usr/bin/env node

const fs = require('fs');

function clean(s) {
  return String(s || '')
    .replace(/\u00a0/g, ' ')
    .replace(/[ \t]+/g, ' ')
    .trim();
}

function linesFromText(text) {
  return String(text || '')
    .split(/\r?\n/)
    .map(clean)
    .filter(Boolean);
}

function isJunkValue(value, labels = []) {
  const v = clean(value);
  if (!v) return true;
  if (v === ':' || v === '：') return true;
  if (/^[::\-\s]+$/.test(v)) return true;
  if (labels.some(l => new RegExp('^' + l + '$', 'i').test(v))) return true;
  return false;
}

function getValueAfterLabel(text, labels) {
  for (const label of labels) {
    const re = new RegExp(label + '\\s*:?\\s*(.+)', 'i');
    const m = text.match(re);
    if (m && m[1]) {
      const val = clean(m[1]);
      if (!isJunkValue(val, labels)) return val;
    }
  }
  return '';
}

function nextUsefulValue(lines, startIndex, labels) {
  for (let j = startIndex + 1; j < Math.min(lines.length, startIndex + 4); j++) {
    const candidate = clean(lines[j]);
    if (!isJunkValue(candidate, labels)) return candidate;
  }
  return '';
}

function isLikelyLabel(line) {
  return /Họ và tên|Ho va ten|Full name|Ngày sinh|Ngay sinh|Date of birth|Số định danh cá nhân|Personal Identification number|Nơi thường trú|Noi thuong tru|Place of residence|Nơi ở hiện tại|Noi o hien tai|Current address|Ngày cấp|Ngay cap|Date of issue|Quê quán|Que quan|Place of origin|Giới tính|Gioi tinh|Sex|Quốc tịch|Quoc tich|Nationality/i.test(line);
}

function collectValueBlock(lines, startIndex, labels, maxLines = 3) {
  const parts = [];
  for (let j = startIndex + 1; j < Math.min(lines.length, startIndex + 1 + maxLines); j++) {
    const candidate = clean(lines[j]);
    if (!candidate) continue;
    if (isJunkValue(candidate, labels)) continue;
    if (isLikelyLabel(candidate)) break;
    parts.push(candidate);
  }
  return clean(parts.join(' '));
}

function getField(lines, labels) {
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const direct = getValueAfterLabel(line, labels);
    if (direct) return direct;
    if (labels.some(l => new RegExp('^' + l + '$', 'i').test(line))) {
      const next = nextUsefulValue(lines, i, labels);
      if (next) return next;
    }
  }
  return '';
}

function getFieldBlock(lines, labels, maxLines = 3) {
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const direct = getValueAfterLabel(line, labels);
    if (direct && !isLikelyLabel(direct)) return direct;
    if (labels.some(l => new RegExp('^' + l + '$', 'i').test(line) || new RegExp(l, 'i').test(line))) {
      const block = collectValueBlock(lines, i, labels, maxLines);
      if (block) return block;
    }
  }
  return '';
}

function pickLikelyNameLine(lines) {
  const blacklist = [
    /CỘNG HÒA|Độc lập|Căn cước|Số định danh|Personal Identification|Ngày sinh|Date of birth|Quê quán|Place of origin|Nơi thường trú|Place of residence|Nơi ở hiện tại|Current address|Ngày cấp|Date of issue|Giới tính|Nationality|Quốc tịch/i
  ];
  for (const line of lines) {
    if (blacklist.some(re => re.test(line))) continue;
    const upper = line.toUpperCase();
    if (/^[A-ZÀ-ỸĐ\s]{6,60}$/.test(upper) && upper.split(/\s+/).length >= 2) {
      return clean(line);
    }
  }
  return '';
}

function isAddressLike(line) {
  const s = clean(line);
  if (!s) return false;
  if (isLikelyLabel(s)) return false;
  return /(Ấp|Ap|Xã|Xa|Phường|Phuong|Quận|Quan|Huyện|Huyen|Tỉnh|Tinh|Thành phố|Thanh pho|Thị trấn|Thi tran|KP|Khu phố|Đường|Duong|P\.|Q\.)/i.test(s);
}

function pickAddressAfterLabel(lines, labels) {
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (labels.some(l => new RegExp(l, 'i').test(line))) {
      const parts = [];
      for (let j = i + 1; j < Math.min(lines.length, i + 5); j++) {
        const candidate = clean(lines[j]);
        if (!candidate) continue;
        if (isLikelyLabel(candidate)) break;
        if (isAddressLike(candidate) || parts.length > 0) parts.push(candidate);
      }
      const merged = clean(parts.join(' '));
      if (merged) return merged;
    }
  }
  return '';
}

function findDateNear(lines, labels) {
  const dateRe = /(\d{2}\/\d{2}\/\d{2,4})/;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (labels.some(l => new RegExp(l, 'i').test(line))) {
      const same = line.match(dateRe);
      if (same) return same[1];
      for (let j = i + 1; j < Math.min(lines.length, i + 4); j++) {
        const next = (lines[j] || '').match(dateRe);
        if (next) return next[1];
      }
    }
  }
  return '';
}

function findCccd(lines) {
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (/Số định danh cá nhân|Personal Identification number|\bSố\/?No\b|\bNo\b/i.test(line)) {
      const direct = line.replace(/\s+/g, '').match(/(\d{12})/);
      if (direct) return direct[1];
      for (let j = i + 1; j < Math.min(lines.length, i + 4); j++) {
        const candidate = lines[j].replace(/\s+/g, '').match(/(\d{12})/);
        if (candidate) return candidate[1];
      }
    }
  }
  for (const line of lines) {
    const squashed = line.replace(/\s+/g, '');
    const m = squashed.match(/(\d{12})/);
    if (m) return m[1];
  }
  return '';
}

function toBlock(fields) {
  return [
    `TEN: ${fields.TEN || ''}`,
    `NGAY_SINH: ${fields.NGAY_SINH || ''}`,
    `CCCD: ${fields.CCCD || ''}`,
    `NGAY_CAP: ${fields.NGAY_CAP || ''}`,
    `NOI_CAP: CTCCS QLHC VTTXH`,
    `THUONG_TRU: ${fields.THUONG_TRU || ''}`,
    `CHO_O_HIEN_TAI: ${fields.CHO_O_HIEN_TAI || ''}`,
    'DIEN_THOAI: ',
    'EMAIL: ',
    'STK: ',
    'NGAN_HANG: ',
    'DU_AN: ',
    'CONG_VIEC: ',
    'TU_NGAY: ',
    'DEN_NGAY: ',
    'SO_TIEN: ',
    'SO_TIEN_CHU: ',
    'THANH_TOAN: '
  ].join('\n');
}

function cleanAddressTail(value) {
  return clean(String(value || '')
    .replace(/\s+(Nơi tạm trú|Noi tam tru|Nơi ở hiện tại|Noi o hien tai|Current address|Đặc điểm nhân dạng|Dac diem nhan dang|Đặc điểm nhận dạng|Ngày cấp|Ngay cap|Date of issue|Nơi cấp|Noi cap).*$/i, '')
    .replace(/\s+/g, ' ')
    .trim());
}

function parseEid(text) {
  const lines = linesFromText(text)
    .filter(line => !/CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM|Độc lập - Tự do - Hạnh phúc/i.test(line));

  let TEN = getFieldBlock(lines, ['Họ và tên', 'Ho va ten', 'Full name'], 2) || getField(lines, ['Họ và tên', 'Ho va ten', 'Full name']);
  if (!TEN) TEN = pickLikelyNameLine(lines);
  if (TEN) TEN = TEN.toUpperCase();

  const NGAY_SINH = findDateNear(lines, ['Ngày sinh', 'Ngay sinh', 'Date of birth']);
  const CCCD = findCccd(lines);
  let THUONG_TRU = getFieldBlock(lines, ['Nơi thường trú', 'Noi thuong tru', 'Place of residence'], 4) || getField(lines, ['Nơi thường trú', 'Noi thuong tru', 'Place of residence']);
  if (!THUONG_TRU) THUONG_TRU = pickAddressAfterLabel(lines, ['Nơi thường trú', 'Noi thuong tru', 'Place of residence']);
  THUONG_TRU = cleanAddressTail(THUONG_TRU);

  let CHO_O_HIEN_TAI = getFieldBlock(lines, ['Nơi ở hiện tại', 'Noi o hien tai', 'Current address'], 4) || getField(lines, ['Nơi ở hiện tại', 'Noi o hien tai', 'Current address']);
  if (!CHO_O_HIEN_TAI) CHO_O_HIEN_TAI = pickAddressAfterLabel(lines, ['Nơi ở hiện tại', 'Noi o hien tai', 'Current address']);
  CHO_O_HIEN_TAI = cleanAddressTail(CHO_O_HIEN_TAI);

  const NGAY_CAP = findDateNear(lines, ['Ngày cấp', 'Ngay cap', 'Ngày cấp Căn cước công dân gần nhất', 'Date of issue']);

  return { TEN, NGAY_SINH, CCCD, NGAY_CAP, THUONG_TRU, CHO_O_HIEN_TAI };
}

function main() {
  const input = process.argv[2];
  if (!input) {
    console.error('Usage: node plan-c-eid-parse.js <ocr-json-file>');
    process.exit(1);
  }
  const data = JSON.parse(fs.readFileSync(input, 'utf8'));
  const text = data.joinedText || (data.lines || []).map(x => x.text).join('\n');
  const fields = parseEid(text);
  console.log(JSON.stringify({ ok: true, version: 'eid-v1', fields, block: toBlock(fields), sourceText: text }, null, 2));
}

main();
