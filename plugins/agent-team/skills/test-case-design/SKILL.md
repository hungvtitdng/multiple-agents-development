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

## Giao diện: trạng thái × chiều rộng (E2E)
Task có UI: mỗi màn trong wireframe → case E2E cho **mỗi trạng thái** (bình thường, rỗng, đang tải, lỗi, không có quyền) và luồng chính chạy ở **mỗi chiều rộng** trong config `VIEWPORTS` (vd 375 / 768 / 1280).
| Kiểm ở mọi chiều rộng | Cách đo (Playwright) |
|---|---|
| Không cuộn ngang | `document.documentElement.scrollWidth <= window.innerWidth` |
| Nút / link chính bấm được | nhìn thấy, nằm trong khung, cao và rộng ≥ 44px ở chiều rộng < 768 |
| Không bị che / tràn | phần tử chính `toBeInViewport()` sau khi cuộn tới; chữ không bị cắt |
| Menu | < 768: nút ☰ mở được menu; ≥ 768: menu hiện sẵn (theo wireframe) |
| Bảng | < 768: thành thẻ hoặc cuộn **trong khung**, không làm trang cuộn ngang |
| Khớp wireframe | chụp ảnh mỗi trạng thái × chiều rộng, so với tab tương ứng trong wireframe |
- Một case mô tả 1 lần, ghi cột `Chiều rộng` = `tất cả` (test chạy lặp theo `VIEWPORTS`), chỉ tách case khi hành vi khác nhau (vd menu ☰).
- Bằng chứng: ảnh `docs/testing/evidence/<task-id>/<TC>-<trạng thái>-<chiều rộng>.png`.

## Ma trận phân quyền tối thiểu
Với mỗi endpoint/hành động mới: khách chưa đăng nhập → 401; user không có quyền → 403; user có quyền nhưng **bản ghi của người khác / tenant khác** → 403/404 (không lộ tồn tại); user đúng → thành công.

## Mẫu `docs/testing/cases/<task-id>.md`
```
| ID | AC | Loại (unit/request/E2E/...) | Chiều rộng | Tiền điều kiện + dữ liệu | Bước | Kết quả mong đợi | Ưu tiên | Tự động hoá |
|---|---|---|---|---|---|---|---|---|
| TC-1 | AC-1 | request | - | user A, đơn #1 của A, trạng thái paid | DELETE /orders/1 | 422, "đơn đã thanh toán" | P1 | Có |
| TC-2 | AC-2 | E2E | tất cả | user A, 3 đơn | mở /orders, bấm Huỷ đơn #1 | đơn #1 "Đã huỷ", không cuộn ngang, nút Huỷ ≥ 44px ở 375 | P1 | Có |
```
- Ưu tiên: **P1** mất dữ liệu, sai tiền, sai quyền, luồng chính · **P2** validation, lỗi thường gặp · **P3** hiển thị, hiếm gặp.
- Không ghi PASS/FAIL (việc của test-executor).
- Migration có thay đổi dữ liệu → thêm case rollback.

## Phản biện trong debate
Chỉ ra: AC không kiểm chứng được, phương án khó test (phụ thuộc thời gian thật, gọi ngoài không mock được, trạng thái ẩn), edge case bị bỏ sót, regression có nguy cơ.
