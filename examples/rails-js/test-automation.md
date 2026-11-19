> **Ví dụ cho dự án Rails + JS/TS**, không thuộc plugin. Dùng làm nội dung nháp khi điền file KB tương ứng của dự án (xem `examples/rails-js/README.md`).


# Test tự động từ test case

## Trước khi viết
1. Đọc `docs/testing/cases/<task-id>.md` và quy ước test trong `docs/engineering/coding-standards.md`.
2. Tìm 1 file test cùng loại đang có trong repo làm mẫu (factory, helper, cấu trúc thư mục) và bắt chước.

## Quy ước viết
- Tên test chứa ID: `it "AC-2 TC-5: không cho huỷ đơn đã thanh toán"`. Một test = một hành vi.
- Chọn tầng rẻ nhất đủ chứng minh: logic → unit; quyền/API → request spec; luồng người dùng quan trọng → E2E.
- **Phân quyền luôn test ở tầng request/API**, không chỉ test ẩn nút ở FE.
- Dữ liệu tạo trong test (factory/fixture), không dựa dữ liệu sẵn có trong DB. Test không phụ thuộc thứ tự chạy.
- Thời gian: đóng băng (`travel_to`, fake timers), không `sleep`.
- Gọi ngoài (HTTP, mail, queue): stub/mocked; kiểm có được gọi đúng tham số.
- Playwright: chọn phần tử theo role/label/test-id, chờ theo điều kiện (`expect(...).toBeVisible()`), không chờ cố định.
- Assert kết quả cụ thể (mã lỗi, giá trị, số bản ghi), không chỉ "không lỗi". Test phải **fail được** nếu bỏ phần code mới.

## Chạy
- Trên DB clone: `.claude/agent-team/agent-db-clone.sh test <task-id> <đường dẫn spec>`.
- Chạy test mới trước, sau đó suite liên quan (cùng module) để bắt regression.
- Test chập chờn: chạy lại 1 lần. Lúc pass lúc fail → báo `FAIL` kèm ghi chú "flaky", không ghi PASS.

## Ghi kết quả
Mỗi test case một dòng trong `docs/testing/test-report.md`:
`| <task-id> | AC-n | <tên test> | PASS/FAIL/BLOCKED/NOT RUN | <lệnh + dòng kết quả, vd "12 examples, 0 failures"> |`
- `BLOCKED`: không chạy được vì môi trường/dữ liệu; ghi lý do.
- `FAIL` do code: kèm bước tái hiện ngắn, file:dòng nghi ngờ, @dev cần sửa.
