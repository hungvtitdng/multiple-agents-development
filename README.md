# Agent Team - debate 4 người chọn best solution, rồi code, test, review

Plugin cho Claude Code. Đưa 1 task → Lead + BA + Architect + Test Design debate, Lead chốt best solution (chọn một hoặc gộp ý), team code, test, review, push lên branch riêng. Thiết kế đầy đủ: `docs/design.md`.

## Cấu trúc

```
├── .claude-plugin/marketplace.json
├── plugins/agent-team/
│   ├── .claude-plugin/plugin.json
│   ├── agents/          ← 11 role (Lead = session chính, nằm trong commands/run.md)
│   ├── commands/
│   │   ├── run.md       ← /agent-team:run    - playbook của Lead
│   │   ├── app.md       ← /agent-team:app    - làm cả app từ ý tưởng (hỏi owner → tài liệu → owner duyệt → build từng module)
│   │   ├── resume.md    ← /agent-team:resume - làm tiếp task dang dở (hết quota, lỗi)
│   │   ├── ask.md       ← /agent-team:ask    - hỏi về logic dự án, có dẫn nguồn
│   │   ├── kb.md        ← /agent-team:kb     - dựng/làm đầy KB từ code (nhiều Scout, kiểm bằng kb-check)
│   │   └── init.md      ← /agent-team:init   - cài cho 1 project, dựng KB
│   ├── hooks/           ← hooks.json, guard.py (chặn thật), show_post.py
│   ├── scripts/         ← agent-db-clone.sh, kb-check.py, board.py (board chat SQLite), gap-check.py (App Mode)
│   ├── skills/          ← 10 skill chung, agent tự nạp khi cần
│   ├── catalog/         ← mặc định theo loại app (chung, quản lý nội bộ, đặt lịch) để bù ý owner không nghĩ tới
│   └── templates/       ← TASK, SUMMARY, POST, CONTEXT, config, mục CLAUDE.md, kb/ (khung docs/), product/ (App Mode)
├── docs/design.md       ← thiết kế
├── tests/
└── release-notes.md
```

## Đội hình (12 agent)

| Nhóm | Role | Model |
|---|---|---|
| **Debate** | Lead, business-analyst, solution-architect (Architect), test-designer | opus |
| Chuẩn bị | scout | sonnet |
| Làm | backend-dev, frontend-dev, test-executor | sonnet |
| Kiểm | code-reviewer | sonnet |
| Kiểm (mù ticket, VỪA/LỚN, ở S5) | challenger: chỉ nhận yêu cầu gốc + diff, tự dựng lại yêu cầu, chấm met / not met / can't tell. Hook chặn nó đọc `docs/` | sonnet |
| Kiểm | security (bắt buộc mọi task) | opus |
| Debate (chỉ khi task có UI) | ui-designer: wireframe đen trắng đủ chức năng + trạng thái, hỏi WHY về luồng thao tác | sonnet |
| Task LỚN | technical-architect (tách khỏi Architect) | opus |

## Luồng 1 task

```
/agent-team:run <task>
   │
 Lead phân loại NHỎ / VỪA / LỚN, tạo branch agent/<task-id>
   │
   ├─ NHỎ (Fast Track): Lead viết tiêu chí nghiệm thu → Dev → test → Code Reviewer ∥ Security
   │
   └─ VỪA / LỚN
       Scout đọc KB + repo MỘT lần → CONTEXT.md
       DEBATE (subagent, mỗi lượt chạy song song, kết quả chỉ về Lead)
         Lượt 1: Architect đưa A/B/C │ BA viết AC
         Lượt 2: BA │ Architect │ Test Design phản biện mọi phương án + chấm điểm kín
         Lượt 3 (chỉ khi cần): bất đồng lớn, Security Critical/High, gộp ý
       Lead chốt: chọn một HOẶC gộp ý các phương án → TASK.md
       Security duyệt nhanh solution (kể cả giải pháp gộp)
       CODE  BE ∥ FE  →  TEST (Test Design viết case, Test Execution chạy)
       REVIEW Code Reviewer ∥ Security  →  cập nhật KB  →  ĐÓNG, push
```

- **Không hỏi user.** Thiếu business rule: Lead chọn best solution, ghi `Assumption`, liệt kê ở báo cáo cuối.
- Giới hạn: debate 3 lượt, sửa 3 vòng/issue rồi Lead phán quyết. Lỗi Security Critical/High không ai override (không xử lý được → `BLOCKED`).
- Agent là **subagent**: trả kết quả (≤ 15 dòng) cho Lead, không nhắn nhau, không ghi board/TASK.md. Lead chép vào `board/` để bạn đọc lại.

## Board chat (SQLite) và skill

```
          Lead (mở/đóng lượt, tóm tắt, export)
                     │
   BA ── Architect ── Test Design ── Security ── Code Reviewer ── Dev
     \        \            |            /             /         /
      └────────┴─── .agent-team/board.db (board.py) ───┴─────────┘
                 read: tóm tắt lượt trước + toàn bộ lượt đang mở
                 post: chỉ bằng tên mình · @role = phải trả lời
                     │ S6
                     ▼
      docs/agent-tasks/<task-id>/board/DEBATE.md  (export, commit)
```
- Agent tự đọc board nên Lead **không chép lại** ý kiến giữa các lượt. Điểm chấm vẫn chỉ trả riêng về Lead.
- Thiết kế mỗi task (`design/`): workflow nghiệp vụ + sơ đồ trạng thái (BA), sequence (Architect), wireframe đen trắng (ui-designer). Báo cáo vẽ sẵn sơ đồ thành hình (cần `mmdc`), nhúng wireframe, client xác nhận từng mục. Mẫu: `examples/design-sample/`.
- Báo cáo mỗi task: `board.py report <task-id>` → `docs/agent-tasks/<task-id>/REPORT.html` (dashboard gửi client: giả định tô đỏ để client xác nhận, bảng so sánh phương án) + `REPORT.md`. Xem mẫu: `examples/report-sample.html`.
- Hook chặn: post bằng tên role khác, role dùng `open/close/summary/export`, challenger đọc board, gọi board qua biến.

| Skill (`agent-team:<tên>`) | Ai dùng |
|---|---|
| `debate-board` | Mọi role trên board |
| `acceptance-criteria` | BA, Test Design |
| `test-case-design` | Test Design |
| `security-review` | Security |
| `migration-safety` | Architect, TA, Backend (file migration chỉ sinh bằng `agent-db-clone.sh generate` trong container) |
| `test-automation` | Test Execution |
| `code-review` | Code Reviewer |
| `decision-record` | Architect, TA, Lead |

Skill chỉ chứa **nguyên tắc chung, không gắn framework**. Cách làm riêng của từng dự án nằm trong KB `docs/` (Scout viết nháp theo stack khi init/kb):

| Skill | File riêng của dự án |
|---|---|
| `security-review` | `docs/security/review-patterns.md` |
| `migration-safety` | `docs/database/migration-rules.md` |
| `test-automation` | `docs/testing/automation-guide.md` |
| `code-review` | `docs/engineering/review-checklist.md` (mục "Mẫu tìm lỗi theo stack") |

Agent đọc file của dự án trước; thiếu mẫu thì làm theo nguyên tắc chung và đề xuất bổ sung. Ví dụ nội dung cho dự án Rails + JS: `examples/rails-js/`.

## Responsive + E2E trình duyệt (Playwright)

```
VIEWPORTS="375 768 1280" (config; chỉ máy tính: "1280")
   │
   ├─ wireframe: mọi màn có tab Mobile        (gap-check báo thiếu)
   ├─ test case: trạng thái × chiều rộng       (không cuộn ngang, nút ≥ 44px, menu ☰, bảng)
   ├─ frontend-dev: breakpoint của dự án, không width cố định
   ├─ code-reviewer: lỗi responsive = High
   └─ agent-db-clone.sh e2e <task-id>
        app (APP_START_CMD) chạy trong container nối DB clone → (FE trên máy nếu tách repo)
        → E2E_CMD trên máy, mỗi chiều rộng 1 project Playwright
        → ảnh docs/testing/evidence/<task-id>/<TC>-<trạng thái>-<rộng>.png → tắt app
```
Hook chặn S5 khi task có UI mà `E2E` không PASS, hoặc thiếu ảnh ở một chiều rộng. Khung `playwright.config.ts` + helper `shot`, `expectResponsive`: skill `test-automation` mục 1b.

## Làm cả app từ ý tưởng (`/agent-team:app <ý tưởng>`)

```
PHASE A: chỉ tài liệu (stage S1-S2)
 A0 Intake        Lead tách ý owner B-n, điền phiếu; câu nghiệp vụ ghi sổ OWNER, câu kỹ thuật ghi sổ DEV
 A1 Vấn đề        BA: mục tiêu G-n + 12 góc nhìn (không ô trống), mỗi câu hỏi có 1 đề xuất
 A2 Giải pháp     debate như run (WHY, chấm điểm, Security): kiến trúc + stack đề xuất (câu DEV)
 A3 Nghiệp vụ     mặc định từ catalog/ → FORM lượt 1 (A owner, B dev) → BA: requirements R-n, flows F-n, data
 A4 Săn gap       challenger (chỉ đọc ý tưởng gốc) ∥ test-designer ∥ security ∥ BA → câu mới → form lượt sau
 ⛔ Owner chốt    logic chốt bằng form (owner không đọc tài liệu, không xem wireframe)
 A3b Wireframe    ui-designer: mọi màn S-n, đen trắng, 5 trạng thái + gap-check --spec
 A5 Chia module   APP.md: M-0 khung project, M-1..n theo phụ thuộc, M-E2E
PHASE B: M-0 trong task app (S3-S6), M-1..n mỗi module 1 /agent-team:run, lần lượt
```

**Form hỏi owner + dev** (`owner-form.py build` → `docs/product/owner-form-<n>.xlsx`, mở bằng Excel hoặc Google Sheet). 1 file, 2 mục; mục A cho owner:

| # | Câu hỏi | Đề xuất của team | Owner duyệt / góp ý |
|---|---|---|---|
| 1 | Khách đã đặt lịch muốn huỷ thì sao? | Cho huỷ trước 2 giờ, sau đó không huỷ online được | *(owner ghi `OK` hoặc góp ý)* |

Mục B cho dev:

| # | Câu hỏi | Đề xuất của team | Dev duyệt / góp ý |
|---|---|---|---|
| 1 | Server có SMTP nội bộ không? | Có, cấu hình bằng `.env` | *(dev ghi `OK` hoặc trả lời)* |

Gửi lại file → `owner-form.py import <file .xlsx|.csv>`: `OK` = duyệt đề xuất · `không` = BA / Architect đề xuất lại lượt sau · chữ khác = góp ý, ghi nguyên văn · để trống = vẫn chờ. Mẫu: `examples/owner-form-sample.xlsx`, `examples/owner-form-sample.html`.

| Khác `run` | Chi tiết |
|---|---|
| Hỏi owner / dev | Không `AskUserQuestion`: mọi câu vào 1 form, mục A nghiệp vụ (`OWNER`), mục B kỹ thuật (`DEV`), mỗi câu 1 đề xuất best solution, gom ít lượt nhất. Câu kỹ thuật làm đổi logic → tách câu logic cho owner + câu hạ tầng cho dev. Câu mức CAO phải có câu trả lời của owner; THẤP được giả định. Chờ owner: task `BLOCKED`, nhận file rồi `/agent-team:resume <task-id> <file>` |
| Tài liệu sản phẩm | `docs/product/` (mẫu ở `templates/product/`, cột cố định) |
| Chống sót ý | 12 góc nhìn · `catalog/` mặc định theo loại app · flow có cột "Nếu lỗi" · Dữ liệu × CRUD · vòng đời trạng thái · vai trò × màn · truy vết B → R → S · challenger mù |
| Cổng | Hook chặn S3 của task APP khi `gap-check.py --gate` còn thiếu; chặn S3 của mọi module khi `APP.md` chưa `Owner duyệt: APPROVED` |
| Không có remote | `PUSH=0`: không fetch/push, module sau tạo branch từ branch module trước |

**Tài liệu ghi lại toàn bộ:** `gap-check.py --spec` sinh `docs/product/SPEC.md` = mọi tài liệu app trong 1 file (ý tưởng, mục tiêu, stack, yêu cầu, flow, màn + link wireframe, dữ liệu, mặc định, câu hỏi, truy vết B → R → S, quyết định, module). Module đổi yêu cầu thì BA sửa `docs/product/`, Lead sinh lại SPEC; hook chặn S6 khi SPEC cũ hơn tài liệu. Mỗi task vẫn có `docs/agent-tasks/<task-id>/` (TASK.md, design/, board, REPORT) như `run`.

`gap-check.py` (chạy được bất cứ lúc nào): báo B-n chưa có yêu cầu, R-n không có nguồn (tự bịa), câu hỏi CAO còn mở, mặc định owner chưa chọn, flow thiếu nhánh lỗi, màn mồ côi / chưa có wireframe, vai trò không có trên màn, dữ liệu thiếu đường tạo/xoá, trạng thái không vào/ra được.

## Hỏi về logic dự án (`/agent-team:ask <câu hỏi>`)

Chỉ đọc, không tạo task. Lead chọn người trả lời, lấy nguồn từ `docs/` rồi đối chiếu code:

| Loại câu hỏi | Người trả lời |
|---|---|
| Nghiệp vụ, quy tắc, quyền | business-analyst |
| Kiến trúc, API, DB, tích hợp | solution-architect (sâu: + technical-architect) |
| Test, độ phủ | test-designer |
| Bảo mật, phân quyền | security |
| Tra một chỗ trong docs | Lead trả lời luôn |
| Xuyên nhiều mảng | 2 role song song, Lead gộp và nêu chỗ khác nhau |

Nguồn theo thứ tự: KB (`docs/`) → `LESSONS.md` → `TASK.md` các task trước → code (`file:dòng`, Graphify). Mỗi ý có nguồn và nhãn `Verified/Unverified/Assumption`; KB lệch code thì tin code và ghi "KB nên cập nhật" (không tự sửa); không có nguồn thì nói thẳng, không bịa.

## Knowledge Base (`docs/`)

```
docs/
├── project-overview, architecture, tech-stack, domain-model, business-rules,
│   roles-and-permissions, glossary (.md)
├── engineering/   quy chuẩn code + checklist clean code
├── api/ database/ integrations/ decisions/ modules/<tên>/
├── testing/       strategy, cases/<task-id>.md, coverage-matrix, test-report
├── security/      findings, permission-decisions
└── agent-tasks/<task-id>/   TASK.md, CONTEXT.md, board/
```
- Mỗi thư mục có chủ ghi riêng (hook chặn), nhãn `Verified/Unverified/Planned/Deprecated`, `verified-at: <commit>`.
- `/agent-team:init` dự án có sẵn code: dựng luôn KB bằng quy trình của `/agent-team:kb`: Bản đồ → nhiều Scout đọc sâu logic song song (module, kiến trúc/API/DB, frontend, quy chuẩn/test) → Scout tổng hợp nghiệp vụ → `kb-check.py` kiểm, gọi lại Scout cho file còn thiếu (tối đa 2 vòng). Mọi mục `Observed/Unverified/Assumption` kèm `file:dòng` và `verified-at`. `--skip-kb` để bỏ qua.
- `kb-check.py`: file KB nào còn là khung (thiếu `verified-at: <commit>` hoặc thiếu nguồn `file:dòng`). Phần chưa quét được ghi trong `docs/README.md` mục "Tình trạng KB", không giấu.
- `/agent-team:kb [--check | <module>]`: dựng/làm đầy/làm mới KB bất cứ lúc nào, tiếp tục được theo module. Không chạy khi đang có task (hook chặn Scout ghi KB).
- Task đổi API/DB/rule/màn hình mà chưa cập nhật KB → không sang S6.
- Quy chuẩn code lấy từ pattern đang dùng nhiều nhất; Code Reviewer review theo `docs/engineering/`. Dev chạy `LINT_CMD`/`FORMAT_CMD` trước khi commit.

## Chặn thật bằng hook (guard.py)

| Áp dụng | Chặn |
|---|---|
| Mọi agent | Đọc/sửa `.env*`, `*.key`, `*.pem`, dump DB. `printenv`, `docker inspect`, `docker compose config` |
| Mọi agent | Push vào main/master/develop, force push, xoá branch, `reset --hard`, `clean -f`. Push khi diff có secret |
| Mọi agent | `db:migrate`, `db:drop`... không qua `agent-db-clone.sh` |
| Project có agent-team | Commit không đúng một dòng `[role] task-id: mô tả`, có body/trailer (`Co-authored-by`, `Signed-off-by`), `--signoff` |
| BA, Architect, TA, Test Design, Code Reviewer, Security, Scout | Sửa code; Bash ngoài danh sách đọc/test/lint; redirect, `tee`, `sed -i`, `--fix`. Chỉ ghi KB của mình |
| backend-dev, frontend-dev, test-executor | Sửa file ngoài vùng của mình (`BE_PATHS`/`FE_PATHS`/`TEST_PATHS`, kèm `*_spec.*`, `*.test.*`, `__tests__/`) |
| Mọi role (trừ Lead) | Ghi `docs/agent-tasks/` (TASK, board) trừ Scout ghi `CONTEXT.md`; ghi KB của role khác (xem bảng chủ ghi trong `docs/README.md`) |
| Mọi role (trừ Lead) | Đọc/ghi `.agent-team/` |
| Mọi role (trừ Lead) | `board.py` ngoài `post/read/status`; post bằng `--role` khác tên mình; challenger dùng board |
| Mọi role (trừ Lead) | Ghi `docs/product/` sai chủ: BA (problem, coverage, defaults, requirements, flows, data), ui-designer (screens, design/), còn lại chỉ Lead |
| Lead | Đổi giai đoạn khi TASK.md chưa đủ điều kiện (xem dưới) |

### Gate chuyển giai đoạn (Lead ghi `.agent-team/stage`, hook kiểm TASK.md)

| Sang | Cần trong TASK.md |
|---|---|
| S3 | `Loại`; NHỎ: `Tiêu chí nghiệm thu`; VỪA/LỚN: `Phương án chốt` + `Security duyệt solution: APPROVED` + `Workflow`, `UI mockup` (file có thật); không còn WHY chưa thống nhất |
| S3 (APP) | `Phương án chốt` + `Security duyệt solution`; hook **chạy** `gap-check.py --gate --spec-check`: tài liệu app đủ, owner đã duyệt, SPEC.md khớp |
| S3 (module, có `docs/product/APP.md`) | Như VỪA/LỚN + `APP.md` có `Owner duyệt: APPROVED` |
| S5 | `Kết quả test: PASS`, `Lint/format: PASS` hoặc `N/A`, `Gap còn mở: 0`, `E2E: PASS` hoặc `N/A`. Có wireframe (`UI mockup: YES`) thì phải PASS; PASS thì hook kiểm có ảnh `docs/testing/evidence/<task-id>/*-<rộng>.png` cho **mọi** chiều rộng trong `VIEWPORTS` |
| S6 | `Code review: APPROVED`, `Security review: APPROVED`, `Cập nhật KB: YES` hoặc `KHÔNG CẦN`, `Bài học: YES` hoặc `KHÔNG CÓ`. `Cập nhật KB: YES` mà không có file KB nào trong `docs/` đổi so với nhánh gốc → chặn. Có App Mode: hook chạy lại `gap-check.py --gate --spec-check` |

Gate chủ yếu đọc các dòng Lead tự điền: chặn quên bước, không kiểm chứng việc đã làm. Ngoại lệ có kiểm thật: file trong `design/`, WHY trên board, `Cập nhật KB: YES` (git diff so với nhánh gốc), và App Mode (hook chạy `gap-check.py` trên tài liệu). Tài liệu khớp **code** thì do `code-reviewer` kiểm (KB và `docs/product/` lệch diff = High).

## Mức model (`COST_TIER`) và bài học (`LESSONS_PATH`)

- `COST_TIER=economy | standard | max` (mặc định standard): Lead truyền `model` cho từng agent theo bảng trong `run.md`. Economy hạ BA, Test Design, TA, Scout; max nâng Code Reviewer, Challenger. Security và Architect luôn opus.
- `LESSONS_PATH` (mặc định `docs/LESSONS.md`): Lead ghi ≤ 3 dòng bài học cuối mỗi task; Scout đưa bài học liên quan vào CONTEXT.md ở task sau.

## Chặn ghi sai vùng: 3 lớp

```
1. PreToolUse   chặn trước theo mẫu lệnh / đường dẫn       (cần agent_type, đã kiểm chứng với subagent)
2. PostToolUse  so diff sau mỗi lệnh Bash, file sai vùng → hoàn tác ngay
3. Giai đoạn    Lead ghi .agent-team/stage: S1-S2 chỉ tài liệu, S3 chỉ code, S4 chỉ test
```
Bật log xem hook nhận `agent_type`: `AGENT_TEAM_DEBUG=1` → `.agent-team/guard.log`. Hook `show_post.py` hiện mỗi bài Lead ghi trên board vào chat.

## Nhiều repo (BE và FE là 2 repo riêng)

Chọn **1 repo chính** (thường API/BE) chứa `.claude/`, `docs/`, `CLAUDE.md`.
```
3.KidTime/                  (thư mục cha, plugin không tạo gì ở đây)
├── API/  ← repo chính, mở Claude Code ở đây
│   ├── .claude/agent-team.config   REPOS=". ../FrontEnd"  FE_PATHS="../FrontEnd"  BASE_BRANCHES="../FrontEnd=master"
│   └── docs/               KB + agent-tasks
└── FrontEnd/ ← repo thứ hai, thêm bằng /add-dir ../FrontEnd
```
- Mỗi repo có branch `agent/<task-id>` riêng, commit/push trong từng repo (`git -C ../FrontEnd ...`). Nhánh gốc theo repo (`BASE_BRANCHES`).
- `/agent-team:init` hỏi chọn repo chính khi thấy ≥ 2 repo. `REPOS` trống = 1 repo.

## Code graph (Graphify, cài riêng)

- [Graphify](https://github.com/Graphify-Labs/graphify) dựng graph bằng tree-sitter (~40 ngôn ngữ), tới mức hàm, có `file:dòng`, **không gọi LLM** khi chỉ đọc code. Ra `graphify-out/GRAPH_REPORT.md` + `graph.json`.
- Role đọc báo cáo trước khi grep, query `explain`, `affected`, `query`, `path`, `god-nodes`. Lead chạy `graphify update` đầu task và sau S3, S4; nhiều repo thì `update` từng repo + `merge-graphs` → `graphify-out/merged-graph.json`, query thêm `--graph`.
- Guard chặn với mọi người: `graphify extract` (gọi LLM), `install`, `hook install`, `claude install`, `watch`, `graphify-mcp`.
- Chưa cài thì agent tìm bằng grep. Thay đổi chưa commit không có trong graph.

## Nguồn bên thứ ba

Checklist bảo mật, quy tắc trả lời ngắn và nguyên tắc code ít nhất được rút gọn từ 3 dự án MIT, xem `plugins/agent-team/THIRD-PARTY.md`.

## Cài đặt

```
1. Trong Claude Code:
   /plugin marketplace add hungvtitdng/multiple-agents-development
   /plugin install agent-team@kevin-agent-team
2. Mở project → /agent-team:init → kiểm tra .claude/agent-team.config
3. /agent-team:run <task>      (dang dở: /agent-team:resume <task-id>)
```
Cập nhật: `/plugin marketplace update kevin-agent-team`, khởi động lại Claude Code. Không còn cần `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`.

## Kiểm tra sau khi cài

1. `python3 tests/test_guard.py`, `python3 tests/test_board.py`, `python3 tests/test_gap_check.py` → toàn bộ pass
2. Trong project, nhờ Claude gọi subagent `agent-team:business-analyst` ghi 1 file ngoài KB của BA → phải bị guard chặn.
3. `.claude/agent-team/agent-db-clone.sh up test1` → `verify test1` → `down test1`
4. Nhờ Claude gọi `agent-team:business-analyst` dùng skill `agent-team:acceptance-criteria`. Agent báo không có tool `Skill` → bản Claude Code chưa cho subagent dùng skill: agent vẫn chạy, chỉ thiếu checklist trong skill.

## Giới hạn

- Guard dựa trên mẫu lệnh, không phải sandbox. Agent cố tình lách vẫn có thể lách; vẫn cần review cuối trên branch.
- Gate chỉ đọc các dòng Lead tự điền trong TASK.md, chặn quên bước chứ không chứng minh việc đã làm. Challenger mù ticket ở mức hook chặn đọc `docs/`; nó vẫn có thể grep nhầm vào `docs/` bằng Bash trên thư mục cha.
- Lead là điểm tập trung ý kiến (subagent không nhắn nhau). Giảm thiên kiến bằng bảng điểm và ghi ý kiến thiểu số.
- Chưa có: chia task nhỏ chạy song song bằng worktree riêng (để bản sau); plugin không tự chạy lại khi hết quota, dùng `/agent-team:resume`.
- Nhiều repo (`REPOS`) mới kiểm thử bằng repo giả, chưa chạy trên dự án thật. Giảm 50-70% token so với 0.8 là ước lượng, chưa đo.
- `agent-db-clone.sh` hỗ trợ Postgres và MySQL/MariaDB chạy bằng docker compose.
