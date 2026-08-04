# Telegram Contract Ops Deployment

## Mục tiêu

Cài skill này trên máy mới theo hướng:
1. install skill
2. nạp token/config local
3. start bot
4. test flow Plan B / Plan C

Skill chỉ đóng gói:
- logic
- scripts
- template `.docx`
- references

Skill **không** đóng gói:
- Telegram bot token
- Google auth/token
- chat IDs thực tế
- `.env*`
- `.state/*`
- logs

## Runtime requirements

### Bắt buộc
- Node.js
- Python 3

### Bắt buộc nếu dùng OCR hiện tại
- macOS
- Swift / Apple Vision runtime

## Portability note

OCR hiện tại của Plan C dùng Apple Vision qua Swift:
- chạy tốt trên macOS
- **không portable nguyên trạng sang Linux**

Nếu máy mới là Linux:
- Plan B vẫn chuyển tốt
- Telegram bot flow vẫn chuyển tốt
- Plan C OCR phải thay engine OCR khác

## Cài ClawHub CLI

```bash
npm i -g clawhub
```

## Install skill từ ClawHub

```bash
clawhub install telegram-contract-ops
```

Hoặc version cụ thể:

```bash
clawhub install telegram-contract-ops --version 1.0.0
```

## Install skill từ file local `.skill`

Nếu chưa publish lên ClawHub mà chỉ copy file package:
- copy `telegram-contract-ops.skill` sang máy mới
- giải nén/cài theo workflow nội bộ của bạn

Khuyến nghị vẫn là publish lên ClawHub để cài bằng `clawhub install`.

## Cấu hình local bắt buộc sau khi install

Tạo file env cục bộ, ví dụ `.env.telegram`:

```bash
TELEGRAM_BOT_TOKEN='YOUR_TELEGRAM_BOT_TOKEN'
TELEGRAM_POLL_INTERVAL_MS='3000'
PLAN_B_OUTPUT_DIR='/ABSOLUTE/PATH/TO/plan-b/output'
PLAN_B_TEMPLATE_DOCX='/ABSOLUTE/PATH/TO/talent_individual_original.docx'
```

Tạo file env group mapping, ví dụ `.env.telegram.groups`:

```bash
TELEGRAM_MANAGEMENT_CHAT_ID='-100xxxxxxxxxx'
TELEGRAM_CONTRACT_CHAT_ID='-100yyyyyyyyyy'
```

## Đường dẫn/asset cần kiểm tra

Sau khi install, xác nhận các file này tồn tại:
- original template `.docx`
- Telegram input template
- bot script
- Plan B generator
- Plan C OCR/parser scripts

## Start bot

Ví dụ:

```bash
cd /path/to/installed/skill-or-workspace
set -a
source ./.env.telegram
source ./.env.telegram.groups
set +a
node scripts/telegram-planb-bot.js
```

Nếu bạn copy scripts ra workspace runtime riêng, đổi path tương ứng.

## Telegram setup checklist

1. Tạo bot bằng BotFather
2. Lấy bot token
3. Disable Group Privacy nếu dùng group flows
4. Add bot vào các group cần dùng
5. Trong mỗi group, gửi `/id` để lấy `chat_id`
6. Ghi `chat_id` vào `.env.telegram.groups`

## Group routing hiện tại

### Management group
- role: Plan A / reminder / management reporting
- không dùng tạo hợp đồng

### Contract group
- role: Plan B + Plan C
- dùng các lệnh:
  - `/start`
  - `/id`
  - `/mauhopdong`
  - `/cccd`
  - `/cccd_debug`
  - `/status`
  - `/cancel`

## Test checklist sau khi cài trên máy mới

### Test 1 — bot sống
Trong Telegram:
```text
/start
```

### Test 2 — lấy mẫu hợp đồng
```text
/mauhopdong
```

### Test 3 — Plan B text input
Paste block hợp đồng mẫu và xác nhận bot trả file `.docx`

### Test 4 — Plan C eID OCR
```text
/cccd
```
Gửi 1 ảnh screenshot CCCD điện tử, kiểm tra bot trả block OCR

### Test 5 — OCR debug
```text
/cccd_debug
```
Gửi ảnh eID và xem raw OCR text

## Publish bằng ClawHub

### Login
```bash
clawhub login
clawhub whoami
```

### Publish
Chạy từ máy có thư mục skill:

```bash
clawhub publish ./skills/telegram-contract-ops --slug telegram-contract-ops --name "Telegram Contract Ops" --version 1.0.0 --changelog "Initial release: Plan B docx generation, Plan C eID OCR, Telegram bot workflow"
```

## Update trên máy khác

```bash
clawhub update telegram-contract-ops
```

hoặc:

```bash
clawhub update telegram-contract-ops --version 1.0.0
```

## Migration checklist

Khi chuyển sang máy mới, làm theo thứ tự:
1. Install Node.js, Python 3
2. Install ClawHub CLI
3. Install skill `telegram-contract-ops`
4. Tạo `.env.telegram`
5. Tạo `.env.telegram.groups`
6. Start bot
7. Test `/mauhopdong`
8. Test `/cccd`
9. Nếu là macOS, test OCR thật
10. Nếu là Linux, quyết định engine OCR thay thế cho Plan C
