#!/usr/bin/env python3
"""Test board.py: python3 tests/test_board.py"""
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

BOARD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "plugins", "agent-team", "scripts", "board.py")
tmp = tempfile.mkdtemp()
ENV = {**os.environ, "AGENT_TEAM_BOARD_DB": os.path.join(tmp, "board.db")}
fail = total = 0


def run(*args, stdin=None):
    r = subprocess.run([sys.executable, BOARD, *args], input=stdin, capture_output=True, text=True, env=ENV, cwd=tmp)
    return r.returncode, r.stdout + r.stderr


def check(desc, ok):
    global fail, total
    total += 1
    fail += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {desc}")


T = "20261119-demo"
check("post khi chưa mở lượt bị từ chối", run("post", T, "--role", "business-analyst", "--body", "x")[0] == 1)
check("mở lượt S2-R1", run("open", T, "S2", "1", "--roles", "business-analyst,solution-architect", "--goal", "đề xuất")[0] == 0)
check("mở trùng khi đang có lượt mở bị từ chối", run("open", T, "S2", "2")[0] == 1)
code, out = run("post", T, "--role", "solution-architect", "--body", "Phương án A, B. @business-analyst xem AC-2")
check("SA post", code == 0 and "#1" in out)
check("BA post qua stdin + trả lời #1", run("post", T, "--role", "business-analyst", "--reply", "1",
                                         stdin="A thiếu AC-3\nB ổn\n")[0] == 0)
check("role không tham gia lượt bị từ chối", run("post", T, "--role", "backend-dev", "--body", "x")[0] == 1)
check("trả lời tin không tồn tại bị từ chối", run("post", T, "--role", "business-analyst", "--reply", "99", "--body", "x")[0] == 1)
check("bài quá dài bị từ chối", run("post", T, "--role", "business-analyst", stdin="x\n" * 100)[0] == 1)
check("bài trống bị từ chối", run("post", T, "--role", "business-analyst", "--body", "  ")[0] == 1)

# nhiều agent post song song: không mất tin
with ThreadPoolExecutor(8) as ex:
    res = list(ex.map(lambda i: run("post", T, "--role", "solution-architect", "--body", f"song song {i}")[0], range(16)))
check("16 post song song đều thành công", res == [0] * 16)
code, out = run("read", T, "--stage", "S2", "--round", "1")
check("đọc đủ 18 tin của lượt", out.count("[S2-R1]") == 18)

code, out = run("read", T, "--mention", "business-analyst")
check("lọc tin @business-analyst", code == 0 and "#1" in out and "song song" not in out)
code, out = run("status", T)
check("status: ai đã post", "Đã post: business-analyst, solution-architect" in out)

check("Lead ghi tóm tắt", run("summary", T, "--body", "A thiếu AC-3, SA sửa ở R2")[0] == 0)
check("đóng lượt", run("close", T)[0] == 0)
check("mở S2-R2", run("open", T, "S2", "2", "--roles", "solution-architect,business-analyst,test-designer")[0] == 0)
check("test-designer post R2", run("post", T, "--role", "test-designer", "--body", "AC-2 không kiểm chứng được")[0] == 0)
code, out = run("read", T)
check("read mặc định: tóm tắt lượt trước + tin lượt đang mở",
      "Tóm tắt S2-R1" in out and "[S2-R2] test-designer" in out and "song song" not in out)
code, out = run("status", T)
check("status: @business-analyst đã trả lời ở #2 nên không còn chờ", "chưa trả lời #1" not in out)
run("post", T, "--role", "test-designer", "--body", "@solution-architect cần contract lỗi")
code, out = run("status", T)
check("status: @ chưa trả lời được liệt kê", "@solution-architect chưa trả lời" in out)

out_file = os.path.join(tmp, "DEBATE.md")
code, _ = run("export", T, "--out", out_file)
text = open(out_file, encoding="utf-8").read() if code == 0 else ""
check("export ra markdown đủ lượt + tóm tắt", "## S2-R1" in text and "## S2-R2" in text and "Tóm tắt của Lead" in text)

# ---- WHY: hỏi đến khi cả team debate đồng ý ----
W = "20261119-why"
run("open", W, "S2", "2", "--goal", "hỏi why")
check("WHY khi chưa chốt team bị từ chối",
      run("post", W, "--role", "test-designer", stdin="WHY @solution-architect: vì sao cần bảng mới?\n")[0] == 1)
check("Lead chốt team", run("team", W, "--roles", "lead,business-analyst,solution-architect,test-designer")[0] == 0)
code, out = run("post", W, "--role", "test-designer", stdin="WHY @solution-architect: vì sao cần bảng mới?\n")
check("tạo WHY-1", code == 0 and "Tạo WHY-1" in out)
check("role ngoài team không hỏi được", run("post", W, "--role", "security", stdin="WHY @lead: x?\n")[0] == 1)
check("hỏi role ngoài team bị từ chối", run("post", W, "--role", "test-designer", stdin="WHY @security: x?\n")[0] == 1)
check("AGREE khi chưa có trả lời bị từ chối", run("post", W, "--role", "business-analyst", stdin="AGREE WHY-1\n")[0] == 1)
check("người khác trả lời thay bị từ chối", run("post", W, "--role", "business-analyst", stdin="RE WHY-1: vì x\n")[0] == 1)
code, out = run("post", W, "--role", "solution-architect", stdin="RE WHY-1: vì 1 đơn huỷ nhiều lần\n(app/models/order.rb:42)\n")
check("SA trả lời, nội dung nhiều dòng", code == 0 and "chờ biểu quyết" in out)
check("người trả lời tự AGREE bị từ chối", run("post", W, "--role", "solution-architect", stdin="AGREE WHY-1\n")[0] == 1)
check("DISAGREE thiếu lý do bị từ chối", run("post", W, "--role", "business-analyst", stdin="DISAGREE WHY-1\n")[0] == 1)
check("bài lỗi không được lưu (rollback)", "DISAGREE WHY-1\n" not in run("read", W, "--all")[1])
code, out = run("post", W, "--role", "test-designer", stdin="AGREE WHY-1\n")
check("1 người AGREE, còn chờ người khác", "còn chờ: business-analyst, lead" in out)
run("post", W, "--role", "business-analyst", stdin="DISAGREE WHY-1: vì sao không thêm cột vào orders?\n")
code, out = run("status", W)
check("status: WHY-1 mở lại, chờ SA trả lời tiếp", "WHY chưa thống nhất: 1" in out and "chờ @solution-architect trả lời tiếp" in out)
check("Lead phán quyết khi mới 1 lần trả lời bị từ chối",
      run("why-close", W, "1", "--as", "ruling", "--note", "x")[0] == 1)
run("post", W, "--role", "solution-architect", stdin="RE WHY-1: cột không chứa được nhiều lần huỷ (order.rb:42)\n")
code, out = run("whys", W, "--open")
check("trả lời mới xoá phiếu cũ, phải biểu quyết lại từ đầu", "chờ biểu quyết: business-analyst, lead, test-designer" in out)
for r in ("business-analyst", "test-designer"):
    run("post", W, "--role", r, stdin="AGREE WHY-1\n")
code, out = run("post", W, "--role", "lead", stdin="AGREE WHY-1\n")
check("cả team AGREE → thống nhất", "cả team đồng ý" in out)
check("WHY đã đóng không nhận phiếu", run("post", W, "--role", "lead", stdin="AGREE WHY-1\n")[0] == 1)

# giằng co: Lead phán quyết sau 2 lần trả lời; Security không đồng ý thì không được
run("team", W, "--roles", "lead,business-analyst,solution-architect,security")
run("post", W, "--role", "security", stdin="WHY @solution-architect: vì sao API trả cả email?\n")
for i in range(2):
    run("post", W, "--role", "solution-architect", stdin=f"RE WHY-2: FE cần hiển thị (lần {i})\n")
    run("post", W, "--role", "security", stdin="DISAGREE WHY-2: vì sao không che email?\n")
check("Security DISAGREE → Lead không phán quyết được", run("why-close", W, "2", "--as", "ruling", "--note", "x")[0] == 1)
run("post", W, "--role", "business-analyst", stdin="WHY @solution-architect: vì sao cần 2 bước?\n")
for i in range(2):
    run("post", W, "--role", "solution-architect", stdin=f"RE WHY-3: an toàn hơn (lần {i})\n")
    run("post", W, "--role", "business-analyst", stdin="DISAGREE WHY-3: vì sao không 1 bước?\n")
code, out = run("why-close", W, "3", "--as", "assumption", "--note", "chọn 2 bước, xem lại sau")
check("giằng co 2 lần → Lead đóng, ghi người không đồng ý", code == 0 and "business-analyst" in out)
code, out = run("status", W)
check("status đếm WHY chưa thống nhất", "WHY chưa thống nhất: 1" in out)

# ---- report: bảng debate + quyết định ----
os.makedirs(os.path.join(tmp, ".claude"), exist_ok=True)
open(os.path.join(tmp, ".claude", "agent-team.config"), "w").write("")
td = os.path.join(tmp, "docs", "agent-tasks", W)
os.makedirs(td, exist_ok=True)
open(os.path.join(td, "TASK.md"), "w", encoding="utf-8").write(
    "## Điều kiện\n- Loại: VỪA\n- Phương án chốt: B\n\n## 0. Yêu cầu gốc\nHuỷ một phần đơn\n\n## 6. Phương án được chốt\n- B vì giữ lịch sử\n")
code, out = run("report", W)
rep = open(os.path.join(td, "REPORT.md"), encoding="utf-8").read() if code == 0 else ""
check("report tạo REPORT.md", code == 0)
check("report có kết quả từ TASK.md", "| Phương án chốt | B |" in rep and "Huỷ một phần đơn" in rep)
check("report có bảng WHY + người không đồng ý", "| WHY-1 |" in rep and "business-analyst: vì sao không thêm cột" in rep)
check("report có số liệu theo role", "| Role | Bài post | WHY đã hỏi |" in rep and "| WHY còn mở | 1 |" in rep)
check("report có phương án chốt", "B vì giữ lịch sử" in rep)
open(os.path.join(td, "TASK.md"), "w", encoding="utf-8").write(
    "## Điều kiện\n- Loại: VỪA\n- Phương án chốt: B\n\n## 2. Giả định\n"
    "| Điểm chưa rõ | Cách hiểu đã chọn | Lý do | Phương án khác đã xét | Ưu | Nhược | Ảnh hưởng nếu sai | Mức ảnh hưởng | Ai đề xuất | Client xác nhận |\n"
    "|---|---|---|---|---|---|---|---|---|---|\n"
    "| Hoàn phí ship? | Không hoàn | KB chưa có | Hoàn theo tỷ lệ | Đơn giản | Khách phàn nàn | Sửa 1 hàm | Thấp | BA | |\n"
    "| Khuyến mãi? | Theo giá sau KM | Công bằng | Giá gốc | Đúng tiền | Số hoàn thấp | Kiểm lại đơn | Cao | dev | Đúng |\n\n"
    "## 3. Các phương án\n### A. Thêm cột\n- Mô tả: cột mới\n- Ưu: nhanh\n- Nhược: mất lịch sử\n- Kết luận: Loại\n"
    "### B. Bảng mới\n- Mô tả: bảng huỷ\n- Ưu: giữ lịch sử\n- Nhược: thêm bảng\n- Kết luận: Chọn\n\n"
    "## 5. Bảng điểm\n| Tiêu chí | Trọng số | A | B |\n|---|---|---|---|\n| Đáp ứng AC | ×3 | 2 | 5 |\n| Công sức | ×1 | 5 | 3 |\n")
code, out = run("report", W)
rep = open(os.path.join(td, "REPORT.md"), encoding="utf-8").read()
html = open(os.path.join(td, "REPORT.html"), encoding="utf-8").read() if code == 0 else ""
check("report giả định: [!CAUTION] + đủ cột", "[!CAUTION]" in rep and "| Phương án khác đã xét | Ưu | Nhược |" in rep)
check("giả định xếp Cao trước Thấp", rep.index("Khuyến mãi?") < rep.index("Hoàn phí ship?"))
check("giả định từ WHY chốt assumption được gộp vào", "vì sao cần 2 bước?" in rep)
check("HTML: bảng giả định đỏ + ô xác nhận + nút copy", 'class="atable"' in html and 'type="radio"' in html and 'class="copybtn"' in html)
check("HTML: giả định client đã xác nhận không còn ô chọn", "pill-sm ok\">Đúng" in html)
check("HTML: bảng so sánh phương án, B điểm cao nhất", 'class="otable"' in html and "Điểm cao nhất" in html and "<b>18</b>/20" in html)
check("HTML tự chứa, không tải ngoài", "http://" not in html and "https://" not in html)

# ---- thiết kế: sơ đồ + mockup trong report ----
dd = os.path.join(td, "design")
os.makedirs(dd, exist_ok=True)
open(os.path.join(dd, "workflow.md"), "w", encoding="utf-8").write("# W\n\n```mermaid\nflowchart TD\n  A[\"Mở đơn\"] --> B[\"Huỷ\"]\n```\n")
open(os.path.join(dd, "mockup-huy-don.html"), "w", encoding="utf-8").write("<!doctype html><title>Huỷ đơn</title><p>wire</p>")
ENV["AGENT_TEAM_NO_MMDC"] = "1"
code, out = run("report", W)
rep = open(os.path.join(td, "REPORT.md"), encoding="utf-8").read()
html = open(os.path.join(td, "REPORT.html"), encoding="utf-8").read()
check("MD: khối mermaid + mockup để client xác nhận", "```mermaid" in rep and "M-1 · Màn hình **Huỷ đơn**" in rep)
check("HTML không có mmdc: hiện mã + hướng dẫn cài", 'class="mmd"' in html and "mermaid-cli" in html)
check("HTML: mockup nhúng iframe + ô xác nhận", 'class="mock"' in html and 'data-id="M-1 Huỷ đơn"' in html and 'name="W-1"' in html)
del ENV["AGENT_TEAM_NO_MMDC"]
import shutil
if shutil.which("mmdc"):
    code, out = run("report", W)
    html = open(os.path.join(td, "REPORT.html"), encoding="utf-8").read()
    check("HTML có mmdc: sơ đồ vẽ sẵn thành SVG, id riêng", '<div class="diagram"><svg' in html and "my-svg" not in html)

# ---- tóm tắt bắt buộc trước khi đóng lượt + đọc đúng 1 câu WHY ----
X = "20261122-sum"
run("open", X, "S2", "1", "--goal", "đề xuất")
run("post", X, "--role", "business-analyst", "--body", "AC-1 ...")
code, out = run("close", X)
check("đóng lượt có bài mà chưa tóm tắt bị từ chối", code == 1 and "chưa tóm tắt" in out)
run("summary", X, "--body", "BA đưa AC-1")
check("tóm tắt xong thì đóng được", run("close", X)[0] == 0)
run("open", X, "S2", "2")
check("lượt không có bài nào đóng được không cần tóm tắt", run("close", X)[0] == 0)
code, out = run("read", W, "--why", "1")
check("read --why: câu hỏi + phiếu + dòng nhắc tới", code == 0 and "WHY-1 [agreed]" in out and "DISAGREE business-analyst" in out and "RE WHY-1" in out)
check("read --why không tồn tại báo lỗi", run("read", W, "--why", "99")[0] == 1)

# ---- report chèn _wf.css / _wf.js vào mockup nhúng ----
open(os.path.join(dd, "_wf.css"), "w", encoding="utf-8").write(".guide{border:2px dashed #666}")
open(os.path.join(dd, "_wf.js"), "w", encoding="utf-8").write("var WF=1;")
open(os.path.join(dd, "mockup-huy-don.html"), "w", encoding="utf-8").write(
    '<!doctype html><title>Huỷ đơn</title><link rel="stylesheet" href="_wf.css"><p>wire</p><script src="_wf.js"></script>')
ENV["AGENT_TEAM_NO_MMDC"] = "1"
run("report", W)
html = open(os.path.join(td, "REPORT.html"), encoding="utf-8").read()
check("report: mockup nhúng có sẵn CSS / JS dùng chung", "border:2px dashed #666" in html and "var WF=1;" in html and "_wf.css" not in html)
del ENV["AGENT_TEAM_NO_MMDC"]

# ---- trạng thái agent: heartbeat (hook), done, progress, wait, stuck ----
import json as _json
HB = os.path.join(os.path.dirname(BOARD), "..", "hooks", "heartbeat.py")
hp = tempfile.mkdtemp()
os.makedirs(os.path.join(hp, ".claude")); os.makedirs(os.path.join(hp, ".agent-team"))
os.makedirs(os.path.join(hp, "docs", "agent-tasks", "H1"))
open(os.path.join(hp, ".claude", "agent-team.config"), "w").write("HANG_MINUTES=1\n")
open(os.path.join(hp, "docs", "agent-tasks", "H1", "TASK.md"), "w").write("x")
HENV = {**os.environ, "AGENT_TEAM_BOARD_DB": ""}
HENV.pop("AGENT_TEAM_BOARD_DB")


def hrun(*args, stdin=None):
    r = subprocess.run([sys.executable, BOARD, *args], input=stdin, capture_output=True, text=True, env=HENV, cwd=hp)
    return r.returncode, r.stdout + r.stderr


def hb(ev, role, tool="Bash", ti=None):
    d = {"agent_type": f"agent-team:{role}", "tool_name": tool, "tool_input": ti or {"command": "graphify explain Order"}, "cwd": hp}
    return subprocess.run([sys.executable, HB, ev], input=_json.dumps(d), capture_output=True, text=True).returncode


hrun("open", "H1", "S2", "1", "--roles", "business-analyst,solution-architect")
check("heartbeat không bao giờ chặn tool", hb("pre", "business-analyst") == 0)
code, out = hrun("status", "H1")
check("status: agent đang làm + tool đang chạy", "business-analyst: đang làm" in out and "graphify explain Order" in out)
check("status: agent chưa bắt đầu", "solution-architect: chưa bắt đầu" in out)
hb("post", "business-analyst")
check("progress ghi bước + eta", hrun("progress", "H1", "--role", "business-analyst", "--step", "AC 3/5", "--eta", "4")[0] == 0
      and "AC 3/5" in hrun("status", "H1")[1])
check("done ghi kết quả", hrun("done", "H1", "--role", "business-analyst", "--body", "AC-1..5 xong")[0] == 0)
code, out = hrun("post", "H1", "--role", "business-analyst", "--body", "thêm")
check("post sau DONE bị từ chối (bảo kết thúc ngay)", code == 1 and "KẾT THÚC NGAY" in out)
check("done lần 2 bị từ chối", hrun("done", "H1", "--role", "business-analyst", "--body", "x")[0] == 1)
check("done quá 5 dòng bị từ chối", hrun("done", "H1", "--role", "solution-architect", "--body", "1\n2\n3\n4\n5\n6")[0] == 1)
hb("pre", "solution-architect")
hb("stop", "solution-architect")
code, out = hrun("wait", "H1", "--interval", "1", "--max", "3")
check("SubagentStop tự ghi DONE → wait trả về XONG (exit 0)", code == 0 and "XONG" in out and "AC-1..5 xong" in out)
hrun("summary", "H1", "--body", "x"); hrun("close", "H1")
hrun("open", "H1", "S2", "2", "--roles", "test-designer")
hb("pre", "test-designer", ti={"command": "docker compose up app"})
import sqlite3 as _sq
_db = _sq.connect(os.path.join(hp, ".agent-team", "board.db"))
_db.execute("UPDATE agent_runs SET last_seen=last_seen-600, busy_since=busy_since-600 WHERE role='test-designer'")
_db.execute("UPDATE rounds SET opened_at=opened_at-600 WHERE stage='S2' AND round=2")
_db.commit(); _db.close()
code, out = hrun("wait", "H1", "--interval", "1", "--max", "3")
check("agent im quá HANG_MINUTES → wait trả về CÓ AGENT TREO (exit 3)", code == 3 and "test-designer: ⚠ im" in out)
code, out = hrun("stuck", "H1")
check("stuck gợi ý lệnh tắt đúng lệnh đang kẹt", "pgrep -fl" in out and "docker compose up app" in out)
hrun("open", "H1", "S9", "1")  # stage sai: không ảnh hưởng
hb("pre", "test-designer", ti={"command": "timeout 1800 bundle exec rspec"})
_db = _sq.connect(os.path.join(hp, ".agent-team", "board.db"))
_db.execute("UPDATE agent_runs SET last_seen=last_seen-600, busy_since=busy_since-600 WHERE role='test-designer'")
_db.commit(); _db.close()
code, out = hrun("wait", "H1", "--interval", "1", "--max", "2")
check("lệnh có timeout 1800: im 10 phút chưa coi là treo (exit 4)", code == 4 and "đang làm" in out)

# ---- v0.20.0: danh sách bước ----
P = "20261123-plan"
code, out = run("plan", P)
check("plan chưa có: nhắc lệnh --set", code == 0 and "Chưa có danh sách bước" in out)
check("plan --set trống bị từ chối", run("plan", P, "--set", " | ")[0] == 1)
code, out = run("plan", P, "--set", "Scaffold @backend-dev | Đăng ký, 2FA @backend-dev | Test + lint @test-executor")
check("plan --set: 3 bước ○, có role", code == 0 and out.count("○") == 3 and "3. Test + lint" in out and "test-executor" in out)
code, out = run("step", P, "1", "done")
check("step done: ✅ bước 1", code == 0 and "✅ 1. Scaffold" in out)
code, out = run("step", P, "2", "start")
check("step start: ▶ bước 2", "▶  2. Đăng ký, 2FA" in out)
check("step bước không có bị từ chối", run("step", P, "9", "done")[0] == 1)
code, out = run("plan", P, "--set", "Scaffold | Đăng ký, 2FA | Khung R-54 @backend-dev | Test + lint @test-executor")
check("lập lại: bước trùng tên giữ trạng thái + role, bước mới ○",
      "✅ 1. Scaffold" in out and "▶  2. Đăng ký, 2FA" in out and "○  3. Khung R-54" in out and "backend-dev" in out.splitlines()[0])
check("status có mục Các bước", "Các bước:" in run("status", P)[1])

# done / SubagentStop tự ✅ bước ▶ của role
hrun("plan", "H1", "--set", "Quét KB @scout | Thiết kế test @test-designer")
hrun("step", "H1", "1", "start"); hrun("step", "H1", "2", "start")
hrun("done", "H1", "--role", "scout", "--body", "KB xong")
check("board.py done: tự ✅ bước ▶ của role", "✅ 1. Quét KB" in hrun("plan", "H1")[1])
hb("stop", "test-designer")
check("SubagentStop (chưa done): tự ✅ bước ▶ của role", "✅ 2. Thiết kế test" in hrun("plan", "H1")[1])

import sqlite3 as _sql3
# ---- v0.26: agent làm trong worktree → nhịp tim ghi vào board.db của worktree ----
WTD = os.path.join(hp, ".worktrees", "W1")
os.makedirs(os.path.join(WTD, ".claude")); os.makedirs(os.path.join(WTD, "docs", "agent-tasks", "W1"))
open(os.path.join(WTD, ".claude", "agent-team.config"), "w").write("X=1\n")
open(os.path.join(WTD, "docs", "agent-tasks", "W1", "TASK.md"), "w").write("x")
hb("pre", "frontend-dev", tool="Edit", ti={"file_path": os.path.join(WTD, "app", "a.tsx")})
_w = _sql3.connect(os.path.join(WTD, ".agent-team", "board.db")) if os.path.isfile(os.path.join(WTD, ".agent-team", "board.db")) else None
check("Edit file trong worktree → agent_runs ở board.db của worktree", _w is not None and
      _w.execute("SELECT count(*) FROM agent_runs WHERE task='W1' AND role='frontend-dev'").fetchone()[0] == 1)
hb("pre", "frontend-dev", ti={"command": f"cd {WTD} && npm test"})
check("`cd <worktree> &&` cũng ghi vào worktree", _w.execute("SELECT last_tool FROM agent_runs WHERE task='W1'").fetchone()[0].startswith("Bash: cd"))
_m = _sql3.connect(os.path.join(hp, ".agent-team", "board.db"))
_m.execute("CREATE TABLE IF NOT EXISTS pool (label TEXT, state TEXT)"); _m.execute("INSERT INTO pool VALUES('M-1/T-1','RUNNING')"); _m.commit()
hrun("plan", "H1", "--set", "Màn hình @frontend-dev"); hrun("step", "H1", "1", "start")
hb("stop", "frontend-dev", tool="", ti={})
check("SubagentStop không đường dẫn + đang điều phối: không ✅ nhầm bước ở thư mục chính", "▶" in hrun("plan", "H1")[1])
_m.execute("DELETE FROM pool"); _m.commit(); _m.close(); _w.close()

# ---- v0.21.0: ∥ song song, tự ▶ / ✅ ----
Q = "20261123-par"
code, out = run("plan", Q, "--set", "Auth BE @backend-dev ∥ Trang auth FE @frontend-dev | Test @test-executor")
check("∥: 2 bước cùng nhóm có dấu ∥, bước 3 không", out.count("∥") == 2 and "3. Test" in out and not out.splitlines()[2].endswith("∥"))
check("' // ' cũng là song song", run("plan", "Q2", "--set", "A @backend-dev // B @frontend-dev")[1].count("∥") == 2)
import importlib.util as _iu, sqlite3 as _sql3
_spec = _iu.spec_from_file_location("board", BOARD); bm = _iu.module_from_spec(_spec); _spec.loader.exec_module(bm)
os.environ["AGENT_TEAM_BOARD_DB"] = ENV["AGENT_TEAM_BOARD_DB"]
_db = bm.connect()
check("parallel_ok: BE ∥ FE", bm.parallel_ok(_db, Q))
check("begin_agent: ▶ bước của backend-dev", bm.begin_agent(_db, Q, "backend-dev", tmp) == 1)
check("begin_agent lần 2 khi đang ▶: không ▶ thêm", bm.begin_agent(_db, Q, "backend-dev", tmp) is None)
check("finish_step: ✅ bước ▶ của role", bm.finish_step(_db, Q, "backend-dev") == 1)
check("finish_step khi không còn ▶: không làm gì", bm.finish_step(_db, Q, "backend-dev") is None)
check("role không có bước: bỏ qua", bm.begin_agent(_db, Q, "security", tmp) is None)
run("plan", "Q3", "--set", "A @backend-dev | B @frontend-dev")
check("parallel_ok: BE rồi FE nối tiếp = không song song", not bm.parallel_ok(_db, "Q3"))
_db.close()
# board.db của v0.20.0 (plan_steps chưa có grp) tự thêm cột
_old = os.path.join(tmp, "old.db")
_c = _sql3.connect(_old); _c.execute("CREATE TABLE plan_steps (task TEXT NOT NULL, n INTEGER NOT NULL, title TEXT NOT NULL, role TEXT, "
                                     "state TEXT NOT NULL DEFAULT 'todo', started_at INTEGER, ended_at INTEGER, PRIMARY KEY(task, n))"); _c.commit(); _c.close()
_r = subprocess.run([sys.executable, BOARD, "plan", "X", "--set", "A @backend-dev ∥ B @frontend-dev"], capture_output=True, text=True,
                    env={**ENV, "AGENT_TEAM_BOARD_DB": _old}, cwd=tmp)
check("board.db cũ (0.20.0): tự thêm cột grp, plan chạy được", _r.returncode == 0 and _r.stdout.count("∥") == 2)

print(f"\n{total - fail}/{total} passed")
sys.exit(1 if fail else 0)
