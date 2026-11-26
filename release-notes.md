# Release notes - 25/11/2026 (v0.44.0 - giảm token phiên Lead)

## Thay đổi
- Sync tự thêm `env.CLAUDE_CODE_DISABLE_1M_CONTEXT=1` vào `.claude/settings.json`: phiên chạy ngữ cảnh 200k, tự nén sớm (có hiệu lực từ phiên sau).
- Agent trả về Lead ≤ 5 dòng (kết luận + đường dẫn file / số tin đã post); điểm chấm, GAP, câu hỏi cho owner vẫn ghi đủ.
- `pool.py commit <M-n/T-k | task-id> <role> "<mô tả>" [--set <STATE>]`: agent xong, 1 lệnh add file vùng của role + commit + đổi trạng thái (file vùng role khác, `.claude/`, file nhạy cảm để lại).
- Lead gom lệnh sổ sách liên tiếp vào 1 lần Bash, không tự `grep` / `cat` code kiểm lại việc của agent.
- Lead không dán bảng tiến độ vào chat sau mỗi bước / mỗi lượt: xem dòng trạng thái + `.agent-team/STATUS.md`.
- README mục "Bắt đầu: làm gì sau mỗi bước" (4 đường: app mới, có code, viết lại hệ thống cũ, đang dở); `/agent-team:init` kết thúc bằng "Bước tiếp" theo trường hợp.
- Branch của task đổi tiền tố `agent/<task-id>` → `task/<task-id>` (branch phiên, worktree, claim module, audit). Phiên đang chạy trên `agent/*` vẫn làm tiếp được: tag module và `claim` nhận cả 2 tiền tố; task mới trong phiên đó tạo branch `task/*`.
- `API_RESPONSE=flat` (config, mặc định `flat` cho dự án init mới; config cũ không có key = `cooked` như trước): BE chỉ đọc + lọc theo quyền, FE tự tính; architect ghi `PHẲNG | XỬ LÝ` cho từng API theo quyền, security chấm High khi API phẳng lộ dữ liệu vượt quyền.
- `CONFIG_APPROVED=` (config mới): hook chặn gọi agent khi user chưa tự ghi `ok`, chặn Lead tự ghi dòng này. Config cũ không có dòng này thì không bị chặn.
- `/agent-team:init`: dừng cho user duyệt cấu hình chạy (`API_RESPONSE`, `COST_TIER`, model Scout, `MAX_PARALLEL`, `MAX_DEBATE`, `TEST_MODE`, `CLONE_MODE`, `PUSH`) trước khi gọi agent.
- `/agent-team:kb` + `init` (dự án có code): Scout mảng đọc logic (Module, Frontend, Tổng hợp nghiệp vụ) tự dùng opus (`COST_TIER=economy`: sonnet); mảng liệt kê giữ sonnet.
- Migrate hệ thống cũ: có `docs/legacy/` (KB + audit của repo cũ) thì `/agent-team:app` chỉ lấy nghiệp vụ từ đó, thiết kế mới workflow / DB / API / giao diện; BA lập `docs/product/legacy-map.md` (GIỮ / ĐỔI / BỎ), thêm module "Chuyển dữ liệu" (`docs/database/legacy-data-map.md`, chỉ chạy trên bản sao).

## Cần làm tay
- Migrate: ở repo cũ chạy `/agent-team:init` + `/agent-team:kb` + `/agent-team:audit`, chép `docs/` của nó vào `docs/legacy/` của repo mới rồi chạy `/agent-team:app`.
- Muốn giữ ngữ cảnh 1M: đổi giá trị `CLAUDE_CODE_DISABLE_1M_CONTEXT` trong `.claude/settings.json` thành `"0"`.

# Release notes - 25/11/2026 (v0.43.0 - hỏi thương hiệu, bàn giao client, rà soát lệnh cho MVP)

## Thay đổi
- Intake (form owner lượt 1) hỏi thêm: thiết kế có sẵn, logo, màu thương hiệu, font, phong cách. File owner gửi → `docs/product/design-ref/`; design system lấy token từ đó (màn có file mẫu giữ bố cục), không có mới dùng màu owner cho / bảng trung tính.
- `docs/product/HANDOVER.md` (mẫu `templates/product/HANDOVER.md`): bàn giao cho client ở mỗi DEMO và cuối app: tài khoản demo mỗi vai trò (không ghi mật khẩu), hướng dẫn sử dụng theo vai trò (BA viết từ flows + screens), có / chưa có, ghi chú phát hành, cách báo lỗi.
- `FE_TEST_CMD` (config) + `agent-db.sh fe-test <task-id> [args]`: chạy test component / unit FE. M-0 dựng runner + 1 test mẫu. `TEST_MODE=mvp` dùng lệnh này.
- `TEST_MODE=mvp`: xong mọi module → giao MVP (`demo-mvp` + `HANDOVER.md`) rồi DỪNG, M-E2E chỉ chạy khi user bảo. test-designer / code-reviewer / challenger hiểu `E2E: DEFER`.
- `pool.py reconcile`: user merge tay branch task vào branch phiên → task thành DONE, dọn worktree (resume tự gọi).
- Module: không chép `HANDOVER.md` / `design-ref/` vào thư mục module; module xong thì cập nhật bản chính `docs/product/HANDOVER.md`.
- Resume: theo branch ghi trong TASK.md (user đặt tên riêng được). ui-designer + skill `ui` đọc `design-ref/` trước. Config mẫu thêm `E2E_WAIT`.

## Cần làm tay
- Dự án có FE dùng `TEST_MODE=mvp`: điền `FE_TEST_CMD` (vd `npx vitest run`).
- Dự án đang chạy: muốn có bàn giao thì chép `templates/product/HANDOVER.md` + `design-ref/` vào `docs/product/`.

# Release notes - 25/11/2026 (v0.42.0 - khung Playwright chuẩn, đổi tên agent-db.sh)

## Thay đổi
- Khung E2E chuẩn `templates/e2e/` (playwright.config.ts, e2e/project.ts, auth.setup.ts, smoke.spec.ts, support/env|db|responsive.ts): workers theo chiều rộng, `@responsive`, đăng nhập 1 lần (`storageState`), reset qua `$APP_EXEC`, ảnh vào `EVIDENCE_DIR`, timeout 30s / 5s. Hook sync chép vào `.claude/agent-team/e2e-template/` mỗi phiên. M-0: dự án chưa có Playwright thì chép khung này, chỉ sửa `e2e/project.ts`, chạy smoke.
- Đổi tên `agent-db-clone.sh` → `agent-db.sh` (chế độ schema không còn clone: DB của task tạo bằng migrate + seed). Tên cũ vẫn chạy (gọi sang tên mới). Chữ "DB clone" trong tài liệu → "DB riêng của task". Hook sync tự thêm quyền `agent-db.sh` vào `.claude/settings.json` khi đã có quyền tên cũ.

## Cần làm tay
- `.gitignore`: thêm `.claude/agent-team/e2e-template/` và `e2e/.auth/`.
- Lệnh / quyền tên cũ `agent-db-clone.sh` vẫn chạy, không cần sửa.

# Release notes - 25/11/2026 (v0.41.0 - Chế độ test MVP)

## Thay đổi
- `TEST_MODE=mvp` (config) hoặc `- Chế độ test: MVP` (TASK.md, từng task): task kiểm bằng test BE + component, spec E2E vẫn sửa nhưng không chạy, ghi `- E2E: DEFER`. Hook cho qua S5 với DEFER chỉ khi MVP. Integration test sau merge chỉ chạy `TEST_CMD`. E2E toàn bộ chạy ở M-E2E. M-0 và M-E2E luôn FULL (M-0 dựng Playwright + smoke E2E để M-E2E chạy được).

- `agent-db-clone.sh e2e` truyền `APP_EXEC` cho `E2E_CMD` (seed / reset gọi `sh -c "$APP_EXEC php …"`, chạy được ở cả 2 chế độ). Chế độ schema: cổng riêng của worktree thắng `E2E_PORT` cố định.

## Sửa
- Chế độ schema: `e2e` luôn thoát mã 1 sau khi chạy (biến `port` local bị trap EXIT đọc sau khi hàm kết thúc).

## Cần làm tay
- E2E đang gọi `docker exec agent-e2e-<task>`: đổi sang `$APP_EXEC`. Bỏ `E2E_PORT` cố định ngoài dải cổng đã mở.
- Muốn bật cho cả dự án: thêm `TEST_MODE=mvp` vào `.claude/agent-team.config`.

# Release notes - 25/11/2026 (v0.40.2 - Phase A bước Mockup dùng lại mockup đã duyệt)

## Sửa
- Module chỉ áp mockup có sẵn: ghi `- Mockup: dùng lại <thư mục>` trong MODULE.md (hoặc APP.md) → bước 4 "Mockup" tính xong khi thư mục đó có `mockup-*.html`, status không còn kẹt ở Mockup.

## Cần làm tay
- Module đang chạy (vd M-UI2 của 04.Cay): thêm dòng `- Mockup: dùng lại docs/product/design` vào MODULE.md.

# Release notes - 25/11/2026 (v0.40.1 - sửa status line gắn nhầm module)

## Sửa
- Status line / STATUS.md: task không thuộc module nào (vd mockup v2) không còn gắn ▶ + "bước x/y" vào module TODO đầu tiên. ▶ hiện ở module đang `DOING` trong APP.md, không kèm bước.

# Release notes - 25/11/2026 (v0.40.0 - 1 container DB + 1 container app, STATUS.md)

## Thay đổi
- `CLONE_MODE=schema`: mọi worktree dùng chung 1 container DB + 1 container app. Mỗi task 1 DB `<DB_NAME>_<task>` (migrate + `SEED_CMD`), lệnh chạy bằng `exec -w /var/www/.worktrees/<task>`; `vendor/`, `node_modules/` là bản riêng của worktree (clone từ thư mục chính). Merge xong tự kill process cổng + xoá DB của task. `CLONE_MODE=container` (cũ) vẫn là mặc định.
- Guard: agent đã làm ở 1 worktree thì bị chặn khi đụng worktree task khác.
- DB của task (`schema`): lần đầu `up` / `test` / `e2e` tự tạo DB + migrate + `SEED_CMD`; lần sau dùng lại, chỉ chạy migration mới. `backend-dev`: bảng mới kèm factory + seeder mock data đăng ký vào seeder gốc; bảng đã có seeder thì dùng lại / bổ sung.
- Chạy chung container an toàn: mỗi worktree có `vendor` / `node_modules` **riêng** (clone APFS / reflink từ thư mục chính, gần như không tốn ổ; lock khác main thì cài lại trong worktree), cài gói ở worktree này không đụng worktree khác; guard chặn cài package hệ thống (apt, pecl, PHP extension) vào container chung; `.env` worktree là symlink về `.env` chính (env riêng truyền bằng `-e`); `SCHEMA_ENV` có `{task}` để tách Redis / cache / search theo task, `SCHEMA_DOWN_CMD` dọn khi xong.
- Merge task có đổi `composer.lock` / `package-lock.json`: `merge-end` tự cài lại `vendor` / `node_modules` của thư mục chính trong container; worktree khác giữ bản riêng, không bị đổi.
- Gói hệ thống (apt, PHP extension): architect ghi ở debate, TASK.md có `- Gói hệ thống:`; biết trước → M-0 (App Mode) / task `INFRA` đầu module / bước đầu S3; lộ ra giữa chừng → GAP hạ tầng, task `INFRA-n`. Rebuild khi pool chạy: Lead hỏi user → `pool.py drain` (không mở task mới, không merge, liệt kê task đang test; `wait` báo `DRAIN XONG`) → rebuild → `pool.py drain --off`.
- `pool.py side <task-id>`: task lẻ chạy song song ở terminal khác trong worktree riêng (branch, cổng, DB riêng); `--done` xoá worktree khi đã commit hết. `STATUS.md` có mục `## Task lẻ`, mỗi task 1 khối.
- M-SKEL-FE: T-1 tạo route + file rỗng cho mọi màn; mỗi component chung 1 task; **mỗi màn 1 task** (agent mới, worktree mới, xong merge → pool mở màn tiếp); agent chuyển mockup dùng sonnet; chỉ lint file đã sửa, build FE 1 lần trước review UI.
- Status line mặc định 1 dòng; bảng đầy đủ ghi vào `.agent-team/STATUS.md` (pool.py cập nhật mỗi lệnh + mỗi vòng `wait`). `PROGRESS_LINES=table` để hiện bảng như cũ.

## Cần làm thủ công
- Dùng chế độ mới: config `CLONE_MODE=schema`, `APP_START_CMD` có `{port}`.
- docker-compose service app: `volumes: ["./:/var/www/main", "./.worktrees:/var/www/.worktrees", "/var/www/main/.worktrees", "./.env:/var/www/.env:ro"]`, `ports: ["8800-8899:8800-8899"]` (main `:8800`, worktree `:8801`, `:8802`... tự cấp), rồi `docker compose up -d app` (làm khi pool rảnh).
- Ignore `.worktrees` trong `tsconfig`, ESLint, Vite watch.
- Xem tiến độ: mở `.agent-team/STATUS.md` bằng preview.

# Release notes - 24/11/2026 (v0.39.0 - E2E nhanh hơn)

## Thay đổi
- Skill `test-automation`: luồng đầy đủ chỉ chạy ở chiều rộng lớn nhất, chiều rộng nhỏ chỉ chạy test `@responsive`; song song theo chiều rộng (`workers` = số chiều rộng, seed / reset tách theo chiều rộng, không xoá bảng dùng chung); đăng nhập 1 lần bằng `storageState` (project `setup`); reset `beforeAll` cho file chỉ đọc; server app phục vụ song song.
- Mẫu `playwright.config.ts` + `e2e/auth.setup.ts` mới.
- Ít E2E: `test-designer` chọn tầng rẻ nhất (logic / validate / quyền → test BE, E2E chỉ luồng chính + responsive), case có cột `Tầng`.
- Chạy đúng phạm vi: spec gắn tag module `@m<n>`; IT khi merge (`pool.py merge-begin`) chỉ `TEST_CMD` + E2E của module, **toàn bộ E2E chỉ ở M-E2E**; sửa lỗi `--last-failed`.
- Không build FE mỗi lần chạy E2E (build khi file FE đổi).

## Cần làm thủ công
- `APP_START_CMD` dùng server nhiều luồng (PHP: thêm `PHP_CLI_SERVER_WORKERS=8` trước `php -S`).
- Dự án đã có E2E (04.Cay): chạy 1 task tăng tốc E2E theo skill (đo thời gian trước / sau).
- Commit + push, `/plugin` update `multiple-agent`, `/exit` rồi `claude -c`.

# Release notes - 24/11/2026 (v0.38.0 - Mockup design full, component dùng lại mọi stack)

## Thay đổi
- Mockup không còn đen trắng: **design full** theo design system, HTML + Tailwind (offline `assets/tailwind.js`) + Web Components (`components/*.js`), dữ liệu mẫu `data/*.js`. Gửi nguyên thư mục `docs/product/design/` cho client, mở bằng double-click.
- 5 quy ước component (1 component 1 file, props là thuộc tính chữ trùng contract, template chỉ in biến / if / lặp, data tách riêng, không thư viện khác) → chuyển sang Blade / React / Vue / ERB... chỉ đổi cú pháp.
- App Mode: A3a design system nháp **trước** mockup; A3b 1 `ui-designer` làm component + màn chuẩn mỗi loại khung trang, N `ui-designer` song song làm các màn còn lại; owner duyệt cả logic lẫn giao diện.
- M-SKEL-FE: chuyển mockup sang code, không tự thiết kế; review chụp app và mockup cùng màn × cùng viewport để so.
- `board.py report` nhúng được mockup có `components/*.js`, `assets/*.js`.
- Skill mới `agent-team:ui`: luật design (tránh dấu hiệu UI do AI làm, thang khoảng cách / chữ, ≤ 1 CTA, đủ trạng thái, chữ trên UI), chế độ `admin` bố cục kiểu Ant Design (sidebar 252, topbar + nút tài khoản có Đăng xuất, breadcrumb có Quay lại, thẻ số liệu, thanh lọc, thẻ bảng, header chi tiết có tab, form trong drawer, token + tone trạng thái), chế độ `app`, quy trình kế hoạch → màn chuẩn → tự chụp ảnh chấm. `ui-designer`, `frontend-dev` bắt buộc dùng.
- Skill `ui`: thao tác trong bảng dùng nút icon nét (outline, không tô đặc) + tooltip, không nút chữ; > 3 thao tác gom vào `⋯`; **xoá ở mọi nơi bắt buộc xác nhận** (popconfirm / modal, nói rõ xoá gì + hệ quả, focus ở Huỷ).
- Skill `ui` thêm: bảng (chọn nhiều + thao tác hàng loạt, cột cố định, cắt chữ + tooltip, sort mặc định, giữ lọc / trang trong URL), lọc trên điện thoại (drawer), rỗng do lọc; hành vi chung (hỏi khi rời form chưa lưu, toast, ô nhập đúng kiểu, nút đang xử lý, validate, ẩn nút theo quyền / trạng thái, định dạng ngày / số / rỗng, phím tắt, tiêu đề tab, trang 403 / 404 / 500).
- Status line: bảng `✅ Done (n)` gọn thành danh sách `M-0, M-1, M-DB, …` tự xuống dòng (task xong của module đang làm ghi `M-5/T-1`).
- Status line: bảng `✅ Done` cao hơn bảng trái không còn bị dồn sang trái (dòng trống bên trái giữ chỗ bằng ký tự ẩn).
- Status line tự ẩn task đã đóng (S6 có `Bài học` + mọi bước xong); `rm .agent-team/stage` cuối S6 ghi rõ là bắt buộc.

## Cần làm thủ công
- Commit + push, `/plugin` update `multiple-agent`, `/exit` rồi `claude -c`.
- App đang làm dở (04.Cay): không bắt buộc làm lại mockup.

# Release notes - 24/11/2026 (v0.37.0 - Dọn process sau khi merge)

## Thay đổi
- `pool.py merge-end pass` tự dọn task: xoá container `agent-clone-<task>` / `agent-e2e-<task>`, kill process còn chạy trong worktree; Lead TaskStop agent + shell nền của task.

## Cần làm thủ công
- Commit + push, `/plugin` update `multiple-agent`, `/exit` rồi `claude -c`.

# Release notes - 24/11/2026 (v0.36.0 - Task khung M-SKEL chạy nhanh)

## Thay đổi
- Task M-SKEL-*: bỏ `code-reviewer`, `security`, `challenger`, review UI từng task; ghi `Code review: N/A`, `Security review: N/A` (hook cho qua). `ui-designer` chỉ review 1 lần ở task cuối.
- M-SKEL-BE / M-SKEL-FE không test, không IT (chưa có dữ liệu thật): `Kết quả test: N/A` (hook cho qua), dev chỉ chạy `LINT_CMD` (FE thêm build FE).
- `pool.py merge-begin` của M-SKEL-* tự merge + commit, không chạy IT.

## Cần làm thủ công
- Commit + push, `/plugin` update `multiple-agent`, `/exit` rồi `claude -c`.

# Release notes - 24/11/2026 (v0.35.0 - M-SKEL-FE chạy ít container)

## Thay đổi
- Task M-SKEL-FE không tạo DB clone, không chạy app: lint + build + `TEST_CMD` bằng container tạm.
- Review UI/UX: 1 container app trên nhánh phiên sau khi mọi màn đã merge, seed trước, chụp mọi màn × `VIEWPORTS`.

## Cần làm thủ công
- Commit + push, `/plugin` update `multiple-agent`, `/exit` rồi `claude -c`.

# Release notes - 24/11/2026 (v0.34.0 - Demo client theo nhánh, debate song song khi M-SKEL chạy)

## Thay đổi
- 3 mốc demo client: 🚀 1 mockup + form · 🚀 2 nhánh `demo-ui` khi M-SKEL-FE DONE · 🚀 3 nhánh `demo-full` khi M-E2E PASS. Lead `git push origin HEAD:demo-ui` / `HEAD:demo-full` (fast-forward, không force), team không dừng.
- M-SKEL chưa DONE: module khác vẫn được debate, chỉ chặn task code (`pool.py fill`).
- Mọi task M-SKEL-FE phải build FE pass trước merge.
- Hàm stub ghi trả thông báo "Tính năng đang hoàn thiện" thay vì trang lỗi 501.
- Status line: bảng trái chỉ còn task đang làm / đang chờ; module và task đã xong sang bảng `✅ Done` bên phải; module có task đang chạy (▶ / 🧪 / 🔧 / 💬) lên đầu, rồi tới chờ merge, cuối là đang chờ.

## Cần làm thủ công
- Staging deploy theo nhánh `demo-ui` / `demo-full`, chạy `SEED_CMD` sau mỗi lần deploy.
- Commit + push, `/plugin marketplace update multiple-agent`, `/restart`.

# Release notes - 24/11/2026 (v0.33.0 - UI làm thẳng trong code, có màn mẫu + review)

## Thay đổi
- App Mode mục 8b chỉ còn design system (màu thương hiệu, font, cỡ chữ, bo góc, khoảng cách, component, `VIEWPORTS`); không vẽ UI design riêng.
- M-SKEL-FE: T-1 file chung + áp design system vào theme + màn mẫu (1 danh sách + 1 form), `ui-designer` duyệt màn mẫu → T-2..T-n N `frontend-dev` song song theo màn mẫu, giữ đủ chức năng mockup, sửa bố cục, bổ sung trạng thái / responsive → review UI/UX trong code (mockup + design system + màn mẫu), lệch sửa thẳng trong code. Bản code là bản client sẽ xem.
- Task thiếu UI: `frontend-dev` bổ sung trong code, không vẽ.
- FE tách riêng xác định theo repo FE riêng trong `REPOS` (không theo `FE_PATHS` trống).

## Cần làm thủ công
- Commit + push, `/plugin marketplace update multiple-agent`, `/restart`.

# Release notes - 24/11/2026 (v0.32.0 - UI thật làm 1 lần, task chỉ review UI rồi làm BE)

## Thay đổi
- App Mode mục 8b: sau khi owner chốt logic, `ui-designer` viết `docs/product/ui/design-system.md` (màu, font, component, trạng thái, `VIEWPORTS`).
- M-SKEL tách 2 module chạy song song: **M-SKEL-BE** (service theo model + hàm stub, controller trả props theo contract) và **M-SKEL-FE** (T-1 tạo file chung: layout, component, trang rỗng, type props → T-2..T-n N `frontend-dev` song song làm UI thật theo nhóm màn, mock data từ props). Client xem mockup, không cần app chạy.
- M-SKEL-FE có task cuối **review UI/UX**: `ui-designer` mở từng màn ở mọi `VIEWPORTS`, đối chiếu mockup + design system → `docs/product/ui/review.md`; lệch → FE sửa, tối đa 2 vòng; M-SKEL-FE chỉ DONE khi review PASS (bản UI client sẽ xem).
- M-SKEL-FE theo `FE_PATHS`: chung repo (Inertia / Blade) → props từ controller stub, song song với BE theo contract; FE tách riêng (SPA) → tự mock theo contract, không phụ thuộc BE, M-E2E grep mock phải rỗng.
- `pool.py` / `progress.py` nhận `M-SKEL-BE`, `M-SKEL-FE`; cổng chặn mở việc mới tới khi mọi `M-SKEL*` DONE.
- Task có UI trong app đã có UI thật: `ui-designer` không vẽ lại, review màn trong code với AC → `design/ui-review.md`. `Đủ` → chỉ làm BE, không gọi `frontend-dev`; thiếu → chỉ vẽ phần thiếu.

## Cần làm thủ công
- Commit + push, `/plugin marketplace update multiple-agent`, `/restart`.

# Release notes - 24/11/2026 (v0.31.3 - M-SKEL chưa xong thì không mở việc mới)

## Thay đổi
- `pool.py fill`: M-SKEL chưa `DONE` → không mở task / debate mới (chỉ M-0 / M-DB / M-SKEL), task đang chạy vẫn chạy tiếp.
- Test: schema 10/10.

## Cần làm thủ công
- Commit + push, `/plugin marketplace update multiple-agent`, `/restart`.

# Release notes - 24/11/2026 (v0.31.2 - M-SKEL theo model, không theo module)

## Thay đổi
- M-SKEL chỉ tạo file sẵn đúng quy chuẩn: service theo model (1 model = 1 service), hàm stub có chữ ký + dấu module chủ (vd `#[Stub('M-7')]`), controller, request, route, trang placeholder. Bỏ interface / `Fake*` / service theo module.
- `contracts/M-SKEL.md`: bảng hàm / file → module chủ; module chỉ sửa thân hàm của mình, hàm mới thêm cuối file.
- M-E2E: grep dấu stub phải rỗng (thay cho grep `Fake`).
- M-SKEL không viết test mới, không E2E, không review chéo: chỉ lint + test có sẵn pass rồi merge.

## Cần làm thủ công
- Commit + push, `/plugin marketplace update multiple-agent`, `/restart`.
- App đang có M-SKEL theo module: SA làm lại contract M-SKEL theo model.

# Release notes - 24/11/2026 (v0.31.1 - status line đúng khi Lead đứng trong worktree)

## Thay đổi
- statusLine chạy `progress.py` của thư mục chính (qua `git rev-parse --git-common-dir`), không chạy bản cũ trong worktree. `sync.py` tự đổi lệnh cũ `python3 .claude/agent-team/progress.py` sang lệnh mới.
- `progress.py` đứng trong worktree vẫn lấy gốc là thư mục chính: luôn hiện bảng điều phối.
- `pool.py` / `progress.py` nhận module `M-SKEL` (trước bỏ qua phụ thuộc `M-SKEL (code)`).
- Bảng điều phối: cột IT riêng; task chờ liền nhau cùng lý do gộp 1 dòng `T-2..T-4 (3 task)`.

## Cần làm thủ công
- Commit + push, `/plugin marketplace update multiple-agent`, `/restart` (Claude Code đọc lại settings.json).

# Release notes - 24/11/2026 (v0.31.0 - schema trước, M-SKEL khung app, module song song)

## Thay đổi
- `pool.py fill`: M-DB chưa `DONE` thì chỉ chạy M-0 / M-DB, module khác (kể cả debate) chờ. M-DB chỉ `DONE` sau khi `MIGRATE_CMD` chạy OK trên DB dev.
- App Mode thêm **M-SKEL** sau M-DB: route + controller rỗng, interface service có chỗ cắm, `Fake*`, trang placeholder, contract mọi module, bảng file → module chủ. Phụ thuộc giữa module mặc định `(contract)`.
- M-E2E: grep `Fake` ngoài `TEST_PATHS` phải rỗng trước khi chạy E2E.
- `MAX_PARALLEL` = số agent user cho phép: Lead mở đủ slot, không hỏi lại.
- Status line: merge hiện `🧪 Integration test mm:ss`; khi có bảng điều phối thì ẩn bảng S1-S6 + bảng bước (không bị che).

## Cần làm thủ công
- Commit + push, `/plugin marketplace update multiple-agent`, `/restart` rồi `/agent-team:resume`.
- App đang chạy dở: thêm M-SKEL cho các module chưa code (prompt cho Lead).

# Release notes - 24/11/2026 (v0.30.2 - thời gian chạy + nhịp tim agent trên status line)

## Thay đổi
- Ô đang chạy hiện thời gian `mm:ss` (quá 1 giờ `h:mm:ss`), lấy từ dữ liệu thật: giai đoạn của task = giờ sửa file `.agent-team/stage` của worktree · merge + IT = giờ tạo `.git/MERGE_HEAD` · debate module = giờ chuyển DESIGN (cột mới `pool_modules.design_at`, board.db cũ tự thêm).
- Trạng thái task đang chạy có nhịp tim agent: `▶ Code · backend-dev 8s trước` (số giây về thấp = agent còn làm), `⚠ backend-dev im 12p` khi quá `HANG_MINUTES`, `chưa có agent` khi worktree chưa có agent nào chạy.
- Merge quá `MERGE_WARN_MINUTES` (mặc định 20) hiện ⚠. Task thường (không pool): bước đang làm `▶ Đang làm 12:40`, dòng agent `backend-dev 8s trước · <tiến độ>`.
- Số giây cập nhật mỗi lần Claude Code vẽ lại status line (khi có tin nhắn / tool chạy), không tự chạy từng giây.
- Test: pool 36, slots 12, progress 30.

## Cần làm thủ công
- Commit + push, `/plugin marketplace update multiple-agent`, khởi động lại Claude Code.
- Key mới (không bắt buộc): `MERGE_WARN_MINUTES=20`. Không phải secret.

# Release notes - 24/11/2026 (v0.30.1 - bảng điều phối theo giai đoạn)

## Thay đổi
- Status line + `pool.py status` (điều phối nhiều task): 1 dòng / task, cột `Module · Task · Debate · Code · Test · Review · Merge · Trạng thái`. Ô: ✅ xong · ▶ Np đang làm · ⏳ chưa tới · 🔧 sửa lại · ⛔ GAP / chặn · ✗ merge lỗi · 🔀 IT đang chạy. Không có dòng tổng.
- Module đã xong: 1 dòng `(n task) ✅ Xong`. Module đang debate chưa có task: `(chưa chia task) 💬 Debate`. Module chưa bắt đầu gộp 1 dòng: `⏳ Chờ slot debate` hoặc `⏳ Chờ phụ thuộc`. Task chờ module / nền dữ liệu hiện lý do (`⏳ Chờ M-1 (contract)`, `⏳ Chờ nền dữ liệu (M-DB)`), không còn hiện nhầm 🟢 READY.
- Chỉ 1 module (không có `APP.md`): bỏ cột Module, tiêu đề `M-n · x/y task xong`. Status line quá 16 dòng: task đã merge gộp, rồi cắt kèm `… +n dòng (pool.py status)`; `pool.py status` in đủ.
- Test: slots 11, pool 34.

## Cần làm thủ công
- Commit + push, `/plugin marketplace update multiple-agent`, khởi động lại Claude Code (hook `sync.py` tự chép `progress.py`, `pool.py`).

 - nền dữ liệu M-DB trước, module độc lập)

## Thay đổi
- **Bảng dữ liệu không thuộc module nào:** mọi bảng trong `docs/database/schema.md` nằm ở module **M-DB** (Phase B, sau M-0): migration + model + quan hệ + enum + factory + seeder + service dùng chung (giao diện + bản tối thiểu). Module mặc định chỉ phụ thuộc `M-DB (code)` → chạy song song. Trước đây bảng đi theo module dùng nó → chuỗi phụ thuộc (vd `04.Cay`: idps ở M-6 nên M-7..M-11 chờ).
- **`pool.py schema`:** đọc mục `## Bảng` của `SCHEMA_DOC` (tên trong backtick ở cột đầu), tìm migration (`Schema::create`, `create_table`, `CREATE TABLE`, `createTable`, `op.create_table`, tên file `create_<bảng>_table`) trong `MIGRATION_PATHS` (hoặc thư mục migration thường gặp). Thiếu → exit 1 + danh sách.
- **`pool.py fill`:** thiếu migration → `⛔ Nền dữ liệu chưa đủ` và chỉ chạy M-0 / M-DB, module khác không debate / không mở task.
- **`merge-begin`:** task (không phải M-DB) có migration mới **đổi / xoá** bảng chung (dropColumn, renameColumn, ->change(), Schema::drop, remove_column, change_column, DROP / ALTER TABLE … DROP / RENAME / MODIFY…) → chặn, bảo GAP; Lead duyệt rồi `merge-begin --allow-schema-change`. Thêm cột / bảng mới thì không chặn.
- `handoff`: thêm "mọi bảng trong schema có migration" + "M-DB DONE". Bảng Module, nhãn task, `## Lý do phụ thuộc` nhận `M-DB`.
- Mẫu `APP.md`: dòng M-DB; config `SCHEMA_DOC`. Test schema 8 (mới).

## Cần làm thủ công
- Commit + push, `/plugin marketplace update multiple-agent`, khởi động lại Claude Code.
- **Key mới (không bắt buộc):** `SCHEMA_DOC=docs/database/schema.md`. Không phải secret.
- **`04.Cay`:** `pool.py schema` hiện báo thiếu 7 bảng (staff_imports, competency_groups, idps, idp_goals, evidence_files, idp_approvals, idp_histories) → sau khi cài bản này, `fill` chỉ chạy M-0 / M-DB. Lead phải thêm dòng **M-DB** vào bảng Module (sau M-1), đổi Phụ thuộc M-3..M-12 → M-DB, bỏ phần tạo bảng khỏi task M-3. Task đang chạy không bị dừng.

# Release notes - 24/11/2026 (v0.29.2 - worktree nhận quyền Claude Code)

## Thay đổi
- `pool.py fill`: worktree mới nhận thêm `.claude/settings.json` và `.claude/settings.local.json` từ thư mục chính (quyền `permissions.allow`, `statusLine`), khi worktree chưa có (file đã commit thì giữ nguyên). Trước đây file chưa commit thì task chạy trong worktree thiếu quyền, vd `agent-db-clone.sh up` bị Claude Code hỏi lại → task BLOCKED khi không ai duyệt.
- Test pool: 34.

## Cần làm thủ công
- Commit + push, `/plugin marketplace update multiple-agent`, khởi động lại Claude Code.
- Muốn agent tạo DB clone không bị hỏi: thêm vào `.claude/settings.json` của dự án
  `"permissions": {"allow": ["Bash(.claude/agent-team/agent-db-clone.sh:*)", "Bash(./.claude/agent-team/agent-db-clone.sh:*)", "Bash(bash .claude/agent-team/agent-db-clone.sh:*)"]}`
  (`04.Cay` đã thêm). Quyền này cho phép script đọc DB thật để tạo bản clone.
- Worktree đã tạo trước bản này (vd `04.Cay-doi-ten`): chép tay `.claude/settings.json` sang.

 - chia slot task + debate, sửa guard hoàn tác chéo)

## Thay đổi
- **Chia slot (`pool.py fill`):** `MAX_PARALLEL` (mặc định 8) = task code + debate module. Debate 1 module = 1 slot, tối đa `MAX_DEBATE` (mặc định 4) cùng lúc, module khác chờ. Module đã chia task (SPLIT) chiếm bao nhiêu slot cũng được (không giới hạn / module). Slot trống cấp theo thứ tự bảng Module: task READY, hoặc bắt đầu debate module kế (`fill` in `💬 M-n: bắt đầu debate`). Không dừng task đang chạy để nhường. Bỏ luật "mỗi lúc 1 module thiết kế".
- **Task READY** kiểm thêm phụ thuộc module trong `APP.md`: `(code)` → module kia DONE · `(contract)` → có `docs/product/contracts/M-n.md`. Module bắt đầu debate khi module phụ thuộc đã chia task (biết contract) hoặc có contract; M-E2E khi mọi module DONE. Task `add` được khi module đang DESIGN, READY sau SPLIT.
- **Sửa guard hoàn tác chéo:** trước đây file người khác ghi trong lúc 1 agent chạy Bash dài bị tính là của agent đó và bị hoàn tác (vd backend-dev chạy test → bài BA viết docs M-2 bị xoá). Giờ guard ghi lại ai ghi file nào (Edit / Write, cả Lead) và ai đang chạy Bash (bảng `act_writes`, `act_bash` trong board.db): file người khác ghi → không hoàn tác; có agent khác chạy Bash cùng lúc → không biết ai ghi → không hoàn tác, ghi `unsure_write` vào `.agent-team/guard.log`. Edit / Write ngoài vùng vẫn bị chặn trước như cũ.
- Status line / `pool.py status`: `chạy 6/8 (task 4 · 💬 debate 2/4)`, dòng `💬 Debate` cho mỗi module đang debate, `chờ debate: …`.
- Test: slots 8 (mới), guard 394 (+4 case nhiều agent cùng thư mục).

## Cần làm thủ công
- Commit + push, `/plugin marketplace update multiple-agent`, khởi động lại Claude Code.
- **Key mới (không bắt buộc):** `MAX_DEBATE=4` trong `.claude/agent-team.config` hoặc config riêng. Không phải secret.

# Release notes - 24/11/2026 (v0.29.0 - 4 phase, team nhận module, đồng bộ develop, kiểm bàn giao)

## Thay đổi
- **`app.md` 4 phase:** A định nghĩa sản phẩm (owner duyệt) · B nền tảng (M-0 + contract module NẶNG + seeder + README + kiểm bàn giao) · C build module · D tích hợp (M-E2E).
- **`APP_BUILD`** (config chung): `auto` (mặc định, 1 người chạy hết, như 0.27) · `manual` (team: Lead dừng sau Phase B, push, báo danh sách module nhận được ngay).
- **`pool.py handoff`:** kiểm bàn giao: gap-check, bảng Module có Loại + Gồm R, mỗi phụ thuộc có lý do (`## Lý do phụ thuộc`: `- M-5 → M-1 (contract|code): ...`), contract `docs/product/contracts/M-n.md` cho module NẶNG / LỚN, M-0 test + E2E PASS, `.env.example` đủ key code dùng **không có giá trị mặc định** (quét `env('X')`, `ENV[]` / `ENV.fetch`, `process.env`, `import.meta.env`, `os.getenv`, `os.Getenv`), `SEED_CMD`, README "Chạy dự án lần đầu".
- **`pool.py claim M-n`** (team): fetch, kiểm phụ thuộc trên `origin/BASE_BRANCH` (`code` = module kia DONE, `contract` = có file contract → làm song song), kiểm chưa ai nhận (APP.md + branch `origin/agent/*-m<n>`), tạo `agent/YYYYMMDD-<DEV_ID>-m<n>`, ghi Người chạy + DESIGN, commit, **push ngay**. Cần `DEV_ID`, remote, `PUSH=1`; máy còn task chưa merge thì không nhận module khác. `pool.py claimable`: 🟢 nhận được · ⏳ chờ · 👤 đã có người.
- **`pool.py sync`:** merge `origin/BASE_BRANCH` vào branch hiện tại, in file docs đổi để đọc lại, cảnh báo khi contract / quy tắc / quyền / ADR đổi; conflict → `--abort`, báo file, không tự gộp. `pool.py wait` trả về ngay khi nhánh gốc có commit mới. `app.md`: sync bắt buộc trước khi chia task, khi wait báo, trước khi PR.
- `/agent-team:task M-n` (task.md mục 0.7): module của app, team thì `claim` trước, xong PR rồi dừng. `resume` nhận biết branch module của team.
- Mẫu `APP.md`: mục `## Lý do phụ thuộc`. Test team mới (remote = bare repo): 18 case.

## Cần làm thủ công
- Commit + push, `/plugin marketplace update multiple-agent`, khởi động lại Claude Code.
- **Key mới trong `.claude/agent-team.config`** (không phải secret): `APP_BUILD=auto|manual`, `SEED_CMD=` (vd `php artisan migrate:fresh --seed`).
- Team: config chung `APP_BUILD=manual`, `PUSH=1`, `BASE_BRANCH` đúng nhánh gốc; mỗi người `DEV_ID` trong `.claude/agent-team.local.config`. `04.Cay` đang `PUSH=0`, `BASE_BRANCH=master`: chuyển sang team thì đổi `PUSH=1`.
- App đang chạy: thêm mục `## Lý do phụ thuộc` vào `APP.md` và file contract cho module NẶNG trước khi `pool.py handoff`.

# Release notes - 24/11/2026 (v0.28.0 - dùng cho team)

## Thay đổi
- **Config riêng mỗi dev `.claude/agent-team.local.config`** (gitignore): ghi đè config chung cho `pool.py`, `progress.py`, `board.py`, guard, `agent-db-clone.sh`. Để trống = không ghi đè. Mẫu: `templates/agent-team.local.config.example` (`DEV_ID`, `MAX_PARALLEL`, `E2E_PORT_BASE`, `HANG_MINUTES`, `PROGRESS_LINES`).
- **Script plugin không commit nữa:** `init` thêm `.claude/agent-team/*.py`, `*.sh`, `__pycache__/`, `.claude/agent-team.local.config` vào `.gitignore`. Hook `sync.py` chép **đủ mọi script** mỗi phiên (clone mới của người trong team chưa có file nào) và báo khi dự án cũ còn commit script (kèm lệnh gỡ). Template vẫn commit.
- `pool.py fill`: worktree mới nhận script + config riêng chép từ thư mục chính (worktree chỉ có file đã commit).
- **`DEV_ID` trong task-id** (`YYYYMMDD-<DEV_ID>-<slug>`): branch không trùng giữa các dev.
- **Cột "Người chạy"** trong bảng Module (`templates/product/APP.md`); `app.md`: module `DESIGN` / `DOING` của người khác thì không động vào, nhận module thì ghi tên + commit + push ngay.
- README: mục "Dùng cho team". Test: pool 33, sync 15.

## Cần làm thủ công
- Commit + push, `/plugin marketplace update multiple-agent`, khởi động lại Claude Code.
- **File mới (không commit): `.claude/agent-team.local.config`** cho từng máy (copy từ mẫu). Không chứa KEY.
- Dự án đang commit script (vd `04.Cay`): thêm vào `.gitignore` 4 dòng
  `.claude/agent-team/*.py` `.claude/agent-team/*.sh` `.claude/agent-team/__pycache__/` `.claude/agent-team.local.config`
  rồi `git rm -r --cached .claude/agent-team/*.py .claude/agent-team/*.sh .claude/agent-team/__pycache__` và commit 1 lần.
- Bảng Module của app đang chạy: thêm cột "Người chạy" trước cột "Trạng thái" (Lead tự thêm khi resume nếu bạn bảo).

# Release notes - 24/11/2026 (v0.25.0 → v0.27.0 - Lead điều phối nhiều task song song)

## Thay đổi
- **1 phiên = 1 branch** (`agent/<task-id app>`). Task chạy song song mỗi task 1 git worktree + branch tạm `agent/<task-id>`, xong merge về branch phiên. Module đủ task ✅ → tag `<app>-m<n>-done`. User merge branch phiên 1 lần (hoặc tới tag). Bảng Module: cột "Branch gốc" → "Tag".
- **Chỉ Lead dùng git ghi** (commit / push / merge / tag / worktree / rebase...): hook chặn agent. Agent trả `File đã sửa: ...`, Lead commit theo role `[role] <task-id>: ...` (tránh 2 agent tranh `.git/index.lock`, commit lẫn file).
- **Loại task `ĐÃ CHIA`**: task con chia từ thiết kế module, bỏ S1-S2 (không debate lại), kế thừa phương án + contract. Hook cho sang S3 khi có `Tiêu chí nghiệm thu`, `Thiết kế module`, `Security duyệt solution`. Chỗ chưa rõ → GAP, đổi contract → quay về module.
- **Thiết kế module theo loại** (cột Loại trong bảng Module): `NHẸ` (SA viết + duyệt, không debate) / `VỪA` (1 đề xuất + 1 lượt WHY) / `NẶNG` (debate đầy đủ). SA ghi phụ thuộc **thật**, chia task với phụ thuộc **theo task**.
- **Script mới `pool.py`** (bảng `pool`, `pool_modules` trong board.db): `module` (mỗi lúc 1 module DESIGN; task chỉ add khi module SPLIT), `add`, `fill` (mở worktree cho task READY tới đủ `MAX_PARALLEL`, cổng E2E riêng, `.worktrees` vào `.git/info/exclude`), `set`, `merge-begin` (merge --no-commit; conflict → --abort, FIX), `merge-end pass|fail` (pass: commit merge 1 dòng `[lead]`, xoá worktree, tag khi module đủ; fail: --abort, FIX), `wait` (exit 0 có việc / 3 treo / 4 chờ tiếp), `status`, `resume`.
- **`MAX_PARALLEL` tự scale:** `fill` / `wait` đọc lại config mỗi lần. Tăng → mở thêm ngay; giảm → task đang chạy chạy tiếp, không mở mới. Đổi config không chặn merge.
- **Guard / heartbeat theo worktree:** gốc repo tính theo đường dẫn file hoặc `cd <worktree> &&` đầu lệnh → stage, vùng ghi, board, nhịp tim của đúng worktree. Đang điều phối thì không bắt `plan` ở thư mục chính, SubagentStop không ✅ nhầm bước.
- `agent-db-clone.sh e2e`: cổng lấy từ `.agent-team/e2e_port` của worktree (do `pool.py` cấp).
- Status line: bảng điều phối `Task | Việc | Agent | Trạng thái` (▶ đang chạy + giai đoạn + phút, 🟢 READY, ⏳ Chờ <task>, 🔀 Chờ merge / IT đang chạy, 🔧 Sửa, ⛔), dòng tổng `Module ✅ x/N · thiết kế: M-k · chạy a/MAX`.
- `resume`: đọc `pool.py resume` → làm tiếp task dở trong worktree, merge dở, rồi `fill`. Hook `sync.py` chép cả `pool.py`.
- Test: pool 30 (mới), guard 390, board 97, progress 30.

## Cần làm thủ công
- Commit + push, `/plugin marketplace update multiple-agent`, khởi động lại Claude Code (hook `sync.py` tự chép `board.py`, `progress.py`, `pool.py`; `agent-db-clone.sh` chép tay nếu project đã có bản cũ: hook chỉ chép khi khác bản, nên cũng tự chép).
- **Key mới trong `.claude/agent-team.config`** (không phải secret): `MAX_PARALLEL=8` (mặc định khi không ghi), `WORKTREE_DIR=.worktrees`, `E2E_PORT_BASE=4000`, `INTEGRATION_CMD=` (trống = TEST_CMD + E2E toàn bộ).
- App đang chạy (`04.Cay`): branch M-1 đã chứa trọn M-0 → dùng `agent/20261123-m1-dang-nhap-quyen` làm branch phiên; gắn tag M-0: `git tag 20261120-app-cay-ca-phe-m0-done agent/20261120-app-cay-ca-phe`.
- Mỗi task song song dùng 1 DB clone + 1 container E2E: `MAX_PARALLEL` theo RAM máy và quota token.

# Release notes - 23/11/2026 (v0.24.0 - status line dạng bảng có khung)

## Thay đổi
- `progress.py` (status line + `--list`): 3 bảng có khung `┌─┬─┐`, căn cột theo độ rộng hiển thị thật (✅ ⏳ = 2 ô, tiếng Việt có dấu = 1 ô):
  - Bảng module của app / task của module: `M | Module | Trạng thái` (module trước / đang làm `· bước k/N` / sau, phần còn lại gộp `+N module`). Module `BLOCKED` hiện ⛔ Chặn.
  - Bảng giai đoạn nằm ngang S1 Scout … S6 Đóng: ✅ / ▶ / ⏳.
  - Bảng bước (khi có `board.py plan`, hoặc 10 bước Phase A): `# | Bước | Role | Trạng thái`, ∥ song song.
  - Dòng cuối: chờ post, thiếu, WHY mở, ⚠ agent im lâu.
- `PROGRESS_LINES=1` vẫn về 1 dòng. Test progress: 30 case.

## Cần làm thủ công
- Commit + push, `/plugin marketplace update multiple-agent`, khởi động lại Claude Code (hook `sync.py` tự chép `progress.py`).

# Release notes - 23/11/2026 (v0.23.1 - status line có giai đoạn ở S1-S2, sửa tầng App)

## Thay đổi
- `progress.py`: task thường luôn có dòng giai đoạn `S1 Scout ✅  S2 Debate ▶  S3 Code ⏳ ...` (theo `.agent-team/stage`), nên S1-S2 (chưa có danh sách bước) vẫn thấy đang ở đâu. "Chưa có danh sách bước" chỉ nhắc ở S3-S5.
- Sửa: TASK.md ghi `- Module: N/A (...)` bị coi là thư mục module → mất tầng `App · x/N module xong`. Giờ chỉ nhận giá trị bắt đầu bằng `docs/`.
- Test progress: 28 case.

## Cần làm thủ công
- Commit + push để plugin cập nhật, rồi `/plugin marketplace update multiple-agent` + khởi động lại Claude Code (hook `sync.py` tự chép `progress.py` mới sang project).

# Release notes - 23/11/2026 (v0.23.0 - Lead tự điều phối module / task con tới hết)

## Thay đổi
- **App Phase B (`app.md` mục 10.2):** Lead tự chạy nối tiếp M-0 → M-1..n → M-E2E trong cùng phiên, mỗi module task-id + branch riêng (từ branch module trước). Không dừng hỏi "chạy module tiếp không?", không bắt user gõ `/agent-team:task` từng module.
- **Chỉ dừng khi:** GAP cần owner hoặc BLOCKED kỹ thuật mà mọi module còn lại đều phụ thuộc (module BLOCKED thì chạy tiếp module không phụ thuộc), hết bảng Module, hoặc hết quota / lỗi phiên.
- **Module (`module.md` mục 5):** đóng task MODULE xong tự chạy T-1 → T-n như trên.
- **`resume`:** chạy tiếp tới khi xong hết việc; task đang dở đã đóng mà bảng còn `TODO` / `DOING` thì tự mở module / task kế.
- `task.md` mục 10: task thuộc app / module đóng xong báo 3-5 dòng rồi chạy tiếp; báo cáo đầy đủ chỉ ở cuối.
- Bảng Module (`templates/product/APP.md`): Trạng thái `TODO` / `DOING` / `DONE` / `BLOCKED (<lý do>)`.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update multiple-agent`, khởi động lại Claude Code.
- App đang chạy (vd `04.Cay`): `/agent-team:resume` là Lead chạy tiếp M-1 → … → M-E2E.
- Không có KEY env mới.

# Release notes - 23/11/2026 (v0.22.0 - status line dạng bảng checklist)

## Thay đổi
- **Status line mặc định là bảng** (`progress.py`), cùng bảng với `progress.py --list` Lead dán vào chat:
  - Tầng trên (khi bảng đã điền): module của app (`APP.md`) hoặc task của module (`MODULE.md`), số đã xong, module / task đang làm `── bước k/N`.
  - Dưới: `# | Bước | Role | Trạng thái` với ✅ Xong / ▶ Đang làm <phút> / ⏳ Chờ, `∥` bước chạy song song. Quá 8 dòng: gộp đoạn ✅ đầu và ⏳ cuối.
  - App / Module Phase A: 10 bước cố định cùng kiểu bảng.
  - Dòng cuối: chờ post, WHY mở, ⚠ agent im lâu.
- Số phút "Đang làm" lấy từ `started_at` trong `board.db`, không ước lượng.
- Test progress: 26 case.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update multiple-agent`, khởi động lại Claude Code (hook `sync.py` tự chép `progress.py` mới sang project).
- **Key mới (không bắt buộc) trong `.claude/agent-team.config`:** `PROGRESS_LINES=table` (mặc định) | `1`. Status line chỉ hiện 1 dòng đầu của bảng → đặt `PROGRESS_LINES=1`. Không phải secret.

# Release notes - 23/11/2026 (v0.21.1 - .env được xem / sửa, chỉ cấm commit)

## Thay đổi
- **Guard:** `.env`, `.env.local`, `.env.production`... được Read / Edit / Write và dùng trong Bash (`cat`, `sed -i`...), mọi role.
- **Vẫn chặn:** commit khi đang stage `.env*`, push commit có `.env*` hoặc chuỗi giống secret; đọc / sửa `*.key`, `*.pem`, `master.key`, `id_rsa*`, `.npmrc`, `.pgpass`, `.netrc`, dump DB; `printenv` / `env` / `docker inspect` / `docker compose config`.
- Quy tắc mới (CLAUDE.md mẫu, agent dev / test / scout, `ask`, `task`): "Không commit `.env*`, key, credentials, dump DB". Sửa `.env` chỉ dòng cần thiết, KEY mới thêm cả vào `.env.example` (để trống giá trị), không in giá trị KEY ra chat / board.
- Test guard: 376 case.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update multiple-agent`, khởi động lại Claude Code.
- Project đã init: mục "## Agent Team" trong CLAUDE.md không tự cập nhật. Nếu còn dòng "Không đọc/sửa/commit `.env*`..." thì sửa thành "Không commit `.env*`, key, credentials, dump DB."
- ⚠ Giá trị KEY agent đọc từ `.env` sẽ nằm trong lịch sử hội thoại. `.env*` vẫn phải nằm trong `.gitignore`.

# Release notes - 23/11/2026 (v0.21.0 - checklist tự cập nhật, BE ∥ FE, tự đồng bộ script)

## Thay đổi
- **Tự đồng bộ script (hook mới `SessionStart` → `hooks/sync.py`):** đầu mỗi phiên, project đã init: `board.py`, `progress.py` (và script project đang dùng: gap-check, owner-form, kb-check, agent-db-clone) khác bản plugin → tự chép lại. Template trong `.claude/agent-team/templates/` khác bản plugin → chỉ báo, không ghi đè (có thể bạn đã sửa).
- **Tự thêm status line:** `.claude/settings.json` chưa có `statusLine` → tự thêm (giữ key khác). Đang có lệnh khác hoặc JSON lỗi → không sửa, chỉ báo.
- **Checklist tự đổi trạng thái:** Lead gọi agent X → bước ○ đầu tiên của X thành ▶ (hook guard); X chạy `board.py done` hoặc kết thúc (`SubagentStop`) → ✅. Gọi lại cùng agent trong 1 giai đoạn: tính là lượt chạy mới (trước đây bị "đã DONE" chặn `done`).
- **Bước song song `∥`** (hoặc ` // `) trong `board.py plan --set`; `progress.py --list` hiện dấu ∥, status line hiện `bước 1+2/3`.
- **Guard S3 có `FE_PATHS`:** kế hoạch phải cho `backend-dev ∥ frontend-dev` cùng nhóm, hoặc TASK.md có `- Song song: KHÔNG - <vì sao>`. Thiếu → chặn gọi agent.
- `board.db` của v0.20.0 tự thêm cột `grp`. Test: board 94, guard 366, progress 22, sync 13 (mới).

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update multiple-agent`, **khởi động lại Claude Code** (hook `SessionStart` mới chỉ nạp khi khởi động). Phiên đầu tiên sau đó sẽ tự chép script + thêm status line; status line hiện từ phiên kế tiếp nếu chưa hiện ngay.
- `.claude/settings.json` do hook tạo chỉ có `statusLine`, không chứa KEY: commit được.
- Không có KEY env mới.

# Release notes - 23/11/2026 (v0.20.0 - hiện bước đang làm và các bước còn lại)

## Thay đổi
- **Danh sách bước trong `board.db`** (bảng `plan_steps`): Lead lập `board.py plan <task> --set "bước 1 @role | bước 2 @role"`, đánh dấu `board.py step <task> <n> start|done|skip`. Lập lại giữa chừng: bước trùng tên giữ trạng thái. `board.py status` có mục "Các bước".
- **Status line bỏ %, bỏ thanh ▓░:** `[task] S3 CODE · bước 2/4: <tên> · còn: <bước chưa làm>`. `progress.py --list` in đủ ✅ xong / ▶ đang làm / ○ chưa làm, kèm `App: x/N module xong` (hoặc `Module: x/N task xong`) khi bảng đã điền.
- **App / Module Phase A:** 10 bước cố định, ✅ theo cổng trong `APP.md` / `MODULE.md` và file có thật (problem.md có G-n, requirements có R-n, flows có F-n, có mockup, có `QnA-v*.xlsx`...). Trước đây Phase A dùng cổng của task thường nên % đứng yên.
- **Guard:** Lead gọi agent (tool `Agent` / `Task`) ở S3-S5 khi task chưa có danh sách bước → chặn, bảo lập `plan` trước.
- `task.md`, `app.md`, `module.md`: Lead dán `progress.py --list` vào chat mỗi khi đổi bước; không tự đoán giờ xong.
- Test: board 82, guard 361, progress 20 case.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update multiple-agent`, khởi động lại Claude Code (matcher hook đổi).
- Project đã init: copy lại `scripts/board.py`, `scripts/progress.py` → `.claude/agent-team/` (chmod +x).
- Status line chưa hiện: kiểm `.claude/settings.json` của project có `"statusLine": {"type": "command", "command": "python3 .claude/agent-team/progress.py"}`.
- Không có KEY env mới.

# Release notes - 23/11/2026 (v0.19.2 - FE và BE chung 1 repo)

## Thay đổi
- `app.md` mục 9, `init.md`: FE và BE chung 1 repo → `FE_PATHS=""`, dồn đường dẫn FE vào `BE_PATHS`. `backend-dev` làm cả FE.
- `task.md` S3: `FE_PATHS` rỗng → không gọi `frontend-dev`.
- `app.md` mục 10: M-0 file test của starter (`tests/`, `phpunit.xml`, `e2e/`) do `test-executor` dựng ở S4.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update multiple-agent`.
- App đang chạy, FE chung repo: sửa `.claude/agent-team.config` → `FE_PATHS=""`, thêm đường dẫn FE vào `BE_PATHS`.

# Release notes - 22/11/2026 (v0.19.1 - phát hiện và xử lý agent treo)

## Thay đổi
- **Nhịp tim agent trong SQLite** (`board.db`, bảng `agent_runs`): hook mới `hooks/heartbeat.py` ghi mỗi lần subagent dùng tool (lần cuối, tool / lệnh đang chạy tối đa 80 ký tự) và hook `SubagentStop` tự ghi DONE khi agent kết thúc. Không bao giờ chặn tool.
- **Lead không kẹt vì 1 agent treo:** gọi agent `run_in_background: true` (bị từ chối thì foreground như cũ), rồi `board.py wait <task-id>`: đọc SQLite mỗi 30 giây, trả về ngay khi mọi agent DONE (exit 0), có agent im quá `HANG_MINUTES` (exit 3 → `TaskStop` + gọi lại đúng agent đó kèm lý do), hoặc sau ~9 phút chưa xong (exit 4 → wait tiếp). Treo = im lặng, không phải chạy lâu; lệnh có `timeout N` thì ngưỡng theo N.
- **Agent kết thúc bằng `board.py done --body "<≤ 5 dòng>"`**, Lead lấy kết quả từ SQLite (không phụ thuộc tin nhắn trả về). Sau `done`, board từ chối post / done thêm ở lượt đó và bảo agent kết thúc ngay (sửa lỗi agent báo xong rồi cứ gửi lại mãi). Việc dài báo `board.py progress --step "4/11 màn" --eta 20`.
- `board.py status` thêm mục Agent (DONE / đang làm / ⚠ im N phút + lệnh đang kẹt / chưa bắt đầu, tiến độ, thời gian thường mất của role). `board.py stuck`: agent treo + gợi ý `pgrep` để tắt lệnh kẹt từ terminal khác. Status line hiện ⚠ agent im lâu.
- **Guard chặn lệnh không tự dừng** (mọi người, kể cả Lead): `docker compose up` không `-d`, `tail -f`, `watch`, `npm|pnpm|yarn run dev|start|serve`, `rails s`, `php artisan serve`, `nodemon`, test `--watch` / `vitest` không `run`. Bọc `timeout <giây>` hoặc chạy nền `&` thì được. Role được `board.py done` / `progress` bằng tên mình.
- `resume`: agent DONE thì không gọi lại, chỉ gọi lại agent còn dở. Test: board 74, guard 357 case.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update multiple-agent`, khởi động lại Claude Code (hook mới `heartbeat.py`, `SubagentStop` chỉ nạp khi khởi động).
- **Key mới trong `.claude/agent-team.config`**: `HANG_MINUTES=10` (phút im lặng coi là treo). Không phải secret.
- Project đã init: copy lại `scripts/board.py`, `scripts/progress.py` → `.claude/agent-team/` (chmod +x); copy lại `templates/POST.md`.
- Cần Claude Code hỗ trợ agent chạy nền + `TaskStop` (đã kiểm có trong bản 2.1.330). Bản cũ hơn: Lead gọi foreground như trước, agent treo thì Esc + `/agent-team:resume`.

# Release notes - 22/11/2026 (v0.19.0 - giảm token)

## Thay đổi
- **Lead giữ ngữ cảnh gọn** (`task.md` mục 2b): không tự đọc bài post; biết debate qua kết quả agent trả về (≤ 5 dòng), `status`, `whys --open`; cần phán quyết 1 điểm thì `board.py read <task-id> --why <n>` (lệnh mới: câu hỏi, các lần trả lời, phiếu, dòng nhắc tới). Sửa TASK.md bằng Edit từng đoạn, không đọc lại cả file.
- **Tóm tắt bắt buộc:** `board.py close` từ chối khi lượt có bài mà chưa `summary`. Đổi giai đoạn (rời S2 / S3 / S4 / S5) bị hook chặn khi `board/SUMMARY.md` chưa có mục `## S<n>`; giai đoạn sau chỉ đọc SUMMARY.md + TASK.md, thiếu thì query board. `templates/SUMMARY.md` có sẵn mục S2-S5. `resume` đọc tóm tắt + `whys --open`, không đọc lại cả board.
- **Tìm code có mục tiêu, không quét mù cả repo:** hook chặn với mọi role (trừ Lead, Scout khi init / kb): Grep / Glob không đường dẫn ở gốc repo, `grep -r .`, `rg` không đường dẫn (trừ khi nhận từ pipe), `git grep` không pathspec, `find .` không `-maxdepth ≤ 2`, `ls -R .`, `tree`. Đọc file cụ thể / tìm trong thư mục cụ thể **không giới hạn**. Thứ tự: CONTEXT → KB + chỉ mục hàm → graphify → đúng file. Thiếu thông tin → trả **`HỎI LEAD`** (mẫu mới cuối `POST.md`); Lead tra KB hoặc gọi Scout đọc đúng phần, bổ sung CONTEXT rồi gọi lại. Dev trả thêm dòng "File đã đọc ngoài CONTEXT".
- **Mockup dùng chung `_wf.css` + `_wf.js`** (skill `wireframe` mục "File dùng chung"): ui-designer chép 1 lần, mọi màn chỉ link tới (giảm token viết mỗi màn). `board.py report` tự chèn 2 file khi nhúng mockup vào REPORT.html. Guard cho ui-designer ghi `_wf.css`, `_wf.js`, `index.html` trong `design/` của task. `gap-check` kiểm link `.css` / `.js` có file thật.
- Test: board 62, guard 346, gap-check 58 case.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update multiple-agent`, khởi động lại Claude Code.
- Project đã init: copy lại `scripts/board.py`, `scripts/gap-check.py` → `.claude/agent-team/` (chmod +x); copy lại `templates/SUMMARY.md`, `templates/POST.md` → `.claude/agent-team/templates/`.
- **Task đang làm dở:** trước khi đổi giai đoạn, thêm mục `## S<giai đoạn hiện tại>` vào `docs/agent-tasks/<task-id>/board/SUMMARY.md`, nếu không hook sẽ chặn.
- Mockup cũ (tự chứa CSS / JS) vẫn chạy và vẫn qua gap-check; muốn giảm token thì giao ui-designer tách ra `_wf.css` / `_wf.js`.
- Không có ENV / key mới.

# Release notes - 22/11/2026 (v0.18.7 - tên file form QnA-v<n>.xlsx)

## Thay đổi
- `owner-form.py build` sinh `QnA-v<n>.xlsx` (thay cho `owner-form-<n>.xlsx`). Số `n` tiếp theo bản lớn nhất đang có, tính cả file `owner-form-<n>.xlsx` cũ (đang có `owner-form-3.xlsx` thì bản mới là `QnA-v4.xlsx`). `import` đọc được cả file tên cũ.
- Sửa theo: `app.md`, `resume.md`, `templates/product/README.md`, README. Test owner-form: 68 case.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update multiple-agent`, khởi động lại Claude Code.
- Project đã init: copy lại `scripts/owner-form.py` → `.claude/agent-team/` (chmod +x). File `owner-form-<n>.xlsx` đã gửi client giữ nguyên, không cần đổi tên.
- Không có ENV / key mới.

# Release notes - 22/11/2026 (v0.18.6 - mockup chia 2 bên cho client)

## Thay đổi
- **Mockup chia 2 bên:** trái là **trang app như thật** (header: logo, menu, tài khoản / Đăng nhập; footer: bản quyền, liên hệ); phải là bảng **"HƯỚNG DẪN XEM MOCKUP (không phải phần của app)"**: mô tả màn, xem với vai trò, trường hợp (Có dữ liệu / Rỗng / Đang tải / Lỗi / Không có quyền / Điện thoại), đi thử theo luồng (chọn luồng, bước x/n ← Trước | Sau →, giữ luồng + vai trò khi sang màn sau), ghi chú màn (lời thường). Màn hẹp: bảng xuống dưới.
- **Không lộ mã nội bộ cho client:** R-n, AC-n, Q-n... gắn vào `data-r` / `data-q`, không in lên màn; ô "Hiện mã (cho team)" để team đối chiếu. Bỏ thanh luồng nhiều dòng và bảng nổi "XEM TRẠNG THÁI" của bản cũ.
- `gap-check.py` mục mới "mockup cho client": thiếu `aside.guide` hoặc chữ hiện trên mockup còn mã → thiếu. Sửa theo: skill `wireframe` (khung mẫu mới), `ui-designer`, `app.md`. Test gap-check: 56 case.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update multiple-agent`, khởi động lại Claude Code.
- Project đã init: copy lại `scripts/gap-check.py` → `.claude/agent-team/` (chmod +x). Mockup cũ sẽ bị `gap-check` báo thiếu: giao ui-designer vẽ lại theo khung mới (chỉ đổi trình bày, giữ nội dung).
- Không có ENV / key mới.

# Release notes - 22/11/2026 (v0.18.5 - câu hỏi owner ngắn, đủ ý)

## Thay đổi
- **Câu OWNER viết ngắn, đi thẳng vào điều cần quyết** (bỏ kiểu "tình huống có người + số liệu" làm câu dài mà mất ý chính): hỏi quy tắc, không hỏi 1 trường hợp; không kể chuyện tên người / phòng ban / số liệu; gộp câu cùng ý; viết tiếng Việt, từ tiếng Anh thông dụng (app, email, Excel, OTP, responsive, Admin...) giữ nguyên, không dịch. Câu hỏi ≤ 25 từ, Đề xuất ≤ 40 từ, Vì sao ≤ 30 từ. Có bảng Sai / Đúng lấy từ câu thật (responsive, lên cấp cây, phân quyền).
- `owner-form.py build` từ chối câu OWNER quá dài (báo số từ từng cột). Sửa theo: `app.md` mục 0b, `business-analyst`, `templates/product/questions.md`, `catalog/README.md`. Test owner-form: 67 case.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update multiple-agent`, khởi động lại Claude Code.
- Project đã init: copy lại `scripts/owner-form.py` → `.claude/agent-team/` (chmod +x), `templates/product/questions.md` (chỉ phần hướng dẫn đầu file). App đang chờ build form: BA viết lại câu quá dài trước khi `build`.
- Không có ENV / key mới.

# Release notes - 22/11/2026 (v0.18.4 - câu hỏi viết sau mockup)

## Thay đổi
- Câu OWNER chỉ viết / sửa sau khi mockup của màn liên quan xong; mockup đổi thì BA đối chiếu lại câu trỏ tới màn đó. BA mở mockup trước khi viết phần "người dùng thấy gì".

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update multiple-agent`, `/reload-plugins`.
- Không có ENV / key mới.

# Release notes - 22/11/2026 (v0.18.3 - mockup bấm được, câu hỏi cho client)

## Thay đổi
- Mockup bấm được như app thật: nút là link sang màn khác hoặc `#trạng-thái`, thanh luồng ← Trước | Sau →, `design/index.html` theo luồng. `gap-check.py` báo link hỏng và `index.html` thiếu màn.
- Nút chuyển trạng thái (có dữ liệu, rỗng, lỗi...) chuyển sang bảng nổi góc dưới phải "XEM TRẠNG THÁI", không lẫn với nút thao tác.
- Câu hỏi OWNER viết cho người không biết kỹ thuật: tình huống + đề xuất (người dùng thấy gì) + giải thích. `owner-form.py build` từ chối câu OWNER thiếu Vì sao hoặc có mã nội bộ / từ kỹ thuật. Form in "Đề xuất: ... / Giải thích: ...". Test: `test_gap_check.py` 53, `test_owner_form.py` 66.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update multiple-agent`, `/reload-plugins`.
- Project App / Module đang làm: copy lại `scripts/gap-check.py`, `owner-form.py` → `.claude/agent-team/`. Mockup cũ chưa có link → giao ui-designer thêm link + `index.html`, nếu không `gap-check` báo `THIEU` mục prototype.
- Câu OWNER cũ thiếu Vì sao hoặc có mã R-/F-... → BA viết lại trước khi `owner-form.py build`.
- Không có ENV / key mới.

# Release notes - 21/11/2026 (v0.18.2 - lệnh /agent-team:audit, mock, quy chuẩn trước kiến trúc)

## Thay đổi
- Lệnh mới `/agent-team:audit [--check | <module>]`: review cấu trúc, code, bảo mật, KB, skill/AI setup → `docs/audit/AUDIT-<ngày>.md` → owner duyệt → sửa KB / quy chuẩn / skill; lỗi code vào Backlog chạy bằng `/agent-team:task`. Template `templates/AUDIT.md`. code-reviewer, security, solution-architect thêm chế độ audit; resume làm tiếp audit dở.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update multiple-agent`, khởi động lại Claude Code.
- Không có ENV / key mới.

# Release notes - 21/11/2026 (quy chuẩn code trước kiến trúc)

## Thay đổi
- `project-setup.md` thêm mục 6 "Quy chuẩn code"; `/agent-team:app` A0 ghi quy chuẩn vào `docs/engineering/` trước A2, A2 viết kiến trúc theo quy chuẩn.

## Cần làm thủ công
- Dự án đã copy `docs/product/project-setup.md`: chép thêm mục 6 từ `templates/product/project-setup.md` và điền trước khi chạy `/agent-team:app`.

# Release notes - 21/11/2026 (mock FE trước, BE nối sau)

## Thay đổi
- FE / view dựng trước bằng mock khi BE chưa xong; sổ `MOCKS.md` (Lead ghi), bước SWAP trong task BE; hook chặn S6 khi mock chưa `VERIFIED` hoặc file mock còn. Test: `test_guard.py` 321 case (+5).

## Cần làm thủ công
- Config mới: `MOCK_PATHS` (1 thư mục mock, trong `FE_PATHS` hoặc `BE_PATHS`). Thêm vào `.claude/agent-team.config` của project.
- Project đã init: copy `templates/MOCKS.md` → `.claude/agent-team/templates/`.
- Cập nhật plugin: `/plugin marketplace update multiple-agent`, khởi động lại Claude Code.

# Release notes - 20/11/2026 (v0.18.1)

## Thay đổi
- **Quy chuẩn code tách BE / FE** trong KB dự án `docs/engineering/`: `coding-standards.md` (chung: đặt tên, xử lý lỗi chung, logging, config, comment, git) · `backend.md` (phân tầng, controller, service, model, validation, kiểm quyền, style API, query, job, gọi dịch vụ ngoài, test BE) · `frontend.md` (cấu trúc, component, state, gọi API, form, trạng thái màn, theme, responsive, a11y, ẩn/hiện theo quyền, test FE). Mỗi quy tắc: 1 câu + ví dụ đúng / sai + `file:dòng` + nhãn.
- backend-dev đọc chung + `backend.md`; frontend-dev đọc chung + `frontend.md`; Code Reviewer đọc theo phần diff; Scout ghi đúng file khi init / kb; test-executor đọc mục Test.
- `backend.md` / `frontend.md` là **1 bảng** `Mã | Nhóm | Quy tắc | Đúng | Sai | Nguồn | Nhãn`, mã `BE-n` / `FE-n` (không đổi, không dùng lại), đầu file có hướng dẫn điền + danh sách Nhóm + 2 dòng mẫu `Example`. Code Reviewer dẫn mã khi báo lỗi ("vi phạm BE-3").
- `kb-check.py`: bắt buộc `backend.md` khi config có `BE_PATHS`, `frontend.md` khi có `FE_PATHS`; mỗi dòng `BE-` / `FE-` phải có nhãn + nguồn (`Planned` được bỏ nguồn file:dòng), không trùng mã, không còn dòng `Example`. Test: `test_kb_check.py` 48 case.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update multiple-agent`, khởi động lại Claude Code.
- Project đã init: copy `templates/kb/engineering/backend.md`, `frontend.md` → `docs/engineering/` (không ghi đè); chuyển phần riêng BE / FE đang nằm trong `docs/engineering/coding-standards.md` sang 2 file mới (hoặc chạy `/agent-team:kb engineering` để Scout làm); copy lại `scripts/kb-check.py` → `.claude/agent-team/` (chmod +x). Chưa làm thì `kb-check` báo `THIEU` 2 file mới.
- Không có ENV / key mới.

# Release notes - 20/11/2026 (đổi tên marketplace)

## Thay đổi
- Tên marketplace trong `.claude-plugin/marketplace.json`: `kevin-agent-team` → `multiple-agent` (lệnh cài: `agent-team@multiple-agent`). Tên plugin và lệnh `/agent-team:...` giữ nguyên.

## Cần làm thủ công (mỗi máy đã cài, 1 lần)
- Trong Claude Code:
```
/plugin marketplace remove kevin-agent-team   (đã cài bản tên kevin: remove kevin)
/plugin marketplace add <repo GitHub hoặc đường dẫn thư mục 03.Multiple-Agents>
/plugin install agent-team@multiple-agent
```
- Khởi động lại Claude Code. Từ nay cập nhật bằng `/plugin marketplace update multiple-agent`.

# Release notes - 20/11/2026 (v0.18.0)

## Thay đổi
- **Đổi tên `/agent-team:run` → `/agent-team:task`** (`commands/run.md` → `commands/task.md`), không giữ tên cũ. Ba lệnh theo phạm vi: `task` (1 task) · `module` (1 module mới) · `app` (cả app). Mọi chỗ nhắc `run` đã đổi theo (app, resume, init, ask, mục CLAUDE.md, README, THIRD-PARTY, template APP.md).
- **Lệnh mới `/agent-team:module <ý tưởng>`**: module mới trong app đang chạy, làm như App Mode Phase A nhưng phạm vi 1 module, tài liệu ở `docs/product/modules/<tên>/`, cổng ở `MODULE.md`:
  - **M0 nền từ KB** (Scout): vai trò, P-, BR-, F-, màn, chỉ mục hàm, `graphify affected` → không hỏi lại stack / auth / vai trò đã có; chỉ điều mới mới thành câu hỏi.
  - Mockup màn mới + **màn cũ bị sửa**; săn gap thêm **ảnh hưởng ngược** (quyền cũ, dữ liệu cũ, hàm / API cũ, báo cáo) → bảng "Ảnh hưởng ngược" + test hồi quy; đổi hành vi phần cũ phải hỏi owner qua form.
  - **Owner duyệt qua form** như App Mode. Sau duyệt: **ghép vào KB** (BR-, P-, vai trò, F-, `modules/<tên>/`, nhãn `Confirmed`), chia **task con** T-1..n → `/agent-team:task docs/product/modules/<tên> T-<n>`.
- `gap-check.py`, `owner-form.py`: thêm `--dir=<thư mục>`; file cổng đọc `MODULE.md` nếu có, không thì `APP.md`; SPEC.md của module sinh trong thư mục module.
- Guard: file trong `docs/product/modules/<tên>/` cùng chủ sở hữu như `docs/product/`; `Loại: MODULE` không được sang S3 (chỉ tài liệu); task con có `- Module: <thư mục>` chỉ sang S3 khi `MODULE.md` có `Owner duyệt: APPROVED`, sang S6 chạy `gap-check --dir=`.
- Template mới `templates/product/module/MODULE.md` (cổng + Ảnh hưởng ngược + Task), `intake.md` (nền từ KB). `TASK.md` thêm dòng `- Module:`. `resume` xử lý `Loại: MODULE`.
- Test: `test_gap_check.py` 49 case (+6), `test_guard.py` 316 case (+11).

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`, khởi động lại Claude Code.
- **Gõ `/agent-team:task` thay cho `/agent-team:run`** (tên cũ không còn).
- Project đã init: thay mục "Agent Team" trong `CLAUDE.md` bằng `templates/claude-md-section.md` (đang ghi `/agent-team:run`); copy lại `templates/TASK.md` → `.claude/agent-team/templates/` (thêm dòng `- Module: N/A`); copy lại `scripts/gap-check.py`, `owner-form.py` → `.claude/agent-team/` (chmod +x).
- Task đang làm dở bằng `run`: làm tiếp bằng `/agent-team:resume <task-id>` như cũ.
- Không có ENV / key mới.

# Release notes - 20/11/2026 (v0.17.0)

## Thay đổi
- **Chỉ mục hàm `docs/functions/`**: graph (Graphify) cho biết hàm nào nối với hàm nào, chỉ mục cho biết **mỗi hàm làm gì**, để dev tìm theo nghĩa và dùng lại thay vì viết trùng. Mỗi model / bảng 1 file (`order.md`...), hàm dùng chung ở `_shared.md`, mục lục `README.md`. Mỗi hàm public 1 dòng `Hàm | Ý nghĩa | Tham số chính | Trả về | file:dòng`. Hàm chạm nhiều model ghi ở model chính, file kia 1 dòng `→ xem`.
- `kb-check.py`: so chỉ mục với `graphify-out/graph.json` (hoặc `merged-graph.json`): hàm public trong `FUNCTION_INDEX_PATHS` chưa có dòng → thiếu; dòng trỏ hàm không còn trong code → thừa; graph build ở commit khác HEAD → nhắc `graphify update`. Hàm private / không export bị bỏ qua (đoán theo cú pháp Ruby, PHP, JS/TS, Python, Go, Java...). File chỉ mục cũng được kiểm `verified-at`, nguồn `file:dòng`, CŨ như KB khác. `--functions` in đủ danh sách thiếu / thừa kèm `file:dòng`.
- Scout: dựng chỉ mục khi init / kb (mảng mới "Chỉ mục hàm", đọc thân hàm để viết nghĩa); CONTEXT.md thêm mục "Hàm có sẵn liên quan". backend-dev / frontend-dev: 3 bước trước khi viết hàm mới (tìm → dùng lại → viết mới + thêm dòng cùng commit). Code Reviewer + skill `code-review`: hàm trùng nghĩa hoặc thiếu / sai dòng chỉ mục = High.
- Guard: `docs/functions/` do Architect, backend-dev, frontend-dev ghi (Scout khi init / kb).
- Template mới `templates/kb/functions/README.md`. Test: `test_kb_check.py` 39 case (+10), `test_guard.py` 305 case (+5).

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`, khởi động lại Claude Code.
- **Key mới trong `.claude/agent-team.config`**: `FUNCTION_INDEX_PATHS` (vd `"app/services app/models app/repositories"`; để trống = không dùng chỉ mục hàm). Không phải secret.
- Project đã init: copy lại `scripts/kb-check.py` → `.claude/agent-team/` (chmod +x), `templates/CONTEXT.md` → `.claude/agent-team/templates/`, `templates/kb/functions/README.md` → `docs/functions/README.md`. Chạy `graphify update .` rồi `/agent-team:kb` để Scout dựng chỉ mục.

# Release notes - 20/11/2026 (v0.16.1)

## Thay đổi
- **Tiến độ task (%):** thêm `scripts/progress.py`, hiện trên status line: `[task] S3 CODE ▓▓▓▓▓░░░░░ 52% · chờ: <role chưa post> · WHY mở: n · thiếu: <mục TASK.md còn TODO>`. Lead in dòng này vào chat sau mỗi lần đổi giai đoạn. Test: `python3 tests/test_progress.py`.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`, khởi động lại Claude Code.
- Project đã init: copy `scripts/progress.py` → `.claude/agent-team/progress.py` (chmod +x), thêm vào `.claude/settings.json`: `"statusLine": {"type": "command", "command": "python3 .claude/agent-team/progress.py"}`.

# Release notes - 20/11/2026 (v0.16.0)

## Thay đổi
- **App Mode: form cuối dựa trên debate + mockup.** Thứ tự mới: A2 debate (team tự làm rõ) → A3 nháp trọn app → A3b mockup mọi màn → A4 săn gap (thêm ui-designer) → debate chốt câu hỏi → form. Lượt 2 chỉ cho câu "không", ô trống, góp ý đổi logic.
- **Form xếp theo hành trình:** `questions.md` thêm cột `Nhóm`, `Màn` (cuối bảng). Form có cột `Màn / mockup`, dòng tiêu đề mỗi nhóm, mỗi luồng F-n có câu xác nhận luồng.
- `owner-form.py build` chặn khi: `APP.md` chưa `Debate: DONE` / `Challenger: DONE`, chưa có mockup, câu OWNER thiếu `Nhóm`, câu trong luồng thiếu `Màn`, luồng F-n chưa có câu.
- `import` đọc cột trả lời / mã theo dòng tiêu đề (đọc được cả form bản cũ).
- Sửa theo: `app.md`, `resume.md`, `business-analyst`, `ui-designer`, `templates/product/APP.md`, `questions.md`, README. Test owner-form: 62 case.
- **KB: quyền 3 tầng + logic ở 1 chỗ.** `roles-and-permissions.md` = vai trò + điều kiện `C-`; mẫu mới `permission-matrix.md` (vai trò × hành động `P-`, không ô trống); mẫu mới `flows/README.md` (luồng qua nhiều page `F-n`); `modules/README.md` có danh sách module, bảng tra Route → file KB, mẫu `screens/<màn>.md`. Page chỉ ghi mã `BR-` / `P-` / `F-`.
- `kb-check.py`: kiểm nguồn `file:dòng` có thật (theo `REPOS`), **CŨ** khi code trích dẫn đổi sau `verified-at`, `BR-` đủ nhãn + nguồn, ma trận quyền, mã trỏ tới có thật, module / route có KB. `--index` tra ngược mã → page. Test: 29 case.
- Guard: `docs/permission-matrix.md`, `docs/flows/` do BA ghi. Sửa theo: `scout`, `security`, `business-analyst`, skill `test-case-design` (mỗi ô ma trận 1 case), `kb.md`, `templates/kb/README.md`.

## Cần làm thủ công
- Cập nhật plugin: `/plugin marketplace update kevin-agent-team`, khởi động lại Claude Code.
- Project đã init: copy lại `scripts/owner-form.py` + `gap-check.py` → `.claude/agent-team/` (chmod +x).
- App đang dở: thêm 2 cột `| Nhóm | Màn |` vào cuối bảng `questions.md`, thêm `- Debate: TODO` vào `APP.md`. Chưa build form thì làm A3b + A4 + debate trước.
- Mẫu `examples/owner-form-sample.xlsx` / `.html` còn bố cục cũ.
- Project đã init: copy lại `scripts/kb-check.py` → `.claude/agent-team/` (chmod +x); copy `templates/kb/permission-matrix.md`, `templates/kb/flows/` vào `docs/` (không ghi đè), thêm 2 bảng `Danh sách module`, `Tra page` vào `docs/modules/README.md`. Rồi chạy `/agent-team:kb` để Scout dựng ma trận + luồng.
- KB cũ ghi nguồn chỉ tên file (`booking_policy.rb:12`) → `kb-check` báo "không có file": sửa thành đường dẫn từ gốc repo.

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
