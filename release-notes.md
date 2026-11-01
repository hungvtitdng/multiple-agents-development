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
