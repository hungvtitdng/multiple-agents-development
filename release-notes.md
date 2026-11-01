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
