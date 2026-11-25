# <tên module>

> Chỉ Lead ghi. Module mới trong app đang chạy (`/agent-team:module`). Hook đọc mục "Cổng" trước khi cho task con sang code (S3).

## Cổng (Lead cập nhật, hook kiểm)
- Intake: TODO (YES khi intake.md đủ: nền lấy từ KB + phạm vi module, không còn TODO)
- Challenger: TODO (DONE khi săn gap trên nháp + mockup xong, kể cả ảnh hưởng ngược lên phần cũ)
- Mockup: VẼ (hoặc `dùng lại <thư mục mockup đã duyệt>` khi module chỉ áp mockup có sẵn, không vẽ lại)
- Debate: TODO (DONE khi team đã debate chốt câu hỏi + đề xuất. Cần Challenger + Debate DONE mới build được form)
- Gap-check: TODO (PASS = `.claude/agent-team/gap-check.py --dir=<thư mục này>` exit 0)
- Owner duyệt: TODO (APPROVED khi owner trả lời hết form cuối)
- Ghép KB: TODO (YES khi quyền P-, quy tắc BR-, luồng F-, module README đã ghi vào KB)

## Ảnh hưởng ngược (phần cũ bị chạm)
| Phần cũ | Đổi gì | Vì sao | Nguồn (KB / file:dòng / graphify affected) | Test hồi quy |
|---|---|---|---|---|

## Task (thứ tự build)
> Mỗi task 1 lần `/agent-team:task <thư mục module> T-<n>`, lần lượt. TASK.md của task con ghi `- Module: <thư mục module>`.
> Task FE / view chạy trước task BE được, dùng mock: sổ `MOCKS.md` cùng thư mục, cột "Chờ task" ghi `T-<n>`. Hook đọc cột Task-id + Trạng thái ở đây để chặn S6 khi mock chưa gỡ.

| T | Task | Gồm R | Phụ thuộc | Loại | Task-id | Trạng thái |
|---|---|---|---|---|---|---|
| T-1 | | | | | | TODO |
