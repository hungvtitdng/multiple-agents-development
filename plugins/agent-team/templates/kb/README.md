# Knowledge Base

Mọi agent **đọc** trước khi làm. Mỗi thư mục có chủ sở hữu (hook chặn ghi sai chủ).

| Nơi | Chủ ghi | Nội dung |
|---|---|---|
| `project-overview.md`, `architecture.md`, `tech-stack.md`, `architecture/`, `decisions/`, `integrations/` | Architect | Tổng quan, kiến trúc, quyết định kỹ thuật |
| `api/`, `database/` | Architect, backend-dev | API, schema |
| `business-rules.md`, `domain-model.md`, `roles-and-permissions.md`, `glossary.md` | BA | Nghiệp vụ |
| `engineering/` | Architect | Quy chuẩn code, checklist clean code |
| `modules/<tên>/` | BA, Architect, dev | Chức năng, màn hình, hành động, API, test liên quan |
| `testing/` | Test Design, Test Execution | Chiến lược, test case, ma trận, kết quả |
| `security/` | Security | Phát hiện, quyết định phân quyền |
| `agent-tasks/<task-id>/` | Lead | TASK.md, CONTEXT.md (Scout), board |

Nhãn: `Verified` đã xác minh · `Unverified` chưa · `Planned` kế hoạch · `Deprecated` bỏ. Không ghi dự kiến như đã làm, không ghi test PASS khi chưa chạy.
