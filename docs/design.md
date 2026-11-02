# KIẾN TRÚC ĐỘI NGŨ AI AGENT PHÁT TRIỂN PHẦN MỀM BẰNG CLAUDE CODE

Khung chính: `kien-truc-doi-ngu-ai-agent-claude-code-v2.md`. Phần lấy thêm từ plugin `agent-team` 0.8.2 và đề xuất Lean được đánh dấu:

| Dấu | Nguồn thêm |
|---|---|
| **[+A]** | Debate có chấm điểm |
| **[+B]** | Thi hành bằng hook (guard) |
| **[+C]** | Tiết kiệm token |
| **[+D]** | Vận hành thực tế (nhiều repo, resume, DB clone...) |
| **[+E]** | Quy chuẩn code / clean code nằm trong KB |

Trạng thái: **ĐÃ CHỐT thiết kế, chưa áp dụng vào code plugin.**

---

## 1. Mục tiêu

Xây dựng đội ngũ AI Agent phối hợp thực hiện quy trình phát triển phần mềm từ tiếp nhận yêu cầu đến code, kiểm thử, review.

- Phân tích yêu cầu trước khi code.
- Tự chia task lớn thành task nhỏ độc lập.
- Phân công đúng agent chuyên môn; chạy song song khi không xung đột.
- Mỗi task nhỏ một Git worktree và branch riêng.
- Kiểm thử đầy đủ trước khi xác nhận hoàn thành.
- Code review và security review độc lập.
- Knowledge Base (KB) phản ánh đúng trạng thái thực của dự án.
- Dùng được cho dự án mới và dự án đang tồn tại.

Nguyên tắc bổ sung:
1. **[+A]** Quyết định giải pháp qua debate nhỏ (4 người), nhiều phương án, chấm điểm kín; Lead chốt best solution và được gộp ý các phương án.
2. **[+D]** **Không hỏi lại user.** Thiếu business rule thì Lead chọn best solution, ghi nhãn `Assumption`, liệt kê ở báo cáo cuối. Không chặn tiến độ.
3. **[+B]** Quy tắc quan trọng phải được hook thi hành, không chỉ viết bằng chữ.
4. **[+D]** Trạng thái nằm trên đĩa (TASK.md, stage, board) để hết quota hoặc lỗi vẫn resume được.

---

## 2. Danh sách Agent

9 agent theo v2 và **[+C]** thêm Scout (10 agent). Chỉ 4 người tham gia debate.

| STT | Agent | Nhóm | Model | Thinking | Quyền ghi |
|---|---|---|---|---|---|
| 1 | Lead | Debate | Opus | High | TASK.md, SUMMARY.md, stage **[+B]** |
| 2 | Business Analyst (BA) | Debate | Opus | High | `docs/domain/` |
| 3 | Solution Architect (SA, "Architect") | Debate | Opus | High | `docs/architecture/` |
| 4 | Tester - Test Design | Debate | Opus | High | `docs/testing/` (test case, matrix) |
| 5 | **[+C]** Scout | Chuẩn bị | Sonnet | Low | `CONTEXT.md` |
| 6 | Backend Developer | Làm | Sonnet | Low/Medium | `BE_PATHS` **[+B]** |
| 7 | Frontend Developer | Làm | Sonnet | Low/Medium | `FE_PATHS` **[+B]** |
| 8 | Tester - Test Execution | Làm | Sonnet | Low/Medium | `TEST_PATHS`, kết quả test |
| 9 | Code Reviewer | Kiểm | Sonnet | Medium | bài review |
| 10 | Security Reviewer | Kiểm | Opus | High | `docs/security/`, bài review |

Chính sách model (giữ từ v2):
- Model và thinking là cấu hình khởi điểm, không gắn cứng. Nâng khi task khó, tác động rộng hoặc kết quả đầu chưa đạt.
- Không mặc định High cho mọi lần chạy. Theo dõi chi phí, thời gian, số vòng sửa, tỷ lệ lỗi để chỉnh.
- Xác minh tên model và mức thinking theo bản Claude Code đang dùng.
- **[+D]** Task LỚN: Architect tách thành SA (làm gì, ở đâu) và TA (làm thế nào: schema, index, cache, API contract).

---

## 3. Vai trò và trách nhiệm

### 3.1 Lead
Điều phối toàn bộ quy trình, không nhất thiết viết code. Chọn quy trình tối thiểu phù hợp từng task; chỉ gọi role khi tạo giá trị rõ ràng hoặc bắt buộc theo rủi ro.

Trách nhiệm (v2): tiếp nhận yêu cầu, xác định phạm vi và thông tin còn thiếu, đánh giá độ phức tạp/rủi ro, quyết định agent nào tham gia, tổng hợp kết quả phân tích, chia task, xác định thứ tự/dependency/song song, tạo worktree + branch, theo dõi trạng thái, điều phối dev, yêu cầu cập nhật KB, test, review, giải quyết bất đồng, kiểm tra kết quả cuối.

Thêm:
- **[+A]** Mở/đóng từng lượt debate, gom phương án, chốt **best solution** (chọn một hoặc gộp ý), ghi bảng điểm và ý kiến từng role.
- **[+D]** Khi thiếu thông tin nghiệp vụ: tự chọn best solution, ghi Assumption, báo ở cuối (thay cho "phải hỏi user" của v2).
- Mỗi task phải có: mục tiêu, phạm vi, dependency, AC, danh sách test, agent phụ trách, worktree + branch, trạng thái.
- **Không** tự đánh dấu DONE chỉ vì agent báo xong. **Không** override lỗi Security Critical/High.
- **[+B]** Lead cũng bị guard chặn ghi sai vùng; cần sửa tay thì đổi stage trước.

### 3.2 Business Analyst (BA)
- Làm rõ yêu cầu, mục tiêu, phạm vi, luồng nghiệp vụ, actor/quyền, business rule, ngoại lệ, AC, mâu thuẫn/thiếu thông tin, ảnh hưởng đến chức năng hiện có.
- Cập nhật tài liệu nghiệp vụ (`docs/domain/`).
- Phân biệt: Confirmed / Verified từ hệ thống / Assumption / Proposed.
- Không tự đổi business rule vì thấy phương án khác hợp lý hơn.
- Đầu ra đủ rõ để SA thiết kế và Dev code mà không đoán nghiệp vụ.

### 3.3 Solution Architect (SA)
- Phân tích kiến trúc hiện tại, module bị ảnh hưởng, luồng FE/BE/hệ thống liên quan, ảnh hưởng API/DB/integration, performance/scalability/maintainability, dependency, cách chia task, hợp đồng giao tiếp, thay đổi rủi ro cao.
- Cập nhật `docs/architecture/` và sở hữu `docs/engineering/` (quy chuẩn code, mục 9.7).
- Ưu tiên giải pháp hợp kiến trúc hiện tại; không tự thêm framework/service/công nghệ không cần.
- **[+A]** Luôn đưa 2–3 phương án (ưu, nhược, chi phí, rủi ro) cho Lead chọn. Chốt API contract giữa BE và FE.

### 3.4 Tester - Test Design
- Đọc yêu cầu/AC; xác định scenario, test case, test data, trường hợp biên, negative case, lỗi/ngoại lệ, authn/authz, regression, test nào tự động hóa, phạm vi API/giao diện.
- Lập ma trận requirement ↔ test case ↔ kết quả.
- Loại test tùy phạm vi: unit, integration, API, E2E, regression, authorization, validation/boundary, error-handling, performance khi cần.
- Không chỉ dựa vào happy path.
- **[+A]** Phản biện bắt buộc AC của BA ở lượt debate (thay cho Requirement Reviewer).

### 3.5 Backend Developer
- Đọc requirement/thiết kế, kiểm code hiện tại trước khi sửa, triển khai business logic theo yêu cầu đã xác nhận, API, DB, validation, xử lý lỗi, authn/authz, unit + integration test, cập nhật tài liệu backend, commit vào branch task.
- Không tự đổi API contract nếu ảnh hưởng FE/hệ thống khác khi chưa phối hợp với Lead và SA.
- **[+D]** Migration chỉ qua `agent-db-clone.sh` (DB clone, không đụng DB thật).
- **[+E]** Code theo `docs/engineering/` (clean code, mục 9.7); chạy lint/format trước khi commit.
- **[+A]** Thấy solution không khả thi → báo Lead; Lead mở lại tối đa 1 lượt.

### 3.6 Frontend Developer
- Đọc requirement/thiết kế, kiểm cấu trúc FE, triển khai giao diện + luồng, tích hợp API, loading/empty/error state, validation, test FE, cập nhật tài liệu màn hình/hành động, commit vào branch task.
- Không tự suy đoán API response hoặc business rule; API contract chưa thống nhất thì phối hợp BE + Lead trước.
- **[+E]** Code theo `docs/engineering/` (clean code, mục 9.7); chạy lint/format trước khi commit.

### 3.7 Tester - Test Execution
- Kiểm môi trường, xác định suite, chạy unit/integration/API/E2E, regression, thu thập kết quả + bằng chứng, phân tích lỗi (code / test data / môi trường / cấu hình), báo cáo, cập nhật trạng thái test trong KB.
- Trạng thái mỗi test case: `PASS`, `FAIL`, `BLOCKED`, `NOT RUN`. **Không báo PASS khi chưa chạy hoặc thiếu bằng chứng.**
- Test fail phải cung cấp đủ thông tin để dev tái hiện.
- **[+D]** Chạy trên DB clone.

### 3.8 Code Reviewer
- Review độc lập với người code: diff, logic, đáp ứng yêu cầu, lỗi tiềm ẩn, edge case, xử lý lỗi, nhất quán kiến trúc, hiệu năng/bảo trì, test đủ phạm vi, **code ↔ KB nhất quán**, thay đổi ngoài phạm vi.
- Ưu tiên lỗi chức năng, mất dữ liệu, lỗi phân quyền, khó bảo trì (không chỉ style).
- Phân mức Critical/High/Medium/Low; nêu vị trí, lý do, tác động; review lại sau khi sửa.
- **[+C]** Diff so với nhánh gốc đúng của từng repo.
- **[+E]** Review theo `docs/engineering/coding-standards.md` và `review-checklist.md`; mỗi lỗi vi phạm quy chuẩn dẫn mục tương ứng.

### 3.9 Security Reviewer
- Kiểm authn, authz, lộ dữ liệu, input validation, injection (SQL...), XSS/CSRF, secrets/credentials, token/session, upload/download, truy cập ngoài quyền, log lộ thông tin nhạy cảm, dependency + cấu hình bảo mật. Cập nhật `docs/security/`.
- Tập trung rủi ro thực của thay đổi, không liệt kê checklist chung.
- Có vấn đề nghiêm trọng → task không được DONE đến khi xử lý hoặc có quyết định chấp nhận rủi ro rõ ràng của người có thẩm quyền.
- **[+A]** Hai lần vào việc: (1) duyệt nhanh phương án đã chốt trước khi code (một lần, ≤15 dòng, kể cả phương án gộp); (2) review code đầy đủ sau khi code xong.
- **[+A]** Security luôn có mặt ở mọi task (Fast Track chỉ có phần review code).

### 3.10 Scout **[+C]**
- Đọc KB (`docs/`) trước, sau đó đọc repo **một lần duy nhất**, ghi `CONTEXT.md` ≤ 1 trang: file liên quan, pattern, schema, convention, phần KB nghi lỗi thời.
- Các agent khác đọc CONTEXT.md, không tự quét lại repo.
- **[+E]** CONTEXT.md trích sẵn các mục `docs/engineering/` liên quan task (đặt tên, phân tầng, xử lý lỗi...), kèm file mẫu trong repo nên bắt chước.
- **Khi `/agent-team:init` chạy trên dự án có sẵn code:** dựng nháp KB từ code ngay lúc init, toàn bộ gắn `Unverified`.

---

## 4. Quy trình xử lý yêu cầu

### Tổng quan
```
Task → Lead phân loại (NHỎ / VỪA / LỚN), ghi lý do
   │
   ├─ NHỎ (workflow nhẹ)
   │    Lead xác định phạm vi + AC + test cần chạy
   │    → Dev → Test Execution → Code Reviewer ∥ Security → DONE
   │
   └─ VỪA / LỚN (workflow đầy đủ)
        Scout đọc KB + repo 1 lần → CONTEXT.md                      [+C]
             ▼
        DEBATE (subagent, mỗi lượt chạy song song, kết quả về Lead)   [+A]
          Lượt 1 ĐỀ XUẤT : SA đưa A/B/C │ BA viết AC
          Lượt 2 PHẢN BIỆN + CHẤM : BA │ SA │ Test Design
                 mỗi người góp ý MỌI phương án + chấm điểm kín (≤15 dòng)
          Lượt 3 (chỉ khi bất đồng lớn / phương án gộp cần xác nhận)
             ▼
        Lead chốt best solution (chọn một hoặc GỘP ý) → TASK.md
             ▼
        Security duyệt nhanh phương án đã chốt                       [+A]
             ▼
        Lead chia task, dependency, worktree + branch
             ▼
        CODE   BE ∥ FE theo API contract
             ▼
        TEST   Test Design viết test case → Test Execution viết/chạy
             ▼
        REVIEW Code Reviewer ∥ Security (đầy đủ); lỗi → dev sửa →
               chỉ reviewer đã báo lỗi review lại
             ▼
        KB cập nhật → Lead kiểm → DONE
```

### Bước 1: Tiếp nhận yêu cầu
Lead kiểm: mục tiêu của user, phạm vi, module ảnh hưởng, yêu cầu nghiệp vụ chưa rõ, rủi ro lớn.

| Loại | Cách xử lý |
|---|---|
| **Nhỏ, rõ, rủi ro thấp** | Lead tự xác định phạm vi, file/module, AC, test cần chạy; giao thẳng Dev + Test Execution. Không cần BA/SA/Test Design nếu không có câu hỏi đáng kể. |
| **Trung bình** | Gọi role cần thiết (vd đổi API: BA nếu rule chưa rõ, SA nếu ảnh hưởng contract/kiến trúc). |
| **Lớn / nhiều module / rủi ro cao** | Debate có cấu trúc với BA + SA + Test Design; chia task, dependency, kế hoạch test trước khi code. |
| **Rủi ro bảo mật cao** | Security duyệt cả solution, bất kể cỡ task, khi chạm authn, authz, dữ liệu nhạy cảm, secrets, bề mặt tấn công quan trọng. |

Không dùng số lượng agent làm thước đo chất lượng.

### Bước 2: Chọn workflow và agent
Lead ghi lý do gọi hoặc bỏ từng role vào TASK.md. Role bị bỏ thì trách nhiệm không được bỏ trống: Lead vẫn bảo đảm yêu cầu đủ rõ, test phù hợp, rủi ro được kiểm soát.

Hướng dẫn chọn agent (v2 mục 15.1, không thay phán đoán của Lead):

| Loại task | Thường cần | Chỉ khi cần |
|---|---|---|
| Sửa lỗi nhỏ, rõ ràng | Lead, Dev | BA, SA, Test Design |
| UI nhỏ, không đổi nghiệp vụ/API | Lead, FE | BA, SA, BE |
| Sửa lỗi API, rule đã rõ | Lead, BE, test phù hợp | BA, SA nếu không ảnh hưởng kiến trúc |
| Nghiệp vụ chưa rõ | Lead, BA, Dev, test | SA nếu ảnh hưởng kiến trúc |
| Đổi API contract / DB nhiều module | Lead, SA, Dev, Test Design/Execution | BA nếu nghiệp vụ đã rõ |
| Feature lớn nhiều module | Lead, BA, SA, Test Design, Dev, Test Execution, Code Reviewer | Security theo rủi ro (**[+A]** luôn có) |
| Authn, authz, dữ liệu nhạy cảm, secrets | Lead, Dev liên quan, test, Security | BA/SA theo mức thay đổi |

**[+C]** Task NHỎ gọi là **Fast Track**: không Scout, không debate.

### Bước 3: Phân tích độc lập (VỪA/LỚN)
Scout tạo CONTEXT.md. BA, SA, Test Design phân tích theo trách nhiệm, chủ động phát hiện vấn đề, không chỉ trả lời đúng phần câu hỏi.

### Bước 4: Debate và thống nhất phương án **[+A]**

**Cách chạy [+C]:** subagent, mỗi lượt chạy song song. Agent không nhắn tin cho nhau; Lead chuyển ý kiến giữa các lượt. Điểm chấm kín vì chỉ trả về Lead. Board `docs/agent-tasks/<task-id>/board/` chỉ Lead ghi (để user đọc lại).

**Mẫu output mỗi agent (≤ 15 dòng):**
```
Vai trò: <role>
Phương án A: ủng hộ/phản đối — rủi ro cụ thể (vd "B gây N+1 ở màn X") — điểm
Phương án B: ...
@role bắt buộc trả lời: ...
Thông tin còn thiếu (Assumption): ...
```
Phản biện chung chung → Lead yêu cầu làm lại.

**Bảng điểm (1–5 × trọng số):** Đáp ứng AC ×3, Ít ảnh hưởng code cũ ×3, Bảo mật ×3, Hiệu năng/mở rộng ×2, Dễ maintain/test ×1, Công sức ×1. Điểm sát nhau → ưu tiên ít sửa code cũ. Phương án có lỗi Security Critical/High chưa xử lý → loại dù điểm cao.

**Lead chốt best solution:**
1. *Chọn một:* điểm cao nhất, không dính lỗi Security Critical/High.
2. *Gộp (hybrid):* lấy ý mạnh nhất từng phương án (vd data model của A + cache của B + API contract của C). TASK.md ghi ý nào từ phương án nào, ai đề xuất, vì sao lấy, vì sao bỏ phần còn lại. Giải pháp gộp là phương án mới: SA kiểm tính nhất quán, Security duyệt nhanh (dùng lượt 3).

**Bế tắc:** cùng một issue hết lượt 3 mà không có lập luận mới → Lead phán quyết, ghi SUMMARY + "Phán quyết của Lead" trong TASK.md, không mở lại, không hỏi user. Ngoại lệ Security Critical/High: không ai override, phải sửa hoặc loại; hết giới hạn vòng vẫn chưa xử lý → `BLOCKED`, ghi vào báo cáo cuối.

**Tổng hợp ý kiến từng role (bắt buộc)** trong TASK.md: ủng hộ phương án nào, ý chính, được chấp nhận hay bị bác và lý do; ý thiểu số bị bác cũng ghi đủ.

**Thay Requirement/Solution Reviewer:** AC của BA → Test Design phản biện bắt buộc; solution → Security duyệt nhanh + Lead đối chiếu bảng điểm.

Lead cần xác định sau debate: phương án, phạm vi, AC, rủi ro, dependency, kế hoạch chia task, kế hoạch test, danh sách `Assumption` cần user xem lại ở cuối.

### Bước 5: Chia task
Task lớn phải chia thành nhiều task nhỏ. Mỗi task nhỏ có: Task ID, tên, mục tiêu, phạm vi, ngoài phạm vi, dependency, AC, test cần làm, agent phụ trách, worktree + branch, trạng thái.

Ví dụ (hủy chuyến đi): A business rules, B API hủy, C UI hủy, D integration test, E regression + tài liệu. Chia theo cấu trúc thực của dự án; không chia quá nhỏ tới mức chi phí điều phối, tạo worktree, review lớn hơn lợi ích.

### Bước 6: Dependency và song song
- API phải có contract trước khi FE tích hợp; FE và BE song song được nếu contract đã thống nhất.
- Integration test cần các thành phần sẵn sàng; regression sau khi thay đổi hoàn thành.
- Chỉ song song khi phạm vi độc lập hoặc contract rõ. Hai task sửa cùng file/kiến trúc → Lead đánh giá xung đột trước.

### Bước 7: Worktree và branch
Mỗi task nhỏ một Git worktree + branch riêng (chi tiết mục 5 và 7). Không sửa trực tiếp main/master.

### Bước 8: Triển khai
Dev làm trong worktree của task: đọc tài liệu (**[+C]** ưu tiên CONTEXT.md), kiểm code hiện tại, **[+E]** code theo `docs/engineering/` (clean code), chỉ đổi trong phạm vi, viết/cập nhật test, cập nhật KB nếu liên quan, kiểm diff trước khi commit. Yêu cầu chưa rõ hoặc thiết kế không khả thi → báo Lead. Không tự mở rộng phạm vi hay đổi business rule.

### Bước 9: Kiểm tra và commit
Dev chạy lint/format (`LINT_CMD`, `FORMAT_CMD`) **[+E]** và kiểm tra phù hợp, commit vào branch task (quy định mục 7). Commit thành công không đồng nghĩa task hoàn thành.

### Bước 10: Code review và security review
Chạy song song. Có issue → Lead giao dev sửa; chạy lại test bị ảnh hưởng. **[+C]** Chỉ reviewer đã báo lỗi review lại, và chỉ khi diff thay đổi.

### Bước 11: Thực thi kiểm thử
Test Execution chạy theo kế hoạch, kết quả có bằng chứng + trạng thái rõ. Gate: test chưa pass → không qua review. Có lỗi → Lead xác định người sửa, điều phối vòng sau.

### Bước 12: Kiểm tra KB
Lead kiểm tài liệu bị ảnh hưởng đã cập nhật chưa; nội dung phản ánh code thực tế. **[+B]** Code đổi API/DB/rule/màn hình/luồng mà KB chưa cập nhật → không được DONE.

### Bước 13: Xác nhận hoàn thành
Lead kiểm: code đúng branch, test theo phạm vi, review xong, Security xong, lỗi nghiêm trọng đã xử lý, KB cập nhật, worktree/branch không có thay đổi ngoài phạm vi, báo cáo đầy đủ. DONE không đồng nghĩa merge vào main.

**Báo cáo cuối cho user** (ngắn, dòng đầu là kết quả + link branch mỗi repo): phương án được chọn + 1 dòng lý do; số issue theo mức, issue còn lại; migration cần chạy khi merge; thay đổi ngoài code đã ghi `release-notes.md`; **mục "Giả định cần xem lại"** liệt kê mọi `Assumption`; cuối cùng đúng 1 việc user làm tiếp (≤ 2 phút).

---

## 5. Chia task lớn, worktree

### 5.1 Khi nào chia
Task ảnh hưởng nhiều module; có cả BE và FE; nhiều hạng mục test độc lập; nhiều dependency; khó review nếu làm một lần; giao được cho nhiều agent không xung đột; rủi ro lớn cần kiểm soát từng giai đoạn. Không chia nếu nhỏ, rõ, làm an toàn trong một lần. Không tạo task hay agent chỉ để đủ hình thức.

Với task nhỏ Lead quyết: cần BA không (chỉ khi nghiệp vụ chưa rõ); cần SA không (chỉ khi có quyết định kiến trúc/dependency); cần Test Design không (chỉ khi scenario không hiển nhiên); Dev nào (chỉ phần code bị ảnh hưởng); cần Test Execution riêng không (Dev chạy được với task đơn giản nếu chính sách cho phép); Code/Security Reviewer độc lập (**[+A]** Security luôn có). Workflow nhẹ vẫn phải có phạm vi, tiêu chí nghiệm thu, kiểm tra phù hợp, trạng thái cuối cùng xác minh được.

### 5.2 Mỗi task nhỏ một worktree riêng
```
Repository
├── main
├── Task A  → Worktree A, Branch feature/trip-cancellation-api
├── Task B  → Worktree B, Branch feature/trip-cancellation-ui
└── Task C  → Worktree C, Branch test/trip-cancellation
```
Tên branch tuân quy ước dự án (mặc định plugin: `agent/<task-id>`). Không checkout cùng một branch trong nhiều worktree theo cách gây xung đột.

### 5.3 Không dùng chung worktree
Tránh lẫn thay đổi, commit nhầm file; dễ xác định trách nhiệm, review, kiểm thử, khôi phục; giảm xung đột song song. Một agent làm nhiều task theo thời điểm, mỗi task vẫn worktree + branch riêng.

### 5.4 Base branch
Task độc lập: tạo từ branch nền thống nhất. Task phụ thuộc: chờ task kia tích hợp, hoặc dựa branch có phần thay đổi phụ thuộc, hoặc dựa contract rồi tích hợp sau. Không chọn base branch khi chưa xem dependency.

### 5.5 Tích hợp
Lead xác định: task nào tích hợp trước, branch nào chứa thay đổi phụ thuộc, file sửa ở nhiều branch, xung đột API contract, test sau tích hợp, KB phản ánh trạng thái cuối. Không tự merge tất cả vì agent báo DONE.

### 5.6 Nhiều repo **[+D]**
- `REPOS=". ../FrontEnd"` trong `.claude/agent-team.config`. Repo chính chứa `.claude/`, `docs/`, `CLAUDE.md`, board; không tạo gì ở thư mục cha.
- Nhánh gốc theo repo: `BASE_BRANCH` + `BASE_BRANCHES="../FrontEnd=master"`.
- Branch, commit, push thực hiện trong từng repo (`git -C ../FrontEnd ...`); chỉ tạo branch ở repo task thực sự đụng tới.
- Vùng code: `BE_PATHS`, `FE_PATHS`, `TEST_PATHS` tính từ repo chính.

---

## 6. Xử lý khi thiếu thông tin

Agent không tự tạo business rule hay đoán quyết định quan trọng **mà không đánh dấu**. Nhãn thông tin:

| Nhãn | Ý nghĩa |
|---|---|
| Verified | Đã xác minh từ yêu cầu, code hoặc nguồn tin cậy |
| Assumption | Giả định chưa xác nhận |
| Proposed | Phương án đang đề xuất |
| Confirmed | Người có thẩm quyền đã xác nhận |

Khi thiếu thông tin, agent: (1) nêu chính xác thiếu gì, (2) vì sao ảnh hưởng, (3) đề xuất phương án + ưu/nhược/rủi ro, (4) báo Lead.

**[+D] Lead quyết, không hỏi user:**
- Thiếu business rule → Lead chọn **best solution** (theo bảng điểm sau khi 4 người debate góp ý), ghi `Assumption`, đưa vào "Giả định cần xem lại" ở báo cáo cuối.
- Thiếu thông tin kỹ thuật → team tự quyết qua debate.

`BLOCKED` chỉ khi không thể tiếp tục an toàn: thiếu quyền hoặc dependency cần thiết, không xác minh được repo/worktree/branch, vượt phạm vi được phép, thiếu môi trường để kiểm tra cần thiết, hoặc Security Critical/High chưa xử lý được. Khi BLOCKED phải ghi lý do + điều kiện để tiếp tục. Không BLOCKED vì khó khăn nhỏ.

---

## 7. Quy định Git bắt buộc

### 7.1 Worktree và branch
Mỗi task nhỏ một worktree + branch riêng. Không sửa trực tiếp main/master. Không dùng chung worktree, không tự chuyển branch của task khác, không sửa file ngoài phạm vi khi chưa thống nhất.

Trước khi sửa, xác minh bằng:
```bash
git rev-parse --show-toplevel
git branch --show-current
git status --short
git worktree list
```
Kiểm: đúng repo, worktree, branch; có thay đổi chưa commit không; có thay đổi của người/task khác không. Không mặc định worktree sạch.

### 7.2 Không làm mất thay đổi hiện có
Không tự xóa thay đổi chưa commit, reset làm mất công việc, checkout làm mất thay đổi, ghi đè file task khác đang dùng, xóa file vì "không cần", commit thay đổi ngoài phạm vi. Thay đổi không rõ nguồn gốc → xác định chủ sở hữu hoặc báo Lead.

### 7.3 Commit
- Mỗi task commit vào branch riêng của nó.
- **Commit message chỉ một dòng tiêu đề.** Quy ước plugin: `[<role>] <task-id>: <mô tả ngắn>`. Không body.
- Không trailer: `Signed-off-by`, `Co-authored-by`, `Reviewed-by`, `Generated-by`. Không tự thêm chữ ký của agent/AI.
- Không empty commit. Không `git add .` máy móc khi worktree có thể chứa thay đổi ngoài phạm vi.
- Trước commit: xem diff, kiểm file đổi, xác nhận thuộc đúng task, chạy test phù hợp, stage đúng file.
- **[+B]** Guard chặn commit có body hoặc trailer, sai format.

### 7.4 Push, merge, lịch sử
Không force push, không rewrite lịch sử, không tự merge vào main/master/develop, không tạo PR, không xóa branch/worktree khi chưa kiểm tra hoặc khi đang dùng/còn thay đổi chưa xử lý. Push dạng `git push -u origin agent/<task-id>`. Hoàn thành task không đồng nghĩa được merge hoặc xóa branch.

**[+B]** Hook chặn push nếu diff có secret, `.env`, key, dump DB.

### 7.5 Kiểm tra trước khi đóng
Đúng branch, đúng worktree, commit tồn tại, message đúng quy định, không thay đổi ngoài phạm vi, không còn thay đổi chưa xử lý, test và review hoàn tất.

---

## 8. Quy trình kiểm thử

Kiểm thử là một phần của phát triển, không phải bước bổ sung cuối cùng.

**8.1 Trước khi code.** Test Design phối hợp BA + SA xác định: luồng chính, trường hợp biên, lỗi, điều kiện vào/ra, quyền truy cập, regression, tiêu chí thành công. **[+A]** Phản biện AC của BA ngay trong debate.

**8.2 Trong khi code.** Dev viết/cập nhật test: BE (unit, integration, API), FE (component hoặc test phù hợp framework), luồng quan trọng (Playwright E2E hoặc tương đương), thay đổi quyền (authorization test), ảnh hưởng nhiều module (regression). Không bắt buộc mọi loại cho mọi task; theo rủi ro.

**8.3 Sau khi code.** Test Execution chạy và báo cáo: Task ID, phạm vi, môi trường, lệnh/suite đã chạy, kết quả từng nhóm, lỗi, bằng chứng, test chưa chạy + lý do, rủi ro còn lại. **[+D]** Chạy trên DB clone. Không tuyên bố toàn bộ hệ thống đã test khi chỉ chạy một phần.

**8.4 Khi test thất bại.**
1. Tester ghi lỗi + bằng chứng.
2. Lead xác định người sửa.
3. Dev tái hiện, sửa trong worktree task phù hợp.
4. Dev chạy lại test liên quan.
5. Tester xác minh.
6. Code Reviewer review lại nếu thay đổi ảnh hưởng phần đã review.
7. Lead xác nhận trạng thái.

Lỗi thuộc task khác → Lead quyết tạo task sửa hoặc cập nhật task hiện có; không tự đổi worktree task khác.

---

## 9. Quản lý Knowledge Base (KB)

KB là nguồn tài liệu kỹ thuật + nghiệp vụ giúp agent hiểu dự án nhất quán qua nhiều task: hệ thống hoạt động thế nào, module liên quan nhau ra sao, màn hình gọi API nào, API dùng dữ liệu nào, business rule áp dụng ở đâu, test nào xác minh chức năng, thay đổi mới ảnh hưởng đâu. **[+C]** Scout đọc KB trước nên mọi agent bớt đọc repo.

### 9.1 Khởi tạo
- **Dự án mới:** tạo cấu trúc ban đầu; ghi yêu cầu + kiến trúc đã thống nhất; quyết định kỹ thuật; danh sách module + luồng nghiệp vụ.
- **Dự án có sẵn:** đọc cấu trúc repo; kiểm code, API, DB, cấu hình; xác định tài liệu hiện có; đối chiếu tài liệu với code; bổ sung phần thiếu; đánh dấu rõ thông tin chưa xác minh.
- Không mặc định tài liệu hiện có luôn đúng. Không ghi đè toàn bộ KB khi chỉ cần cập nhật một phần.
- **[+D]** `/agent-team:init` luôn tạo bộ khung bên dưới (file gốc). **Dự án đã có code thì init tạo luôn nội dung KB:**
  1. Nhận diện có code sẵn: repo có file mã nguồn đã commit (`git ls-files`).
  2. Scout (Sonnet) đọc một lần: cấu trúc repo, tech stack, module, API/route, schema DB, tích hợp ngoài, test hiện có; **mọi repo trong `REPOS`**.
  3. Điền: `project-overview`, `architecture`, `tech-stack`, `domain-model`, `api/endpoints`, `database/schema`, `integrations/`, `testing/test-strategy`; tạo `modules/<tên>/README.md` cho các module nhận diện được (`screens/`, `actions/` thêm dần theo task).
  3b. **[+E] Quy chuẩn code (`engineering/`):** Scout đếm pattern code đang dùng (đặt tên, phân tầng, xử lý lỗi, logging, validation, style API, quy ước DB/migration/test, lint/format đang có), ghi pattern chiếm đa số kèm ví dụ `file:dòng`, nhãn `Observed`. Tự nhận diện lệnh lint/format điền `LINT_CMD`, `FORMAT_CMD` vào config.
  4. Mọi mục gắn `Unverified`, ghi nguồn (file/commit) và `verified-at: <commit hiện tại>`. Business rule suy ra từ code chỉ ghi là `Assumption`, không ghi Confirmed.
  5. Tài liệu có sẵn của dự án (README, wiki, docs cũ): đọc làm nguồn, đối chiếu với code, mâu thuẫn thì đánh dấu, không di chuyển hay ghi đè.
  6. Giới hạn chi phí: repo lớn thì quét theo module chính, ghi rõ phần chưa quét; user có thể bỏ qua bước này bằng cờ `--skip-kb` (KB tạo dần ở các task sau).
  7. Không commit; báo user danh sách file đã tạo. BA xác nhận dần theo từng task (Unverified → Verified/Confirmed).

### 9.2 Cấu trúc (v2, nằm trong `docs/` của repo chính; tên `docs` luôn viết thường)
```
docs/
├── design.md                  (tài liệu này)
├── README.md
├── project-overview.md
├── architecture.md
├── tech-stack.md
├── domain-model.md
├── business-rules.md
├── roles-and-permissions.md
├── glossary.md                [+D] thuật ngữ
├── engineering/               [+E] quy chuẩn code
│   ├── coding-standards.md    đặt tên, cấu trúc, phân tầng, lỗi, log, validation, API, DB, test, comment
│   └── review-checklist.md    clean code checklist cho Code Reviewer
├── modules/
│   └── <module-name>/
│       ├── README.md
│       ├── screens/<screen-name>.md
│       └── actions/<action-name>.md
├── api/
│   ├── README.md
│   └── endpoints.md
├── database/
│   ├── schema.md
│   └── entities.md
├── integrations/<integration-name>.md
├── testing/
│   ├── test-strategy.md
│   ├── api-tests.md
│   ├── playwright-e2e.md
│   ├── coverage-matrix.md
│   └── test-report.md
├── security/                  [+D]
│   ├── findings.md
│   └── permission-decisions.md
├── decisions/
│   ├── README.md
│   └── <decision-id>.md
└── agent-tasks/<task-id>/     [+A][+D]
    ├── TASK.md                chỉ Lead ghi
    └── board/                 chỉ Lead ghi: SUMMARY.md + kết quả từng lượt
```
Có thể điều chỉnh theo quy mô, nhưng duy trì tổ chức nhất quán. Dự án mới: `modules/<tên>/` tạo khi có task chạm module đó. Dự án có sẵn code: init tạo `modules/<tên>/README.md` cho module nhận diện được (mục 9.1).

### 9.3 Nội dung cần lưu
- **Project overview:** mục tiêu hệ thống, phạm vi, thành phần chính.
- **Architecture:** cấu trúc, module, luồng giao tiếp, dependency quan trọng, quyết định kiến trúc đã xác nhận.
- **Business rules:** quy tắc, điều kiện áp dụng, ngoại lệ, nguồn xác nhận.
- **Module:** chức năng, màn hình, hành động, API, DB, rule áp dụng, test liên quan.
- **Screen:** mục đích, trạng thái giao diện, hành động, API gọi, validation, quyền, test.
- **Action:** điều kiện, luồng xử lý, API + dữ liệu, rule, trường hợp lỗi, test.
- **Testing:** chiến lược, danh sách test case, coverage, kết quả thực thi, phần chưa test.
- **Engineering [+E]:** quy chuẩn code và checklist clean code (mục 9.7).

### 9.4 Ai cập nhật gì
| Agent | Tài liệu phụ trách |
|---|---|
| BA | Requirements, business rules, AC, `domain/`, glossary |
| Solution Architect | Architecture, technical decisions, dependencies, API contract, `engineering/` **[+E]** |
| Backend Developer | API, backend logic, database, integrations |
| Frontend Developer | Screens, components, actions, frontend flows |
| Test Design | Test strategy, test cases, coverage matrix |
| Test Execution | Test reports, execution results, failures |
| Code Reviewer | Kiểm nhất quán giữa code và tài liệu |
| Security Reviewer | Security findings, permissions, security decisions |
| Lead | Điều phối, kiểm đầy đủ và nhất quán |

Lead không nhất thiết tự viết hết; đảm bảo cập nhật đúng người, phạm vi, thời điểm. **[+B]** Guard chặn ghi sai thư mục KB theo bảng này.

### 9.5 Kiểm tra tính chính xác
Nhãn: **Verified / Unverified / Planned / Deprecated**; **[+D]** mỗi file ghi `verified-at: <commit>` và nguồn (task-id hoặc commit). Không ghi phương án dự kiến như đã triển khai; không ghi test PASS khi chưa có kết quả; không ghi business rule là Confirmed nếu chỉ là suy đoán.

**[+D] Phát hiện lỗi thời:** Scout so `verified-at` với code hiện tại; module đổi nhiều mà KB cũ → đánh `Unverified` trong CONTEXT.md. Code graph (tùy chọn) giúp tìm API/model đã đổi mà tài liệu chưa nhắc.

### 9.6 KB và Git worktree
KB là một phần của quy trình thay đổi phần mềm. Task đổi API, DB, business rule, màn hình, luồng → cập nhật tài liệu liên quan; không đổi thông tin cần duy trì thì không bắt buộc. Giảm conflict khi song song:
- Mỗi task chỉ cập nhật tài liệu trong phạm vi thay đổi.
- Lead phân quyền sở hữu tài liệu theo module khi nhiều task chạy đồng thời.
- Tránh nhiều task cùng sửa file tổng hợp (`api/endpoints.md`); chia theo module/endpoint khi cần.
- Nhiều thay đổi cần tổng hợp: task ghi đề xuất hoặc sửa trong branch của mình; Lead hoặc KB Maintainer gộp ở bước tích hợp.
- Không ghi đè cả file; khi conflict phải hợp nhất nội dung và kiểm nhất quán với code đã tích hợp.
- Tài liệu cuối phản ánh code sau tích hợp, không chỉ branch riêng lẻ.

### 9.7 Quy chuẩn code (clean code) **[+E]**

Quy chuẩn nằm trong KB (`docs/engineering/`), không nằm trong đầu từng agent, để mọi task code nhất quán.

**Nguồn quy chuẩn**
- Dự án có sẵn code: Scout ghi pattern đang dùng nhiều nhất (nhãn `Observed`, kèm ví dụ trong repo). Task đầu tiên, Architect xác nhận trong debate → `Verified`. Nguyên tắc: **theo convention hiện có, không tự đổi**.
- Dự án mới: Architect đặt quy chuẩn theo convention chuẩn của stack ở task đầu tiên, ghi vào `decisions/`.

**Nội dung `coding-standards.md`**: đặt tên; cấu trúc thư mục; phân tầng (controller/service/repository...); xử lý lỗi; logging (không log dữ liệu nhạy cảm); validation; style API (response, mã lỗi, phân trang); quy ước DB + migration (index, rollback); quy ước test; quy tắc comment (ngắn, chỉ khi cần); lệnh lint/format.

**Clean code checklist (`review-checklist.md`)**
1. Tên rõ nghĩa; hàm nhỏ, một trách nhiệm.
2. Không lặp code; không code chết, không `console.log`/debug sót.
3. Không magic number/string; cấu hình qua config/ENV.
4. Xử lý lỗi và edge case rõ ràng; không nuốt lỗi.
5. Không N+1; list có phân trang; truy vấn có index.
6. Không sửa code cũ khi không cần; không refactor ngoài phạm vi task; diff nhỏ nhất đủ dùng.
7. Test đi kèm, dễ test (ít phụ thuộc cứng).
8. Comment ngắn, chỉ khi thật cần.
9. Không để secret, `.env`, dữ liệu thật trong code.

**Áp dụng trong quy trình**
- Scout đưa mục liên quan vào CONTEXT.md; dev đọc và code theo.
- Dev chạy `FORMAT_CMD` và `LINT_CMD` trước khi commit. Lead chỉ chuyển sang S5 khi lint/format pass.
- Code Reviewer review theo checklist, dẫn mục vi phạm; vi phạm quy chuẩn xếp Medium trở lên khi ảnh hưởng chức năng/bảo trì, còn lại Low.
- Đổi quy chuẩn chỉ qua debate của một task, Architect cập nhật `engineering/` và ghi `decisions/`. Dev không tự đổi.
- Không dùng quy chuẩn làm lý do refactor hàng loạt code cũ; chỉ áp dụng cho code mới và phần đang sửa.

---

## 10. Quản lý trạng thái task

| Trạng thái | Ý nghĩa |
|---|---|
| TODO | Chưa bắt đầu |
| ANALYZING | Đang phân tích |
| READY | Đủ thông tin để triển khai |
| IN_PROGRESS | Đang thực hiện |
| BLOCKED | Không thể tiếp tục an toàn |
| CODE_COMPLETE | Hoàn thành triển khai ban đầu |
| IN_REVIEW | Đang review |
| TESTING | Đang kiểm thử |
| FIX_REQUIRED | Có lỗi cần sửa |
| DONE | Đáp ứng tiêu chí hoàn thành |
| CANCELLED | Hủy theo quyết định có thẩm quyền |

Trạng thái phản ánh công việc thực tế, không chỉ báo cáo của agent. Code xong chưa test thì chưa DONE; đang chờ task phụ thuộc mà còn việc bắt buộc thì chưa DONE.

**[+B] Stage (guard dùng):** `.agent-team/stage` do Lead ghi.

| Stage | Trạng thái tương ứng | Guard cho phép ghi |
|---|---|---|
| S1 yêu cầu | ANALYZING | chỉ tài liệu/board |
| S2 solution | ANALYZING → READY | chỉ tài liệu/board |
| S3 code | IN_PROGRESS, CODE_COMPLETE | code BE/FE |
| S4 test | TESTING | test |
| S5 review | IN_REVIEW, FIX_REQUIRED | theo quyền role |
| S6 đóng | DONE | theo quyền role |

**[+D] Resume:** `/agent-team:resume <task-id>` đọc TASK.md, stage, SUMMARY, kết quả lượt gần nhất; xác định bước dang dở; làm tiếp trên **branch cũ**, không tạo task-id mới. Dùng được sau khi hết quota (plugin không tự chạy lại; người dùng gọi resume).

---

## 11. Quy tắc phối hợp giữa các Agent

**11.1 Không giao việc trùng lặp.** Lead xác định ai chịu trách nhiệm chính từng phần. Agent khác hỗ trợ review/ý kiến nhưng không sửa cùng phần code trong nhiều worktree khi chưa có kế hoạch. **[+B]** Guard khoá quyền ghi theo role.

**11.2 Không tự mở rộng phạm vi.** Dev chỉ làm phần được giao; cần đổi ngoài phạm vi → báo Lead (tạo task mới hoặc điều chỉnh).

**11.3 Giao tiếp dựa trên thông tin cụ thể.** Báo cáo gồm: đã làm gì, đổi gì, đã kiểm gì, kết quả thực tế, vấn đề còn lại, dependency/quyết định đang chờ, worktree + branch. Không chỉ nói "đã xong". **[+C]** Tối đa 15 dòng theo mẫu.

**11.4 Điều phối tinh gọn, tránh vòng lặp.**
- Không gọi cả đội cho mọi task; mỗi lần gọi có mục tiêu, đầu vào, đầu ra cụ thể.
- Truyền ngữ cảnh cần thiết (**[+C]** CONTEXT.md thay vì lịch sử dài).
- Không nhờ nhiều agent làm cùng phân tích trừ khi cần đối chiếu độc lập.
- Không review lại nếu diff không đổi và không có bằng chứng mới.
- Chạy song song được, nhưng kiểm dependency và tránh cùng sửa một phạm vi.
- **Giới hạn cụ thể [+C]:**

| Giới hạn | Giá trị |
|---|---|
| Lượt debate | tối đa 3 |
| Vòng sửa mỗi issue review | tối đa 3, rồi Lead phán quyết |
| Mở lại solution do dev báo không khả thi | tối đa 1 lượt |
| Không có tiến triển | `BLOCKED`, ghi vào báo cáo cuối |

**11.5 Ưu tiên đúng đắn hơn tốc độ.** Rủi ro mất dữ liệu, sai phân quyền, phá tương thích → dừng phần không an toàn, báo Lead; không chọn phương án "nhanh nhất" khi chưa đánh giá ảnh hưởng.

---

## 12. Cấu trúc cấu hình Claude Code

```
plugin agent-team/
├── commands/   init.md, run.md, resume.md (mới)
├── agents/     scout, business-analyst, solution-architect (Architect; TA tách cho LỚN),
│               test-designer, test-executor, backend-developer, frontend-developer,
│               code-reviewer, security-reviewer      (Lead do command run.md đảm nhiệm)
├── hooks/      guard.py, show_post.py
├── scripts/    agent-db-clone.sh, code-graph.py
└── templates/  TASK.md, SUMMARY.md, POST.md (mẫu ≤15 dòng), CONTEXT.md,
                agent-team.config.example, claude-md-section.md, bộ khung docs/ (mục 9.2)

project (repo chính)/
├── .claude/agent-team.config      REPOS, BASE_BRANCH(ES), BE/FE/TEST_PATHS, COMPOSE_DIR, USE_CODE_GRAPH, LINT_CMD, FORMAT_CMD
├── .claude/agent-team/            script + template copy từ plugin
├── .agent-team/stage              (gitignore)
├── CLAUDE.md                      mục "Agent Team"
├── release-notes.md               thay đổi ngoài code (ENV mới, lệnh mới)
└── docs/                          mục 9.2
```

Đây là cấu trúc đề xuất; kiểm cú pháp và khả năng hỗ trợ của phiên bản Claude Code đang dùng trước khi triển khai. File agent quy định rõ: vai trò, phạm vi, được/không được làm, đầu vào cần, đầu ra bắt buộc, cách báo lỗi/BLOCKED, quy tắc Git + KB liên quan. Commands chuẩn hóa quy trình thường xuyên; rules chứa nguyên tắc chung cho mọi agent (trong plugin là mục "Agent Team" của CLAUDE.md).

---

## 13. Tiêu chí xác nhận DONE

| Nhóm | Điều kiện |
|---|---|
| **Code** | Đúng yêu cầu; đúng quy chuẩn `engineering/`, lint/format pass **[+E]**; không thay đổi ngoài phạm vi chưa xử lý; commit đúng branch; message đúng quy định; không sót thay đổi chưa commit |
| **Testing** | Đã chạy test bắt buộc, có bằng chứng; không còn lỗi nghiêm trọng; test chưa chạy được ghi rõ |
| **Review** | Code review xong; phát hiện đã sửa hoặc có quyết định rõ; Security xong, Critical/High đã xử lý |
| **Knowledge Base** | Tài liệu bị ảnh hưởng đã cập nhật; không mâu thuẫn code; giả định và thông tin chưa xác minh ghi rõ |
| **Git** | Đúng worktree + branch; commit đúng phạm vi; không tự merge/xóa branch |

Thiếu điều kiện bắt buộc → ghi rõ phần thiếu, không đánh dấu DONE.

---

## 14. Các quyết định đã chốt (trả lời các câu hỏi Reviewer của v2)

**14.1 Cấu trúc đội ngũ**
- 9 agent đủ chưa? Đủ, thêm Scout (**[+C]**). Không thêm Database/DevOps agent: `agent-db-clone.sh` đủ cho migration.
- Tách SA thành SA + TA? Mặc định gộp thành Architect; chỉ tách cho task LỚN.
- Gộp Test Design và Execution? Giữ tách (Opus thiết kế, Sonnet thực thi).
- Requirement/Solution Reviewer: không thêm; vai trò do Test Design (phản biện AC) và Security (duyệt solution) đảm nhận.

**14.2 Chia task và worktree**
- Mỗi task nhỏ worktree + branch riêng (v2) là bắt buộc trong thiết kế; khi code plugin làm sau cùng (phần tốn công nhất).
- Base branch cho task phụ thuộc, tích hợp: theo mục 5.4–5.5. Lead tạo kế hoạch dependency trước khi triển khai.
- Giảm xung đột API/DB/KB: chia tài liệu theo module, phân quyền sở hữu, Lead gộp ở tích hợp.

**14.3 Model**
- Opus: Lead, BA, SA, Test Design, Security. Sonnet: Scout, BE, FE, Test Execution, Code Reviewer.
- Giảm chi phí: Scout đọc repo một lần, debate chỉ 4 người, output ≤15 dòng, review lại có chọn lọc.

**14.4 Kiểm thử**
- Không đặt coverage tối thiểu cố định; theo rủi ro và ma trận requirement ↔ test.
- E2E bắt buộc cho luồng người dùng quan trọng và thay đổi quyền.
- Tự động chạy test: hook gate chặn chuyển stage khi test chưa pass.

**14.5 Knowledge Base**
- Giữ cấu trúc v2 đầy đủ (mục 9.2). Dự án có sẵn code: `init` dựng KB nháp ngay (mục 9.1); dự án mới: tạo khung, điền dần. Requirement ↔ API ↔ DB ↔ màn hình ↔ test liên kết qua module README và coverage matrix.
- Phát hiện lỗi thời: `verified-at` + Scout + code graph. Task đổi API/DB/rule mà chưa cập nhật KB thì chặn DONE.

**14.6 Cấu hình Claude Code**
- Chọn workflow: bảng ở Bước 2; Lead ghi lý do.
- Giới hạn retry/vòng: mục 11.4.
- Không sửa nhầm worktree: guard kiểm repo/branch trước khi ghi.
- Kiểm soát tạo task, phân công, DONE: Lead, có gate ở hook.
- Tự động hóa: tạo branch, commit, push branch task, chạy test, build code graph. Cần user: merge vào main, tạo PR, xem "Giả định cần xem lại".

---

## 15. Tối ưu chi phí và điều phối

- Chọn workflow theo độ phức tạp, phạm vi, rủi ro (bảng ở Bước 2). Lead có thể kết hợp vai trò trong workflow nhẹ nhưng không bỏ trách nhiệm quan trọng.
- Mỗi lần gọi agent gắn một đầu ra cụ thể; không gửi ngữ cảnh dài khi chỉ cần một phần; chỉ song song khi dependency rõ; không để nhiều agent cùng sửa một vùng hay một tài liệu khi chưa có phân quyền sở hữu.
- Theo dõi số lần gọi, thời gian, chi phí ước tính, số vòng sửa để tối ưu dần.
- Chính sách model: bắt đầu bằng model phù hợp chi phí; nâng cho quyết định khó/phạm vi rộng/lỗi phức tạp/rủi ro bảo mật cao; không nâng chỉ vì tên vai trò; đánh giá định kỳ chất lượng, chi phí, latency.
- Ước lượng giảm 50–70% token so với phiên bản debate 11 agent là **chưa đo**, chỉ tính theo số agent và số lượt.

---

## 16. Thi hành bằng guard **[+B]**

| Quy tắc | Thi hành |
|---|---|
| Khoá ghi theo stage (S1–S2 tài liệu, S3 code, S4 test) | Hook, đã có |
| Khoá vùng theo role (BE/FE/test) | Hook, đã có; **phụ thuộc `agent_type` tới hook khi chạy subagent (chưa kiểm chứng)** |
| Khoá ghi theo thư mục KB (mục 9.4) | Hook, mở rộng từ `docs/domain/` |
| Điểm chấm kín | Tự nhiên (subagent trả về Lead) |
| Chặn commit có body/trailer, sai format `[role] task-id:` | Hook, thêm mới |
| Chặn push main/master/develop, force push, secret/.env/dump | Hook, đã có |
| Migration và test DB chỉ qua `agent-db-clone.sh` | Hook, đã có |
| Gate chuyển stage (AC xong, test pass, lint/format pass, KB cập nhật) | Thêm mới |
| Code theo quy chuẩn `engineering/` | Hướng dẫn cho dev + Code Reviewer chặn ở S5 (lint do Lead gate) |
| Tự chốt khi thiếu rule + Assumption, giới hạn vòng, gộp phương án, nhãn thông tin | Hướng dẫn trong `run.md` (không enforce) |

---

## 17. Lộ trình và rủi ro

| Bản | Nội dung | Ước tính |
|---|---|---|
| **v0.3** | 10 agent (Scout, Architect gộp, Test Design/Execution), debate 4 người bằng subagent, Fast Track, Security duyệt solution, tự chốt + Assumption, gộp phương án, bộ khung KB v2 + `init` dựng KB nháp từ code có sẵn + khoá theo thư mục, giới hạn vòng, trạng thái task, commit 1 dòng, `/agent-team:resume` | 1–2 ngày |
| **v0.4** | Chia task nhỏ + worktree riêng song song, kế hoạch tích hợp, KB chia theo module | 1–2 ngày |
| Sau đó | Đo token thật trên task thật, chỉnh model/thinking/giới hạn | liên tục |

**Rủi ro đã biết**
1. Chưa kiểm chứng `agent_type` có tới hook khi chạy subagent. Nếu không, khoá vùng theo role không hoạt động; cần phương án thay (khoá theo stage + thư mục). Thử trước khi làm.
2. Subagent không nhắn tin trực tiếp; Lead là điểm nghẽn và có thể thiên kiến. Giảm bằng ghi đủ ý kiến thiểu số + bảng điểm.
3. Tự chốt business rule có thể sai nghiệp vụ; giảm bằng nhãn `Assumption`, chọn best solution qua debate, và báo cuối cùng.
4. Ước lượng token chưa đo.

---

## 18. Kết luận

Mỗi task chỉ chạy quy trình tối thiểu cần thiết để đạt chất lượng. Lead điều phối và chịu trách nhiệm trạng thái cuối. Quyết định giải pháp qua debate 4 người, chốt best solution, ghi lại ý kiến từng role. Task lớn chia nhỏ, mỗi task nhỏ một worktree + branch. Chỉ song song khi dependency cho phép. Dev kiểm code và chạy test trước khi báo xong; Code Reviewer và Security review độc lập; Tester không báo PASS khi chưa chạy. KB cập nhật theo code thực tế, phân quyền để giảm conflict. Commit một dòng, không signature; không tự merge, force push, rewrite lịch sử, xóa worktree. Giới hạn vòng lặp; không tiến triển thì dừng. Chỉ DONE khi đủ tiêu chí. Quy tắc quan trọng được hook thi hành.
