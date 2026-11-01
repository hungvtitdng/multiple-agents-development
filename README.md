# Agent Team - đội 12 agent debate để chọn best solution

Plugin cho Claude Code. Đưa 1 task → team tự debate, chọn best solution, code, test, review, push lên branch riêng.

## Cấu trúc

```
03.Multiple-Agents/
├── .claude-plugin/marketplace.json      ← marketplace local
├── plugins/agent-team/
│   ├── .claude-plugin/plugin.json
│   ├── agents/          ← 11 role (Lead = session chính, nằm trong commands/run.md)
│   ├── commands/
│   │   ├── run.md       ← /agent-team:run  - playbook của Lead
│   │   └── init.md      ← /agent-team:init - cài cho 1 project
│   ├── hooks/
│   │   ├── hooks.json   ← đăng ký guard
│   │   └── guard.py     ← chặn thật (secret, git, DB, role chỉ đọc)
│   ├── scripts/agent-db-clone.sh   ← DB clone để migrate/test
│   └── templates/       ← TASK.md, POST.md, SUMMARY.md, config, mục CLAUDE.md
├── tests/test_guard.py
└── release-notes.md
```

## Debate Board: nơi làm việc chung

```
docs/agent-tasks/<task-id>/
├── TASK.md                       ← kết quả cuối (chỉ Lead ghi)
└── board/
    ├── SUMMARY.md                ← Lead tóm tắt từng vòng (chỉ Lead ghi)
    └── S2-R2-security-1.md       ← bài post: S<giai đoạn>-R<vòng>-<role>-<n>
```

- Mỗi vòng, mỗi role đọc **SUMMARY + toàn bộ bài post của vòng hiện tại**, góp ý cho **tất cả** phương án.
- `@role` = bắt buộc trả lời ở vòng sau.
- Đã post thì không sửa, chỉ post thêm. Không debate qua tin nhắn.
- Điểm V4 gửi **riêng cho Lead** (không file, không board). Lead ghi bảng điểm vào TASK.md.
- Khi chốt, Lead tổng hợp ý kiến **từng role** (kể cả ý kiến bị bác) vào TASK.md.

## Luồng 1 task

```
/agent-team:run <task>
        │
        ▼
 LEAD (session chính) ─► tạo branch agent/<task-id> ─► phân loại NHỎ/VỪA/LỚN
        │
 ① YÊU CẦU    BA viết AC ─► mơ hồ? ─► cả team debate ─► Requirement Reviewer APPROVED
 ② SOLUTION   đề xuất A/B/C ─► phản biện ─► đối đáp ─► chấm điểm độc lập
              🔐 Security soi từng phương án ─► Solution Reviewer APPROVED
 ③ CODE       BE ◄─► FE ─► migration trên DB clone ─► commit + push
 ④ TEST       Tester (AC + test bảo mật) trên DB clone ─► commit + push
 ⑤ REVIEW     Code │ Solution │ Test │ Requirement │ 🔐 Security  ─► issue? về ③/④
 ⑥ ĐÓNG       TASK.md hoàn chỉnh ─► xoá DB clone ─► push ─► báo link branch
```

Bế tắc (cùng 1 issue tranh luận 2 lần, không có lập luận mới) → Lead phán quyết.
**Lead không được override lỗi Security Critical/High.**

## Model theo vai trò

| Model | Role | Lý do |
|---|---|---|
| **opus** | Lead, Solution Architect, Technical Architect, Security, Solution Reviewer, Requirement Reviewer | Quyết định thiết kế, rủi ro cao |
| **sonnet** | BA, Backend, Frontend, Tester, Code Reviewer, Test Reviewer | Làm theo design đã chốt |

Cách giảm token thêm:
- Task NHỎ/VỪA chỉ gọi role liên quan (Security luôn có mặt)
- Chỉ tạo teammate cho giai đoạn hiện tại, xong thì cho nghỉ
- Mỗi vòng chỉ đọc SUMMARY các vòng trước + bài của vòng hiện tại, không đọc lại cả board

## Chặn thật bằng hook (guard.py)

| Áp dụng | Chặn |
|---|---|
| Mọi agent | Đọc/sửa `.env*`, `*.key`, `*.pem`, dump DB. `printenv`, `docker inspect`, `docker compose config` |
| Mọi agent | Push vào main/master/develop, force push, xoá branch, `reset --hard`, `clean -f` |
| Mọi agent | Commit/merge khi đang ở main/develop. Push khi diff có secret hoặc file nhạy cảm |
| Mọi agent | `db:migrate`, `db:drop`... không chạy qua `agent-db-clone.sh` |
| BA, SA, TA, 4 Reviewer, Security | Sửa code (đã bỏ `Edit` khỏi `tools`; `Write` chỉ còn để post board, guard chặn ghi ngoài board). Bash ngoài danh sách đọc/test/lint. Redirect `>`, `tee`, `sed -i`, `--fix`, `-a` |
| backend-dev, frontend-dev, tester | Sửa file ngoài vùng của mình: BE↔FE↔test (theo `BE_PATHS`/`FE_PATHS`/`TEST_PATHS`, kèm file `*_spec.*`, `*.test.*`, `__tests__/`) |
| Mọi role (trừ Lead) | Post bằng tên role khác, sửa/ghi đè bài đã post, ghi TASK.md/SUMMARY.md, ghi board bằng Bash |
| Mọi role (trừ Lead) | Đọc/ghi `.agent-team/` (state DB clone) |
| Mọi role trừ BA và Lead | Ghi knowledge base `docs/domain/` (kể cả bằng Bash) |

## Chặn ghi sai vùng: 3 lớp

```
1. PreToolUse   chặn trước theo mẫu lệnh / đường dẫn       (cần agent_type)
2. PostToolUse  so diff sau mỗi lệnh Bash, file sai vùng → hoàn tác ngay
3. Giai đoạn    Lead ghi .agent-team/stage: S3 chỉ ghi code, S4 chỉ ghi test
                → không cần biết ai gọi (lớp 1, 2 cũng dùng luật này)
```
Xem debate trực tiếp: hook `show_post.py` hiện mỗi bài post trên board vào chat (`[role · S2-R1]`).
Bật log để xem hook có nhận `agent_type` không: `AGENT_TEAM_DEBUG=1` → `.agent-team/guard.log`.

## Nhiều repo (BE và FE là 2 repo riêng)

```
Tên dự án/                 ← mở Claude Code ở đây (có thể không phải repo)
├── .claude/agent-team.config   REPOS="be fe"  BE_PATHS="be"  FE_PATHS="fe"
├── docs/
│   ├── domain/            ← knowledge base (BA ghi, mọi role đọc)
│   └── agent-tasks/       ← board chung của cả BE và FE
├── be/  (.git riêng)      ← branch agent/<task-id> riêng
└── fe/  (.git riêng)      ← branch agent/<task-id> riêng
```
- Một team, một board; API contract chốt ngay trên board. Commit/push từng repo bằng `git -C be ...`.
- Guard chặn commit/push vào main/develop ở từng repo (hiểu `git -C` và `cd be && git ...`), hoàn tác diff theo từng repo.
- Khuyên `git init` ở thư mục cha để lưu `docs/` + `.claude/` (thêm `be/`, `fe/` vào `.gitignore` của nó).
- `REPOS` trống = 1 repo, chạy như cũ.

## Code graph (tự có, không cài gói ngoài)

- `scripts/code-graph.py` quét file đã commit, tạo `code-graph-out/GRAPH_REPORT.md` + `graph.json`: file nào dùng file nào (rb, py, js/ts, go, java, php, vue).
- Cạnh `EXTRACTED` = import/require tường minh. Cạnh `INFERRED` = tên class/module xuất hiện trong file khác (gợi ý, không phải parser đầy đủ).
- BA, SA, TA, Code Reviewer, Security đọc báo cáo trước khi grep, query bằng `who-uses`, `uses`, `explain` (guard chỉ cho 3 lệnh này). Lead chạy `build` đầu task và sau S3, S4. Graph cũ so với HEAD thì query in cảnh báo.
- Giới hạn: quan hệ ở mức file/class, không tới mức hàm gọi hàm. Thay đổi chưa commit không có trong graph.

## Nguồn bên thứ ba

Checklist bảo mật, quy tắc trả lời ngắn và nguyên tắc code ít nhất được rút gọn từ 3 dự án MIT, xem `plugins/agent-team/THIRD-PARTY.md`.

## Cài đặt

Xem `release-notes.md`. Tóm tắt:

```
1. ~/.claude/settings.json  → bật CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
2. Trong Claude Code:
   /plugin marketplace add /Users/hung.vo/Kevin/Projects/03.Multiple-Agents
   /plugin install agent-team@kevin-agent-team
3. Mở project → /agent-team:init → kiểm tra .claude/agent-team.config
4. /agent-team:run <task>
```

## Kiểm tra sau khi cài

1. `python3 tests/test_guard.py` → 99/99 passed
2. Trong project, nhờ Claude gọi subagent `agent-team:code-reviewer` sửa 1 file code → phải bị guard chặn.
   - Nếu **không bị chặn**: đặt `AGENT_TEAM_DEBUG=1`, chạy lại, xem `.agent-team/guard.log`. `agent_type` trống → rule theo role không có hiệu lực, còn lớp chặn theo giai đoạn (lớp 3) vẫn chạy.
3. `.claude/agent-team/agent-db-clone.sh up test1` → `verify test1` → `down test1`

## Giới hạn

- Guard là lớp chặn dựa trên mẫu lệnh, không phải sandbox. Agent cố tình lách vẫn có thể lách được, vì vậy vẫn cần review cuối trên branch.
- Agent Teams đang là tính năng thử nghiệm. Nếu không bật, `run.md` tự chuyển sang chế độ subagent (Lead chuyển lời giữa các role).
- Nhiều repo (`REPOS`) mới kiểm thử bằng test tự động với repo giả, chưa chạy trên dự án thật. Task xuyên nhiều repo cần Lead nhớ commit/push từng repo.
- `agent-db-clone.sh` hỗ trợ Postgres và MySQL/MariaDB chạy bằng docker compose.
