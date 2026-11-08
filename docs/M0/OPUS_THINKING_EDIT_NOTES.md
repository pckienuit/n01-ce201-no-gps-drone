# OPUS Thinking Edit Notes — N01_M0_DAC_TA

Bản sửa: `N01_M0_DAC_TA_OPUS.tex`
Nguồn gốc: `N01_M0_DAC_TA.tex` (không sửa)
Model: ag/claude-opus-4-6-thinking
Ngày: 29/09/2026

## Nguyên tắc biên tập

- Giọng văn: tiếng Việt tự nhiên, học thuật vừa phải, giống sinh viên kỹ thuật UIT viết báo cáo đồ án. Không sáo rỗng, không lặp từ.
- Giữ nguyên: cấu trúc section/subsection, tên/MSSV, 13 tuần, KPI, phương trình, citations/bibliography, phân công, điều kiện an toàn, trạng thái chưa kiểm chứng, bảng kế hoạch, phân biệt hold error/estimator error.
- Không thêm: claim, nguồn, kết quả mới.
- Không xóa: bảng kế hoạch, bảng rủi ro, bảng thiết bị, bảng I/O, bảng khảo sát.

## Danh sách thay đổi cụ thể

### Tóm tắt (section Tóm tắt)
1. "khảo sát và đề xuất giải pháp giữ vị trí" → "khảo sát và đề xuất cách giữ vị trí" — bỏ từ "giải pháp" thừa (pattern #7: overused AI vocabulary áp dụng cho văn phong sáo).
2. "drone bốn cánh quạt" → "drone bốn cánh" — gọn hơn, tự nhiên.
3. "giảng viên hướng dẫn (GVHD)" → "GVHD" — viết tắt đã giới thiệu ở trang bìa.
4. "Đồ án 1 tập trung vào khảo sát" → "Trong CE201, nhóm tập trung khảo sát" — bỏ cụm "tập trung vào" (filler, pattern #23), dùng mã môn.
5. "Nhóm không đặt mục tiêu viết lại toàn bộ bộ ước lượng EKF2" → ghép vào câu trước bằng ", không viết lại toàn bộ bộ ước lượng EKF2" — giảm hai câu thành một.
6. "Phạm vi bộ giám sát là đề xuất kỹ thuật để GVHD xem xét, chưa phải nội dung đã được phê duyệt riêng" → "Bộ giám sát là đề xuất kỹ thuật để GVHD xem xét, chưa được phê duyệt riêng" — bỏ "Phạm vi...là" (copula avoidance ngược, pattern #8 ngược), bỏ "nội dung" thừa.
7. "nhưng chưa có kết quả chạy SITL, kiểm tra cảm biến trên bàn hoặc bay thật" → "nhưng chưa chạy SITL, chưa kiểm tra cảm biến trên bàn và chưa bay thật" — liệt kê rõ ràng hơn, mỗi mệnh đề có chủ ngữ.

### Section 1: Thông tin và căn cứ đặc tả
8. "Giữ nguyên tên đề tài:" → "Tên đề tài giữ nguyên:" — đặt chủ ngữ rõ.
9. "Hướng thực hiện là giữ vị trí và bay waypoint..." → "Hướng thực hiện: giữ vị trí..." — dùng dấu hai chấm thay "là" dài dòng.
10. "phần mềm điều khiển bay" → "firmware điều khiển bay" — chính xác hơn (PX4 firmware, không phải phần mềm chung chung).
11. "kết nối với mô hình vật lý của drone" → "nối với mô hình vật lý drone" — gọn.
12. "nhất là yêu cầu M0, các mốc M1–M5 và mô tả N01" → "nhất là yêu cầu M0 và các mốc M1–M5" — bỏ "mô tả N01" lặp (đã nói ở đoạn trước).
13. "Kế hoạch áp dụng ... ; thay thế kế hoạch nội bộ 15 tuần trước đây" → "..., thay kế hoạch nội bộ 15 tuần trước đây" — dấu phẩy thay chấm phẩy, bỏ "thế" thừa.
14. "Lịch bảo vệ thực hiện theo thông báo riêng của Khoa/GVHD, không đồng nhất với hạn M5" → "Lịch bảo vệ do Khoa/GVHD thông báo riêng, không nhất thiết trùng hạn M5" — tự nhiên hơn.
15. "Nhóm ưu tiên đồng bộ với cấu hình này nhưng chưa coi đó là một môi trường đã được kiểm chứng trên máy N01" → "Nhóm ưu tiên đồng bộ với cấu hình này nhưng chưa kiểm chứng trên máy N01" — gọn, bỏ "coi đó là một môi trường đã được".
16. "cần ghi nhận khác biệt và xác nhận cấu hình thay thế trong kế hoạch, không mặc định mọi tổ hợp phiên bản đều tương thích" → "cần ghi nhận khác biệt và xác nhận trước, không mặc định mọi tổ hợp phiên bản đều tương thích" — bỏ "cấu hình thay thế trong kế hoạch" dài dòng.

### Section 2: Bài toán, mục tiêu và phạm vi
17. "cung cấp thông tin tỷ lệ" → "cung cấp tỷ lệ" — bỏ "thông tin" thừa.
18. "chuyển động có đơn vị mét" → "đơn vị mét" — gọn.
19. "hỗ trợ dự đoán trạng thái và bù ảnh hưởng chuyển động quay" → "hỗ trợ dự đoán trạng thái và bù ảnh hưởng quay" — bỏ "chuyển động" lặp.
20. "Vị trí ngang thu được vẫn có thể trôi theo thời gian" → "Tuy nhiên, vị trí ngang vẫn có thể trôi theo thời gian" — thêm "Tuy nhiên" để nối ý rõ hơn, bỏ "thu được".
21. "ánh sáng phù hợp" → "đủ ánh sáng" — cụ thể hơn.
22. "Hướng thân/yaw" → "Hướng thân (yaw)" — giải thích thuật ngữ lần đầu dùng.
23. "Nhóm phải kiểm tra" → "Nhóm cần kiểm tra" — "phải" quá cứng cho đề xuất.
24. "trước từng đợt đo" → "trước mỗi đợt đo" — tự nhiên hơn.
25. "Làm chủ luồng" → "Nắm rõ luồng" — bỏ sáo rỗng "làm chủ".
26. "Hiện thực, đánh giá" → "Hiện thực và đánh giá" — thêm "và".
27. "Bài hình vuông thật được chuẩn bị sau khi" → "Bài hình vuông thật chỉ thực hiện sau khi" — rõ ý hơn.
28. "Tương tự, phương án hình vuông trên SITL kết hợp hover thật chỉ có hiệu lực khi GVHD đồng ý" → "Phương án hình vuông trên SITL kết hợp hover thật chỉ có hiệu lực khi GVHD đồng ý" — bỏ "Tương tự," lặp pattern mở đầu.

### Section 3: Đầu vào, đầu ra và kiến trúc hệ thống
29. "không đặt một tần số chung cho mọi loại cảm biến" → "không đặt chung một tần số cho mọi loại cảm biến" — đảo vị trí "chung" tự nhiên hơn.
30. "PX4 là lựa chọn ưu tiên để thống nhất với N02" → "PX4 được chọn để thống nhất với N02" — bỏ copula avoidance "là lựa chọn ưu tiên" (pattern #8).
31. "cả revision kho mô hình" → "revision kho mô hình" — bỏ "cả" không cần.
32. "đường cảm biến qua Gazebo Transport và gz_bridge vào uORB nội bộ PX4; không mặc định toàn bộ đường này đi qua MAVLink" → "cảm biến đi qua Gazebo Transport và gz_bridge vào uORB nội bộ PX4, không mặc định đi qua MAVLink" — gọn, bỏ "đường...toàn bộ đường này".
33. "không dùng telemetry.position như tọa độ ngang cục bộ vì API đó biểu diễn vị trí toàn cầu" → "không dùng telemetry.position vì API đó biểu diễn vị trí toàn cầu" — bỏ "như tọa độ ngang cục bộ" lặp ý.
34. "Lệnh Offboard và các điều kiện hợp lệ" → "Lệnh Offboard và điều kiện hợp lệ" — bỏ "các" thừa.
35. "Tên topic GT xác định từ môi trường đang chạy, không giả định sẵn đường dẫn" → "Tên topic GT xác định từ môi trường đang chạy, không giả định sẵn" — bỏ "đường dẫn" (topic không nhất thiết là đường dẫn).
36. "Bản dùng thử tối thiểu, người xử lý lỗi và ngày bàn giao do hai nhóm cùng thống nhất" → "...do hai nhóm thống nhất" — bỏ "cùng" thừa.
37. "không phải điều kiện bắt buộc của module đầu tiên" → "không bắt buộc cho module đầu tiên" — gọn.
38. "Việc mô phỏng sàn thiếu hoa văn chỉ có ý nghĩa nếu" → "Mô phỏng sàn thiếu hoa văn chỉ có ý nghĩa nếu" — bỏ "Việc" (filler pattern #23).

### Section 4: Giải pháp đề xuất và kế hoạch khảo sát
39. "Không tuyên bố cấu hình tham số là một EKF mới" → "Cấu hình tham số không được coi là một EKF mới" — chuyển sang dạng khẳng định, đỡ giọng phòng thủ.
40. "Đề xuất module giám sát gồm ba trạng thái:" → "Module giám sát đề xuất gồm ba trạng thái:" — đảo trật tự tự nhiên hơn.
41. "Dùng khoảng trễ chuyển trạng thái" → "Nhóm dùng khoảng trễ chuyển trạng thái" — thêm chủ ngữ.
42. "Đối chứng là cùng phiên bản PX4..." → "Để đánh giá bộ giám sát, nhóm so với cùng phiên bản PX4..." — thêm ngữ cảnh, bỏ câu mở kiểu "Đối chứng là..." (copula avoidance ngược).
43. "Nhóm so sai số bám, tỷ lệ hoàn thành..." → "Các chỉ số so sánh gồm sai số bám, tỷ lệ hoàn thành..." — rõ ý hơn.
44. "Nếu không có lợi ích, nhóm báo cáo kết quả âm" → "Nếu module không mang lại lợi ích, nhóm báo cáo kết quả âm" — thêm chủ ngữ "module".
45. "nên không được chuyển số liệu" → "không được chuyển số liệu" — bỏ "nên" (đã có dấu phẩy nối).
46. "ARK Flow là ví dụ sản phẩm thương mại tích hợp" → "ARK Flow là ví dụ sản phẩm tích hợp" — bỏ "thương mại" lặp (bảng đã ghi "sản phẩm thương mại").

### Section 5: Tiêu chí đạt và phương pháp đo
47. "Để phép thử có thể lặp lại" → "Để phép thử lặp lại được" — giọng tự nhiên hơn.
48. "Sai số $e_{hold}$ đánh giá giữ vị trí của toàn hệ thống; $e_{est}$ đánh giá bộ ước lượng" → "$e_{hold}$ đánh giá khả năng giữ vị trí của toàn hệ thống; $e_{est}$ đánh giá riêng bộ ước lượng" — bỏ "Sai số" thừa (đã nói ở trên), thêm "riêng" phân biệt rõ.
49. "đi qua bốn đỉnh phân biệt và khép đường về điểm đầu" → "đi qua bốn đỉnh và khép về điểm đầu" — bỏ "phân biệt" và "đường" thừa.
50. "Thử lỗi mất flow, range không hợp lệ, dữ liệu trễ và mất liên lạc chỉ thực hiện trong SITL/replay" → "Thử lỗi...chỉ trong SITL/replay" — gọn.

### Section 6: Thiết bị, phần mềm và an toàn
51. "Tình trạng sở hữu/cho mượn chưa được xác nhận" → "Tình trạng sở hữu/cho mượn chưa xác nhận" — bỏ "được".
52. "Dây giữ hoặc bảo vệ cánh phải được bố trí phù hợp để không vướng cánh" → "Dây giữ hoặc bảo vệ cánh phải bố trí sao cho không vướng cánh" — gọn, giọng kỹ thuật.

### Section 7: Kế hoạch 13 tuần và phân công
53. "Các đầu ra đều là dự kiến, chưa đánh dấu hoàn thành" → "Các đầu ra đều là dự kiến, chưa hoàn thành" — bỏ "đánh dấu".
54. "Các hạn nộp đều là 23:59:" → "Hạn nộp đều là 23:59:" — bỏ "Các" thừa.
55. "sau đó đối chiếu cấu hình khi tích hợp" → "rồi đối chiếu cấu hình khi tích hợp" — tự nhiên hơn.

### Không thay đổi (giữ nguyên có chủ đích)
- Toàn bộ phương trình (1)–(2) giữ nguyên ký hiệu và ý nghĩa.
- Bảng kế hoạch 13 tuần: nội dung giữ nguyên.
- Bảng rủi ro: nội dung giữ nguyên.
- Bảng I/O: nội dung giữ nguyên.
- Bảng khảo sát: nội dung giữ nguyên.
- Bảng thiết bị: nội dung giữ nguyên.
- TikZ diagram: giữ nguyên.
- Bibliography: giữ nguyên toàn bộ (kể cả lỗi chính tả "Stabilzation" trong title nguồn — đó là title gốc).
- Titlepage: giữ nguyên tên, MSSV, ngày tháng.
- Tất cả các câu về trạng thái chưa kiểm chứng (chưa SITL, chưa bay thật, chưa nhận thiết bị, etc.): giữ nguyên.
- Phân biệt hold error / estimator error: giữ nguyên.
- Phân biệt yêu cầu thầy vs đề xuất nhóm: giữ nguyên.
- Điều kiện an toàn: giữ nguyên toàn bộ nội dung, chỉ sửa văn phong.

## Tóm tắt dạng sửa đổi

| Loại sửa | Số lượng |
|---|---|
| Bỏ từ thừa / filler | ~20 |
| Gọn câu / ghép câu | ~10 |
| Sửa giọng tự nhiên hơn | ~15 |
| Thêm chủ ngữ / nối ý rõ | ~5 |
| Sửa copula avoidance | ~3 |
| Sửa nội dung / claim | 0 |
| Thêm nguồn / kết quả | 0 |
| Xóa bảng / section | 0 |
