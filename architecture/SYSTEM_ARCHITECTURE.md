# Kiến trúc N01: bay indoor không GPS, Simulation-First

> **CE201, nhóm Phan Chí Kiên – Hồ Nhật Khanh.** Tài liệu kiến trúc cũ về UAV nông nghiệp, ExG/YOLO/GPS đã **ngừng áp dụng** sau khi nhận đề tài N01. Cập nhật 02/11: PX4 v1.16.0/Gazebo Harmonic 8.15.0/MAVSDK 3.17.4 đã build/boot và smoke disarmed đạt, local valid, OF/range fusion active, GPS/vision tắt; chưa mission/hover/square/fault/KPI, bench hoặc bay thật. Setup tại [`../sim/README.md`](../sim/README.md); các phần mission bên dưới vẫn là thiết kế đề xuất. Nguồn nghiên cứu tại [`../docs/N01_RESEARCH_BRIEF.md`](../docs/N01_RESEARCH_BRIEF.md).

> **Cập nhật 24/10/2026, quyết định stack chưa chốt:** Bảng thiết bị GVHD gửi 23/10 (`DanhMuc_DayDu!A2:F3`) ghi cấp F405 sau lý thuyết + SITL, hướng ArduPilot/EKF3, OF/range sinh viên tự chuẩn bị sau M2. Mục tài liệu N01/N02 vẫn PX4/MAVSDK. Kiến trúc PX4 bên dưới giữ làm **phương án cũ chưa triển khai**, không phải xác nhận tương thích F405. Cần mã board/revision, firmware hỗ trợ sensor và lựa chọn chung với GVHD/N02 trước version lock; không dựng đồng thời hai autopilot. Nguồn: [`../progress/SUBMISSION_CONFIG.md`](../progress/SUBMISSION_CONFIG.md), Mục 4.

```text
RC pilot / kill / mode switch ───> PX4 Commander / failsafe
                                        │
IMU trên FC ───────────────────────> PX4 EKF2 ─> local position/velocity
Optical flow hướng xuống ─────────> │                    │
Rangefinder hướng xuống ───────────> │                    ▼
                                    │          Position controller → motors
GCS/companion: local-NED setpoint ─┴───────> Offboard mode
                                    │
                         ULog (estimate + status + inputs)
                                    │
Gazebo GT / camera overhead GT ─────┴───────> align + metrics offline
```

## Ranh giới trách nhiệm

- **Flight controller PX4:** IMU, driver flow/range, EKF2, stabilizer, position controller, prearm và failsafe. Không tự viết lại EKF trong CE201.
- **Mission runner:** gửi local-NED setpoint và proof-of-life Offboard, đặt giới hạn tốc độ/vùng bay; xử lý sensor invalid/loss link đã test. Pilot phải có đường giành lại điều khiển độc lập với companion.
- **Measurement pipeline:** tách `setpoint`, `p_est` (EKF), `p_GT` (độc lập); tính sai số thực của hold so với tâm lệnh và sai số estimator so với GT.
- **Môi trường N02:** nếu được chia sẻ world/model, yêu cầu có sàn texture, model `x500_flow` tương thích, GT/time cùng frame và version lock. Baseline N01 không phụ thuộc tiến độ bàn giao N02.

## Lựa chọn và điều kiện xác minh

PX4 EKF2 + Gazebo mới (GZ) là **ứng viên chính**, chưa phải cấu hình đã chạy. Spike thử `make px4_sitl gz_x500_flow` trên release/commit cố định; model tồn tại ở nhánh nguồn `main`, nhưng phải chứng minh sensor + estimator thực sự hoạt động. ArduPilot EKF3 là phương án dự phòng đã nghiên cứu, không chạy song song hai firmware. Xem bảng so sánh và điều kiện đổi stack trong research brief.

**Sensor thật:** Pixhawk-class/6C + H-Flow DroneCAN (ít dây) hoặc PMW3901 UART + VL53L1X I2C đúng SKU; TFmini-S UART chỉ khi có lý do từ bench. Không mua chỉ theo tên chip, không cấp LiPo trực tiếp lên FC/sensor. Khóa pinout/firmware/harness/nguồn trước PO.

## Hệ tọa độ và giao diện

- Local NED của PX4: X Bắc theo local frame, Y Đông, Z xuống. Square setpoint local `(0,0)`, `(2,0)`, `(2,2)`, `(0,2)` m; tọa độ có thể quay so với khu đo và cần đo biến đổi frame với ground truth. Không gửi WGS-84 GPS mission để chứng minh indoor.
- Dữ liệu flow là angular motion, không phải pixel hay mét; PX4 mô tả drone tiến cho integrated flow +Y, sang phải −X. Xác minh bằng bench trước khi arm.
- HAL ứng dụng chỉ bao giao tiếp telemetry/setpoint và cấu hình endpoint; **không** tuyên bố “zero-code-change” cho sensor drivers, firmware, nguồn và hiệu chuẩn khi đổi sang drone thật. Release + parameter snapshot + extrinsics là thành phần deployment bắt buộc.
- RC takeover, loss-of-Offboard action, estimator-invalid response và vùng lưới là gates bắt buộc. “RTL” không được chọn mặc định indoor vì vị trí local có thể trôi.

## Tiêu chí chuyển cấp

1. **G1 SITL:** GPS fusion tắt, flow/range fusion active, local position valid, giữ vị trí + square + fault/loss mode có ULog và Gazebo GT.
2. **G2 Bench không cánh:** đúng nguồn, flow sign/quality, range valid 1–1,5 m, sensor topic, RC/kill, motor mapping, parameter export.
3. **G3 Flight low hover:** prop guard + lưới an toàn + pilot/observer; chỉ tiến từng mức độ cao sau review ULog/GT.
4. **G4 Square thật:** chỉ nếu hover đạt và vùng bay có đủ biên cho footprint/overshoot/recovery; nếu không, square giới hạn SITL và ghi đúng sự thật.

Không có trong CE201 N01: ExG, YOLO, geotag GPS, SLAM/VIO, bay xuyên nhiều phòng. Các hướng này chỉ cân nhắc riêng sau khi nền tảng N01 có số liệu.
