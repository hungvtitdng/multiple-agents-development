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
| M-1 | | | M-0 | | | | | TODO |
| M-E2E | E2E toàn app: mọi luồng "1 ngày của <vai trò>" × mọi VIEWPORTS | tất cả | mọi module | VỪA | | | | TODO |

## Lý do phụ thuộc
> Mỗi phụ thuộc trong cột "Phụ thuộc" 1 dòng. `contract` = chỉ cần `docs/product/contracts/M-<n>.md` của module kia (làm song song được) · `code` = cần code của module kia đã merge.
- M-1 → M-0 (code): <vì sao>
