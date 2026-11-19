# <tên app>

> Chỉ Lead ghi. Hook đọc mục "Cổng" trước khi cho sang code (S3).

## Cổng (Lead cập nhật, hook kiểm)
- Intake: TODO (YES khi intake.md đủ, không còn TODO)
- Challenger: TODO (DONE khi đã đối chiếu danh sách của challenger với requirements)
- Gap-check: TODO (PASS = `.claude/agent-team/gap-check.py` exit 0; hook tự chạy lại)
- Owner duyệt: TODO (APPROVED khi owner đã xác nhận mockup + flow + defaults)

## Module (thứ tự build)
> Mỗi module là 1 task `/agent-team:run`. Không có remote (`PUSH=0`): branch module sau tạo từ branch module trước, user merge theo thứ tự.

| M | Module | Gồm R | Phụ thuộc | Loại | Branch gốc | Task-id | Trạng thái |
|---|---|---|---|---|---|---|---|
| M-0 | Khung project (scaffold, CI, Docker, env) | | | VỪA | | | TODO |
| M-1 | | | M-0 | | | | TODO |
