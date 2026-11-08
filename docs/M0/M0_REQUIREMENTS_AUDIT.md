# Đối chiếu M0 N01 với yêu cầu GVHD

Ngày kiểm: 04/10/2026. Đối tượng: `N01_M0_DAC_TA_OPUS.pdf` hiện hành, 18 trang. Không sửa bản đặc tả hoặc nộp Form trong lần kiểm này.

## Nguồn và kết luận

- Nguồn yêu cầu: `../../MoTa_DeTai_DoAn_HK1_2026-2027.pdf`, tr. 1–3 và **tr. 12, Mục 6**; email 25/09/2026 trong `../../emails/gvhd/thong-bao-do-an-hk1-2026-2027__1a0ae91694772515/thread.md:144–160`.
- **Đã có các phần nội dung chính nhưng chưa đáp ứng đầy đủ để coi là bản nộp hoàn chỉnh.** Mục 6 tài liệu gốc ghi “Bản đặc tả (3–5 trang)”; bản hiện hành 18 trang, riêng phần nội dung trước tài liệu tham khảo dài 14 trang. QA kỹ thuật không kiểm yêu cầu độ dài này.
- Trang dưới đây là số trang in trong bản đặc tả, không phải chỉ số trang của trình đọc PDF.

| Yêu cầu | Bằng chứng trong đặc tả | Kết quả |
|---|---|---|
| Nhóm, tên, hướng đề tài | Bìa, mục 1.1, tr. 1 | Có |
| Bài toán, mục tiêu, phạm vi làm/không làm | Mục 2, tr. 2–3 | Có; nên nêu rõ đối tượng sử dụng N01/N02 và nền tảng kế thừa CE206 |
| Input/output cụ thể, định dạng, tần số, đơn vị | Bảng 1, tr. 3–4 | Một phần: chưa có định dạng/interface và tần số cụ thể từng luồng; một số đơn vị chỉ ghi sẽ đối chiếu |
| Sơ đồ phần cứng/phần mềm | Hình 1, tr. 5; mô tả thay mô phỏng bằng sensor/motor thật | Có; ảnh render rõ, không thấy mũi tên đè chữ; bản rút gọn nên ghi trực tiếp IMU/OF/range, FC và motor |
| KPI và cách đo | Mục 5, tr. 8–9 | Có; giữ nguyên KPI, phân biệt lỗi hold/estimator và GT độc lập; diễn giải bán kính/max và protocol waypoint còn chờ xác nhận |
| Thiết bị/phần mềm đã có/cần mượn/cần mua | Mục 1.2, 3.3, Bảng 3, tr. 10–11 | Một phần: có danh mục mượn và số lượng, chưa tách rõ ba trạng thái cho từng hạng mục |
| Kế hoạch 13 tuần khớp M1–M5 | Bảng 4, tr. 12–13; mục 7.2 | Có: đủ tuần, ngày và đầu ra |
| Phân công hai thành viên | Mục 7.1, Bảng 4 | Có nhưng dự kiến; cần Kiên/Khanh xác nhận |
| Rủi ro/dự phòng | Mục 8, tr. 13–14 | Có |
| Nguồn khảo sát ĐA1, tuần 2–3 | Mục 4.2, tr. 7–8; W02/W03 | Có: nguồn quốc tế, trong nước, tài liệu kỹ thuật và sản phẩm; bảng so sánh hoàn chỉnh thuộc M1 |
| Độ dài 3–5 trang | Yêu cầu tại tr. 12 PDF GVHD; `pdfinfo` bản đặc tả | Chưa đạt: 18 trang |

## Sửa trước khi nộp

1. Rút thành bản M0 3–5 trang; giữ bản dài làm tài liệu nội bộ. Chưa có bằng chứng GVHD cho phép phụ lục ngoài giới hạn, nên không mặc định thêm phụ lục vẫn hợp lệ.
2. Bổ sung bảng I/O với trường dữ liệu, định dạng/interface, hệ trục, đơn vị và rate dự kiến từng luồng. Rate/phiên bản chưa khóa phải đánh dấu dự kiến và nêu mốc xác minh W02/W03; không bịa kết quả đo.
3. Tách thiết bị/phần mềm đã có, cần mượn, cần mua/chưa quyết định; không nhận đã sở hữu nếu chưa xác nhận. Chốt phân công, bỏ nhãn bản dự thảo sau khi hai thành viên duyệt.
4. M4 đã có so module với baseline; bổ sung rõ đối chiếu với các giải pháp khảo sát, cùng giới hạn khác protocol/thiết bị. Sửa ghi chú phản hồi trước 30/09 để không hướng dẫn thực hiện một hạn đã qua; yêu cầu điều chỉnh muộn phải báo thầy, không nhận là đã chấp thuận.

## Kiểm thật

- `python3 docs/M0/verify_m0.py`: exit 0; 18 trang, 13 tuần, 15 tài liệu; citation order PASS, tex warnings NONE, page bounds PASS. Đây là QA build/layout, không phải xác nhận đáp ứng toàn bộ yêu cầu GVHD.
- `pdfinfo` và `pdftotext -layout`: xác nhận độ dài và nội dung hai PDF.
- Render/xem tr. 12 PDF GVHD: xác nhận chữ “3–5 trang” và trường I/O, thiết bị. Render/xem trang PDF 7 bản đặc tả (trang in 5): sơ đồ rõ, không thấy lỗi chữ/mũi tên.
- Workspace chưa có Git repository. Không chạy SITL/bench/flight; chưa có xác nhận đã nộp hoặc GVHD duyệt.

## Sau rút gọn ngày 04/10/2026

- Bản mới `N01_M0_DAC_TA_RUT_GON.pdf`: **5 trang tính cả thông tin nhóm, kế hoạch và nguồn**, không phụ lục ngoài giới hạn; bản OPUS giữ nguyên để tham khảo nội bộ.
- Tr. 1: nhóm/tên/hướng, bài toán/mục tiêu/phạm vi; Bảng 1 ghi trường dữ liệu, interface/định dạng, đơn vị, rate dự kiến và mốc xác minh. Rate là lựa chọn thiết kế, không phải số đo/hằng số PX4.
- Tr. 2: sơ đồ sensor/FC/phần mềm/motor, đóng góp dự kiến, KPI gốc, phương pháp đo và GT; phân biệt điều cần GVHD xác nhận.
- Tr. 3: trạng thái đã có/chưa xác nhận/cần mượn/cần mua, phối hợp N02, gate, rủi ro/dự phòng. Không bịa thiết bị đã nhận hoặc ngày bàn giao.
- Tr. 4: đủ W01–W13, việc Kiên/Khanh và đầu ra/hạn M0–M5; Kiên chọn phân công đề xuất, sẽ chỉnh sau trao đổi Khanh.
- Tr. 5: kế hoạch khảo sát M1 và 10 nguồn (9 nguồn khảo sát + nguồn GVHD); có quốc tế, trong nước, sản phẩm. M4 có đối chiếu khảo sát và so baseline.
- Build XeLaTeX exit 0; `python3 docs/M0/verify_m0_short.py` PASS page limit, dates/weeks, citation order, required content, warnings/page bounds. `QA_SHORT_RESULT.json` lưu kết quả. Render xem 5 trang; sửa hình chen giữa câu, giữ KPI “trong 30 s”, xem lại trang 2–3: không cắt/tràn/chồng.
- Nội dung/bố cục đã xử lý các thiếu hụt của bản dài; thiết bị, version, rate, protocol KPI và hàm lượng module vẫn là dự kiến/cần xác nhận. Không coi QA là thầy duyệt, đã nộp hoặc SITL pass.

## Đánh giá bản rút gọn sau biên tập lại (04/10/2026)

Đối tượng: `N01_M0_DAC_TA_RUT_GON.tex/.pdf` hiện hành. Thay thế phần đánh giá "Sau rút gọn" ở trên về bố cục; số trang dưới đây là số trang in.

| Yêu cầu Mục 6 / email 25/09 | Vị trí trong bản rút gọn | Kết quả |
|---|---|---|
| Nhóm, tên đề tài, hướng cụ thể | Khối tiêu đề + Mục 1, tr. 1 | Có; tên chính thức, MSSV, GVHD |
| Bài toán, mục tiêu, cho ai | Mục 2, tr. 1 | Có; giải nghĩa optical flow, rangefinder, EKF, SITL, GT |
| Input/Output: định dạng, tần số, đơn vị | Mục 3, Bảng 1, tr. 1–2 | Có; tần số là thiết kế dự kiến, chưa đo; tách cảm biến/setpoint/telemetry; PX4 cần setpoint trên 2 Hz có trích dẫn |
| Phạm vi làm / không làm | Mục 4, tr. 2 | Có; không thêm ROS 2/SLAM/AI |
| Sơ đồ khối phần cứng + phần mềm | Mục 5, Hình 1, tr. 2 | Có; tách phần PX4 có sẵn và phần nhóm làm; GT không vào EKF2/bộ điều khiển |
| Tiêu chí đạt, số liệu M4, cách đo | Mục 6, Bảng 2, tr. 2–3 | Có; KPI gốc giữ nguyên; diễn giải max bán kính ghi "chưa được duyệt"; tách $e_{hold}$ và $e_{est}$ |
| Thiết bị: đã có, cần mượn, cần mua | Mục 7, Bảng 3, tr. 3 | Có; thêm "chưa xác nhận" cho PC/phiên bản; không nhận thiết bị đã được cấp |
| Kế hoạch 13 tuần, phân công, M1–M5 | Mục 8, Bảng 4, tr. 3–4 | Có; cột riêng Kiên/Khanh; tuần 2–3 khảo sát; phân công ghi là đề xuất, chờ trao đổi Khanh |
| Rủi ro, dự phòng | Mục 9, Bảng 5, tr. 4–5 | Có; 4 bước an toàn SITL → bàn tháo cánh → hover thấp có bảo hộ → hình vuông thật; SITL không thay bay thật |
| Nguồn dự kiến khảo sát ĐA1 | Mục 10, tr. 5 | Có; bài báo nước ngoài, nghiên cứu trong nước, sản phẩm thương mại, tài liệu PX4; 10 mục IEEE theo thứ tự trích dẫn |
| 3–5 trang | `pdfinfo`, validator | Đạt: 5 trang, không phụ lục |

Định dạng: Times New Roman 13pt cho văn bản, bảng, chú thích và tài liệu tham khảo; chỉ nhãn trong Hình 1 là 11–12pt. Văn bản `\onehalfspacing` (khoảng dòng 19,9pt); bảng và tài liệu giãn đơn 15pt. Lề 3,0/3,5/3,5/2,0 cm. Rút trang bằng biên tập nội dung, gộp thông tin nhóm vào khối tiêu đề, thụt đầu dòng thay khoảng cách đoạn; không giảm cỡ chữ hay lề.

Kiểm thật: `latexmk -xelatex` exit 0, log 0 warning; `python3 docs/M0/verify_m0_short.py` exit 0. Validator đổi token "Chưa nộp M0" thành các kiểm chặt hơn (câu hiện trạng "chưa chạy SITL", KPI gốc nguyên văn, nhãn chưa duyệt/cần xác nhận, cấm cụm nhận đã nộp/đã duyệt/pass, cấm cỡ chữ dưới 13pt ngoài hình); thử âm hai trường hợp đều bị bắt. Đã render xem cả 5 trang.

Còn cần xác nhận: cách hiểu "±0,5 m", tốc độ/ngưỡng waypoint, module giám sát có được tính là phần thuật toán, thiết bị/người lái/khu bay của Lab, phân công sau trao đổi Khanh, phiên bản và giao diện với N02. Tần số I/O chưa đo. QA PASS không có nghĩa GVHD đã duyệt, đã nộp hay đã chạy SITL.

### Cập nhật cùng ngày: giọng báo cáo gửi GVHD

Câu chữ được viết lại theo giọng báo cáo gửi GVHD; nội dung các mục không đổi. Bản PDF bỏ link Google Form, vì Form do GVHD tạo và link nộp đúng đã lưu ở `progress/SUBMISSION_CONFIG.md`. Phân công ghi là phương án đề xuất, hai thành viên chưa chốt. Validator giữ mức kiểm tương đương: cấm link Form cũ bị lỗi và bắt buộc câu phân công đề xuất. Kết quả: 5 trang, `verify_m0_short.py` exit 0, log không cảnh báo.
