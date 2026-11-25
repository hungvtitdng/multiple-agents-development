# Quy tắc migration của dự án

> Chủ sở hữu: Architect, backend-dev. Nhãn mỗi mục: `Verified` / `Unverified` / `Planned` / `Deprecated` (+ `Assumption`, `Observed` nếu suy từ code). Ghi nguồn (task-id hoặc file) và `verified-at: <commit>`. Chỉ sửa phần bị ảnh hưởng, không ghi đè cả file.
> Skill `agent-team:migration-safety` nêu nguyên tắc chung; file này ghi **cú pháp và quy ước cụ thể của dự án**.

## Công cụ và CSDL
<công cụ migration, loại CSDL + phiên bản, nơi để file migration, file schema/snapshot>

## Cú pháp theo thao tác
| Thao tác | Cách làm trong dự án | Ví dụ trong repo (file:dòng) | Nhãn |
|---|---|---|---|
| Thêm cột | | | |
| Thêm index không khoá ghi | | | |
| NOT NULL nhiều bước | | | |
| Backfill theo lô | | | |
| Đổi tên / xoá cột | | | |
| Khoá ngoại | | | |
| Rollback | | | |

## Bảng lớn đã biết
| Bảng | Ước lượng số dòng | Lưu ý |
|---|---|---|

## Lệnh
<sinh file migration (MIGRATION_GEN_CMD, chạy trong container), migrate, rollback, kiểm trên DB riêng của task>
