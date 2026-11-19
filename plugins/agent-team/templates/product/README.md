# Tài liệu sản phẩm (App Mode)

> Dựng bởi `/agent-team:app`. Code chỉ bắt đầu khi `gap-check.py` PASS và owner duyệt (`APP.md`).
> Bảng trong các file dưới đây có **cột cố định**: `gap-check.py` đọc theo tên cột. Không đổi tên cột.

| File | Chủ ghi | Nội dung |
|---|---|---|
| `APP.md` | Lead | Điều kiện qua cổng, danh sách module + thứ tự build |
| `brief.md` | Lead | Ý tưởng gốc nguyên văn + tách thành ý `B-n` |
| `intake.md` | Lead | Phiếu: loại app, nền tảng, stack, ràng buộc |
| `questions.md` | Lead | Sổ câu hỏi `Q-n` (mức CAO phải trả lời hết) |
| `problem.md` | BA | Vấn đề, mục tiêu `G-n`, thước đo, ngoài phạm vi |
| `coverage.md` | BA | 12 góc nhìn, không ô nào trống |
| `defaults.md` | BA | Mục mặc định `D-n` từ catalog, owner chọn GIỮ/BỎ/KHÁC |
| `requirements.md` | BA | Yêu cầu `R-n`, truy về B/G/D, màn, AC |
| `flows.md` | BA | Luồng `F-n`: sơ đồ + bảng bước có cột "Nếu lỗi" |
| `data.md` | BA | Dữ liệu × CRUD, vòng đời trạng thái |
| `screens.md` | ui-designer | Màn `S-n` × vai trò × flow × file mockup |
| `design/mockup-*.html` | ui-designer | Wireframe đen trắng cấp app |
| `SPEC.md` | Lead (sinh bằng `gap-check.py --spec`) | **Toàn bộ tài liệu app trong 1 file**, không sửa tay. Hook chặn S6 khi SPEC cũ hơn tài liệu |

Kiến trúc, stack, quyết định: ghi vào KB sẵn có (`tech-stack.md`, `architecture.md`, `decisions/`, Architect). Quyền: `roles-and-permissions.md` (BA).

```
brief B-n ─► requirements R-n ─► screens S-n ─► mockup
   ▲              │   ▲
problem G-n ──────┘   └── defaults D-n (GIỮ/KHÁC)
```
