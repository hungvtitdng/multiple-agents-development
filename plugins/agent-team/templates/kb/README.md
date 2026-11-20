# Knowledge Base

Mọi agent **đọc** trước khi làm. Mỗi thư mục có chủ sở hữu (hook chặn ghi sai chủ).

| Nơi | Chủ ghi | Nội dung |
|---|---|---|
| `project-overview.md`, `architecture.md`, `tech-stack.md`, `architecture/`, `decisions/`, `integrations/` | Architect | Tổng quan, kiến trúc, quyết định kỹ thuật |
| `api/`, `database/` | Architect, backend-dev | API, schema |
| `business-rules.md`, `domain-model.md`, `roles-and-permissions.md`, `glossary.md` | BA | Nghiệp vụ |
| `roles-and-permissions.md` (vai trò + điều kiện `C-`), `permission-matrix.md` (vai trò × hành động `P-`) | BA (Security đọc, Test Design sinh test) | Quyền: ai · làm gì · trên dữ liệu nào |
| `flows/` | BA | Luồng qua nhiều page `F-n` |
| `engineering/` | Architect | Quy chuẩn code, checklist clean code |
| `modules/<tên>/` | BA, Architect, dev | Chức năng, màn hình, hành động, API, test liên quan. `modules/README.md`: danh sách module + bảng tra Route → file KB |
| `testing/` | Test Design, Test Execution | Chiến lược, test case, ma trận, kết quả |
| `security/` | Security | Phát hiện, quyết định phân quyền |
| `agent-tasks/<task-id>/` | Lead | TASK.md, CONTEXT.md (Scout), board |
| `product/` (App Mode, `/agent-team:app`) | BA: `problem`, `coverage`, `defaults`, `requirements`, `flows`, `data` · ui-designer: `screens.md`, `design/` · Lead: còn lại | Tài liệu cả app; `SPEC.md` gộp toàn bộ (sinh bằng `gap-check.py --spec`, không sửa tay) |

Nhãn: `Verified` đã xác minh · `Unverified` chưa · `Planned` kế hoạch · `Deprecated` bỏ. Không ghi dự kiến như đã làm, không ghi test PASS khi chưa chạy.

**Logic ở 1 chỗ:** quy tắc chung (`BR-`), quyền (`P-`, `C-`), luồng (`F-`) nằm ở KB tổng; page chỉ ghi mã. `kb-check.py` kiểm mã có thật, nguồn `file:dòng` có thật, KB cũ so với code; `--index` in tra ngược mã → page.
