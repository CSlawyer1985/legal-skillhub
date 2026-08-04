# Telegram Contract Ops on Windows

## Hỗ trợ hiện tại
- Plan B: supported
- Telegram bot runtime: supported
- Plan C OCR Apple Vision: not supported natively

## Khuyến nghị
- dùng skill này trên Windows cho Plan B trước
- tạm disable OCR hoặc thay OCR engine riêng cho Windows

## Runtime
- Node.js
- Python 3
- PowerShell hoặc Command Prompt

## Cấu hình
- dùng `.env.telegram`
- dùng `.env.telegram.groups`
- đảm bảo path Windows tuyệt đối cho output/template
- xem file mẫu trong `assets/windows/`

## Chạy bot
Khuyên dùng PowerShell wrapper có sẵn trong `assets/windows/start-telegram-contract-bot.ps1`

## OCR note
Nếu cần Plan C trên Windows, thay OCR layer:
- Tesseract
- PaddleOCR
- OCR cloud API
