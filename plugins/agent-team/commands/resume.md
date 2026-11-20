---
description: Làm tiếp task dang dở (hết quota, lỗi, đóng phiên) - đọc TASK.md, stage, board rồi tiếp tục đúng bước, không tạo task mới.
argument-hint: <task-id> [file form đã trả lời .xlsx/.csv] (bỏ trống = task mới nhất)
model: opus
---

Bạn là **Team Lead**. Làm tiếp task: $ARGUMENTS

Trạng thái nằm trên đĩa nên làm tiếp được. Không hỏi user (task `APP`: mọi câu đi form, mục A owner, mục B dev; xem mục 2), không tạo task-id hoặc branch mới.

## 1. Khôi phục trạng thái
1. Đọc `CLAUDE.md`, `.claude/agent-team.config`. Chưa có thì báo user chạy `/agent-team:init`.
2. Xác định task: `$ARGUMENTS` hoặc thư mục mới nhất trong `docs/agent-tasks/`. Không có task nào → báo user dùng `/agent-team:task`.
3. Đọc theo thứ tự: `TASK.md` (điều kiện chuyển giai đoạn, phương án chốt, trạng thái), `.agent-team/stage`, `board/SUMMARY.md`, `.claude/agent-team/board.py status <task-id>` và `board.py read <task-id>` (lượt gần nhất), `CONTEXT.md`. Task cũ chưa có board SQLite thì đọc các file `board/S*-R*`.
4. Mỗi repo trong `REPOS`: `git branch --show-current` phải là `agent/<task-id>`; `git status --short` xem thay đổi chưa commit; `git log --oneline <nhánh gốc>..HEAD` xem đã commit gì. Sai branch → `git checkout agent/<task-id>` (nếu có thay đổi chưa commit thuộc task khác thì dừng và báo user).
5. File `.agent-team/stage` mất (đã bị xoá/đóng phiên) → suy ra giai đoạn từ TASK.md rồi ghi lại bằng `echo S<n> > .agent-team/stage` (hook kiểm điều kiện).

## 2. Xác định bước dang dở
| Dấu hiệu | Tiếp tục từ |
|---|---|
| Chưa có `CONTEXT.md` (VỪA/LỚN) | Scout |
| Có CONTEXT, chưa có "Phương án chốt" | Debate: `board.py status` → lượt đang mở còn ai chưa post thì gọi tiếp role đó; lượt đã đủ thì `summary` + `close` rồi mở lượt kế (agent tự đọc board; **điểm kín chưa nộp thì gọi lại** để chấm) |
| Đã chốt, chưa có Security duyệt solution | Security duyệt nhanh |
| Stage S3, có commit dở | Dev tiếp (đọc `git diff`, `git log` để biết đã làm gì) |
| Stage S4 | test-executor chạy tiếp; xem `docs/testing/test-report.md`. Task có UI: xem ảnh đã có trong `docs/testing/evidence/<task-id>/` để biết chiều rộng nào chưa chạy E2E |
| Stage S5 | Reviewer chưa APPROVED; issue còn mở trong TASK.md mục 11 |
| Stage S6 | Điền TASK.md, `agent-db-clone.sh down`, push, báo cáo |
| TASK.md mục 14 có gap chưa `Closed` | Xử lý gap đó theo `task.md` mục 7b (`board.py status` xem lượt debate nhỏ đang mở), rồi giao dev làm tiếp phần đã dừng |
| TASK.md ghi `BLOCKED` | Đọc lý do + điều kiện tiếp tục; còn thiếu thì báo user, đủ thì mở khoá |
| `Loại: APP`, `BLOCKED (chờ owner, form lượt n)` | Có đường dẫn file trả lời trong `$ARGUMENTS` → `.claude/agent-team/owner-form.py import <file>`, báo số OK / góp ý / không / để trống, rồi làm tiếp theo `app.md` mục 0b. Chưa có file → báo user vẫn đang chờ owner / dev (đường dẫn `docs/product/owner-form-<n>.xlsx`), làm phần không phụ thuộc (A2) |
| `Loại: MODULE` | Như dòng APP ở trên nhưng mọi lệnh `owner-form.py` / `gap-check.py` thêm `--dir=<Module trong TASK.md>`; làm tiếp theo `/agent-team:module` |
| `Loại: APP`, stage S1-S2 (Phase A) | Làm tiếp theo `app.md` (plugin). Bước dang dở suy từ `docs/product/`: `APP.md` `Intake` chưa YES → A0 · `coverage.md` còn TODO → A1 · chưa `Phương án chốt` → A2 · chưa có `requirements` → A3 (nháp) · `screens.md` trống → A3b mockup · `Challenger` chưa DONE → A4 · `Debate` chưa DONE → debate chốt câu hỏi · chưa có `owner-form-1.xlsx` → build form cuối · `Owner duyệt` chưa APPROVED → mục 7 · chưa có bảng Module → A5. Câu hỏi đi **form** (A owner, B dev), không `AskUserQuestion` |
| Có `docs/product/APP.md`, task module | Như `run`; module tiếp theo xem cột Trạng thái của bảng Module trong `APP.md` |

Ghi vào TASK.md mục "Phán quyết"/SUMMARY: "Resume từ <bước>" kèm lý do dừng nếu biết (hết quota, lỗi...).

## 3. Tiếp tục
Làm đúng playbook của `/agent-team:task` từ bước vừa xác định (mục 4-10): subagent chạy song song, giới hạn debate 3 lượt và 3 vòng sửa/issue, không hỏi user, Security bắt buộc, commit một dòng. Không làm lại bước đã xong và đã có bằng chứng (commit, file board, test pass).

Báo cáo ngắn: đang resume từ bước nào, đã xong gì, còn gì; cuối là đúng 1 việc user làm tiếp (≤ 2 phút).
