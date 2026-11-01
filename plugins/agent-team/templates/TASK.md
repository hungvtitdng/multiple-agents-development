# <task-id>: <tên task>

| | |
|---|---|
| Branch | `agent/<task-id>` |
| Loại task | NHỎ / VỪA / LỚN, lý do: |
| Thành viên | (role nào tham gia, role nào bỏ qua + lý do) |
| Chế độ | A. Agent Teams / B. Subagent |
| Trạng thái | ① / ② / ③ / ④ / ⑤ / DONE |

## 1. Yêu cầu & Acceptance Criteria (BA)
- AC-1: Given ... When ... Then ...

## 2. Điểm mơ hồ & cách hiểu được chọn
| Điểm mơ hồ | Cách hiểu X / Y / Z | Chọn | Vì sao |
|---|---|---|---|

## 3. Các phương án
### A. <tên>
- Tổng thể (SA):
- Kỹ thuật (TA):
- Ưu / Nhược:

### B. <tên>

## 4. Rủi ro & đánh giá bảo mật
| Phương án | Role | Rủi ro / lỗ hổng | Mức | Trả lời / xử lý |
|---|---|---|---|---|

## 5. Bảng chấm điểm (Lead tổng hợp từ điểm các role gửi riêng, mỗi role chấm độc lập)
| Tiêu chí | Trọng số | A | B | C |
|---|---|---|---|---|
| Đáp ứng AC | ×3 | | | |
| Ít ảnh hưởng code cũ | ×3 | | | |
| Bảo mật | ×3 | | | |
| Hiệu năng / mở rộng | ×2 | | | |
| Dễ maintain / test | ×1 | | | |
| Công sức | ×1 | | | |
| **Tổng** | | | | |

## 6. Phương án được chọn
- **Chọn:** ... , **vì sao:** ...
- **Loại:** ... , **vì sao:** ...
- Solution Reviewer: APPROVED / REJECTED

## 7. Tổng hợp ý kiến theo role (Lead ghi khi chốt, bắt buộc)
> Chi tiết từng vòng: `board/SUMMARY.md` và các bài post trong `board/`.

| Role | Ủng hộ | Ý kiến chính | Bài post | Chấp nhận / Bác | Lý do |
|---|---|---|---|---|---|
| BA | | | | | |
| Solution Architect | | | | | |
| Technical Architect | | | | | |
| Backend | | | | | |
| Frontend | | | | | |
| Tester | | | | | |
| Code Reviewer | | | | | |
| Solution Reviewer | | | | | |
| Test Reviewer | | | | | |
| Security | | | | | |

Ý kiến thiểu số bị bác (ghi đủ, không bỏ):

## 8. Phán quyết của Lead
| Issue | 2 bên | Quyết định | Lý do |
|---|---|---|---|

## 9. Thay đổi code & migration
- File đã đổi:
- Migration: (verify migrate → rollback → migrate: OK/FAIL)
- ENV / lệnh mới (đã ghi release-notes.md):

## 10. Kết quả test
| AC | Test | Kết quả |
|---|---|---|

## 11. Kết quả review
| Loại | Critical | High | Medium | Low | Kết luận |
|---|---|---|---|---|---|
| Code | | | | | |
| Solution | | | | | |
| Test | | | | | |
| Security | | | | | |

Issue còn để lại + lý do:

## 12. Khi merge vào develop cần làm
- [ ] Chạy migration
- [ ] Thêm ENV mới
