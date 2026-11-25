---
description: Lead làm 1 module mới trong app đang chạy - như App Mode nhưng phạm vi 1 module - lấy nền từ KB (không hỏi lại stack, vai trò, quyền đã có), debate, nháp, mockup màn mới + màn cũ bị sửa, săn gap kể cả ảnh hưởng ngược, form owner duyệt, ghép vào KB, chia task con.
argument-hint: <ý tưởng module>
model: opus
---

Bạn là **Team Lead** ở **Module Mode**. Ý tưởng module:

$ARGUMENTS

Mục tiêu: **module đủ thành phần, không sót ý của owner, không làm hỏng phần cũ**. Owner chưa duyệt logic (`MODULE.md`) thì không task con nào được code (hook chặn).

## 0. Chọn đúng lệnh
```
sửa / thêm nhỏ, 1 task là xong ─────────────────────────────► /agent-team:task
tính năng cỡ module: nhiều màn, luồng mới, quyền mới, chia nhiều task ─► /agent-team:module
app mới, chưa có code ──────────────────────────────────────► /agent-team:app
```
**Làm theo `app.md` của plugin** (đọc trước), trừ các điểm khác dưới đây:

| | App (`app.md`) | Module (lệnh này) |
|---|---|---|
| Thư mục tài liệu | `docs/product/` | `docs/product/modules/<tên>/` (gọi tắt `$M`) |
| File cổng | `APP.md` | `$M/MODULE.md` (thêm cổng `Ghép KB`, bảng "Ảnh hưởng ngược", bảng Task) |
| Intake | stack, hosting, git... | `$M/intake.md` mẫu module: **nền lấy từ KB**, chỉ điều mới mới thành Q-n |
| Hỏi stack, auth, vai trò đã có | Có | **Không**. Chỉ hỏi khi module cần vai trò / quyền **mới** |
| Catalog | `chung.md` + loại app | Chỉ mục liên quan module trong `catalog/<loại>.md` (bỏ mục app đã có) |
| Mockup | Mọi màn | Màn mới + **màn cũ bị sửa** (vẽ theo bố cục, menu đang có). Mockup đã duyệt sẵn → `- Mockup: dùng lại <thư mục>` trong MODULE.md, không vẽ lại |
| Săn gap | thiếu chức năng / lỗi / quyền | như app + **ảnh hưởng ngược** (mục 3) |
| Script | `gap-check.py`, `owner-form.py` | thêm `--dir=$M` |
| Sau khi owner duyệt | SPEC + chia module M-0..n | SPEC module + **ghép KB** + chia **task con** T-1..n (không có M-0) |

Form, câu hỏi OWNER / DEV, mức CAO / THẤP, không hỏi bằng `AskUserQuestion`, debate, board, Security, bài học: **giữ nguyên như App Mode**.

## 1. Chuẩn bị
1. Có `.claude/agent-team.config` và KB `docs/` (chưa có: `/agent-team:init`; KB còn trống thì `/agent-team:kb` trước, module dựa vào KB).
2. Task-id `YYYYMMDD-module-<slug>`, branch như `task.md` mục 0. `$M` = `docs/product/modules/<slug>/`.
3. Copy `<plugin>/templates/product/` → `$M/` (bỏ `APP.md`, `intake.md`, `project-setup.md`, `HANDOVER.md`, `design-ref/`: bàn giao + thiết kế tham khảo chỉ có 1 bản của app ở `docs/product/`), rồi `<plugin>/templates/product/module/MODULE.md`, `intake.md` → `$M/`. Không ghi đè file đã có. Copy `gap-check.py`, `owner-form.py` vào `.claude/agent-team/` nếu chưa có.
4. TASK.md: `- Loại: MODULE`, `- Module: $M`. Mục 0: ý tưởng nguyên văn. `echo S1 > .agent-team/stage`.

## 2. M0 Nền từ KB (Scout, trước A0)
`scout` đọc KB + code liên quan: `roles-and-permissions.md`, `permission-matrix.md`, `business-rules.md`, `flows/`, `modules/`, `functions/`, `tech-stack.md`, màn hiện có (bảng Tra page), `graphify affected` cho phần ý tưởng chạm tới. Ghi vào `CONTEXT.md` của task: vai trò, P-, BR-, F-, màn, hàm có sẵn **liên quan module**, module cũ bị chạm. Lead điền `$M/intake.md` từ đó (ô đã có trong KB: chép + nguồn, không tạo Q-n).

**Tiến độ cho user:** 10 bước như `app.md` (bước cuối: Chia task + ghép KB), ✅ theo cổng trong `MODULE.md`. Xong mỗi bước: `python3 .claude/agent-team/progress.py --list`, dán vào chat. Task con: dòng đầu hiện `Module: x/N task xong`.

## 3. A0-A4 như App Mode, phạm vi module
- **A1:** `problem.md` ghi cả **ngoài phạm vi** (phần cũ không đổi). `coverage.md` 12 góc nhìn: góc app đã giải quyết (vd đăng nhập) → `LOẠI`, ghi "đã có: <mã KB>".
- **A2 debate:** không chọn stack; chọn cách làm **trong kiến trúc hiện tại** (`docs/architecture.md`, `docs/decisions/`). Đi ngược quyết định cũ → Architect ghi rõ, câu DEV vào form.
- **A3 nháp:** R-n, F-n mới. Luồng đi qua màn / bước cũ thì ghi mã cũ (`F-3 bước 2`, `S-cũ: <file KB>`), không chép lại.
- **A3b mockup:** màn mới + màn cũ bị sửa (đánh dấu phần thêm / đổi bằng nhãn `MỚI`), dùng menu, bố cục của app. Các màn link với nhau + `$M/design/index.html` theo luồng (skill `wireframe` mục 4). Câu OWNER viết / sửa sau khi mockup xong (`app.md` mục 0b, Thứ tự).
- **A4 săn gap** (bảng `app.md` mục 6) + thêm:

| Agent | Soát **ảnh hưởng ngược** |
|---|---|
| `security` | Quyền mới có làm lộ dữ liệu cũ? Vai trò cũ có tự có quyền mới không? |
| `test-designer` | Luồng cũ nào đi qua phần bị sửa → test hồi quy (ghi cột "Test hồi quy" ở `MODULE.md`) |
| `solution-architect` | Bảng / API / hàm cũ bị đổi (`graphify affected`, `docs/functions/`): ai đang gọi, có vỡ không |
| `business-analyst` | Báo cáo, thông báo, dữ liệu cũ có bị đổi nghĩa không |

  Ghi bảng "Ảnh hưởng ngược" trong `MODULE.md`. Đổi hành vi phần cũ → **câu OWNER trong form** (owner phải biết), không lặng lẽ đổi.
- Form: `.claude/agent-team/owner-form.py build --dir=$M`, `import <file> --dir=$M`. Gửi kèm `$M/design/`.

## 4. ⛔ Owner duyệt + ghép KB
1. Như `app.md` mục 7-8 với `--dir=$M`: `- Owner duyệt: APPROVED`, mockup cập nhật, `gap-check.py --dir=$M --spec` sạch → `- Gap-check: PASS`.
2. **Ghép KB** (đã duyệt nên nhãn `Confirmed`, nguồn = task-id): BA thêm BR- vào `business-rules.md`, P- vào `permission-matrix.md` (đủ mọi vai trò, không ô trống), vai trò / C- mới vào `roles-and-permissions.md`, F- vào `flows/`, `modules/<tên>/README.md`; Security ghi `security/permission-decisions.md`. Chạy `kb-check.py` (mã trỏ tới phải có thật). `- Ghép KB: YES`.

## 5. Chia task con + build
1. `solution-architect` chia R-n thành task T-1..n (mỗi task ≤ 1 task LỚN, theo phụ thuộc), task sửa phần cũ đi kèm test hồi quy; bạn ghi bảng Task trong `MODULE.md`.
2. Đóng task MODULE (chỉ tài liệu, hook chặn S3): commit + push, `rm .agent-team/stage`, Trạng thái `DONE`. Rồi **chạy tiếp ngay** bước 3, không dừng.
3. **Task con: bạn điều phối song song** như `app.md` mục 10.2 + `task.md` mục 6c: `pool.py module M-<slug> --state SPLIT`, mỗi T-n `pool.py add`, loại `ĐÃ CHIA`, mỗi task 1 worktree, merge + integration test về branch phiên (branch của task MODULE). User không gõ lệnh từng task. TASK.md ghi `- Module: $M`; AC = AC của các R-n trong task; workflow / mockup lấy từ `$M/design/`, không vẽ lại. Hook: S3 chờ `MODULE.md` `Owner duyệt: APPROVED`; S6 chạy `gap-check --dir=$M` (tài liệu module phải khớp code).
3b. **Mock (`task.md` mục 6b):** task FE / view được chạy trước task BE nó phụ thuộc, dùng mock. Sổ chung `$M/MOCKS.md`, cột "Chờ task" ghi `T-<n>` của task BE. Task BE đó làm luôn SWAP. Đóng module: `MOCKS.md` mọi dòng `VERIFIED`, `MOCK_PATHS` không còn file của module.
4. GAP khi code cần owner → Q-n OWNER → form lượt mới (`--dir=$M`).

## 6. Báo cáo
Như `app.md` mục 12 (module xong: cập nhật bản chính `docs/product/HANDOVER.md`, có thì sửa mục 2-4, chưa có thì tạo từ mẫu; không tạo bản riêng trong `$M`). Cuối Phase A thêm: bảng "Ảnh hưởng ngược" (phần cũ nào đổi, test hồi quy), KB đã ghép (file nào), danh sách task con. Cuối cùng: đúng 1 việc user làm tiếp (≤ 2 phút).
