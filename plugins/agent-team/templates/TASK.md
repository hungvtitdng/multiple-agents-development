# <task-id>: <tên task>

> Chỉ Lead ghi. Hook đọc mục "Điều kiện chuyển giai đoạn" để cho phép Lead sang S3/S5/S6. Điền `TODO` → giá trị thật khi đạt.

| | |
|---|---|
| Branch | `agent/<task-id>` (nhiều repo: liệt kê repo + branch từng repo) |
| Trạng thái | ANALYZING / READY / IN_PROGRESS / TESTING / IN_REVIEW / FIX_REQUIRED / BLOCKED / DONE |
| Giai đoạn | S1 / S2 / S3 / S4 / S5 / S6 |
| Thành viên | (role tham gia; role bỏ qua + lý do) |

## Điều kiện chuyển giai đoạn (Lead cập nhật, hook kiểm)
- Loại: TODO (NHỎ / VỪA / LỚN)
- Tiêu chí nghiệm thu: TODO (chỉ cần cho NHỎ, vd AC ngắn do Lead viết)
- Phương án chốt: TODO (tên/mô tả; VỪA/LỚN)
- Workflow: TODO (YES = có design/workflow.md / N/A)
- UI mockup: TODO (YES = có design/mockup-<màn>.html đen trắng / N/A nếu task không có UI)
- Security duyệt solution: TODO (APPROVED / N/A)
- Kết quả test: TODO (PASS / FAIL)
- Lint/format: TODO (PASS / N/A)
- Gap còn mở: TODO (số gap chưa đóng ở mục 14; 0 mới sang S5)
- Code review: TODO (APPROVED)
- Security review: TODO (APPROVED)
- Cập nhật KB: TODO (YES / KHÔNG CẦN)
- Bài học: TODO (YES = đã ghi vào LESSONS_PATH / KHÔNG CÓ)

## 0. Yêu cầu gốc (nguyên văn, Lead chép từ user, không sửa)
> Đây là phần duy nhất `challenger` được biết (Lead đưa trong prompt; challenger không đọc file này).

## 1. Yêu cầu & Acceptance Criteria (BA)
- AC-<n>: Given ... When ... Then ... (đánh số AC-1, AC-2, ...)

## 2. Giả định (Assumption) cần user xem lại
> Hiện đỏ ở đầu REPORT.html để client xác nhận. Xếp theo Mức ảnh hưởng. Client trả lời thì ghi vào cột cuối: `Đúng` / `Sai: <cách đúng>`.

| Điểm chưa rõ | Cách hiểu đã chọn (best solution) | Lý do | Phương án khác đã xét | Ưu | Nhược | Ảnh hưởng nếu sai | Mức ảnh hưởng (Cao / Trung bình / Thấp) | Ai đề xuất | Client xác nhận |
|---|---|---|---|---|---|---|---|---|---|

## 3. Các phương án (A/B/C)
> Mỗi phương án ghi đúng các dòng dưới: REPORT.html dựng bảng so sánh (cột = phương án) từ các dòng này + bảng điểm mục 5.

### A. <tên>
- Mô tả: <tổng thể + kỹ thuật>
- API contract:
- Ưu:
- Nhược:
- Rủi ro:
- Kết luận: Chọn / Gộp (lấy ý ...) / Loại (vì ...)

### B. <tên>

## 4. Rủi ro & đánh giá bảo mật
| Phương án | Role | Rủi ro / lỗ hổng | Mức | Trả lời / xử lý |
|---|---|---|---|---|

## 5. Bảng chấm điểm (Lead tổng hợp từ điểm các role, mỗi role chấm độc lập)
| Tiêu chí | Trọng số | A | B | C |
|---|---|---|---|---|
| Đáp ứng AC | ×3 | | | |
| Ít ảnh hưởng code cũ | ×3 | | | |
| Bảo mật | ×3 | | | |
| Hiệu năng / mở rộng | ×2 | | | |
| Dễ maintain / test | ×1 | | | |
| Công sức | ×1 | | | |
| **Tổng** | | | | |

## 6. Phương án được chốt
- **Cách chốt:** chọn một / gộp
- **Giải pháp:** ...
- **Nếu gộp:** ý nào lấy từ phương án nào, ai đề xuất, vì sao lấy, vì sao bỏ phần còn lại:
- **Phân loại NHỎ/VỪA/LỚN:** ... , **vì sao:** ...
- **Security duyệt nhanh:** APPROVED / REJECTED (ghi lại ở mục điều kiện)

## 7. Tổng hợp ý kiến theo role (bắt buộc khi chốt)
| Role | Ủng hộ | Ý kiến chính | Chấp nhận / Bác | Lý do |
|---|---|---|---|---|
| BA | | | | |
| Architect (SA/TA) | | | | |
| Test Design | | | | |
| Security | | | | |
| Backend | | | | |
| Frontend | | | | |
| Code Reviewer | | | | |

Ý kiến thiểu số bị bác (ghi đủ, không bỏ):

## 7b. WHY đã thống nhất (chép từ `board.py whys`)
| WHY | Ai hỏi → ai | Câu hỏi | Kết luận cuối | Trạng thái (agreed / ruled / assumption) | Không đồng ý (nếu ruled/assumption) |
|---|---|---|---|---|---|

## 8. Phán quyết của Lead
| Issue | 2 bên | Quyết định | Lý do |
|---|---|---|---|

## 9. Thay đổi code & migration
- File đã đổi (mỗi repo):
- Migration: (verify migrate → rollback → migrate: OK/FAIL)
- ENV / lệnh mới (đã ghi release-notes.md):

## 10. Kết quả test (Test Execution, chỉ kết quả đã chạy thật)
| AC | Test | PASS / FAIL / BLOCKED / NOT RUN |
|---|---|---|

## 11. Kết quả review
| Loại | Critical | High | Medium | Low | Kết luận |
|---|---|---|---|---|---|
| Code | | | | | |
| Security | | | | | |

Issue còn để lại + lý do:

## 12. KB đã cập nhật
- File trong `docs/`:

## 13. Khi merge vào nhánh gốc cần làm
- [ ] Chạy migration
- [ ] Thêm ENV mới
- [ ] Xem lại các Assumption ở mục 2

## 14. Gap phát hiện khi làm (S3-S4)
> Dev/test-executor báo thiếu thông tin → debate nhỏ (tối đa 2 lượt) → Lead chốt. Mỗi gap phải có nguyên nhân gốc và bài học.

| ID | Thiếu gì | Báo bởi | Loại | Người debate | Quyết định | Vì sao S1-S2 bỏ sót (AC thiếu case / KB sai-thiếu / CONTEXT thiếu / Phương án chưa tính / Yêu cầu mơ hồ) | Bài học | Trạng thái |
|---|---|---|---|---|---|---|---|---|
