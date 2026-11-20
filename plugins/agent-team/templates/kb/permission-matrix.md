# Permission matrix

> Chủ sở hữu: BA. Nhãn mỗi mục: `Verified` / `Unverified` / `Planned` / `Deprecated` (+ `Assumption`, `Observed` nếu suy từ code). Ghi nguồn (task-id hoặc file) và `verified-at: <commit>`. Chỉ sửa phần bị ảnh hưởng, không ghi đè cả file.
> - Mỗi dòng 1 hành động `P-<tài nguyên>.<hành động>`. Mỗi cột vai trò (tên đúng như `roles-and-permissions.md`) là 1 quyết định: `✅` · `❌` · `✅ C-<tên>` (có điều kiện) · thêm `BR-n` nếu có quy tắc. **Không để trống ô.**
> - Page / API: page (`modules/<tên>/screens/<màn>.md`) và endpoint dùng quyền này. Nguồn: `file:dòng` của policy / guard kiểm quyền.
> - Test Design: mỗi ô = 1 test case (ô `❌` phải bị chặn, ô `C-` thử dữ liệu của người khác). Security: ô `C-` phải kiểm ở tầng dữ liệu (IDOR).
> - Thêm cột vai trò: chèn trước cột `Page / API`.

| P | Hành động | <Vai trò 1> | <Vai trò 2> | Page / API | Nhãn | Nguồn |
|---|---|---|---|---|---|---|
