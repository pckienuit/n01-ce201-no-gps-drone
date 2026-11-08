# N01 SITL: PX4 v1.16.0 + Gazebo Harmonic

Trạng thái 02/11/2026: **image/build PX4 và smoke disarmed PASS**; MAVSDK kết nối, local valid, flow/range fusion active, GPS/vision fusion tắt. Chưa hover/square/fault test hoặc KPI. Không dùng tài liệu này như biên bản G1 pass. Thiết lập theo phương án một mình Kiên làm, không phụ thuộc N02; không đổi thành viên nhóm chính thức.

## Phạm vi

- PX4 commit `6ea3539157ca358c70a515878b77077af7d4611d`, model `gz_x500_flow` từ submodule Gazebo khóa theo release.
- Ubuntu 24.04 bên trong Docker; toolchain/Python của host giữ nguyên. Runtime đã kiểm: Python 3.12.3, Gazebo sim 8.15.0 (Harmonic), CMake 3.28.3, MAVSDK-Python khóa 3.17.4. Gazebo khác bản 8.11.0 N02 từng báo.
- Source/build/log PX4 ở `${HOME}/.local/share/n01-sitl/PX4-Autopilot`; đổi bằng `N01_PX4_SOURCE` nếu cần. Không nằm trong workspace tài liệu riêng tư.
- Container chạy non-root, không privileged, không mount serial/USB hoặc Docker socket, không host network. Runtime dùng mạng Docker internal `n01-sim`, MAVSDK ở cùng container.
- Chạy headless bằng Xvfb/Mesa software vì camera flow/range GPU lidar vẫn cần render dù không mở GUI. Chưa kiểm hiệu năng hoặc hình GUI.
- Chưa cài ArduPilot/ROS 2 và không khẳng định PX4 chạy được trên F405 thầy cấp.

## Lệnh từ root workspace

Sau khi image/source hoàn tất:

```bash
bash sim/sitl.sh image
bash sim/sitl.sh build
bash sim/sitl.sh start     # Chạy nền headless (nhẹ máy, phù hợp tự động hóa)
bash sim/sitl.sh gui       # Mở cửa sổ đồ họa 3D Gazebo trực tiếp trên Desktop
bash sim/sitl.sh hover     # Chạy nhiệm vụ bay giữ vị trí 30s
bash sim/sitl.sh square    # Chạy nhiệm vụ bay hình vuông 2x2m
bash sim/sitl.sh fault     # Chạy thử nghiệm tiêm lỗi Failsafe
bash sim/sitl.sh logs
bash sim/sitl.sh stop
```

`image` tải/cài dependency bên trong Docker; lần đầu cần mạng. `build` giới hạn 6 CPU/7 GiB RAM. `start` không arm và không gửi mission; cần đợi startup/estimator ổn định rồi chạy smoke. `smoke` đọc MAVSDK qua UDP 14540 và PX4 listener nội bộ, kiểm model 4021, disarmed, local valid, GPS/external vision fusion tắt, flow/range fusion active. Nó không chứng minh hover đạt KPI. Chỉ chạy một MAVSDK server dùng cổng 14540 tại một thời điểm.

Console detach bằng Ctrl+] để không dừng SITL. Không dùng Ctrl+C nếu chỉ muốn rời console. `stop` xóa container nhưng giữ source/build/log và mạng internal để tái dùng; không xóa evidence.

## Các tham số runtime được đặt rõ

- `EKF2_GPS_CTRL=0`, `EKF2_EV_CTRL=0`: không fuse GPS/external vision.
- `EKF2_OF_CTRL=1`: yêu cầu bật optical flow. Stock airframe 4021 chỉ tắt GPS, không đủ làm chứng cứ OF active.
- Range settings giữ default release ở bước setup; phải đọc giá trị và kiểm range aiding thực tế trước baseline bay.

Không hạ prearm checks, không giả `global_position_ok`, không dùng GT làm feedback. Cần kiểm riêng `sensor_optical_flow`, `distance_sensor`, `vehicle_local_position`, trạng thái aid source/fusion và timestamp. Drone trên mặt đất có thể chưa có range/flow đủ điều kiện; phải ghi đúng, không nhận absence hoặc quality thấp là pass.

## Evidence

- `evidence/docker-build.log`: build image ban đầu; `docker-mavsdk3-build.log` là layer pin MAVSDK cuối.
- `evidence/submodules.log`: tải các submodule cần cho SITL.
- `evidence/source-lock.json`: SHA nguồn/model đã kiểm; `runtime_verified=false` ở snapshot ban đầu.
- `evidence/px4-build.log`: build PX4 exit 0, gồm OpticalFlowSystem.
- `evidence/smoke-final.log`: kiểm MAVSDK + listener disarmed PASS; `sensors-disarmed.log` có mẫu flow quality 255, range khoảng 0,177 m, `cs_opt_flow=True`, `cs_rng_hgt=True` và OF `fused=True` tại lúc đo.
- `evidence/gazebo-gt-sample.txt`: mẫu dynamic pose GT độc lập; chưa đồng bộ frame/time hoặc tính KPI.
- `evidence/smoke-restart.log`: stop/start rồi kiểm lại đạt, không chỉ một lần boot.
- `evidence/environment-lock.json`: image ID cuối và hash evidence; `python-lock.txt`, `dpkg-lock.txt`, hai `setup-*.ulg`, `setup-params.bson` giữ cấu hình/log setup. Container đã dừng sau kiểm; khởi động lại bằng lệnh start ở trên.

## Lỗi setup đã xử lý và giới hạn

- MAVSDK 4.1.0 import được nhưng `System()` bị đổi API; pin 3.17.4 để giữ API gRPC đã dùng trong thiết kế. Package có cảnh báo đổi tên sang mavsdk-grpc; không nâng v4 tự động. Dockerfile giữ layer cài ban đầu để tận dụng cache rồi ghi đè pin ở layer cuối; môi trường runtime thực là 3.17.4.
- `xvfb-run` làm PID 1 đã chờ tín hiệu readiness không tiến; `docker run --init` giải quyết, đã quan sát PX4/Gazebo khởi động.
- Boot có cảnh báo thiếu ground control station; snapshot health `is_armable=false`, heading_good_for_control=false khi disarmed. Không hạ kiểm tra an toàn để ép arm. Baro/ekf missing data lúc đầu là cảnh báo startup, không chứng minh đã hết mọi lỗi prearm.
- Default world có sàn màu đồng nhất. Flow quality cao ở trạng thái đứng yên không chứng minh bám ảnh đúng khi chuyển động; cần sàn có vân và kiểm bằng GT trước mission/KPI.

Bước tiếp theo: sàn có vân và kiểm heading/GCS/prearm trước mission; sau đó thu GT đồng bộ và đo hover/square. G1 đầy đủ còn yêu cầu nominal và lỗi có log + GT. Không có kết quả bench/bay thật.
