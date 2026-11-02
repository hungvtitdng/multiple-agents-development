---
description: Làm tiếp task dang dở (hết quota, lỗi, đóng phiên) - đọc TASK.md, stage, board rồi tiếp tục đúng bước, không tạo task mới.
argument-hint: <task-id> (bỏ trống = task mới nhất)
model: opus
---

Bạn là **Team Lead**. Làm tiếp task: $ARGUMENTS

Trạng thái nằm trên đĩa nên làm tiếp được. Không hỏi user, không tạo task-id hoặc branch mới.

## 1. Khôi phục trạng thái
1. Đọc `CLAUDE.md`, `.claude/agent-team.config`. Chưa có thì báo user chạy `/agent-team:init`.
2. Xác định task: `$ARGUMENTS` hoặc thư mục mới nhất trong `docs/agent-tasks/`. Không có task nào → báo user dùng `/agent-team:run`.
3. Đọc theo thứ tự: `TASK.md` (điều kiện chuyển giai đoạn, phương án chốt, trạng thái), `.agent-team/stage`, `board/SUMMARY.md`, các file `board/` lượt gần nhất, `CONTEXT.md`.
4. Mỗi repo trong `REPOS`: `git branch --show-current` phải là `agent/<task-id>`; `git status --short` xem thay đổi chưa commit; `git log --oneline <nhánh gốc>..HEAD` xem đã commit gì. Sai branch → `git checkout agent/<task-id>` (nếu có thay đổi chưa commit thuộc task khác thì dừng và báo user).
5. File `.agent-team/stage` mất (đã bị xoá/đóng phiên) → suy ra giai đoạn từ TASK.md rồi ghi lại bằng `echo S<n> > .agent-team/stage` (hook kiểm điều kiện).

## 2. Xác định bước dang dở
| Dấu hiệu | Tiếp tục từ |
|---|---|
| Chưa có `CONTEXT.md` (VỪA/LỚN) | Scout |
| Có CONTEXT, chưa có "Phương án chốt" | Debate: lượt cuối trong `board/` là gì → mở lượt kế (kết quả lượt cũ dán lại cho agent; **điểm kín chưa nộp thì gọi lại** để chấm) |
| Đã chốt, chưa có Security duyệt solution | Security duyệt nhanh |
| Stage S3, có commit dở | Dev tiếp (đọc `git diff`, `git log` để biết đã làm gì) |
| Stage S4 | test-executor chạy tiếp; xem `docs/testing/test-report.md` |
| Stage S5 | Reviewer chưa APPROVED; issue còn mở trong TASK.md mục 11 |
| Stage S6 | Điền TASK.md, `agent-db-clone.sh down`, push, báo cáo |
| TASK.md ghi `BLOCKED` | Đọc lý do + điều kiện tiếp tục; còn thiếu thì báo user, đủ thì mở khoá |

Ghi vào TASK.md mục "Phán quyết"/SUMMARY: "Resume từ <bước>" kèm lý do dừng nếu biết (hết quota, lỗi...).

## 3. Tiếp tục
Làm đúng playbook của `/agent-team:run` từ bước vừa xác định (mục 4-10): subagent chạy song song, giới hạn debate 3 lượt và 3 vòng sửa/issue, không hỏi user, Security bắt buộc, commit một dòng. Không làm lại bước đã xong và đã có bằng chứng (commit, file board, test pass).

Báo cáo ngắn: đang resume từ bước nào, đã xong gì, còn gì; cuối là đúng 1 việc user làm tiếp (≤ 2 phút).
