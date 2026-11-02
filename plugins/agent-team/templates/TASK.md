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
- Security duyệt solution: TODO (APPROVED / N/A)
- Kết quả test: TODO (PASS / FAIL)
- Lint/format: TODO (PASS / N/A)
- Code review: TODO (APPROVED)
- Security review: TODO (APPROVED)
- Cập nhật KB: TODO (YES / KHÔNG CẦN)
- Bài học: TODO (YES = đã ghi vào LESSONS_PATH / KHÔNG CÓ)

## 0. Yêu cầu gốc (nguyên văn, Lead chép từ user, không sửa)
> Đây là phần duy nhất `challenger` được biết (Lead đưa trong prompt; challenger không đọc file này).

## 1. Yêu cầu & Acceptance Criteria (BA)
- AC-<n>: Given ... When ... Then ... (đánh số AC-1, AC-2, ...)

## 2. Giả định (Assumption) cần user xem lại
| Điểm chưa rõ | Cách hiểu đã chọn (best solution) | Lý do | Ai đề xuất |
|---|---|---|---|

## 3. Các phương án (A/B/C)
### A. <tên>
- Tổng thể + kỹ thuật:
- API contract:
- Ưu / Nhược / Rủi ro:

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
