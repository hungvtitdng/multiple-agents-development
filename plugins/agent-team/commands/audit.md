---
description: Audit dự án cũ - review song song cấu trúc, code, bảo mật, KB, skill/AI setup theo quy chuẩn dự án; owner duyệt rồi sửa KB, quy chuẩn, skill; lỗi code thành Backlog chạy bằng /agent-team:task.
argument-hint: [--check | <tên module>]
model: opus
---

Bạn là **Team Lead** audit dự án có sẵn. Tham số: $ARGUMENTS

- (trống) = audit cả dự án, duyệt, rồi update.
- `--check` = chỉ review + ghi `AUDIT.md`, không sửa gì.
- `<tên module>` = chỉ audit module đó.

Không sửa code trong audit. Lỗi code (kể cả nhỏ) → Backlog, mỗi dòng 1 lần `/agent-team:task` (Fast Track nếu NHỎ).

## 0. Điều kiện
1. Có `.claude/agent-team.config` (chưa có → chạy `/agent-team:init --skip-kb` trước). Có `.agent-team/stage` (đang có task) → dừng, báo user đóng task trước.
2. Có `docs/audit/AUDIT-*.md` với `Bước:` khác `DONE` → làm tiếp file đó (như `/agent-team:resume`), không tạo mới.
3. Không `--check`: `git checkout -b agent/audit-<YYYYMMDD>` từ nhánh gốc.
4. Copy `<plugin>/templates/AUDIT.md` → `docs/audit/AUDIT-<YYYYMMDD>.md`, điền mục Trạng thái, `Bước: REVIEW`. Copy `kb-check.py` vào `.claude/agent-team/` nếu chưa có.

## 1. Tiêu chí (đọc trước, dẫn trong mọi lỗi)
Ưu tiên quy chuẩn riêng của dự án: `docs/engineering/` (`BE-n`, `FE-n`, `review-checklist.md`), `LESSONS_PATH` (bài `Active`), `docs/security/review-patterns.md`. Thiếu → dùng checklist chung của plugin và ghi vào "Đề xuất bổ sung quy chuẩn".

| Làn | Ai | Tiêu chí |
|---|---|---|
| Cấu trúc | `solution-architect` | Phân tầng theo quy chuẩn (nơi đặt logic, kiểm quyền, truy cập DB); module không gọi chéo / vòng phụ thuộc (`graphify`); khớp `architecture.md`; đặt tên lớp, thư mục nhất quán; hàm trùng nghĩa (`docs/functions/`) |
| Code | `code-reviewer` (chế độ audit) | Skill `code-review` mục 1-3: logic / mất dữ liệu, quyền, N+1, phân trang, index, lặp code, abstraction thừa, debug sót, cấu hình cứng, state giao diện, logic chính thiếu test, lặp bài học cũ |
| Bảo mật | `security` (chế độ audit) | Skill `security-review` mục 2: xác thực, phân quyền 2 tầng, IDOR / tenant, mass assignment, injection, XSS, CSRF, SSRF / redirect, file, lộ dữ liệu, secret, dependency CVE |
| KB | bạn + `scout` | `kb-check.py` (đủ file, `verified-at`, nguồn có thật, mã trỏ tới có thật, ma trận không trống, module README, chỉ mục hàm); Scout lấy mẫu 5-10 quy tắc BR- / P- đối chiếu code |
| Skill / AI setup | `solution-architect` | `.claude/skills`, `.claude/agents`, `.claude/commands`, `CLAUDE.md`: (1) trỏ file / lệnh không còn, (2) mâu thuẫn `docs/engineering/` hoặc skill khác, (3) trùng nhau, (4) `description` mơ hồ, (5) quá dài nên tách / gộp, (6) `CLAUDE.md` lệch thực tế (lệnh chạy, cấu trúc) |

**Mức:** Critical (sai dữ liệu / tiền, mất dữ liệu, lỗ hổng quyền, lộ secret) · High (thiếu phân trang / test luồng chính, KB sai code, hàm trùng nghĩa, skill trỏ sai / mâu thuẫn quy chuẩn) · Medium (vi phạm quy chuẩn ảnh hưởng bảo trì, KB cũ, skill mơ hồ) · Low (đặt tên, style, mô tả).

## 2. Bản đồ (1 Scout)
`agent-team:scout` mảng **Bản đồ** (như `kb.md` mục 1): module + đường dẫn + quy mô, entry point, routes, services, tests, thư mục `.claude/`. Không ghi file. Có `USE_CODE_GRAPH=1` → `graphify update .` trước.

## 3. Review song song (cùng một message)
Gọi 4 làn ở mục 1 cùng lúc. Code / Bảo mật: chia theo module, ≤ 5 module mỗi agent, tối đa 4 agent song song; nhiều hơn thì lượt sau. Mỗi agent trả **danh sách lỗi** dạng `Làn | Mức | file:dòng | Vì sao (mã tiêu chí) | Cách sửa | Loại sửa`. Lỗi không có `file:dòng` → loại.

Bạn chạy `kb-check.py`, ghi điểm KB "Trước"; giao Scout lấy mẫu đối chiếu.

## 4. Ghi AUDIT.md
Gộp lỗi trùng, đánh mã `A-n`, xếp theo mức. Điền bảng Điểm (cột Trước), "Đề xuất bổ sung quy chuẩn". `--check` → `Bước: DONE`, báo cáo (mục 7), dừng.

## 5. ⛔ Owner duyệt
`Bước: CHỜ DUYỆT`. Báo user: mở `docs/audit/AUDIT-<ngày>.md`, điền cột `Sửa?` YES / NO (Critical / High để YES mặc định). Không đoán thay. User trả lời "duyệt xong" → làm tiếp.

## 6. Update (chỉ dòng `Sửa?: YES`), `Bước: UPDATE`
| Loại sửa | Ai | Cách |
|---|---|---|
| `KB` | `scout` | Như `kb.md` mục 2-4, chỉ file có lỗi; `kb-check.py` lại, tối đa 2 vòng |
| `QUY CHUẨN` | `solution-architect` | Sửa `docs/engineering/` (thêm `BE-n` / `FE-n`) + `docs/decisions/` (skill `decision-record`) |
| `SKILL` | bạn | Sửa `.claude/skills/`, `.claude/agents/`, `.claude/commands/`, `CLAUDE.md` theo cách sửa đã duyệt; mỗi file 1 dòng báo user |
| `CODE` | không ai | Ghi 1 dòng Backlog: `/agent-team:task "<A-n>: <cách sửa> (<file:dòng>)"`, loại task ước lượng (NHỎ / VỪA / LỚN) |

Xong mỗi dòng → `Trạng thái: FIXED` (CODE: `BACKLOG`). Điền cột Sau của bảng Điểm. Commit `[lead] audit-<ngày>: <mô tả>` một dòng. Đổi quy trình / lệnh / env → ghi `release-notes.md`. `Bước: DONE`.

## 7. Báo cáo
Dòng đầu: điểm Trước → Sau từng làn, làn nào còn KHÔNG ĐẠT. Rồi tối đa 5 mục mỗi nhóm: lỗi Critical / High còn lại, file KB / quy chuẩn / skill đã sửa, số dòng Backlog. Cuối cùng đúng 1 việc user làm tiếp (≤ 2 phút), thường là chạy dòng Backlog đầu tiên.
