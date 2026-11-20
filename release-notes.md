# Release notes - 20/11/2026 (v0.15.0)

## Thay đổi
- **App Mode hỏi 1 lần:** BA viết nháp trọn app theo đề xuất của team (`Assumption (Q-n)`), A4 săn gap trên nháp, rồi mới build form. Lượt 2 chỉ cho câu "không", ô trống, góp ý đổi logic.
- `owner-form.py build` từ chối khi `APP.md` chưa `Challenger: DONE`.
- Sửa theo: `app.md` (0, 0b, A2-A4), `resume.md`, `business-analyst`, `templates/product/APP.md`, README.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`, khởi động lại Claude Code.
- Project đã init: copy lại `scripts/owner-form.py` → `.claude/agent-team/` (chmod +x).
- App đang dở chưa có `Challenger: DONE`: chạy A3 nháp + A4 trước rồi mới `build`.

# Release notes - 20/11/2026 (v0.14.1)

## Thay đổi
- Template mới `templates/product/project-setup.md`: dev điền stack, DB, hạ tầng, env, deploy.
- `init` (dự án mới) copy phiếu vào `docs/product/`; `app` A0 đọc phiếu, ô đã điền không tạo Q-n `DEV`.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`, khởi động lại Claude Code.
- Project đã init: copy `templates/product/project-setup.md` → `docs/product/`, điền trước khi chạy `/agent-team:app`.

# Release notes - 20/11/2026 (v0.14.0)

## Thay đổi
- **App Mode: 1 form, 2 mục.** `owner-form-<n>.xlsx` có mục **A. Owner: nghiệp vụ** (cột `Owner duyệt / góp ý`) và **B. Dev: kỹ thuật** (cột `Dev duyệt / góp ý`). Mục không có câu thì không in.
- **Không hỏi dev bằng `AskUserQuestion` nữa** (trước đây câu `DEV` như SMTP, hosting, stack bị hỏi ngay giữa Phase A). Mọi câu ghi sổ `questions.md`, đi form. Ngoại lệ: `/agent-team:init`.
- Câu kỹ thuật làm đổi logic (vd SMTP → cách quên mật khẩu) → BA tách 2 câu: câu logic cho owner (đề xuất có đường dự phòng) + câu hạ tầng cho dev.
- Câu `DEV` bắt buộc có `Đề xuất của team` (Architect đề xuất). Trạng thái mới `CHỜ DEV`. Dev ghi "không" → Architect đề xuất lại lượt sau.
- `gap-check.py`: câu DEV thiếu đề xuất → thiếu; `CHỜ DEV` hợp lệ; câu CAO `CHỜ DEV` → thiếu.
- `import` ghi `Owner: ...` hoặc `Dev: ...` theo người trả lời; bỏ qua dòng tên mục / tiêu đề.
- Sửa theo: `app.md` (mục 0, 0b, A0, A2, A3, báo cáo), `resume.md`, `business-analyst`, `templates/product/questions.md`, `intake.md`, `README.md` (product), README, `docs/design.md`. Mẫu `examples/owner-form-sample.xlsx` / `.html` có 2 mục.
- `tests/test_owner_form.py`: 54 case (thêm mục Dev, CHỜ DEV, câu DEV thiếu đề xuất, chỉ có câu DEV).

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`, khởi động lại Claude Code.
- Project đã init: copy lại `scripts/owner-form.py` và `scripts/gap-check.py` → `.claude/agent-team/` (chmod +x).
- App đang làm dở: không đổi cột `questions.md`. Câu `DEV` đang `MỞ` chưa có đề xuất → bổ sung `Đề xuất của team`, nếu không `owner-form.py build` từ chối.
- Không có key config mới.

# Release notes - 20/11/2026 (v0.13.0)

## Thay đổi
- **App Mode: câu nghiệp vụ gửi owner bằng form, không hỏi dev.** Trước đây Lead hỏi bằng `AskUserQuestion`, nên người chạy lệnh (thường là dev) phải trả lời thay owner. Nay `questions.md` có cột `Ai trả lời`: `DEV` (stack, hosting, git) hỏi người chạy lệnh; `OWNER` (nghiệp vụ, quy tắc, tiền, quyền, mặc định) gom vào form.
- **Script mới `scripts/owner-form.py`** (copy vào `.claude/agent-team/`, cần `gap-check.py` cùng thư mục, không cần thư viện ngoài, chạy được Python 3.9+):
  - `build` → `docs/product/owner-form-<n>.xlsx`: tên app + 1 bảng `# · Câu hỏi · Đề xuất của team · Owner duyệt / góp ý` (cột cuối để trống, mã câu ở cột E ẩn). Gồm câu `OWNER` đang `MỞ` / `CHỜ OWNER` (CAO lên đầu) + mặc định chưa chốt. Đổi trạng thái sang `CHỜ OWNER`. Câu thiếu đề xuất → từ chối sinh form. Mở bằng Excel, Numbers hoặc tải lên Google Sheet.
  - `import <file .xlsx|.csv>`: `OK` / đồng ý / duyệt → `ĐÃ TRẢ LỜI` (mặc định: `GIỮ`); `không` / không cần / bỏ → `MỞ`, BA đề xuất lại lượt sau (mặc định: `BỎ`); chữ khác → góp ý ghi nguyên văn (mặc định: `KHÁC` + ghi chú); để trống → vẫn chờ. Đọc được file Excel / Google Sheet lưu lại (sharedStrings) và CSV; mất cột mã thì khớp theo câu hỏi.
- **Mỗi câu gửi owner chỉ 1 đề xuất best solution** của team (kèm 1 câu "vì sao"), không liệt kê phương án khác. Owner ghi OK hoặc góp ý.
- `templates/product/questions.md` thêm cột `Đề xuất của team`, `Vì sao`, `Ai trả lời`; trạng thái mới `CHỜ OWNER`. `defaults.md`: `Mục` viết thành câu hỏi, trạng thái `CHỜ OWNER`.
- `app.md`: gom ít lượt nhất (lượt 1 = câu A0, A1 + toàn bộ mặc định, gửi trước khi BA viết yêu cầu; lượt sau chỉ câu owner ghi "không" + câu mới từ A4). Chờ owner: task `BLOCKED`, A2 kiến trúc làm song song. **Chốt logic trước, wireframe sau**: owner không xem wireframe, chốt bằng form là đủ; A3b vẽ sau khi logic chốt.
- `gap-check.py`: câu `OWNER` thiếu đề xuất → thiếu; câu CAO `CHỜ OWNER` hoặc `GIẢ ĐỊNH` → thiếu.
- `resume.md`: `/agent-team:resume <task-id> <file trả lời>` tự `import` rồi làm tiếp. `business-analyst`: mỗi câu trả về Lead đủ 5 trường (câu hỏi tình huống, đề xuất, vì sao, mức, ai trả lời); owner ghi "không" thì đề xuất cách khác.
- Mẫu: `examples/owner-form-sample.xlsx` (sinh bằng script), `examples/owner-form-sample.html` (bản xem trên trình duyệt).
- Test mới `tests/test_owner_form.py` (43 case: build, import Excel / CSV, lượt 2, mất cột mã, lỗi dữ liệu, đọc chữ owner, gap-check).

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`, khởi động lại Claude Code.
- Project đã init: copy `scripts/owner-form.py` → `.claude/agent-team/owner-form.py` (chmod +x). Copy lại `templates/claude-md-section.md` vào mục "Agent Team" của `CLAUDE.md`.
- App đang làm dở: thay bảng trong `docs/product/questions.md` bằng bảng mới của `templates/product/questions.md` (thêm 3 cột `Đề xuất của team`, `Vì sao`, `Ai trả lời`), nếu không `owner-form.py build` báo "bản cũ".
- Không có key config mới.

# Release notes - 19/11/2026 (v0.12.0)

## Thay đổi
- **Responsive xuyên suốt, nguồn duy nhất là `VIEWPORTS`** (config, vd `"375 768 1280"`; chỉ máy tính `"1280"`):
  - Wireframe (skill `wireframe`, `ui-designer`): có chiều rộng < 768 thì **mọi màn bắt buộc có tab `Mobile`** (`data-s="mobile"`, 375px). `gap-check.py` báo thiếu (khi `intake.md` ghi `Responsive: CÓ` hoặc `VIEWPORTS` có < 768).
  - Test case (skill `test-case-design`, `test-designer`): trạng thái × chiều rộng; kiểm không cuộn ngang, nút chính ≥ 44px, menu ☰, bảng không làm trang cuộn ngang. Mẫu test case thêm cột `Chiều rộng`.
  - `frontend-dev`: dùng breakpoint của dự án, không width cố định cho khung nội dung, thêm `data-testid` khi cần cho E2E.
  - `code-reviewer`: lỗi responsive = High, đối chiếu ảnh E2E.
  - App Mode: `intake.md` thêm `Responsive`, catalog hỏi bằng tình huống kèm 375 / 768 / 1280px; A5 ghi `VIEWPORTS`; M-0 dựng Playwright; module cuối **M-E2E** chạy lại toàn bộ luồng "1 ngày của vai trò" ở mọi chiều rộng.
- **E2E trình duyệt: `agent-db-clone.sh e2e <task-id> [args]`**: chạy app (`APP_START_CMD`) trong container `APP_SERVICE` nối DB clone, mở cổng `E2E_PORT`, chờ app lên; FE tách repo thì chạy `E2E_FE_START_CMD` trên máy (nhận `API_URL`); rồi chạy `E2E_CMD` trên máy với `BASE_URL`, `VIEWPORTS`, `EVIDENCE_DIR=docs/testing/evidence/<task-id>/`, `TASK_ID`; xong (pass hay fail) đều tắt app và FE. Exit code = exit code của E2E.
- Skill `test-automation` mục 1b: khung `playwright.config.ts` (mỗi chiều rộng 1 project `vp-<rộng>`), helper `shot()` (ảnh `<TC>-<trạng thái>-<rộng>.png`) và `expectResponsive()`, test mẫu. `automation-guide.md` thêm mục E2E.
- **Guard S5:** TASK.md thêm dòng `- E2E:` (PASS / N/A). Chặn khi chưa điền, khi `UI mockup: YES` mà ghi `N/A`, hoặc PASS mà thiếu ảnh ở một chiều rộng trong `VIEWPORTS`. Role chỉ đọc được chạy `agent-db-clone.sh e2e`.
- Test: `test_guard.py` thêm 7 case E2E (296), case "S5 đủ" cũ thêm `E2E: N/A`; `test_gap_check.py` thêm 5 case responsive (43). `agent-db-clone.sh e2e` đã chạy thử với `docker` giả lập: pass, fail (vẫn tắt app), FE tách riêng, thiếu config.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`, khởi động lại Claude Code.
- **Key mới trong `.claude/agent-team.config`:** `VIEWPORTS`, `E2E_CMD`, `APP_START_CMD`, `APP_PORT`, `E2E_PORT`, `E2E_FE_START_CMD`, `E2E_FE_URL` (xem `templates/agent-team.config.example`). Lệnh có `$` để trong nháy **đơn** vì config được nạp bằng shell. Copy lại `scripts/agent-db-clone.sh` → `.claude/agent-team/agent-db-clone.sh`.
- **Cài Playwright** trong repo FE (mỗi dự án, không tự cài): `npm i -D @playwright/test && npx playwright install chromium`. Cần `curl` trên máy (chờ app lên).
- Task đang làm dở: thêm dòng `- E2E: N/A` (hoặc PASS khi đã có ảnh) vào TASK.md, nếu không hook chặn sang S5. Copy lại `templates/TASK.md`.
- Chưa có: so ảnh tự động (visual diff) giữa màn thật và wireframe; code-reviewer so bằng mắt.

# Release notes - 19/11/2026 (v0.11.0)

## Thay đổi
- **App Mode: lệnh mới `/agent-team:app <ý tưởng>`** làm cả app từ 1 ý tưởng. Phase A chỉ tài liệu (S1-S2): A0 Intake → A1 Vấn đề + 12 góc nhìn → A2 Giải pháp (debate như `run`) → A3 Nghiệp vụ → A3b Wireframe → A4 Săn gap → cổng owner → A5 Chia module. Phase B: M-0 khung project trong chính task app (S3-S6), M-1..n mỗi module 1 `/agent-team:run`, lần lượt.
- **Được hỏi owner ở Phase A** (ngoại lệ của "không hỏi user"): chỉ Lead hỏi, bằng `AskUserQuestion` (≤ 4 câu/lượt, có lựa chọn đề xuất, hỏi bằng tình huống). Câu mức CAO phải được trả lời; mức THẤP được giả định. Agent vẫn không hỏi, trả câu hỏi về Lead. Owner không phải đọc tài liệu: chỉ bấm chọn, xem wireframe và sơ đồ flow.
- **Tài liệu sản phẩm `docs/product/`** (mẫu `templates/product/`, cột cố định): `APP.md` (cổng + module), `brief.md` (ý owner B-n), `intake.md`, `questions.md` (Lead) · `problem.md`, `coverage.md`, `defaults.md`, `requirements.md`, `flows.md`, `data.md` (BA) · `screens.md`, `design/mockup-*.html` (ui-designer).
- **`catalog/`** mặc định theo loại app để bù phần owner không nghĩ tới: `chung.md` (21 mục mọi app), `quan-ly-noi-bo.md` (14 mục), `dat-lich.md` (17 mục). Mỗi mục có câu hỏi tình huống + lựa chọn. Owner chỉ chọn GIỮ / BỎ / KHÁC.
- **Script mới `scripts/gap-check.py`** (copy vào `.claude/agent-team/gap-check.py`): kiểm intake, ý owner B-n chưa có yêu cầu, R-n không có nguồn, câu hỏi CAO còn mở, 12 góc nhìn, mặc định owner chưa chọn, flow thiếu nhánh lỗi, màn mồ côi / chưa có wireframe, vai trò × màn, Dữ liệu × CRUD, vòng đời trạng thái. `--gate` kiểm thêm `APP.md` (Intake, Challenger, Owner duyệt).
- **`docs/product/SPEC.md`: toàn bộ tài liệu app trong 1 file**, sinh bằng `gap-check.py --spec` (không sửa tay): ý tưởng, mục tiêu, stack, yêu cầu, flow, màn + link wireframe, dữ liệu, mặc định, câu hỏi đã hỏi owner, 12 góc nhìn, bảng truy vết B → R → S (ý chưa có yêu cầu ghi **CHƯA CÓ**), link KB + quyết định, bảng module. `--spec-check`: SPEC phải khớp tài liệu hiện tại.
- **Tài liệu app luôn đúng khi build (Phase B):** module đổi yêu cầu / có GAP → BA, ui-designer sửa `docs/product/`; S6 của module: Lead cập nhật trạng thái module + sinh lại SPEC.
- **Guard:** loại `APP`; sang S3 với task APP thì guard chạy `gap-check.py --gate --spec-check`, thiếu gì báo đó. Có `docs/product/APP.md` thì mọi task khác bị chặn sang S3 khi chưa `Owner duyệt: APPROVED`, và **mọi task bị chặn sang S6** khi tài liệu app thiếu hoặc SPEC.md cũ hơn tài liệu. Chủ ghi `docs/product/`: BA (problem, coverage, defaults, requirements, flows, data), ui-designer (screens, design/), còn lại chỉ Lead.
- **Mỗi task phải cập nhật tài liệu thật, không chỉ khai:**
  - Guard S6: `Cập nhật KB: YES` mà không có file KB nào trong `docs/` đổi so với `BASE_BRANCH` (git diff + file mới, gồm cả chưa commit; không tính `agent-tasks/`, `testing/`, `LESSONS.md`, `SPEC.md`) → chặn. Không xác định được nhánh gốc thì bỏ qua.
  - `code-reviewer`: có `docs/product/` thì hành vi trong diff phải khớp R-n / flow / màn / dữ liệu; lệch hoặc hành vi mới không có R-n = High, kể cả task sửa bug.
- Tài liệu: `templates/kb/README.md` (bảng chủ ghi thêm `product/`), `resume.md` (làm tiếp task APP: suy bước A0-A5 từ `docs/product/`), `ask.md` (đọc `SPEC.md` trước), README (bảng gate + guard), `docs/design.md` mục 19.
- Agent: `business-analyst`, `ui-designer` thêm chế độ App Mode; `challenger` thêm chế độ Phase A (chỉ đọc ý tưởng gốc, tự liệt kê app cần gì).
- `run.md`: ý tưởng cả app → chuyển sang `/agent-team:app`; task module lấy AC từ `R-n`. `init.md`: dự án mới chưa có git → `git init -b main`; không có remote → `PUSH=0`.
- Test mới `tests/test_gap_check.py` (38 case), `tests/product_fixture.py`; `test_guard.py` thêm 36 case (App Mode + kiểm KB thật).
- Xoá thư mục `Claude outputs/` bị commit nhầm ở v0.10.0 (bản cũ của `board.py`, `report-sample.html`).

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`, khởi động lại Claude Code.
- **Key mới trong `.claude/agent-team.config`**: `PUSH` (`1` = có remote, mặc định; `0` = repo chỉ ở máy, không fetch/push). Project đã init: thêm `PUSH=1`.
- Project đã init: copy `scripts/gap-check.py` → `.claude/agent-team/gap-check.py` (chmod +x); copy lại `templates/TASK.md`; thay mục "Agent Team" trong `CLAUDE.md` bằng `templates/claude-md-section.md`.
- Chưa có: `REPORT.html` cho cấp app (owner duyệt bằng `AskUserQuestion` + mở file wireframe), test E2E Playwright (dự kiến v0.12.0).

# Release notes - 19/11/2026 (v0.10.0)

## Thay đổi
- **Board chat SQLite** `scripts/board.py` (copy vào `.claude/agent-team/board.py`), dữ liệu ở `.agent-team/board.db`. Agent tự `read` (tóm tắt lượt trước + toàn bộ lượt đang mở) và `post` bằng tên mình; `@role` = phải trả lời (`status` liệt kê @ chưa trả lời). Chỉ Lead `open/close/summary/export`. Cuối task `export` ra `docs/agent-tasks/<task-id>/board/DEBATE.md`. Lead không còn dán lại kết quả lượt trước cho agent. Điểm chấm vẫn chỉ trả riêng về Lead.
- **8 skill chung** trong `skills/`: `debate-board`, `acceptance-criteria`, `test-case-design`, `security-review` (mẫu grep Rails/JS), `migration-safety`, `test-automation`, `code-review`, `decision-record`. Agent có thêm tool `Skill`, mỗi agent liệt kê skill của mình và chỉ nạp khi cần. Kiến thức riêng của dự án vẫn ở KB `docs/` (không tạo skill trùng).
- Guard: role chỉ được `board.py post|read|status`, post bằng `--role` đúng tên mình, không gọi board qua biến; challenger không dùng board; thân heredoc của `board.py post` không bị soi như lệnh.
- Skill chỉ chứa **nguyên tắc chung, không gắn framework**. Cách làm riêng của dự án nằm trong KB, 3 file khung mới: `docs/security/review-patterns.md` (Security), `docs/database/migration-rules.md` (Architect, backend-dev), `docs/testing/automation-guide.md` (Test Design/Execution); `engineering/review-checklist.md` thêm mục "Mẫu tìm lỗi theo stack". Agent đọc file dự án trước, thiếu thì làm theo nguyên tắc chung và đề xuất bổ sung.
- Scout (`/agent-team:init`, `/agent-team:kb`) viết nháp các file trên theo stack của dự án (nhãn `Observed`, có `file:dòng`). `kb-check.py` kiểm thêm 3 file mới.
- Ví dụ nội dung Rails + JS/TS (không thuộc plugin): `examples/rails-js/`.
- `run.md`, `resume.md`, `init.md`, `POST.md` (bỏ dòng điểm), `SUMMARY.md`, mục CLAUDE.md cập nhật theo board mới. Task cũ có file `board/S*-R*` vẫn resume được.
- **Code graph chuyển hẳn sang [Graphify](https://github.com/Graphify-Labs/graphify)** (tree-sitter, ~40 ngôn ngữ, tới mức hàm, không gọi LLM khi chỉ đọc code). Xoá `scripts/code-graph.py` tự viết và `tests/test_code_graph.py`. Lệnh: role `graphify explain|affected|query|path|god-nodes`; Lead `graphify update` (+ `merge-graphs` khi nhiều repo → `graphify-out/merged-graph.json`, query thêm `--graph`). Guard chặn với mọi người: `extract` (gọi LLM), `install`, `hook install`, `claude install`, `watch`, `graphify-mcp`. Thư mục output `code-graph-out/` đổi thành `graphify-out/`.
- **GAP khi đang làm**: backend-dev, frontend-dev, test-executor không còn tự chọn + ghi `Assumption` khi thiếu thông tin. Họ dừng đúng phần đó, trả **GAP** cho Lead (mẫu cuối `POST.md`). Lead mở debate nhỏ trên board với đúng người (nghiệp vụ: BA + Test Design; thiết kế: Architect + Test Design; quyền/dữ liệu: + Security), tối đa 2 lượt mỗi gap, chốt rồi giao lại. Mỗi gap bắt buộc ghi **vì sao S1-S2 bỏ sót** (AC thiếu case / KB sai-thiếu / CONTEXT thiếu / phương án chưa tính / yêu cầu mơ hồ) và **bài học** vào `LESSONS_PATH` ngay. ≥ 3 gap trong một task → quay lại S2 debate toàn bộ (`run.md` mục 7b).
- TASK.md thêm mục 14 "Gap phát hiện khi làm" và dòng `- Gap còn mở:`; hook chặn sang S5 khi chưa `Gap còn mở: 0`.
- **Debate hỏi WHY trước, quyết sau.** Lead chốt team debate (`board.py team`). Sau lượt đề xuất: mỗi role đặt ≥ 2 `WHY @role:` → người bị hỏi `RE WHY-n:` có bằng chứng → mọi thành viên `AGREE` / `DISAGREE WHY-n: <vì sao>` (bắt buộc lý do). Trả lời mới thì biểu quyết lại. WHY chỉ đóng khi **cả team** (trừ người trả lời) đồng ý; không giới hạn số lượt. Giằng co (≥ 2 lần trả lời): Lead `board.py why-close --as ruling|assumption`, board ghi người không đồng ý; Security không đồng ý thì không đóng được. Chấm điểm chỉ sau khi hết WHY.
- `board.py`: lệnh `team`, `whys`, `why-close`; `status` liệt kê WHY còn nợ trả lời / biểu quyết; `export` có bảng WHY. Guard: role được `whys`, không được `team`/`why-close`; **chặn sang S3 khi board còn WHY chưa thống nhất**. Agent debate (BA, Architect, TA, Test Design, Security) có danh sách câu hỏi WHY thay cho "Góc nhìn khi debate". TASK.md thêm mục 7b "WHY đã thống nhất".
- **Migration chỉ sinh bằng generator trong container**: `agent-db-clone.sh generate <task-id> <Tên> [args]` chạy `MIGRATION_GEN_CMD` trong container app (`exec` nếu đang chạy, không thì `run --rm`), báo file mới. Guard chặn **mọi người** tự tạo / đổi tên / chép file vào `MIGRATION_PATHS`; Edit file đã sinh vẫn được. Script chặn version trùng trước `generate`, `migrate`, `verify`.
- **Báo cáo task dạng dashboard** `board.py report <task-id>` → `REPORT.html` (gửi client, tự chứa, sáng/tối, xem được trên điện thoại, in được) + `REPORT.md`. Đầu trang là **bảng giả định tô đỏ** (xếp theo mức ảnh hưởng: team đã chọn, phương án khác, ưu/nhược, ảnh hưởng nếu sai, client chọn Đúng/Sai + nút Copy câu trả lời); **bảng so sánh phương án** (cột = phương án: mô tả, ưu, nhược, rủi ro, điểm từng tiêu chí, tổng, kết luận); ô kết quả; timeline debate; thẻ WHY. TASK.md mục 2 thêm cột (phương án khác, ưu, nhược, ảnh hưởng nếu sai, mức ảnh hưởng, client xác nhận), mục 3 ghi theo dòng `Mô tả / Ưu / Nhược / Rủi ro / Kết luận`. Client trả lời Sai → mở GAP + bài học.
- Bản Markdown `REPORT.md`: kết quả (từ TASK.md), số liệu debate theo role, diễn biến từng lượt, bảng WHY (kết luận, ai đồng ý / không đồng ý kèm lý do), phương án, bảng điểm, phán quyết, giả định, gap, test, review. Lead chạy sau khi chốt solution và khi đóng task. Mẫu: `examples/report-sample.md`. Board lưu thêm lịch sử biểu quyết (`vote_log`).
- **Workflow + wireframe cho mỗi task (VỪA/LỚN)**: agent mới **`ui-designer`** (sonnet, chỉ vào team khi task có UI) vẽ wireframe **đen trắng, đủ chức năng và trạng thái** (bình thường, rỗng, đang tải, lỗi, không có quyền) → `design/mockup-<màn>.html`. BA vẽ `design/workflow.md` + `state.md`, Architect vẽ `design/sequence.md` (Mermaid). Cả team hỏi WHY vào thiết kế. FE code đủ chức năng của wireframe nhưng dùng màu, font, component của dự án; Code Reviewer coi thiếu chức năng/trạng thái là High; Test Design có test cho mỗi nhánh/trạng thái. Skill mới `wireframe`, `diagrams`.
- Guard: chỉ đúng role ghi đúng file trong `design/`; gate S3 cần `- Workflow:` và `- UI mockup:` (`YES` thì file phải tồn tại, hoặc `N/A`).
- REPORT.html thêm phần **Thiết kế**: sơ đồ **vẽ sẵn thành SVG** khi chạy report (không cần internet khi mở; cần Mermaid CLI `mmdc`, cache ở `.agent-team/mermaid-cache/`), wireframe nhúng xem trực tiếp, client chọn Đúng ý / Chưa đúng từng mục; nút Copy câu trả lời gom cả giả định và thiết kế. Mẫu: `examples/design-sample/`, `examples/report-sample.html`.
- Test mới `tests/test_board.py` (21 case, có 16 post song song); `test_guard.py` thêm 16 case board.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`, khởi động lại Claude Code.
- Project đã init: copy `scripts/board.py` → `.claude/agent-team/board.py` (chmod +x); copy lại `templates/POST.md`, `SUMMARY.md`; thay mục "Agent Team" trong `CLAUDE.md` bằng `templates/claude-md-section.md`. Hoặc chạy lại `/agent-team:init`.
- Project đã init: copy 3 file khung mới từ `templates/kb/` vào `docs/` (không ghi đè), thêm mục "Mẫu tìm lỗi theo stack" vào `docs/engineering/review-checklist.md`, rồi chạy `/agent-team:kb` để Scout điền. Dự án Rails có thể lấy nháp từ `examples/rails-js/`.
- **Cài Graphify** (mỗi máy, đã thử bản 0.9.112; tên gói có **2 chữ y**, uv tự tải Python 3.11):
```
uv tool install --python 3.11 graphifyy==0.9.112
```
- **ENV mới** trong `~/.claude/settings.json` mục `env`: `GRAPHIFY_BACKEND=none` (không gọi LLM), `GRAPHIFY_QUERY_LOG_DISABLE=1` (không ghi log câu hỏi vào `~/.cache`).
- **Không chạy** `graphify install`, `graphify hook install`, `graphify claude install` (đụng hook guard của agent-team).
- Project đang dùng code graph cũ: xoá `.claude/agent-team/code-graph.py` và thư mục `code-graph-out/`; thêm `graphify-out/` vào `.gitignore` của **mọi repo** trong `REPOS`; chạy `graphify update .` để build lần đầu.
- Task đang làm dở (tạo trước bản này): thêm dòng `- Gap còn mở: 0` vào mục "Điều kiện chuyển giai đoạn" của TASK.md, nếu không hook sẽ chặn sang S5. Copy lại `templates/TASK.md`, `POST.md` vào `.claude/agent-team/templates/` của project.
- **Key mới trong `.claude/agent-team.config`**: `MIGRATION_PATHS` (vd `db/migrate`), `MIGRATION_GEN_CMD` (vd `bin/rails generate migration`), `MIGRATION_GEN_USER` (trống, hoặc `host` để file sinh ra thuộc user máy thay vì root). Project đã init: thêm 3 dòng này (xem `templates/agent-team.config.example`), copy lại `agent-db-clone.sh` vào `.claude/agent-team/`. Container app phải mount source code để file sinh ra xuất hiện trong repo.
- **Cài Mermaid CLI** (máy chạy `board.py report`, để sơ đồ hiện thành hình): `npm i -g @mermaid-js/mermaid-cli` (lần đầu tải Chromium). Không cài thì báo cáo hiện sơ đồ dạng văn bản.
- Task đang làm dở: thêm `- Workflow: N/A` và `- UI mockup: N/A` (hoặc YES khi đã có file) vào TASK.md, nếu không hook chặn sang S3. Copy lại `templates/TASK.md`.
- Ngoài 2 ENV của Graphify, không có key mới. `.agent-team/` đã gitignore nên `board.db` không bị commit.
- Kiểm tra subagent dùng được skill: README mục "Kiểm tra sau khi cài", bước 4.

# Release notes - 02/11/2026 (v0.9.4)

## Thay đổi
- **Sửa init không dựng đủ KB / không đọc sâu logic.** Nguyên nhân: Scout thiếu tool `Edit` nên không điền được khung đã có; một Scout đọc cả dự án; không chỉ cách đọc logic; có lối thoát "quá dài thì báo user"; không ai kiểm đủ hay chưa.
- `scout`: thêm `Edit`, phải `Read` khung trước khi điền; thêm bảng cách đọc logic (routes/controller → API, service/job → luồng nghiệp vụ, model → validation/trạng thái, policy → quyền, migration → DB, test → quy tắc); mỗi quy tắc `BR-<tên>-<n>` kèm `file:dòng`; mỗi file có `verified-at: <commit>` và mục "Phạm vi đã quét / Chưa quét".
- Lệnh mới `/agent-team:kb [--check | <module>]`: Bản đồ → nhiều Scout song song theo mảng (mỗi file KB chỉ một Scout ghi) → Scout tổng hợp nghiệp vụ → `kb-check.py` → gọi lại Scout cho file còn thiếu (tối đa 2 vòng); không giấu phần chưa quét. `init` dùng chung quy trình này.
- Script mới `scripts/kb-check.py` (copy vào `.claude/agent-team/kb-check.py`): báo file KB nào còn là khung. Role chỉ đọc chạy được (hook cho phép); Lead dùng để kiểm sau init.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`, khởi động lại Claude Code.
- Project đã init: chạy `/agent-team:kb` (đang có task thì đóng task / xoá `.agent-team/stage` trước).

# Release notes - 02/11/2026 (v0.9.3)

## Thay đổi
- Sửa mô tả plugin (`plugin.json`) còn ghi "Đội 12 agent" của bản cũ: nay là Lead + 11 agent theo thiết kế mới.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`, khởi động lại Claude Code.

# Release notes - 02/11/2026 (v0.9.2)

## Thay đổi
- Lệnh mới `/agent-team:ask <câu hỏi>`: hỏi về logic dự án, chỉ đọc, không tạo task. Lead chọn người trả lời (nghiệp vụ → business-analyst, kiến trúc/API/DB → solution-architect, test → test-designer, bảo mật → security, câu đơn giản Lead tự trả lời, xuyên nhiều mảng → 2 role song song rồi gộp).
- Nguồn theo thứ tự: KB `docs/` → `LESSONS.md` → `TASK.md` các task trước → code (`file:dòng`, code-graph). Mỗi ý có nguồn và nhãn `Verified/Unverified/Assumption`. KB lệch code thì tin code và nêu "KB nên cập nhật" (không tự sửa). Không có nguồn thì nói thẳng.
- Không cần key hay config mới. Không sửa guard (các role trả lời vốn chỉ đọc).

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`, khởi động lại Claude Code.
- Project đã init: thêm câu về `/agent-team:ask` vào mục "Agent Team" của `CLAUDE.md` (hoặc chạy lại phần CLAUDE.md của init).

# Release notes - 02/11/2026 (v0.9.1)

## Thay đổi
- **Agent mới `challenger`** (sonnet, 11 agent): reviewer mù ticket, chỉ nhận yêu cầu gốc nguyên văn + diff, tự dựng lại yêu cầu và chấm met / not met / can't tell kèm `file:dòng`. Hook chặn nó đọc `docs/` (TASK, board, CONTEXT, KB). Dùng ở S5 cho task VỪA/LỚN; không có gate riêng (gate vẫn đọc dòng Lead điền trong TASK.md).
- **`COST_TIER`** (`economy | standard | max`): bảng model theo mức trong `run.md`; Lead truyền `model` khi gọi agent. Security và Architect luôn opus.
- **`LESSONS_PATH`** (`docs/LESSONS.md`): mục đích "đã sai một lần thì không vấp lại". Lead ghi **ngay khi có lỗi thật** (review Medium trở lên, test fail do code, Assumption sai, Security finding, làm lại, user sửa cách làm), mỗi bài gồm Sai gì, Nguyên nhân gốc, Cách tránh kiểm tra được, tối đa 3 dòng mỗi task. Dùng lại: Scout chép bài `Active` liên quan vào CONTEXT.md, dev đọc trước khi code, `code-reviewer` coi diff lặp lại lỗi cũ là High; lặp lại thì chuyển thành quy tắc trong `docs/engineering/review-checklist.md` (`Promoted`). Gate S6 chỉ kiểm dòng `Bài học: YES` hoặc `KHÔNG CÓ` trong TASK.md. User sửa cách team làm việc: ghi bài học `process` và sửa chỗ gây lỗi nếu nằm trong project (lỗi trong plugin thì nêu ở báo cáo cuối).
- Định dạng gợi ý: `test-report.md` một dòng mỗi test (`| task-id | AC-n | test | PASS | bằng chứng |`); dòng cuối bài reviewer `Kết luận: APPROVED | Critical=0 High=0 ...`.
- TASK.md thêm mục 0 "Yêu cầu gốc (nguyên văn)" cho challenger; AC đánh số `AC-<n>`.

## Key mới trong `.claude/agent-team.config`
- `COST_TIER`, `LESSONS_PATH`.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`, khởi động lại Claude Code, kiểm tra có 11 agent.
- Project đã init: thêm `COST_TIER=standard`, `LESSONS_PATH=docs/LESSONS.md` vào config; copy `templates/kb/LESSONS.md` → `docs/LESSONS.md`; copy lại `TASK.md`, `CONTEXT.md` vào `.claude/agent-team/templates/`; thêm dòng `- Bài học: TODO` vào mục "Điều kiện chuyển giai đoạn" của TASK.md.

# Release notes - 02/11/2026 (v0.9.0)

## Thay đổi
- **Lean Debate**: chỉ 4 người debate (Lead, BA, Architect, Test Design, đều opus), 2 lượt song song + lượt 3 khi cần. Bỏ Agent Teams, chạy bằng subagent trả kết quả cho Lead (điểm chấm kín tự nhiên, không cần file).
- 10 agent: thêm `scout` (đọc repo một lần → `CONTEXT.md`), `test-designer` (opus), `test-executor` (sonnet). Gộp SA+TA thành `solution-architect` (LỚN mới gọi thêm `technical-architect`). Bỏ `requirement-reviewer`, `solution-reviewer`, `test-reviewer`, `tester`.
- Lead được **chọn một hoặc gộp ý** các phương án. Thiếu business rule: **không hỏi user**, Lead chọn best solution, ghi `Assumption`, liệt kê ở báo cáo cuối.
- Task NHỎ: Fast Track (không Scout, không debate). Security luôn có mặt, duyệt nhanh solution trước khi code và review đầy đủ sau khi code.
- Giới hạn: debate 3 lượt, sửa 3 vòng/issue rồi Lead phán quyết; sửa xong chỉ reviewer đã báo lỗi review lại.
- Knowledge Base đầy đủ trong `docs/` (domain, architecture, engineering, api, database, testing, security, modules, decisions); mỗi thư mục có chủ ghi riêng (guard chặn), nhãn Verified/Unverified, `verified-at`. Template ở `templates/kb/` (thay `templates/domain/`).
- `/agent-team:init` dự án có sẵn code: Scout dựng luôn nháp KB + quy chuẩn code (`docs/engineering/`, nhãn `Observed`). `--skip-kb` để bỏ qua.
- Quy chuẩn code (clean code) nằm trong KB; dev chạy lint/format; Code Reviewer review theo `docs/engineering/`.
- Lệnh mới `/agent-team:resume <task-id>`: làm tiếp task dang dở (hết quota, lỗi) từ TASK.md, stage, board, trên branch cũ.
- Guard: chặn commit không đúng một dòng `[role] task-id: mô tả` / có trailer / `--signoff` (chỉ project có `.claude/agent-team.config`); Lead đổi giai đoạn phải đủ điều kiện trong TASK.md (S3, S5, S6); bỏ luật post board theo tên role; thêm quyền ghi KB theo chủ sở hữu.
- Đã kiểm chứng: `agent_type` tới được hook khi chạy subagent (BA ghi ngoài KB bị chặn).
- Tài liệu thiết kế: `docs/design.md`.

## Key mới trong `.claude/agent-team.config`
- `LINT_CMD`, `FORMAT_CMD` (để trống = bỏ qua; init tự nhận diện).

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`, khởi động lại Claude Code. Không còn cần `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`.
- Project đã init bản cũ: thêm `LINT_CMD`, `FORMAT_CMD` vào config; copy `templates/kb/` vào `docs/` (không ghi đè file có sẵn); copy lại `TASK.md`, `SUMMARY.md`, `POST.md`, `CONTEXT.md` vào `.claude/agent-team/templates/`; thay mục "Agent Team" trong `CLAUDE.md` bằng `templates/claude-md-section.md` mới. Hoặc chạy lại `/agent-team:init`.
- `docs/domain/` bản cũ vẫn dùng được (BA vẫn ghi được).

# Release notes - 01/11/2026 (v0.8.2)

## Thay đổi
- Config mới `BASE_BRANCHES="../FrontEnd=master"`: nhánh gốc riêng cho repo khác `BASE_BRANCH` (vd BE `main`, FE `master`). Repo không khai báo dùng `BASE_BRANCH`.
- `run.md`, `code-reviewer`, `init.md` dùng nhánh gốc theo từng repo. Init tự đọc nhánh mặc định của từng repo.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`.
- Project đang dùng: thêm dòng `BASE_BRANCHES="../FrontEnd=master"` vào `.claude/agent-team.config` (trống nếu mọi repo cùng nhánh gốc).

# Release notes - 01/11/2026 (v0.8.1)

## Thay đổi
- Nhiều repo: **chọn 1 repo chính** (vd `API/`) chứa `.claude/`, `docs/`, `CLAUDE.md`, không còn đặt ở thư mục cha. `REPOS=". ../FrontEnd"` (`.` là repo chính). Docs và board được commit cùng repo chính.
- `/agent-team:init`: khi thấy ≥ 2 repo chỉ hỏi 1 câu "chọn repo chính", không tạo gì ở thư mục cha. Dặn user mở Claude Code ở repo chính và `/add-dir` repo còn lại.
- Guard: khóa vùng hiểu đường dẫn ngoài repo chính (`FE_PATHS="../FrontEnd"`); file `*_test.*` nằm ngoài mọi repo khai báo không bị chặn.
- `code-graph.py`: `REPOS` chấp nhận `.` và `../x`.
- Init luôn dùng `docs/` viết thường (guard so khớp phân biệt hoa thường).

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`, khởi động lại Claude Code.
- Project đã init ở thư mục cha (v0.8.0): chuyển `.claude/`, `Docs/` (đổi tên thành `docs/`), mục Agent Team trong `CLAUDE.md`, `code-graph-out/` vào repo chính; sửa config thành `REPOS=". ../FrontEnd"`. Hoặc xoá các thứ này ở thư mục cha rồi chạy lại `/agent-team:init` ở repo chính.

# Release notes - 01/11/2026 (v0.8.0)

## Thay đổi
- **Hỗ trợ nhiều repo con**: mở Claude Code ở thư mục cha (không cần là repo), khai báo `REPOS="be fe"` trong `.claude/agent-team.config`. Một team, một board chung, branch/commit/push theo từng repo (`git -C be ...`).
- Guard: hiểu `git -C <repo>` và `cd <repo> && git ...` khi chặn commit/push vào main/master/develop; snapshot + hoàn tác diff chạy trên từng repo con.
- `code-graph.py`: build gộp tất cả repo trong `REPOS` (cạnh FE -> BE hiện được), cảnh báo graph cũ theo từng repo.
- `agent-db-clone.sh`: tìm config bằng cách đi ngược từ thư mục hiện tại (không cần repo git); `COMPOSE_DIR` tương đối tính từ thư mục có `.claude/`.
- **Knowledge base `docs/domain/`** (glossary, business-rules, decisions): `/agent-team:init` tạo cấu trúc `docs/` (domain + agent-tasks). Mọi role đọc, chỉ BA và Lead ghi (guard chặn role khác, kể cả bằng Bash). S6: BA cập nhật, Requirement Reviewer duyệt.
- `business-analyst` được thêm tool `Edit` (chỉ sửa được board và `docs/domain/`).
- Config mới `REPOS` (để trống = 1 repo, chạy như cũ).

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`
- Project đã init: chạy lại `/agent-team:init` (tạo `docs/domain/`, thêm dòng `REPOS` vào config).
- Dự án BE/FE là 2 repo riêng: tạo thư mục cha, mở Claude Code ở đó, đặt `REPOS="be fe"`, `BE_PATHS="be"`, `FE_PATHS="fe"`. Khuyên `git init` ở thư mục cha để lưu `docs/` và `.claude/` (thêm `be/`, `fe/` vào `.gitignore` của nó).

# Release notes - 01/11/2026 (v0.7.0)

## Thay đổi
- **Thay Graphify bằng `code-graph.py` tự có**: không cài gói ngoài, chỉ cần `python3`. Lệnh: `build` (Lead), `who-uses`, `uses`, `explain` (mọi role). Graph cũ so với HEAD thì cảnh báo.
- Config `USE_GRAPHIFY` đổi thành `USE_CODE_GRAPH`. Thư mục `graphify-out/` đổi thành `code-graph-out/`.
- Guard: role chỉ được `code-graph.py who-uses|uses|explain`; `build` chỉ Lead (kể cả khi gọi qua `python3`).

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`
- Project đã init: chạy lại `/agent-team:init` (copy `code-graph.py`, đổi `USE_GRAPHIFY` thành `USE_CODE_GRAPH`, thêm `code-graph-out/` vào `.gitignore`).
- Đã cài Graphify trước đó thì gỡ bỏ được, plugin không còn dùng: `uv tool uninstall graphifyy` hoặc `pipx uninstall graphifyy`; xóa thư mục `graphify-out/`.

# Release notes - 01/11/2026 (v0.6.0)

## Thay đổi
- `security`: thêm checklist chi tiết (kỷ luật xác nhận, web/xác thực, cô lập dữ liệu) rút gọn từ `cloudflare/security-audit-skill`. Audit đầy đủ nhiều phase vẫn do Lead chạy riêng trước khi release.
- `backend-dev`, `frontend-dev`, `code-reviewer`: thêm nguyên tắc "code ít nhất" rút gọn từ `ponytail` (không cài plugin ponytail, tránh đụng hook).
- Mục "Agent Team" trong CLAUDE.md mẫu và báo cáo cuối của Lead: quy tắc trả lời ngắn rút gọn từ `i-have-adhd`.
- Thêm `plugins/agent-team/THIRD-PARTY.md` ghi nguồn + giấy phép + commit.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`
- Project đã init: chạy lại `/agent-team:init` hoặc tự thêm mục "Trả lời ngắn" từ `templates/claude-md-section.md` vào CLAUDE.md.

# Release notes - 01/11/2026 (v0.5.0)

## Thay đổi
- Tích hợp **Graphify** (code graph) như bước tùy chọn của `/agent-team:init`. 5 role (BA, SA, TA, Code Reviewer, Security) đọc `graphify-out/GRAPH_REPORT.md` và query `graphify query/path/explain`. Lead chạy `graphify update .` đầu task, sau S3 và S4.
- Guard: role chỉ được `graphify query|path|explain`; `install/update/extract/hook...` chỉ Lead.
- Config mới `USE_GRAPHIFY=1`.

## Cần làm thủ công
- Cài Graphify (đúng tên gói **graphifyy**, 2 chữ y; kiểm tra PyPI trỏ về `github.com/Graphify-Labs/graphify`):
```
uv tool install graphifyy==0.9.100
```
- Cần Python 3.10+. Trong project: `graphify install --project`, rồi `/graphify .` để build graph lần đầu.
- **Không** chạy `graphify hook install` (dễ đụng hook guard của agent-team).
- Muốn không log câu query vào `~/.cache/graphify-queries.log`: đặt biến môi trường `GRAPHIFY_QUERY_LOG_DISABLE=1`.
- Chạy lại `/agent-team:init` để thêm `USE_GRAPHIFY` vào config và `graphify-out/` vào `.gitignore`.
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`

# Release notes - 01/11/2026 (v0.4.1)

## Thay đổi
- Hook `PostToolUse` mới `show_post.py`: khi role ghi bài lên `board/`, nội dung bài (tối đa 15 dòng) hiện thẳng trong chat dạng `[role · S2-R1]`. Điểm V4 và suy nghĩ của agent không hiện.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`, rồi mở lại Claude Code.

# Release notes - 01/11/2026 (v0.4.0)

## Thay đổi
- Hook `PostToolUse`: sau mỗi lệnh Bash của dev/tester/reviewer, so `git status` trước/sau. File ghi sai vùng bị **hoàn tác ngay** và báo agent.
- Role không được chạy `chmod`/`chown`/`chgrp`/`setfacl`/`chattr`.
- **Chặn theo giai đoạn**: Lead ghi `.agent-team/stage` (`echo S3 > .agent-team/stage`). S1/S2 chặn mọi code + test, S3 chỉ ghi code, S4 chỉ ghi test. Không cần `agent_type`, áp dụng cả với Bash. Xoá file khi xong S6.
- Biến môi trường mới `AGENT_TEAM_DEBUG=1`: ghi `.agent-team/guard.log` để kiểm tra hook có nhận `agent_type` không.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`
- (Tùy chọn) thêm `"AGENT_TEAM_DEBUG": "1"` vào `env` trong `~/.claude/settings.json` để bật log.

# Release notes - 01/11/2026 (v0.3.0)

## Thay đổi
- Thêm agent `requirement-reviewer` (opus): duyệt AC của BA ở S1 (APPROVED mới qua S2), đối chiếu AC ↔ code ↔ test ở S5.
- Khóa vùng ghi: `backend-dev` chỉ sửa `BE_PATHS`, `frontend-dev` chỉ sửa `FE_PATHS`, `tester` chỉ sửa `TEST_PATHS` (kèm `*_spec.*`, `*.test.*`, `__tests__/`). Chỉ BA viết AC. Chặn cả ghi bằng Bash (`>`, `tee`, `sed -i`, `mv`, `cp`, `rm`...).
- Mọi task (kể cả NHỎ) có đủ BA + Requirement Reviewer + Test Reviewer: mỗi sản phẩm có người review riêng.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`
- Kiểm tra `BE_PATHS`, `FE_PATHS`, `TEST_PATHS` trong `.claude/agent-team.config` đã đúng cấu trúc repo. Để trống hoặc `TODO` thì không khóa vùng đó.

# Release notes - 01/11/2026 (v0.2.1)

## Thay đổi
- Bỏ `.agent-team/scores/`: điểm V4 gửi **riêng cho Lead**, Lead ghi bảng điểm vào TASK.md. Không còn file điểm để đọc lọt.
- 7 role chỉ đọc (BA, SA, TA, 3 Reviewer, Security) bỏ `Edit` khỏi `tools` (chặn ở tầng Claude Code, không phụ thuộc `agent_type`).
- Guard: bỏ rule về scores, chặn thêm `Write` vào `.agent-team/` (state DB clone).

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`
- Project đã chạy `/agent-team:init`: thêm mục "Điểm chấm (V4)" mới vào `CLAUDE.md` (xem `templates/claude-md-section.md`).
- Có thể xoá thư mục `.agent-team/scores/` cũ.

# Release notes - 01/11/2026 (v0.2.0)

## Thay đổi
- Thêm **Debate Board** `docs/agent-tasks/<task-id>/board/`: nơi debate chung, thay cho nhắn tin trực tiếp và `notes/<role>.md`.
- Mỗi vòng: role đọc `SUMMARY.md` + toàn bộ bài post của vòng hiện tại.
- Điểm chấm lưu ở `.agent-team/scores/` (đã gitignore), guard chặn agent đọc.
- TASK.md thêm mục "Tổng hợp ý kiến theo role".

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`
- Project đã chạy `/agent-team:init` trước đó: chạy lại để copy thêm `templates/POST.md`, `templates/SUMMARY.md`.

# Release notes - 01/11/2026

## Thêm mới
- Plugin `agent-team` v0.1.0: 10 agent + Lead playbook, guard hook, DB clone script, template.

## Cần làm thủ công

### 1. Bật Agent Teams (biến môi trường mới)
Thêm vào `~/.claude/settings.json`:
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```
Không bật thì team vẫn chạy ở chế độ subagent (dự phòng), nhưng agent không nhắn trực tiếp với nhau.

### 2. Cài plugin (chạy trong Claude Code)
```
/plugin marketplace add /Users/hung.vo/Kevin/Projects/03.Multiple-Agents
/plugin install agent-team@kevin-agent-team
```
Cập nhật sau khi sửa plugin: `/plugin marketplace update kevin-agent-team`

### 3. Cài cho từng project
```
/agent-team:init
```
Lệnh này tạo trong project:
- `.claude/agent-team.config` (không chứa secret, kiểm tra các giá trị `TODO`)
- `.claude/agent-team/agent-db-clone.sh`, `.claude/agent-team/templates/TASK.md`
- Mục `## Agent Team` cuối `CLAUDE.md`
- `.gitignore`: `.agent-team/`, `.env*`, `*.dump`, `*.sql.gz`
- `docs/agent-tasks/`

## Yêu cầu
- `python3` (guard hook), `git`, `docker compose`, `openssl`

## ⚠️ File nhạy cảm
- `.agent-team/clones/*.state` chứa password **ngẫu nhiên của DB clone** (không phải password DB thật). Đã gitignore, không commit.
- Không commit `.env*`. Guard chặn đọc/commit/push các file này.
