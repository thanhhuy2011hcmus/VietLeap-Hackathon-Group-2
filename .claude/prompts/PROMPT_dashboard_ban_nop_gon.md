# PROMPT: Dựng bản dashboard gọn, trọng tâm "Quyết định cho doanh nghiệp"

> Cách dùng: mở Claude chat, đính kèm file `dashboard_stress_test_BDS_v3.html`, dán toàn bộ nội dung dưới đây.

---

Tôi gửi kèm file `dashboard_stress_test_BDS_v3.html`. Đây là dashboard stress test thanh khoản của 9 chủ đầu tư nhà ở niêm yết, gồm 10 phần.

Hãy tạo **một file HTML mới** (dạng artifact HTML, tự chứa, JS vanilla + SVG như file gốc) bằng cách **sắp xếp lại và rút gọn** file này cho bài thi **Data Decision**. Trọng tâm là **Phần 9 · Quyết định cho doanh nghiệp**.

## Nguyên tắc bắt buộc

1. **Giữ nguyên thiết kế:** màu (CSS variables), font (Source Serif 4 / Be Vietnam Pro / JetBrains Mono), style của kicker, H2, card, badge, tooltip, thanh menu sticky và nền tối của hero.
2. **Giữ nguyên nội dung gốc:** không viết lại tiêu đề, đoạn dẫn, khuyến nghị hay nhãn đang có; không đổi số.
3. **Giữ nguyên dữ liệu và mô hình:** `const D`, `model()`, `full()`, `classify`, phân nhóm A/B/C/D, các tham số `P`, các kịch bản cài sẵn và hàm `run()`.
   - Mọi con số mới (nếu có) phải tính từ các hàm này.
   - Không được bịa số.
4. **Giữ nguyên tên nhóm:** "A · Vững", "B · Theo dõi", "C · Cần hỗ trợ thanh khoản", "D · Stress cao". Không dùng "Nguy cấp", "Cứu được" hay "vỡ nợ".
5. Chỉ được làm các việc ở mục **"Cấu trúc mới"** dưới đây.

## Cấu trúc mới (theo thứ tự)

### 0. Hero — giữ nguyên
- Giữ nguyên toàn bộ hero (tiêu đề, đoạn dẫn động, lưới ô màu, chú giải).

### Thanh menu
- 6 mục: `1 · Chẩn đoán` · `2 · Mô phỏng` · `3 · Phân loại` · **`4 · Quyết định DN`** · `5 · Ngân hàng` · `6 · Kinh tế`.
- Mục "Quyết định DN" in đậm, có gạch chân màu `--red`.

### 1. CHẨN ĐOÁN — gộp Phần 1–5 cũ vào một phần
- **Kicker:** "PHẦN 1 · CHẨN ĐOÁN TỪ BÁO CÁO TÀI CHÍNH".
- **H2:** dùng nguyên tiêu đề Phần 1 cũ.
- **Hàng KPI** (4 ô, cùng style `.kpis/.kpi` của Phần 10 cũ), tất cả tính từ `D`:
  - số DN có hệ số phủ 2026Q3 < 1 (dạng "x/9");
  - tổng khoảng hụt 2026Q3 của các DN hụt (tỷ đồng);
  - hệ số tương quan Pearson D/E – hệ số phủ (lấy từ Phần 4 cũ);
  - mức giảm doanh thu trung vị 2023 (−44,5%, lấy từ `D.cal`).
- **Biểu đồ tổng hợp mới (mặc định hiển thị):** "dumbbell" ngang, mỗi dòng một DN.
  - Hai chấm: hệ số phủ 2025Q4 (chấm rỗng) và 2026Q3 (chấm đặc, màu theo thang rủi ro), nối bằng đường xám. Vạch đậm tại 1,0×.
  - Bên phải mỗi dòng có hai cột số nhỏ: **D/E** và **% tồn kho/TS ngắn hạn** của 2026Q3.
  - Sắp xếp theo hệ số phủ 2026Q3 tăng dần.
  - Tooltip hiện liquid, nợ ngắn hạn, gap.
  - Biểu đồ này thay thế được góc nhìn của Phần 1, 2, 3, 4 cũ trên một hình.
- **Các biểu đồ gốc đặt dưới dạng tab** (nút tab cùng style với `.presets button`). Giữ **nguyên** code vẽ, chú thích và đoạn dẫn của từng phần cũ:
  - Tab "Khoảng hụt" = Phần 1 cũ (thanh + bảng)
  - Tab "Xu hướng 4 quý" = Phần 2 cũ
  - Tab "Tiền bị khóa" = Phần 3 cũ
  - Tab "Đòn bẩy" = Phần 4 cũ (bong bóng + "Đọc biểu đồ")
  - Tab "Bài học 2022–23" = Phần 5 cũ (5a, 5b, 5c)
- **Lưu ý kỹ thuật:** SVG được vẽ theo `viewBox` nên vẽ được ngay cả khi tab đang ẩn. Vẫn phải kiểm tra rằng mọi tab hiển thị đúng khi bấm.

### 2. MÔ PHỎNG — giữ nguyên Phần 6 cũ
- Giữ thanh trượt, kịch bản, thanh hệ số phủ, bảng kết quả, biểu đồ độ nhạy. Chỉ đổi số trong kicker thành "PHẦN 2".
- **Bỏ** khối thẻ "Hành động ngay" cũ của Phần 6 (nếu còn), vì đã có ở Phần 4 mới.

### 3. PHÂN LOẠI — giữ nguyên Phần 7 cũ
- Giữ 4 thẻ tiêu chí, cây quyết định và bảng phân loại. Chỉ đổi số trong kicker.

### 4. QUYẾT ĐỊNH CHO DOANH NGHIỆP — Phần 9 cũ, phần TRỌNG TÂM
- Giữ nguyên kicker (đổi số thành "PHẦN 4"), H2, đoạn dẫn và **toàn bộ thẻ khuyến nghị `recs()`** (gồm lộ trình 0–3 / 3–6 / 6–12 tháng của nhóm D).
- **Làm nổi bật phần này:**
  - Nền section đổi sang `--card`.
  - Viền trên 4px màu `--red`.
  - Thêm nhãn mono nhỏ "TRỌNG TÂM · DATA DECISION" phía trên kicker.
- **Thêm "Bảng quyết định"** phía trên các thẻ (cập nhật khi đổi kịch bản; gọi trong `run()`). Mỗi DN một dòng, sắp theo nhóm D → C → B → A. Các cột:

| Cột | Nội dung |
|---|---|
| Mã | mã DN |
| Nhóm | badge |
| Quyết định chính | dòng in nghiêng đầu tiên của thẻ (`PLAY[g].dev`), rút gọn tối đa 12 từ |
| Con số then chốt | D/C: "hụt {−gap} tỷ · cần gia hạn {rNeed}%"; B/A: "dư {gap} tỷ · chịu sốc {sMax}%" |
| Hạn hành động | D: "0–3 tháng"; C: "3 tháng"; B: "6 tháng"; A: "theo dõi định kỳ" |

- Bấm vào một dòng của bảng thì cuộn tới thẻ của DN đó. Gán `id` cho thẻ theo mã, ví dụ `rec-PDR`.

### 5. NGÂN HÀNG — Phần 8 cũ, RÚT GỌN
- Giữ H2, đoạn dẫn và **bảng 4 chính sách gia hạn** (`t8`) cùng ghi chú của nó.
- Giữ biểu đồ "Ai gánh khoảng hụt?" (`c8`) nhưng đặt trong thẻ `<details>` đóng sẵn, tiêu đề "Xem chi tiết: ai gánh khoảng hụt".
- Bốn thẻ nhóm (`g8`): giữ nội dung nhưng thu gọn thành 4 cột ngang, mỗi thẻ chỉ hiện tên nhóm, danh sách DN, nợ ngắn hạn và **dòng khuyến nghị đầu tiên** cho ngân hàng. Hai dòng còn lại đặt trong `<details>` "thêm".

### 6. KINH TẾ — giữ nguyên Phần 10 cũ
- Giữ KPI, biểu đồ kênh cú sốc và 5 khuyến nghị chính sách. Chỉ đổi số trong kicker.

### Footer — giữ nguyên

## Kiểm tra trước khi trả file

1. Console không có lỗi. Kéo từng thanh trượt và bấm từng kịch bản: hero, bảng quyết định, thẻ Phần 4, bảng phân loại, bảng ngân hàng và Phần 6 đều cập nhật.
2. Mọi tab ở Phần 1 bấm được và hiển thị đủ biểu đồ; tooltip hoạt động.
3. Số ở kịch bản mặc định "Lặp lại 2022–23" phải trùng file gốc (hero, bảng Phần 2, bảng phân loại).
4. Không còn chữ "Nguy cấp", "Cứu được" hay "vỡ nợ".
5. Liên kết trên menu cuộn đúng tới từng phần.
6. Trả **toàn bộ file HTML** hoàn chỉnh. Nếu bị giới hạn độ dài, tạo artifact và tiếp tục khi tôi nhắn "tiếp tục". Không được lược code bằng "..." hay "giữ nguyên như cũ".
