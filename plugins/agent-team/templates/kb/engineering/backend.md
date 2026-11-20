# Quy chuẩn Backend

> Chủ sở hữu: Architect (Lead sửa được). Áp dụng cho code trong `BE_PATHS`; phần dùng chung ở `coding-standards.md`.
> **Cách điền:** mỗi quy tắc 1 dòng, viết 1 câu; Đúng / Sai là ví dụ ngắn; Nguồn = `file:dòng` từ gốc repo hoặc task-id (nhãn `Planned` được để task-id / quyết định).
> **Nhóm:** Phân tầng · Controller · Service · Model · Validation · Quyền · API · Query · Migration · Job · Dịch vụ ngoài · Test.
> **Nhãn:** `Verified` đã xác nhận · `Observed` thấy trong code · `Planned` sẽ áp dụng · `Deprecated` bỏ.
> Mã `BE-n` không đổi, không dùng lại khi xoá. Reviewer dẫn mã khi báo lỗi ("vi phạm BE-3"). **Xoá 2 dòng mẫu (`Example`) khi điền thật** (kb-check báo nếu còn).

verified-at: <commit>

| Mã | Nhóm | Quy tắc (1 câu) | Đúng | Sai | Nguồn | Nhãn |
|---|---|---|---|---|---|---|
| BE-1 | Phân tầng | Controller chỉ nhận input, kiểm quyền, gọi service | gọi service huỷ đơn | tính tiền hoàn trong controller | | Example |
| BE-2 | API | Lỗi trả cùng 1 dạng `{code, message}` | `422 {code: "ORDER_SHIPPED"}` | trả chuỗi lỗi tự do | | Example |
