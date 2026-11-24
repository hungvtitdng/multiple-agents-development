# <tên app>

> Chỉ Lead ghi. Hook đọc mục "Cổng" trước khi cho sang code (S3).

## Cổng (Lead cập nhật, hook kiểm)
- Intake: TODO (YES khi intake.md đủ, không còn TODO)
- Challenger: TODO (DONE khi A4 săn gap trên nháp + mockup xong, không còn gap mới)
- Debate: TODO (DONE khi team đã debate chốt câu hỏi + đề xuất. Cần Challenger + Debate DONE mới build được form)
- Gap-check: TODO (PASS = `.claude/agent-team/gap-check.py` exit 0; hook tự chạy lại)
- Owner duyệt: TODO (APPROVED khi owner trả lời hết form cuối)

## Module (thứ tự build)
> **Lead điều phối** M-0 → … → M-E2E trên 1 branch phiên: thiết kế từng module (Loại: `NHẸ` / `VỪA` / `NẶNG`), chia task, task chạy song song (tối đa `MAX_PARALLEL`), merge + integration test, module xong gắn tag. User không gõ lệnh từng module. Phụ thuộc: chỉ ghi phụ thuộc thật. Trạng thái: `TODO` / `DESIGN` / `DOING` / `DONE` / `BLOCKED (<lý do>)`.

| M | Module | Gồm R | Phụ thuộc | Loại | Tag | Task-id | Người chạy | Trạng thái |
|---|---|---|---|---|---|---|---|---|
| M-0 | Khung project (scaffold, CI, Docker, env, Playwright + e2e/) | | | VỪA | | | | TODO |
| M-DB | Nền dữ liệu: mọi bảng trong docs/database/schema.md (migration, model, quan hệ, enum, factory, seeder) + service dùng chung | | M-0 | NHẸ | | | | TODO |
| M-SKEL-BE | Khung BE: service theo model + hàm stub, controller trả props theo contract, request, route | | M-DB | NHẸ | | | | TODO |
| M-SKEL-FE | Khung FE: file chung (layout, component, trang rỗng) → UI thật mọi màn, mock data từ props | | M-DB, M-SKEL-BE | NHẸ | | | | TODO |
| M-1 | | | M-SKEL-BE, M-SKEL-FE | | | | | TODO |
| M-E2E | E2E toàn app: mọi luồng "1 ngày của <vai trò>" × mọi VIEWPORTS | tất cả | mọi module | VỪA | | | | TODO |

## Lý do phụ thuộc
> Mỗi phụ thuộc trong cột "Phụ thuộc" 1 dòng. `contract` = chỉ cần `docs/product/contracts/M-<n>.md` của module kia (làm song song được) · `code` = cần code của module kia đã merge.
- M-DB → M-0 (code): migration chạy trên khung project
- M-SKEL-BE → M-DB (code): hàm stub đọc dữ liệu từ factory / seeder
- M-SKEL-FE → M-DB (code): mock data qua props đọc từ dữ liệu mẫu
- M-SKEL-FE → M-SKEL-BE (contract): props mỗi màn theo contracts/M-SKEL.md, code song song
- M-1 → M-SKEL-BE (code): điền thân hàm stub của mình trong file có sẵn
- M-1 → M-SKEL-FE (code): nối dữ liệu thật vào màn có sẵn
