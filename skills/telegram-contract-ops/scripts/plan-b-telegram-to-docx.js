#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const REQUIRED_KEYS = [
  'TEN', 'NGAY_SINH', 'CCCD', 'NGAY_CAP', 'NOI_CAP', 'THUONG_TRU', 'CHO_O_HIEN_TAI',
  'DIEN_THOAI', 'EMAIL', 'STK', 'NGAN_HANG', 'DU_AN', 'CONG_VIEC', 'TU_NGAY',
  'DEN_NGAY', 'SO_TIEN', 'SO_TIEN_CHU', 'THANH_TOAN'
];

const KEY_MAP = {
  TEN: 'party_b_name',
  NGAY_SINH: 'party_b_dob',
  CCCD: 'party_b_id_number',
  NGAY_CAP: 'party_b_id_issue_date',
  NOI_CAP: 'party_b_id_issue_place',
  THUONG_TRU: 'party_b_permanent_address',
  CHO_O_HIEN_TAI: 'party_b_current_address',
  DIEN_THOAI: 'party_b_phone',
  EMAIL: 'party_b_email',
  STK: 'party_b_bank_account',
  NGAN_HANG: 'party_b_bank_name',
  DU_AN: 'project_name',
  CONG_VIEC: 'job_title',
  TU_NGAY: 'start_date',
  DEN_NGAY: 'end_date',
  SO_TIEN: 'service_fee',
  SO_TIEN_CHU: 'service_fee_text',
  THANH_TOAN: 'payment_terms',
};

const DEFAULTS = {
  contract_title: 'HỢP ĐỒNG KHOÁN VIỆC',
  sign_city: 'Thành phố Hồ Chí Minh',
  payment_method: 'Chuyển khoản',
  tax_note: 'chưa bao gồm tiền thuế thu nhập cá nhân',
  usage_territory: 'Việt Nam',
  usage_term: '1 năm không độc quyền kể từ ngày phát hành đầu tiên',
  usage_purpose: 'Sử dụng hình ảnh và video trên các nền tảng truyền thông kỹ thuật số của dự án trong phạm vi đã được phê duyệt.',
  party_a_company_name: 'CÔNG TY TNHH FLEX FILMS',
  party_a_address: 'Số 79 Đường 30, Phường Tân Hưng, Thành phố Hồ Chí Minh',
  party_a_tax_code: '0315637917',
  party_a_legal_representative: 'NGUYỄN ANH TÚ',
  party_a_representative_pronoun: 'Ông',
  party_a_title: 'Tổng Giám Đốc',
  party_a_sign_name: 'NGUYỄN ANH TÚ',
};

function parseDate(s) {
  const m = String(s || '').trim().match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (!m) return null;
  const [_, dd, mm, yyyy] = m;
  const dt = new Date(Number(yyyy), Number(mm) - 1, Number(dd));
  if (dt.getFullYear() !== Number(yyyy) || dt.getMonth() !== Number(mm) - 1 || dt.getDate() !== Number(dd)) return null;
  return dt;
}

function daysBetween(a, b) {
  const ua = Date.UTC(a.getFullYear(), a.getMonth(), a.getDate());
  const ub = Date.UTC(b.getFullYear(), b.getMonth(), b.getDate());
  return Math.round((ub - ua) / 86400000);
}

function slugify(input) {
  return String(input || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd').replace(/Đ/g, 'D')
    .replace(/[^a-zA-Z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .toUpperCase();
}

function buildContractNo(data, now) {
  const dd = String(now.getDate()).padStart(2, '0');
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const yy = String(now.getFullYear()).slice(-2);
  return `HĐKV-${dd}${mm}${yy}-FF-${slugify(data.TEN)}`;
}

function parseTemplateInput(text) {
  const lines = String(text || '').split(/\r?\n/);
  const parsed = {};
  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;
    const idx = line.indexOf(':');
    if (idx === -1) continue;
    const key = line.slice(0, idx).trim().toUpperCase();
    const value = line.slice(idx + 1).trim();
    if (REQUIRED_KEYS.includes(key)) parsed[key] = value;
  }
  return parsed;
}

function validate(parsed) {
  const missingFields = REQUIRED_KEYS.filter((k) => !parsed[k]);
  const invalidFields = [];
  for (const field of ['NGAY_SINH', 'NGAY_CAP', 'TU_NGAY', 'DEN_NGAY']) {
    if (parsed[field] && !parseDate(parsed[field])) invalidFields.push({ field, reason: 'invalid_date_format' });
  }
  if (parsed.EMAIL && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(parsed.EMAIL)) invalidFields.push({ field: 'EMAIL', reason: 'invalid_email' });
  if (parsed.TU_NGAY && parsed.DEN_NGAY) {
    const s = parseDate(parsed.TU_NGAY);
    const e = parseDate(parsed.DEN_NGAY);
    if (s && e && e < s) invalidFields.push({ field: 'DEN_NGAY', reason: 'end_before_start' });
  }
  return { missingFields, invalidFields, ok: missingFields.length === 0 && invalidFields.length === 0 };
}

function mapToPlanB(parsed) {
  const now = new Date();
  const start = parseDate(parsed.TU_NGAY);
  const end = parseDate(parsed.DEN_NGAY);
  const durationDays = start && end ? String(daysBetween(start, end) + 1) : '';
  const mapped = { ...DEFAULTS };
  for (const [src, dest] of Object.entries(KEY_MAP)) mapped[dest] = parsed[src] || '';
  mapped.contract_no = buildContractNo(parsed, now);
  mapped.sign_day = String(now.getDate()).padStart(2, '0');
  mapped.sign_month = String(now.getMonth() + 1).padStart(2, '0');
  mapped.sign_year = String(now.getFullYear());
  mapped.duration_days = durationDays;
  mapped.party_b_sign_name = parsed.TEN || '';
  mapped.currency = 'VND';
  mapped.party_b_role_category = 'talent_individual';
  mapped.contract_status = 'draft';
  mapped.source_channel = 'telegram';
  mapped.created_by = 'FlexClawBot';
  mapped.created_at = now.toISOString();
  return mapped;
}

function main() {
  const inputPath = process.argv[2] || 'plan-b-telegram-input-sample.txt';
  const outputDir = process.argv[3] || path.join('plan-b', 'output');
  const templatePath = process.argv[4] || path.join('plan-b', 'originals', 'talent_individual_original.docx');

  const rawText = fs.readFileSync(path.resolve(inputPath), 'utf8');
  const parsed = parseTemplateInput(rawText);
  const validation = validate(parsed);

  if (!validation.ok) {
    console.error(JSON.stringify({ ok: false, ...validation }, null, 2));
    process.exit(1);
  }

  const mapped = mapToPlanB(parsed);
  fs.mkdirSync(path.resolve(outputDir), { recursive: true });
  const tempJson = path.resolve(outputDir, '.plan-b-telegram-mapped.json');
  fs.writeFileSync(tempJson, JSON.stringify(mapped, null, 2));

  const out = execFileSync('python3', [
    'plan-b-docx-generate.py',
    'generate',
    tempJson,
    templatePath,
    outputDir,
  ], { encoding: 'utf8' });

  const payload = JSON.parse(out);
  console.log(JSON.stringify({
    ok: true,
    inputPath: path.resolve(inputPath),
    parsed,
    mappedJson: tempJson,
    generated: payload.output,
  }, null, 2));
}

main();
