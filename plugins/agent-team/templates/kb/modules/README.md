# Modules

> Chủ sở hữu: BA, Architect, dev. Nhãn mỗi mục: `Verified` / `Unverified` / `Planned` / `Deprecated` (+ `Assumption`, `Observed` nếu suy từ code). Ghi nguồn (task-id hoặc file) và `verified-at: <commit>`. Chỉ sửa phần bị ảnh hưởng, không ghi đè cả file.

Mỗi module `modules/<tên>/README.md` (chức năng, API, DB, rule `BR-<tên>-<n>`, test liên quan), `screens/<màn>.md`, `actions/<hành động>.md`. Tạo dần khi task chạm module.

**Không chép logic chung vào page.** Quy tắc dùng ở nhiều nơi → `business-rules.md` / `BR-<tên>-<n>`; quyền → `permission-matrix.md`; luồng nhiều page → `flows/`. Page chỉ ghi mã. `kb-check.py` báo mã trỏ tới không có thật; `kb-check.py --index` in bảng tra ngược mã → page.

## Danh sách module
> Lead ghi từ bước Bản đồ. `kb-check.py` báo module chưa có `<tên>/README.md`.

| Module | Code |
|---|---|

## Tra page
> Scout Frontend ghi. Có 1 page (URL) → tra ra file KB.

| Route | Module | File KB | File code |
|---|---|---|---|

## Mẫu `screens/<màn>.md`
```
# <Tên màn>
- Route: /bookings/:id/edit
- File: src/pages/bookings/Edit.vue:1
- Vai trò: <vai trò được vào>
- Quyền: P-booking.update, P-booking.cancel
- API: PUT /api/bookings/:id (api/endpoints.md)
- Quy tắc: BR-bookings-2 (chỉ ghi mã)
- Luồng: F-1 bước 3
- Trạng thái: bình thường · rỗng · đang tải · lỗi · không có quyền
- Logic riêng của màn (validate, ẩn/hiện): <ghi ở đây, kèm file:dòng>
- verified-at: <commit>
```
