# Telegram Contract Ops Troubleshooting

## Bot không phản hồi
- kiểm tra bot process có đang chạy không
- kiểm tra token đúng chưa
- kiểm tra bot đã được add vào đúng group chưa
- kiểm tra đã disable Group Privacy trong BotFather chưa
- kiểm tra `TELEGRAM_CONTRACT_CHAT_ID` đúng chưa

## `/mauhopdong` không trả template
- kiểm tra chat hiện tại có đúng contract group không
- kiểm tra bot route theo `chat_id` đã đúng chưa

## Bot không gửi được `.docx`
- kiểm tra `PLAN_B_OUTPUT_DIR` có tồn tại và có quyền ghi
- kiểm tra template `.docx` path đúng chưa
- kiểm tra parser/generator có trả lỗi không

## OCR eID sai field
- dùng `/cccd_debug`
- xem raw OCR text
- tinh chỉnh parser theo text thực tế

## OCR không chạy
- trên macOS: kiểm tra `swift --version`
- trên Windows/Linux: OCR Apple Vision hiện không dùng nguyên trạng

## Chat/group sai chức năng
- dùng `/id` trong group để kiểm tra `chat_id`
- so lại với env group mapping
