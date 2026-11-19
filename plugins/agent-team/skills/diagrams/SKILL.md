---
name: diagrams
description: Viết sơ đồ Mermaid cho task - workflow nghiệp vụ (flowchart), sơ đồ trạng thái (stateDiagram), sơ đồ kỹ thuật (sequenceDiagram) - đúng cú pháp, dễ đọc cho client và dev. Dùng khi BA viết design/workflow.md, design/state.md hoặc Architect viết design/sequence.md.
---

# Sơ đồ Mermaid của task

| File | Ai viết | Dùng để | Loại Mermaid |
|---|---|---|---|
| `design/workflow.md` | BA | Người dùng làm gì, hệ thống phản hồi, rẽ nhánh lỗi / không có quyền | `flowchart TD` |
| `design/state.md` | BA (chỉ khi task đổi trạng thái dữ liệu) | Trạng thái và chuyển trạng thái được / bị cấm | `stateDiagram-v2` |
| `design/sequence.md` | Architect | Thành phần gọi nhau theo thứ tự: FE, API, service, DB, job, bên thứ ba | `sequenceDiagram` |

Mỗi file: tiêu đề `#`, 1-3 dòng giải thích, một khối ` ```mermaid `, sau đó ghi chú ngắn (AC liên quan, điểm cần chú ý). `board.py report` vẽ sẵn thành hình trong REPORT.html.

## Quy tắc chung
- Chữ trong sơ đồ là **tiếng Việt, ngắn**, đặt trong dấu ngoặc kép khi có dấu câu: `A["Bấm Huỷ"]`.
- Mỗi nhánh lỗi / không có quyền là một nút riêng, ghi rõ hệ thống trả gì (mã lỗi / thông báo).
- Gắn AC vào nút hoặc cạnh liên quan: `-->|AC-2| E`.
- Tối đa ~20 nút mỗi sơ đồ; dài hơn thì tách theo bước.
- Không đưa secret, dữ liệu thật của khách.

## Mẫu
```mermaid
flowchart TD
  A["Khách mở chi tiết đơn"] --> B["Chọn sản phẩm muốn huỷ"]
  B --> C{"Là chủ đơn?"}
  C -- Không --> X["404 Không tìm thấy đơn"]
  C -- Có --> D{"Đơn đang giao?"}
  D -- Có --> Y["422 Đơn đang giao, không huỷ được"]
  D -- Không --> E["Ghi lần huỷ"] -->|AC-1| F["Hoàn tiền bằng job"] --> G["Báo: Đã huỷ, hoàn X đ"]
```
```mermaid
stateDiagram-v2
  [*] --> DaThanhToan
  DaThanhToan --> HuyMotPhan: huỷ một phần
  HuyMotPhan --> HuyMotPhan: huỷ tiếp
  DaThanhToan --> DangGiao: giao hàng
  HuyMotPhan --> DangGiao: giao hàng
  DangGiao --> [*]
  note right of DangGiao: Không được huỷ (AC-2)
```
```mermaid
sequenceDiagram
  participant FE
  participant API
  participant SV as CancellationService
  participant DB
  participant JOB as RefundJob
  FE->>API: POST /orders/:id/cancellations
  API->>SV: kiểm chủ đơn + trạng thái
  SV->>DB: khoá dòng đơn, ghi order_cancellations
  SV-->>JOB: enqueue hoàn tiền
  API-->>FE: 201 {refund_amount}
  JOB->>JOB: gọi cổng thanh toán (thử lại khi lỗi)
```
