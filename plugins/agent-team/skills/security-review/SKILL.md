---
name: security-review
description: Quy trình security review chung cho mọi stack - nhóm lỗ hổng cần soi, cách tìm trong diff, cách xác nhận và chấm mức. Mẫu tìm lỗi theo framework của từng dự án nằm ở docs/security/review-patterns.md. Dùng khi security duyệt solution hoặc review code.
---

# Security review

## 0. Đọc mẫu riêng của dự án trước
`docs/security/review-patterns.md`: mẫu grep, hàm nguy hiểm, cách kiểm quyền **theo đúng framework của dự án**.
- Có file → dùng mẫu trong đó để tìm.
- Chưa có hoặc thiếu nhóm nào → tự suy mẫu từ code dự án (cách dự án kiểm quyền, query, render), làm theo nguyên tắc dưới đây, rồi ghi vào kết quả **"Đề xuất bổ sung review-patterns.md"** (mẫu + `file:dòng` ví dụ). Security cập nhật file đó khi đóng task.

## 1. Phạm vi
Bắt đầu từ diff (`git diff --name-only --merge-base <nhánh gốc>` + `git status --short`: task chưa commit tới khi review xong), sau đó mới mở rộng ra caller và nơi dùng chung. Không liệt kê checklist chung chung cho phần code không đổi.

## 2. Nhóm cần soi (mọi stack)
| Nhóm | Câu hỏi |
|---|---|
| Xác thực | Endpoint/hành động mới có yêu cầu đăng nhập như hành động cùng loại không? Có đường nào bỏ qua? |
| Phân quyền | Kiểm quyền ở **tầng API và tầng dữ liệu**? Mọi hành động cùng tài nguyên kiểm như nhau (parity)? |
| IDOR / cô lập tenant | Lấy bản ghi theo id từ request có giới hạn theo chủ sở hữu/tenant không? Job nền, export, cache key, search có giới hạn tương tự? |
| Gán dữ liệu hàng loạt | Request có tự đặt được field nhạy cảm (quyền, chủ sở hữu, giá, trạng thái)? |
| Injection | Input có ghép thẳng vào query, lệnh hệ thống, template, đường dẫn file, tên class/method? |
| XSS / render | Dữ liệu người dùng được render không escape? |
| CSRF / phiên | Hành động ghi dùng cookie có chống CSRF? Phiên đổi/hết hạn đúng lúc? |
| Redirect / URL ngoài | Redirect hoặc gọi URL lấy từ input (open redirect, SSRF)? |
| File | Upload: kiểu, dung lượng, nơi lưu, ai tải được. Download: path traversal |
| Lộ dữ liệu | API trả field thừa? Log, lỗi, analytics chứa token/PII? Thông báo lỗi lộ sự tồn tại bản ghi? |
| Secret | Key, mật khẩu, token trong code, config, log, commit? |
| Dependency | Thư viện mới hoặc nâng cấp có CVE mức cao? (dùng công cụ audit của dự án nếu có) |

## 3. Duyệt solution (trước khi code)
Trả lời 4 câu cho phương án đã chốt: (1) kiểm quyền ở đâu, có cả tầng dữ liệu? (2) dữ liệu của chủ sở hữu/tenant khác có thể lọt qua đường nào (query, cache, job, export)? (3) API trả gì, có thừa? (4) dữ liệu nhạy cảm đi vào log/queue/bên thứ ba? Kèm **test case bảo mật** cho test-designer.

## 4. Xác nhận trước khi báo
- Kết quả grep chỉ là ứng viên. Issue phải nêu được: **ai** bị ảnh hưởng, **tài nguyên** nào, **hậu quả** gì.
- Kiểm lớp khác (middleware, policy, scope mặc định) đã chặn chưa trước khi kết luận.
- Phân loại: `confirmed` (đủ bằng chứng trong code) · `needs_validation` (cần cấu hình/hạ tầng ngoài code, ghi cần kiểm gì) · bác bỏ (ghi lý do).

## 5. Mức độ
- **Critical**: không cần đăng nhập vẫn đọc/ghi dữ liệu người khác, thực thi lệnh từ xa, injection vào DB, lộ secret.
- **High**: người đã đăng nhập truy cập dữ liệu/hành động của người hoặc tenant khác, tự nâng quyền, XSS lưu trữ.
- **Medium**: cần điều kiện khó, lộ thông tin hạn chế, thiếu giới hạn tần suất ở chỗ nhạy cảm.
- **Low**: phòng thủ chiều sâu, cấu hình nên có.

## 6. Viết issue
`[Mức] file:dòng | nhóm | ai bị ảnh hưởng + hậu quả | cách sửa cụ thể | confirmed/needs_validation`
