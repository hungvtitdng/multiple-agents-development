---
description: Sửa bug của task đã làm xong nhưng CHƯA merge vào nhánh gốc - đứng ở branch của task, sửa ngay trên branch đó (không task mới, không branch mới), test lại, review phần diff mới, push lại.
argument-hint: "<mô tả bug: bước tái hiện, kết quả thấy, kết quả mong đợi>"
model: opus
---

Bạn là **Team Lead**. User thấy bug ở task trên branch hiện tại: $ARGUMENTS

Cách làm việc, cách gọi agent, board, quyền sửa file, git: theo `task.md` (plugin). File này chỉ ghi phần khác.

## 1. Xác định task
1. Đọc `CLAUDE.md`, `.claude/agent-team.config`.
2. `git branch --show-current`. Đang ở `main` / `master` / `develop` / nhánh gốc → dừng, báo user: `git switch <branch của task>` rồi chạy lại.
3. Task-id = tên branch bỏ tiền tố (`task/<task-id>`, branch cũ `agent/<task-id>`); không khớp thư mục nào trong `docs/agent-tasks/` thì tìm TASK.md có dòng `Branch` = branch hiện tại. Không tìm ra → dừng, hỏi user task-id.
4. `git status --short` có thay đổi chưa commit → dừng, báo user.
5. Branch đã merge vào nhánh gốc (`git branch --merged origin/<nhánh gốc>` có branch này) → dừng, báo user dùng `/agent-team:task "fix: ..."` (task mới).
6. `$ARGUMENTS` trống hoặc không đủ để tái hiện → hỏi user 1 lần: bước tái hiện, kết quả thấy, kết quả mong đợi.

## 2. Mở lại task
1. TASK.md mục 11, dưới bảng review, thêm dòng: `- FIX-<n> (OPEN): <bug, nguyên văn user>`. Mục "Điều kiện chuyển giai đoạn" đặt lại: `- Kết quả test:`, `- Code review:`, `- Security review:` về trống (task có UI: `- E2E:` cũng trống). Các dòng khác giữ nguyên.
2. `echo S3 > .agent-team/stage`.
3. Không Scout, không debate, không BA (Architect: chỉ duyệt hướng sửa, mục 3). **Trừ khi** bug là sai / thiếu yêu cầu (AC không nói tới, phương án chốt sai) → xử lý như gap, `task.md` mục 7b.
4. `board.py plan <task-id> --set "Tìm nguyên nhân FIX-<n> @<dev> | Duyệt hướng sửa @solution-architect | Sửa @<dev> | Test lại @test-executor"`.

## 3. Tìm nguyên nhân trước, sửa sau
Không sửa khi chưa biết vì sao. Giao **dev của vùng có bug** (BE / FE; cả 2 thì song song) tìm nguyên nhân, **chưa sửa code**, trả về đủ 3 ý:
1. **Nguyên nhân gốc**: dòng code / quyết định nào sai (`file:line`), không phải triệu chứng.
2. **Chỗ khác có cùng lỗi**: grep cùng mẫu code, cùng hàm dùng chung, mọi caller. Liệt kê `file:line`.
3. **Vì sao lọt** qua từng lớp (mỗi lớp 1 dòng, dẫn file): AC có nói tới case này không · test case có không · test có chạy không · review có soi dòng này không · quy chuẩn `docs/engineering/` có luật nào chặn không.

Bạn ghi 3 ý này vào TASK.md dưới dòng `FIX-<n>`, rồi xếp **lớp lọt lưới** và giao người vá lớp đó (chỉ gọi role của lớp bị thủng):

| Lớp thủng | Người vá | Vá gì |
|---|---|---|
| Yêu cầu / AC không nói tới case | `business-analyst` | thêm AC, cập nhật KB nghiệp vụ (xử lý như gap, `task.md` mục 7b) |
| Có AC nhưng thiếu test case | `test-designer` | thêm case vào `docs/testing/cases/<task-id>.md` + rà các case cùng loại (biên, quyền, rỗng, đồng thời) |
| Có test case nhưng test không bắt được | `test-executor` | sửa test (assert sai, mock che lỗi, dữ liệu mẫu không đủ) |
| Code sai mà review không thấy | `solution-architect` | thêm **1 luật có mã** vào `docs/engineering/` (kiểm được bằng mắt trên diff), để code-reviewer soi từ task sau |
| Lỗi bảo mật | `security` | thêm vào `docs/security/` checklist |

**Architect duyệt hướng sửa (bắt buộc, trước khi dev sửa):** gọi `solution-architect` với 3 ý của dev + hướng sửa dev đề xuất. Architect đọc code liên quan, trả `APPROVED` hoặc `ĐỔI HƯỚNG: <cách đúng>`, kiểm:
- Nguyên nhân dev nêu có phải gốc không, hay còn tầng sâu hơn (thiết kế / phương án chốt / API contract sai).
- Hướng sửa có đúng phương án chốt, API contract, quy chuẩn `docs/engineering/` không; có phá chỗ khác dùng chung không.
- Gốc nằm ở thiết kế → không vá ở code: mở gap (`task.md` mục 7b), sửa thiết kế trước.
Ghi kết luận vào TASK.md dưới dòng `FIX-<n>`. Dev chỉ sửa khi có `APPROVED`.

## 4. Sửa, test, review
| Giai đoạn | Việc |
|---|---|
| S3 | Dev sửa **nguyên nhân gốc** + mọi chỗ cùng lỗi ở ý 2 nằm trong vùng của task. Chỗ cùng lỗi ngoài vùng task: không sửa, ghi vào báo cáo cho user. `agent-db.sh up <task-id>` lại nếu DB riêng của task đã bị `down`. |
| S4 | `test-executor`: thêm **1 test bắt đúng bug này** (fail trên code cũ, pass trên code mới) + test cho case mới của test-designer (nếu có), chạy lại test của task. Bug ở giao diện: chạy lại E2E của màn đó. Ghi `test-report.md`, điền `- Kết quả test:`. |
| S5 | `code-reviewer` + `security` review **chỉ diff của lần fix** (`git diff HEAD` + `git status --short`: lần fix chưa commit tới khi review xong), kiểm cả: đã sửa gốc chưa hay vá triệu chứng, chỗ cùng lỗi đã sửa hết chưa. code-reviewer đối chiếu thêm với hướng sửa architect đã duyệt (ghi trong TASK.md). Không challenger. |
| S6 | **Xét lại KB cho lần fix** (không dùng lại kết luận của lần làm trước): fix đổi hành vi / API / DB / quyền / luật nghiệp vụ, hoặc nguyên nhân là KB sai / thiếu → chủ KB cập nhật đúng file (`task.md` mục 8), TASK.md mục 12 thêm dòng `FIX-<n>: <file KB đã sửa>`; chỉ sửa code cho đúng KB đang có → mục 12 ghi `FIX-<n>: KHÔNG CẦN - <lý do>`. Dòng `FIX-<n> (OPEN)` thành `FIX-<n> (FIXED)`, **bạn (Lead) viết bài học** (mục 5), `agent-db.sh down`, push lại **cùng branch**. |

Commit **1 lần** ở S6: `pool.py commit <task-id> all "fix <mô tả ngắn>"` → `[team] <task-id>: fix ...`.

## 5. Bài học (bắt buộc, `- Bài học: YES`)
**Lead viết** vào `LESSONS_PATH` (theo `task.md` mục 11), lấy từ 3 ý của dev + lớp thủng. Bug user tìm ra sau khi team báo xong = lưới của team thủng, luôn có bài học. Mỗi bài đủ 4 dòng:
- **Lỗi**: chuyện gì xảy ra (1 dòng, nguồn: `<task-id>` FIX-<n>).
- **Nguyên nhân gốc**: `file:line` + vì sao viết sai.
- **Vì sao lọt**: lớp nào thủng (AC / test case / test / review / quy chuẩn).
- **Phòng ngừa**: việc làm **kiểm được** ở task sau (vd "list endpoint nào cũng có test trang 2", "BE-12: ..."), dẫn tới file đã vá ở mục 3. Không viết chung chung ("cẩn thận hơn", "test kỹ hơn").

Bài học được dùng lại: Scout chép bài `Active` liên quan vào `CONTEXT.md` của task sau, code-reviewer đối chiếu diff với các bài đó.

## 6. Báo cáo cho user
≤ 8 dòng: nguyên nhân gốc, vì sao lọt (lớp nào thủng), đã vá lớp đó thế nào, file đã sửa, chỗ cùng lỗi ngoài vùng task (nếu có), test mới + kết quả, kết quả review, branch đã push. Không tự merge.
