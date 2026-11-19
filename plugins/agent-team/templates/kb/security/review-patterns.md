# Mẫu tìm lỗi bảo mật của dự án

> Chủ sở hữu: Security. Nhãn mỗi mục: `Verified` / `Unverified` / `Planned` / `Deprecated` (+ `Assumption`, `Observed` nếu suy từ code). Ghi nguồn (task-id hoặc file) và `verified-at: <commit>`. Chỉ sửa phần bị ảnh hưởng, không ghi đè cả file.
> Skill `agent-team:security-review` nêu nguyên tắc chung; file này ghi **cách tìm theo đúng stack của dự án**.

## Stack
<framework, ngôn ngữ, thư viện auth/phân quyền, ORM>

## Cách dự án kiểm quyền
<nơi kiểm xác thực, nơi kiểm phân quyền, cách giới hạn theo chủ sở hữu/tenant, ví dụ file:dòng>

## Mẫu tìm theo nhóm
| Nhóm | Mẫu grep / hàm nguy hiểm | Cách xác nhận | Ví dụ đúng trong repo (file:dòng) | Nhãn |
|---|---|---|---|---|
| Phân quyền / IDOR | | | | |
| Gán dữ liệu hàng loạt | | | | |
| Injection (DB, lệnh, template) | | | | |
| XSS / render | | | | |
| CSRF / phiên | | | | |
| Redirect / URL ngoài | | | | |
| Upload / download file | | | | |
| Log / lỗi lộ dữ liệu | | | | |

## Công cụ
<lệnh audit/quét tĩnh dự án dùng được, cách đọc kết quả>
