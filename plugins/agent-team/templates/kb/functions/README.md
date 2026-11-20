# Chỉ mục hàm (đọc trước khi viết hàm mới)

> Graph (Graphify) cho biết **hàm nào nối với hàm nào**. Thư mục này cho biết **mỗi hàm làm gì**, để tìm theo nghĩa, dùng lại thay vì viết trùng.
> Mỗi model / bảng một file: `order.md`, `payment.md`... Hàm tiện ích dùng chung: `_shared.md`. `kb-check.py` so chỉ mục với graph: hàm public trong `FUNCTION_INDEX_PATHS` chưa có dòng → thiếu; dòng trỏ hàm đã xoá → thừa.

## Mục lục
| Model / bảng | File | Mô tả 1 dòng |
|---|---|---|

## Mẫu một file (`<model>.md`)
```
# Order (bảng orders)
verified-at: <commit>

| Hàm | Ý nghĩa (1 dòng) | Tham số chính | Trả về | Nguồn |
|---|---|---|---|---|
| `OrderService.list_active` | Đơn chưa huỷ của 1 user, có phân trang | user_id, page | danh sách đơn | app/services/order_service.rb:42 |
| `OrderService.cancel` | Huỷ đơn + hoàn kho, chỉ khi status=pending | order_id, reason | đơn đã huỷ | app/services/order_service.rb:88 |
| `InventoryService.restock` | → xem product.md | | | |
```

## Quy tắc
- **Tên hàm** viết `Class.method` (hàm ngoài class: tên hàm), đúng tên trong code để so được với graph.
- **Ý nghĩa** viết theo nghiệp vụ, đủ để phân biệt với hàm gần giống: điều kiện lọc, điều kiện được chạy, tác dụng phụ (gửi mail, ghi log, hoàn kho...).
- **Hàm chạm nhiều model**: ghi ở model chính mà hàm thay đổi; file model kia ghi một dòng `→ xem <file>.md`.
- **Chỉ hàm public** của tầng nằm trong `FUNCTION_INDEX_PATHS` (service, repository, model...). Không ghi hàm private, controller action (đã có ở `api/endpoints.md`).
- Nguồn ghi **đường dẫn từ gốc repo** + dòng. Mỗi file có `verified-at`.

## Dev dùng thế nào
1. Cần một hàm → mở file của model liên quan (không chắc model nào: `grep -ri "<từ khoá>" docs/functions/`).
2. Có hàm cùng nghĩa → mở `file:dòng` xác nhận → **dùng lại**; gần đúng → thêm tham số tuỳ chọn, không viết hàm mới.
3. Không có → viết hàm mới **và thêm 1 dòng vào đây trong cùng commit**. Sửa nghĩa / đổi tên / xoá hàm → sửa dòng tương ứng.
