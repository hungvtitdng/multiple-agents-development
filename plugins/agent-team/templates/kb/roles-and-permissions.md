# Roles and permissions

> Chủ sở hữu: BA. Nhãn mỗi mục: `Verified` / `Unverified` / `Planned` / `Deprecated` (+ `Assumption`, `Observed` nếu suy từ code). Ghi nguồn (task-id hoặc file) và `verified-at: <commit>`. Chỉ sửa phần bị ảnh hưởng, không ghi đè cả file.
> Quyền 3 tầng: **AI** (vai trò, file này) → **LÀM GÌ** (`permission-matrix.md`) → **TRÊN DỮ LIỆU NÀO / KHI NÀO** (điều kiện `C-<tên>`, file này). Vì sao quyết định như vậy: `security/permission-decisions.md`.

## Vai trò
> Tên vai trò ở đây là tên cột trong `permission-matrix.md`.

| Vai trò | Mô tả | Gán bởi | Kế thừa | Nhãn | Nguồn |
|---|---|---|---|---|---|

## Điều kiện (phạm vi dữ liệu)
> Giới hạn dữ liệu user được chạm (của mình, chi nhánh mình, tenant mình, trạng thái nào). Ma trận ghi mã `C-<tên>`, không chép lại nội dung.

| C | Điều kiện | Kiểm ở đâu (API / query / policy) | Nhãn | Nguồn |
|---|---|---|---|---|
