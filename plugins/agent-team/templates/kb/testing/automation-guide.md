# Hướng dẫn viết test tự động của dự án

> Chủ sở hữu: Test Design, Test Execution. Nhãn mỗi mục: `Verified` / `Unverified` / `Planned` / `Deprecated` (+ `Assumption`, `Observed` nếu suy từ code). Ghi nguồn (task-id hoặc file) và `verified-at: <commit>`. Chỉ sửa phần bị ảnh hưởng, không ghi đè cả file.
> Skill `agent-team:test-automation` nêu nguyên tắc chung; file này ghi **công cụ và quy ước cụ thể của dự án**.

## Công cụ theo tầng
| Tầng | Framework | Thư mục | File mẫu nên bắt chước (file:dòng) |
|---|---|---|---|
| Unit | | | |
| API / request | | | |
| E2E | | | |

## Quy ước
| Việc | Cách làm trong dự án | Ví dụ (file:dòng) |
|---|---|---|
| Tạo dữ liệu (factory/fixture) | | |
| Đăng nhập / giả lập người dùng có quyền | | |
| Đóng băng thời gian | | |
| Giả lập gọi ngoài (HTTP, mail, queue) | | |
| Chọn phần tử E2E | | |
| Đặt tên test (AC-n) | | |

## E2E + responsive
| Việc | Cách làm trong dự án | Ví dụ (file:dòng) |
|---|---|---|
| Config Playwright (project theo `VIEWPORTS`) | | |
| Helper chụp ảnh + kiểm responsive (`shot`, `expectResponsive`) | | |
| Tạo dữ liệu E2E trên DB clone | | |
| Đăng nhập trong E2E | | |

## Lệnh chạy
<lệnh chạy một file, một nhóm, toàn bộ; chạy trên DB clone>
E2E: `.claude/agent-team/agent-db-clone.sh e2e <task-id> [args]` (config `E2E_CMD`, `APP_START_CMD`, `VIEWPORTS`)
