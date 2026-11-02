# Lessons

> Mục đích: **đã sai một lần thì không vấp lại.** File của repo (commit + push cùng branch), không phải trí nhớ của trợ lý. Chủ ghi: Lead, **ghi ngay khi có lỗi thật** (review Medium trở lên, test fail do code, Assumption sai, Security finding, làm lại/BLOCKED, user sửa cách làm), không chờ cuối task.
>
> - Tối đa 3 dòng mỗi task. Đã có bài giống thì tăng cột `Lặp lại`, không thêm dòng.
> - **Cách tránh phải kiểm tra được** bằng grep / đọc diff / test (vd "mọi list endpoint có pagination"), không phải lời khuyên chung.
> - Scout đưa bài `Active` liên quan vào CONTEXT.md; dev đọc trước khi code; Code Reviewer đối chiếu diff, lặp lại lỗi cũ = High.
> - `Lặp lại` ≥ 1: Architect chuyển "Cách tránh" vào `docs/engineering/review-checklist.md`, đổi `Trạng thái` thành `Promoted` (giữ dòng để truy nguồn).

| Task | Sai gì | Nguyên nhân gốc | Cách tránh (kiểm tra được) | Phát hiện bởi | Loại (rule / test / security / process) | Lặp lại | Trạng thái (Active / Promoted) |
|---|---|---|---|---|---|---|---|
