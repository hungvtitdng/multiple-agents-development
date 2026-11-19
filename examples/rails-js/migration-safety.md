> **Ví dụ cho dự án Rails + JS/TS**, không thuộc plugin. Dùng làm nội dung nháp khi điền file KB tương ứng của dự án (xem `examples/rails-js/README.md`).


# Migration an toàn

Mục tiêu: deploy không khoá bảng lâu, không mất dữ liệu, **rollback được**. Kiểm bằng `.claude/agent-team/agent-db-clone.sh verify <task-id>` (migrate → rollback → migrate).

## Bảng thao tác
| Việc | Cách an toàn | Tránh |
|---|---|---|
| Thêm cột | `add_column` nullable, không default tính toán. PG ≥ 11 / MySQL 8 thêm default hằng số an toàn | default gọi hàm trên bảng lớn |
| Thêm index (PG) | `disable_ddl_transaction!` + `add_index ..., algorithm: :concurrently` | `add_index` thường trên bảng lớn (khoá ghi) |
| Thêm index (MySQL) | `algorithm: :inplace, lock: :none` nếu bản hỗ trợ | — |
| NOT NULL | 3 bước: thêm cột nullable → backfill → `change_column_null` (PG: thêm `CHECK ... NOT VALID` rồi `VALIDATE`) | thêm NOT NULL ngay khi bảng đã có dữ liệu |
| Backfill | Migration/task riêng, theo lô (`in_batches(of: 1000)`), không dùng model class (định nghĩa class tối thiểu trong migration) | `Model.update_all` một phát trên bảng lớn trong cùng migration đổi schema |
| Đổi tên cột/bảng | Thêm mới → ghi cả hai → backfill → đổi code đọc → xoá cũ ở release sau | `rename_column` khi app cũ còn chạy |
| Xoá cột | Release 1: `self.ignored_columns += ["x"]`. Release 2: `remove_column` | xoá khi code vẫn đọc cột |
| Foreign key | `add_foreign_key ..., validate: false` rồi migration sau `validate_foreign_key` | validate ngay trên bảng lớn |
| Đổi kiểu cột | Thêm cột kiểu mới + backfill như đổi tên | `change_column` đổi kiểu trên bảng lớn |
| Enum/trạng thái mới | Thêm giá trị ở cuối; code xử lý được giá trị chưa biết | đổi thứ tự/giá trị số của enum cũ |

## Rollback
- Dùng `change` chỉ khi Rails tự đảo được; còn lại viết `up`/`down` rõ ràng.
- Migration không đảo được (xoá dữ liệu) → `raise ActiveRecord::IrreversibleMigration` **và** ghi rõ trong TASK.md mục migration, Security/Architect phải biết.
- Backfill: `down` không cần khôi phục dữ liệu nhưng không được lỗi.

## Kiểm trước khi báo xong
1. `agent-db-clone.sh verify <task-id>` pass.
2. `db/schema.rb` (hoặc `structure.sql`) thay đổi khớp migration, commit cùng.
3. Bảng lớn (ước lượng số dòng trên DB clone: `SELECT count(*)`): có dùng cách an toàn ở bảng trên không.
4. Ghi vào TASK.md: migration nào, có backfill không, thứ tự deploy, cần chạy gì khi merge.
