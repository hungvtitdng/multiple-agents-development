# Quy chuẩn Frontend

> Chủ sở hữu: Architect (Lead sửa được). Áp dụng cho code trong `FE_PATHS`; phần dùng chung ở `coding-standards.md`.
> **Cách điền:** mỗi quy tắc 1 dòng, viết 1 câu; Đúng / Sai là ví dụ ngắn; Nguồn = `file:dòng` từ gốc repo hoặc task-id (nhãn `Planned` được để task-id / quyết định).
> **Nhóm:** Cấu trúc · Component · State · Gọi API · Form · Trạng thái màn · Theme · Responsive · Quyền · Đa ngôn ngữ · Test.
> **Nhãn:** `Verified` đã xác nhận · `Observed` thấy trong code · `Planned` sẽ áp dụng · `Deprecated` bỏ.
> Mã `FE-n` không đổi, không dùng lại khi xoá. Reviewer dẫn mã khi báo lỗi ("vi phạm FE-2"). **Xoá 2 dòng mẫu (`Example`) khi điền thật** (kb-check báo nếu còn).

verified-at: <commit>

| Mã | Nhóm | Quy tắc (1 câu) | Đúng | Sai | Nguồn | Nhãn |
|---|---|---|---|---|---|---|
| FE-1 | Component | Dùng component có sẵn của dự án trước khi tạo mới | dùng `<Button>` chung | tự viết `<button>` với style riêng | | Example |
| FE-2 | Trạng thái màn | Màn có gọi API phải có đủ loading / rỗng / lỗi | hiện khung tải, "Chưa có dữ liệu", nút Thử lại | màn trắng khi API lỗi | | Example |
