# Review checklist (clean code)

> Chủ sở hữu: Architect. Nhãn mỗi mục: `Verified` / `Unverified` / `Planned` / `Deprecated` (+ `Assumption`, `Observed` nếu suy từ code). Ghi nguồn (task-id hoặc file) và `verified-at: <commit>`. Chỉ sửa phần bị ảnh hưởng, không ghi đè cả file.

1. Tên rõ nghĩa; hàm nhỏ, một trách nhiệm.
2. Không lặp code; không code chết, không debug sót.
3. Không magic number/string; cấu hình qua config/ENV.
4. Xử lý lỗi và edge case rõ ràng; không nuốt lỗi.
5. Không N+1; list có phân trang; truy vấn có index.
6. Không sửa code cũ khi không cần; không refactor ngoài phạm vi; diff nhỏ nhất đủ dùng.
7. Test đi kèm, dễ test.
8. Comment ngắn, chỉ khi thật cần.
9. Không secret, `.env`, dữ liệu thật trong code.
