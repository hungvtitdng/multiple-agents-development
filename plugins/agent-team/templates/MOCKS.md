# Sổ mock

> Chỉ Lead ghi. Đặt ở thư mục module (`docs/product/modules/<tên>/MOCKS.md`) hoặc thư mục task đứng một mình (`docs/agent-tasks/<task-id>/MOCKS.md`).
> FE / view dựng trước bằng mock (theo API contract hoặc data shape đã chốt) khi BE chưa xong. Dev tạo mock → báo Lead → Lead thêm 1 dòng.
> Mock chỉ nằm trong `MOCK_PATHS` của config. Trạng thái: `OPEN` (đang dùng mock) → `SWAPPED` (đã nối BE thật, đã xoá file mock) → `VERIFIED` (E2E với BE thật PASS).
> Hook chặn S6 của task trong cột "Chờ task" (và mọi task sau khi task đó DONE) khi dòng chưa `VERIFIED` hoặc file mock còn tồn tại.

| Mã | File mock | Thay cho (API / data) | Contract | Chờ task | Trạng thái |
|---|---|---|---|---|---|
