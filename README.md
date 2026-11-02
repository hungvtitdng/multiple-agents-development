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
│   │   ├── resume.md    ← /agent-team:resume - làm tiếp task dang dở (hết quota, lỗi)
│   │   ├── ask.md       ← /agent-team:ask    - hỏi về logic dự án, có dẫn nguồn
│   │   ├── kb.md        ← /agent-team:kb     - dựng/làm đầy KB từ code (nhiều Scout, kiểm bằng kb-check)
│   │   └── init.md      ← /agent-team:init   - cài cho 1 project, dựng KB
│   ├── hooks/           ← hooks.json, guard.py (chặn thật), show_post.py
│   ├── scripts/         ← agent-db-clone.sh, code-graph.py
│   └── templates/       ← TASK, SUMMARY, POST, CONTEXT, config, mục CLAUDE.md, kb/ (khung docs/)
├── docs/design.md       ← thiết kế
├── tests/
└── release-notes.md
```

## Đội hình (11 agent)

| Nhóm | Role | Model |
|---|---|---|
| **Debate** | Lead, business-analyst, solution-architect (Architect), test-designer | opus |
| Chuẩn bị | scout | sonnet |
| Làm | backend-dev, frontend-dev, test-executor | sonnet |
| Kiểm | code-reviewer | sonnet |
| Kiểm (mù ticket, VỪA/LỚN, ở S5) | challenger: chỉ nhận yêu cầu gốc + diff, tự dựng lại yêu cầu, chấm met / not met / can't tell. Hook chặn nó đọc `docs/` | sonnet |
| Kiểm | security (bắt buộc mọi task) | opus |
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

Nguồn theo thứ tự: KB (`docs/`) → `LESSONS.md` → `TASK.md` các task trước → code (`file:dòng`, code-graph). Mỗi ý có nguồn và nhãn `Verified/Unverified/Assumption`; KB lệch code thì tin code và ghi "KB nên cập nhật" (không tự sửa); không có nguồn thì nói thẳng, không bịa.

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
| Lead | Đổi giai đoạn khi TASK.md chưa đủ điều kiện (xem dưới) |

### Gate chuyển giai đoạn (Lead ghi `.agent-team/stage`, hook kiểm TASK.md)

| Sang | Cần trong TASK.md |
|---|---|
| S3 | `Loại`; NHỎ: `Tiêu chí nghiệm thu`; VỪA/LỚN: `Phương án chốt` + `Security duyệt solution: APPROVED` |
| S5 | `Kết quả test: PASS`, `Lint/format: PASS` hoặc `N/A` |
| S6 | `Code review: APPROVED`, `Security review: APPROVED`, `Cập nhật KB: YES` hoặc `KHÔNG CẦN`, `Bài học: YES` hoặc `KHÔNG CÓ` |

Gate chỉ đọc các dòng Lead tự điền: chặn quên bước, không kiểm chứng việc đã làm.

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

## Code graph (tự có, không cài gói ngoài)

- `scripts/code-graph.py` quét file đã commit, tạo `code-graph-out/GRAPH_REPORT.md` + `graph.json` (rb, py, js/ts, go, java, php, vue). Cạnh `EXTRACTED` = import tường minh, `INFERRED` = gợi ý theo tên.
- Role đọc báo cáo trước khi grep, query `who-uses`, `uses`, `explain`. Lead chạy `build` đầu task và sau S3, S4.
- Giới hạn: quan hệ ở mức file/class; thay đổi chưa commit không có trong graph.

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

1. `python3 tests/test_guard.py` → toàn bộ pass
2. Trong project, nhờ Claude gọi subagent `agent-team:business-analyst` ghi 1 file ngoài KB của BA → phải bị guard chặn.
3. `.claude/agent-team/agent-db-clone.sh up test1` → `verify test1` → `down test1`

## Giới hạn

- Guard dựa trên mẫu lệnh, không phải sandbox. Agent cố tình lách vẫn có thể lách; vẫn cần review cuối trên branch.
- Gate chỉ đọc các dòng Lead tự điền trong TASK.md, chặn quên bước chứ không chứng minh việc đã làm. Challenger mù ticket ở mức hook chặn đọc `docs/`; nó vẫn có thể grep nhầm vào `docs/` bằng Bash trên thư mục cha.
- Lead là điểm tập trung ý kiến (subagent không nhắn nhau). Giảm thiên kiến bằng bảng điểm và ghi ý kiến thiểu số.
- Chưa có: chia task nhỏ chạy song song bằng worktree riêng (để bản sau); plugin không tự chạy lại khi hết quota, dùng `/agent-team:resume`.
- Nhiều repo (`REPOS`) mới kiểm thử bằng repo giả, chưa chạy trên dự án thật. Giảm 50-70% token so với 0.8 là ước lượng, chưa đo.
- `agent-db-clone.sh` hỗ trợ Postgres và MySQL/MariaDB chạy bằng docker compose.
