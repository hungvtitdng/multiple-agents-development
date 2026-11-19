---
name: test-case-design
description: Kỹ thuật thiết kế test case từ AC - phân vùng tương đương, giá trị biên, bảng quyết định, chuyển trạng thái, ma trận phân quyền, case lỗi/đồng thời - và mẫu file test case. Dùng khi test-designer viết docs/testing/cases/<task-id>.md hoặc phản biện khả năng test.
---

# Thiết kế test case

## Quy trình
1. Mỗi `AC-n` → liệt kê biến đầu vào và trạng thái liên quan.
2. Áp kỹ thuật phù hợp (bảng dưới), chọn **ít case nhất mà vẫn phủ hết rủi ro**.
3. Thêm case bảo mật Security yêu cầu và case regression.
4. Ghi theo mẫu, gắn mức ưu tiên.

## Kỹ thuật
| Kỹ thuật | Dùng khi | Cách |
|---|---|---|
| Phân vùng tương đương | Input có nhóm giá trị xử lý giống nhau | 1 case mỗi vùng hợp lệ + 1 mỗi vùng không hợp lệ |
| Giá trị biên | Có min/max, độ dài, ngày | min-1, min, max, max+1 (và 0, rỗng) |
| Bảng quyết định | Nhiều điều kiện kết hợp | Mỗi tổ hợp điều kiện có kết quả khác nhau = 1 case |
| Chuyển trạng thái | Có trạng thái (draft → paid → cancelled) | Mọi chuyển hợp lệ + chuyển bị cấm quan trọng |
| Ma trận phân quyền | Có role/chủ sở hữu/tenant | role × hành động × (của mình / của người khác / tenant khác) |
| Case lỗi | Gọi ngoài, DB, input xấu | timeout, 5xx, dữ liệu thiếu, trùng khoá |
| Đồng thời / lặp | Thanh toán, tạo bản ghi, job | bấm 2 lần, 2 request song song, job chạy lại → idempotent |
| Vòng đời dữ liệu | Xoá mềm, archive, export | bản ghi đã xoá có còn lộ qua list/search/export không |

## Ma trận phân quyền tối thiểu
Với mỗi endpoint/hành động mới: khách chưa đăng nhập → 401; user không có quyền → 403; user có quyền nhưng **bản ghi của người khác / tenant khác** → 403/404 (không lộ tồn tại); user đúng → thành công.

## Mẫu `docs/testing/cases/<task-id>.md`
```
| ID | AC | Loại (unit/request/E2E/...) | Tiền điều kiện + dữ liệu | Bước | Kết quả mong đợi | Ưu tiên | Tự động hoá |
|---|---|---|---|---|---|---|---|
| TC-1 | AC-1 | request | user A, đơn #1 của A, trạng thái paid | DELETE /orders/1 | 422, "đơn đã thanh toán" | P1 | Có |
```
- Ưu tiên: **P1** mất dữ liệu, sai tiền, sai quyền, luồng chính · **P2** validation, lỗi thường gặp · **P3** hiển thị, hiếm gặp.
- Không ghi PASS/FAIL (việc của test-executor).
- Migration có thay đổi dữ liệu → thêm case rollback.

## Phản biện trong debate
Chỉ ra: AC không kiểm chứng được, phương án khó test (phụ thuộc thời gian thật, gọi ngoài không mock được, trạng thái ẩn), edge case bị bỏ sót, regression có nguy cơ.
