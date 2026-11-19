---
name: test-automation
description: Nguyên tắc chuyển test case thành test tự động cho mọi framework test - chọn tầng test, đặt tên theo AC, dữ liệu, thời gian, gọi ngoài, assert, chạy trên DB clone, ghi bằng chứng PASS/FAIL. Quy ước công cụ của dự án nằm ở docs/testing/automation-guide.md. Dùng khi test-executor viết và chạy test.
---

# Test tự động từ test case

## 0. Đọc hướng dẫn riêng của dự án trước
`docs/testing/automation-guide.md`: framework test, thư mục, cách tạo dữ liệu (factory/fixture), helper đóng băng thời gian, cách mock gọi ngoài, lệnh chạy, file mẫu nên bắt chước. Đọc thêm `docs/testing/cases/<task-id>.md`.
- Chưa có hoặc thiếu mục nào → tìm 1-2 file test cùng loại trong repo làm mẫu, làm theo nguyên tắc dưới, ghi **"Đề xuất bổ sung automation-guide.md"** trong kết quả.

## 1. Quy ước viết (mọi framework)
- Tên test chứa ID: `AC-2 TC-5: <hành vi>`. Một test = một hành vi.
- Chọn **tầng rẻ nhất đủ chứng minh**: logic thuần → unit; API/quyền → test tầng request/API; luồng người dùng quan trọng → E2E.
- **Phân quyền luôn test ở tầng API/request**, không chỉ test giao diện ẩn nút.
- Dữ liệu tự tạo trong test, không dựa dữ liệu có sẵn. Test độc lập, không phụ thuộc thứ tự chạy.
- Thời gian: đóng băng/giả lập, không chờ cố định (`sleep`).
- Gọi ngoài (HTTP, mail, queue, bên thứ ba): giả lập, và kiểm có được gọi đúng tham số.
- E2E: chọn phần tử theo vai trò/nhãn/test-id ổn định, chờ theo điều kiện hiển thị.
- Assert kết quả cụ thể (mã lỗi, giá trị, số bản ghi, trạng thái). Test phải **fail được** nếu bỏ phần code mới.

## 2. Chạy
- Trên DB clone: `.claude/agent-team/agent-db-clone.sh test <task-id> <phạm vi test>`.
- Chạy test mới trước, sau đó nhóm test liên quan để bắt regression.
- Lúc pass lúc fail: chạy lại 1 lần; vẫn chập chờn → ghi `FAIL` kèm "flaky", không ghi PASS.

## 3. Ghi kết quả
Mỗi test case một dòng trong `docs/testing/test-report.md`:
`| <task-id> | AC-n | <tên test> | PASS/FAIL/BLOCKED/NOT RUN | <lệnh + dòng kết quả làm bằng chứng> |`
- `BLOCKED`: không chạy được vì môi trường/dữ liệu, ghi lý do.
- `FAIL` do code: bước tái hiện ngắn, `file:dòng` nghi ngờ, @dev cần sửa.
