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

print(f"\n{total - fail}/{total} passed")
sys.exit(1 if fail else 0)
