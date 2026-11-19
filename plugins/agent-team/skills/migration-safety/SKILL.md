---
name: migration-safety
description: Nguyên tắc thay đổi schema DB an toàn cho mọi framework và CSDL - thêm cột, index, ràng buộc NOT NULL, đổi tên, xoá cột, backfill, khoá ngoại, rollback - và cách kiểm trên DB clone. Cú pháp cụ thể của dự án nằm ở docs/database/migration-rules.md. Dùng khi architect thiết kế schema hoặc backend-dev viết migration.
---

# Migration an toàn

Mục tiêu: deploy **không khoá bảng lâu, không mất dữ liệu, rollback được**, và app phiên bản cũ vẫn chạy được trong lúc deploy.

## 0. Đọc quy tắc riêng của dự án trước
`docs/database/migration-rules.md`: công cụ migration, loại CSDL và phiên bản, cú pháp tạo index không khoá, cách backfill, bảng lớn đã biết.
- Chưa có hoặc thiếu mục nào → suy từ migration cũ trong repo + tài liệu CSDL, làm theo nguyên tắc dưới, ghi **"Đề xuất bổ sung migration-rules.md"** trong kết quả (Architect/backend-dev cập nhật khi đóng task).

## 0b. Tạo file migration
- **Luôn sinh bằng generator của framework, chạy trong container app**: `.claude/agent-team/agent-db-clone.sh generate <task-id> <Tên> [tham số]` (lệnh generator lấy từ `MIGRATION_GEN_CMD`).
- **Không tự tạo file, tự đặt version/timestamp, không đổi tên file migration**: tự tạo dễ sinh nhiều file trùng version, thứ tự chạy sai. Guard chặn tạo file mới trong `MIGRATION_PATHS`.
- Sinh xong mới sửa nội dung file vừa sinh. Script tự kiểm version trùng trước `generate`, `migrate`, `verify`.

## 1. Nguyên tắc theo thao tác
| Việc | Nguyên tắc an toàn | Tránh |
|---|---|---|
| Thêm cột | Cho phép null, hoặc default là hằng số nếu CSDL hỗ trợ thêm nhanh | Default tính toán trên bảng lớn |
| Thêm index | Dùng cách tạo index **không khoá ghi** mà CSDL hỗ trợ | Tạo index thường trên bảng lớn đang chạy |
| Ràng buộc NOT NULL | 3 bước: thêm cột cho null → backfill → thêm ràng buộc (kiểm sau nếu CSDL cho phép) | Thêm NOT NULL ngay trên bảng có dữ liệu |
| Backfill | Bước riêng, chạy **theo lô**, không phụ thuộc model của app (model đổi sau sẽ làm hỏng migration cũ) | Cập nhật cả bảng trong một lệnh cùng migration đổi schema |
| Đổi tên cột/bảng | Thêm mới → ghi cả hai → backfill → đổi code đọc → xoá cũ ở bản sau | Đổi tên trực tiếp khi app cũ còn chạy |
| Xoá cột/bảng | Bản 1: code ngừng đọc/ghi. Bản 2: xoá | Xoá khi code vẫn dùng |
| Khoá ngoại | Thêm mà chưa kiểm dữ liệu cũ, kiểm ở bước sau (nếu CSDL hỗ trợ) | Kiểm ngay trên bảng lớn |
| Đổi kiểu cột | Như đổi tên: cột mới + backfill + chuyển code | Đổi kiểu trực tiếp trên bảng lớn |
| Giá trị trạng thái/enum | Chỉ thêm; code chịu được giá trị chưa biết | Đổi nghĩa hoặc thứ tự giá trị cũ |

## 2. Rollback
- Mỗi migration có đường lùi rõ ràng. Không lùi được (xoá dữ liệu) → đánh dấu rõ trong code migration **và** ghi vào TASK.md mục migration để Security/Architect biết.
- Backfill: bước lùi không cần khôi phục dữ liệu nhưng không được lỗi.

## 3. Kiểm trước khi báo xong
1. `.claude/agent-team/agent-db-clone.sh verify <task-id>` pass (migrate → rollback → migrate).
2. File schema/snapshot của dự án (nếu có) đổi khớp migration và được commit cùng.
3. Ước lượng số dòng bảng bị đổi trên DB clone; bảng lớn phải dùng cách an toàn ở bảng trên.
4. TASK.md: migration nào, có backfill không, thứ tự deploy, việc cần làm khi merge.
