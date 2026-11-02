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
