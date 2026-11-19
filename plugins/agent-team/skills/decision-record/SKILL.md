---
name: decision-record
description: Ghi quyết định kỹ thuật/nghiệp vụ dạng ADR ngắn vào docs/decisions/ - bối cảnh, các phương án, quyết định, hệ quả, nguồn task. Dùng khi Lead chốt phương án, architect đổi quy chuẩn hoặc kiến trúc, hoặc khi phán quyết bế tắc.
---

# Ghi quyết định (ADR ngắn)

## Khi nào ghi
- Chốt phương án có ảnh hưởng lâu dài: schema, API contract dùng chung, pattern mới, thư viện mới, đổi quy chuẩn `docs/engineering/`.
- Lead phán quyết bế tắc giữa các role.
- Chấp nhận rủi ro (vd bỏ qua Medium security có lý do).
Không ghi cho chi tiết chỉ nằm trong một task (đã có TASK.md).

## File
`docs/decisions/<YYYYMMDD>-<slug>.md`, thêm 1 dòng vào `docs/decisions/README.md` (ngày | tiêu đề | trạng thái | task).

```
# <Tiêu đề quyết định>
- Trạng thái: Proposed | Accepted | Superseded by <file> | Deprecated
- Ngày: <YYYY-MM-DD> · Task: <task-id> · Người quyết: Lead (sau debate) | Architect
- verified-at: <commit>

## Bối cảnh
<2-4 dòng: vấn đề, ràng buộc, dữ liệu liên quan>

## Các phương án
| Mã | Tóm tắt | Ưu | Nhược | Điểm (từ bảng điểm task) |

## Quyết định
<Chọn gì / gộp ý nào từ đâu. 1-3 dòng>

## Hệ quả
- Phải làm theo: <quy tắc kiểm chứng được, vd "mọi list endpoint dùng Pagy">
- Đánh đổi chấp nhận: ...
- Assumption còn mở: ...
```

## Quy tắc
- Ngắn (≤ 40 dòng). Dẫn board (`DEBATE.md`) thay vì chép lại cuộc debate.
- Quyết định mới thay quyết định cũ: không sửa file cũ ngoài dòng Trạng thái → `Superseded by ...`.
- Quyết định đổi quy chuẩn phải cập nhật `docs/engineering/` cùng lúc.
