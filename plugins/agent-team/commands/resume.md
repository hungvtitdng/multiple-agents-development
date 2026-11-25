---
description: Làm tiếp việc dang dở (hết quota, lỗi, đóng phiên) - đọc TASK.md, stage, board rồi tiếp tục đúng bước; app / module thì chạy nối tiếp các module / task con còn lại tới hết.
argument-hint: <task-id> [file form đã trả lời .xlsx/.csv] (bỏ trống = task mới nhất)
model: opus
---

Bạn là **Team Lead**. Làm tiếp task: $ARGUMENTS

Trạng thái nằm trên đĩa nên làm tiếp được. **Chạy tiếp tới khi xong hết việc**, không chỉ task đang dở: task thuộc app / module đóng xong thì tự mở task kế theo bảng (mục 3). Không hỏi user (task `APP`: mọi câu đi form, mục A owner, mục B dev; xem mục 2), không tạo lại task-id hoặc branch của task đang dở (task kế của app / module thì tạo mới như mục 3).

## 1. Khôi phục trạng thái
1. Đọc `CLAUDE.md`, `.claude/agent-team.config`. Chưa có thì báo user chạy `/agent-team:init`. Đầu phiên hook `sync.py` tự chép script plugin mới sang `.claude/agent-team/` và thêm status line; có dòng `[agent-team] ...` thì báo lại user 1 dòng.
1b. Chạy `python3 .claude/agent-team/progress.py --list`, dán vào chat: user thấy đang ở bước nào, còn bước nào.
2. Xác định task: `$ARGUMENTS` hoặc thư mục mới nhất trong `docs/agent-tasks/`. Không có task nào → báo user dùng `/agent-team:task`.
3. Đọc theo thứ tự: `TASK.md` (điều kiện chuyển giai đoạn, phương án chốt, trạng thái), `.agent-team/stage`, `board/SUMMARY.md`, `.claude/agent-team/board.py status <task-id>` và `board.py whys <task-id> --open` (không đọc lại cả board; cần chi tiết 1 câu WHY: `board.py read <task-id> --why <n>`), `CONTEXT.md`. Task cũ chưa có board SQLite thì đọc các file `board/S*-R*`. Làm theo task.md mục 2b (giữ ngữ cảnh gọn).
4. Mỗi repo trong `REPOS`: `git branch --show-current` phải là `agent/<task-id>`; `git status --short` xem thay đổi chưa commit; `git log --oneline <nhánh gốc>..HEAD` xem đã commit gì. Sai branch → `git checkout agent/<task-id>` (nếu có thay đổi chưa commit thuộc task khác thì dừng và báo user).
5. File `.agent-team/stage` mất (đã bị xoá/đóng phiên) → suy ra giai đoạn từ TASK.md rồi ghi lại bằng `echo S<n> > .agent-team/stage` (hook kiểm điều kiện).

## 2. Xác định bước dang dở
| Dấu hiệu | Tiếp tục từ |
|---|---|
| Chưa có `CONTEXT.md` (VỪA/LỚN) | Scout |
| Có CONTEXT, chưa có "Phương án chốt" | Debate: `board.py status` → lượt đang mở còn ai chưa post thì gọi tiếp role đó; lượt đã đủ thì `summary` + `close` rồi mở lượt kế (agent tự đọc board; **điểm kín chưa nộp thì gọi lại** để chấm) |
| Đã chốt, chưa có Security duyệt solution | Security duyệt nhanh |
| Lượt / giai đoạn có agent dở (`board.py status` mục Agent) | Agent `DONE`: lấy kết quả từ đó, **không gọi lại**. Agent còn `RUNNING` / ⚠ im / chưa bắt đầu: gọi lại **chỉ agent đó** (chạy nền + `board.py wait`, task.md mục 2), kèm lý do treo trong status (lệnh đang kẹt) |
| Stage S3, có commit dở | Dev tiếp (đọc `git diff`, `git log` để biết đã làm gì) |
| `MOCKS.md` (task hoặc module) có dòng chờ task này chưa `VERIFIED` | SWAP theo `task.md` mục 6b: `OPEN` → giao dev nối thật + xoá mock; `SWAPPED` → E2E với BE thật |
| Có `docs/audit/AUDIT-*.md` với `Bước:` khác `DONE` | Làm tiếp theo `audit.md`: `REVIEW` → gọi lại làn chưa có lỗi trong bảng · `CHỜ DUYỆT` → báo user điền cột `Sửa?` · `UPDATE` → dòng `Sửa?: YES` chưa `FIXED` / `BACKLOG` |
| Stage S4 | test-executor chạy tiếp; xem `docs/testing/test-report.md`. Task có UI: xem ảnh đã có trong `docs/testing/evidence/<task-id>/` để biết chiều rộng nào chưa chạy E2E |
| Stage S5 | Reviewer chưa APPROVED; issue còn mở trong TASK.md mục 11 |
| Stage S6 | Điền TASK.md, `agent-db.sh down`, push, báo cáo |
| TASK.md mục 14 có gap chưa `Closed` | Xử lý gap đó theo `task.md` mục 7b (`board.py status` xem lượt debate nhỏ đang mở), rồi giao dev làm tiếp phần đã dừng |
| TASK.md ghi `BLOCKED` | Đọc lý do + điều kiện tiếp tục; còn thiếu thì báo user, đủ thì mở khoá |
| `Loại: APP`, `BLOCKED (chờ owner, form lượt n)` | Có đường dẫn file trả lời trong `$ARGUMENTS` → `.claude/agent-team/owner-form.py import <file>`, báo số OK / góp ý / không / để trống, rồi làm tiếp theo `app.md` mục 0b. Chưa có file → báo user vẫn đang chờ owner / dev (đường dẫn `docs/product/QnA-v<n>.xlsx`), làm phần không phụ thuộc (A2) |
| `Loại: MODULE` | Như dòng APP ở trên nhưng mọi lệnh `owner-form.py` / `gap-check.py` thêm `--dir=<Module trong TASK.md>`; làm tiếp theo `/agent-team:module` |
| `Loại: APP`, stage S1-S2 (Phase A) | Làm tiếp theo `app.md` (plugin). Bước dang dở suy từ `docs/product/`: `APP.md` `Intake` chưa YES → A0 · `coverage.md` còn TODO → A1 · chưa `Phương án chốt` → A2 · chưa có `requirements` → A3 (nháp) · `screens.md` trống → A3b mockup · `Challenger` chưa DONE → A4 · `Debate` chưa DONE → debate chốt câu hỏi · chưa có `QnA-v1.xlsx` → build form cuối · `Owner duyệt` chưa APPROVED → mục 7 · chưa có bảng Module → A5. Câu hỏi đi **form** (A owner, B dev), không `AskUserQuestion` |
| Có `docs/product/APP.md`, task module | Như `task`; xong thì sang module kế (mục 3) |
| Task mới nhất đã đóng (S6 xong, không còn stage), bảng Module (`APP.md`) / Task (`MODULE.md`) còn dòng `TODO` / `DOING` | Mở module / task kế theo `app.md` mục 10.2, không báo "đã xong" |
| Branch hiện tại `agent/YYYYMMDD-<DEV_ID>-m<n>` (team, Phase C) | Làm tiếp module đó (`pool.py resume`), trước tiên `pool.py sync`. Module đã PR xong → báo user, không tự nhận module khác |
| Có bảng `pool` (điều phối nhiều task) | `python3 .claude/agent-team/pool.py resume`: task RUNNING / FIX / GAP → `cd <worktree>` làm tiếp như bảng này (agent DONE thì không gọi lại); MERGING → chạy lại integration test rồi `merge-end`; module đang DESIGN → làm tiếp debate. Rồi `pool.py fill` cho đủ `MAX_PARALLEL` → vòng điều phối (`task.md` mục 6c) |

Ghi vào TASK.md mục "Phán quyết"/SUMMARY: "Resume từ <bước>" kèm lý do dừng nếu biết (hết quota, lỗi...).

## 3. Tiếp tục
Làm đúng playbook của `/agent-team:task` từ bước vừa xác định (mục 4-10): subagent chạy song song, giới hạn debate 3 lượt và 3 vòng sửa/issue, không hỏi user, Security bắt buộc, commit một dòng. Không làm lại bước đã xong và đã có bằng chứng (commit, file board, test pass).

**Không dừng sau khi xong task đang dở:** task thuộc app (`docs/product/APP.md` có bảng Module) hoặc module (`- Module:` trong TASK.md) → tự tạo task cho module / task con kế tiếp và làm tiếp, theo `app.md` mục 10.2 (tạo task-id + branch theo `task.md` mục 0-1, ghi bảng). Chỉ dừng ở điểm dừng trong `app.md` mục 10.2. `MAX_PARALLEL` là số agent user đã cho phép chạy cùng lúc: mở đủ slot, không hỏi lại vì "nhiều agent".

Báo cáo ngắn: đang resume từ bước nào, đã xong gì, còn gì; cuối là đúng 1 việc user làm tiếp (≤ 2 phút), hoặc "chưa cần làm gì" khi đang chạy tiếp.
