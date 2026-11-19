# Trạng thái đơn hàng

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
