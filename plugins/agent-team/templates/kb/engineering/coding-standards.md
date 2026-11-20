# Coding standards (chung BE + FE)

> Chủ sở hữu: Architect. Nhãn mỗi mục: `Verified` / `Unverified` / `Planned` / `Deprecated` (+ `Assumption`, `Observed` nếu suy từ code). Ghi nguồn (task-id hoặc file) và `verified-at: <commit>`. Chỉ sửa phần bị ảnh hưởng, không ghi đè cả file.

Theo convention hiện có của dự án, không tự đổi. Nhãn `Observed` = quan sát từ code (kèm ví dụ `file:dòng`), `Verified` = Architect đã xác nhận.
Quy tắc riêng: **BE** → `backend.md` · **FE** → `frontend.md`. File này chỉ giữ phần dùng chung.

Mỗi quy tắc: 1 câu + ví dụ đúng / sai + `file:dòng` + nhãn.

## Lệnh
- Lint: `LINT_CMD` · Format: `FORMAT_CMD` (trong `.claude/agent-team.config`)

## Đặt tên (biến, hàm, file, thư mục)
## Nguyên tắc xử lý lỗi chung (không nuốt lỗi, thông báo cho người dùng vs log cho dev)
## Logging (không log dữ liệu nhạy cảm)
## Cấu hình / ENV (không hard-code, không secret trong code)
## Comment (ngắn, chỉ khi cần)
## Git (commit, branch)
