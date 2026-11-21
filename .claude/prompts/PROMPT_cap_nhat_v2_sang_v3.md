# PROMPT: Cập nhật dashboard v2 → v3 (đổi "Nguy cấp" thành "Stress cao" và viết lại lộ trình)
Dán prompt này vào Claude **kèm file `dashboard_stress_test_BDS_v2.html`**.

---
Tôi gửi kèm file dashboard HTML. Hãy sửa file theo **đúng và chỉ** các thay thế dưới đây, rồi trả lại **toàn bộ file HTML** đã sửa.

**Quy tắc:**
- Không đổi thiết kế, màu, bố cục, số liệu, công thức, biểu đồ hay logic phân nhóm.
- Không sửa bất kỳ chỗ nào khác ngoài danh sách.
- Mỗi đoạn "TÌM" xuất hiện đúng 1 lần trong file. Thay nguyên văn bằng đoạn "THAY BẰNG".
- Nếu một đoạn không tìm thấy, báo lại cho tôi; không tự đoán.

## Phần 1 — Thay thế chuỗi (14 mục)

### Mục 1
TÌM:
```
C · Cứu được</span><span><i style="background:var(--red)"></i>D · Nguy cấp
```
THAY BẰNG:
```
C · Cần hỗ trợ thanh khoản</span><span><i style="background:var(--red)"></i>D · Stress cao
```

### Mục 2
TÌM:
```
<b>C · Cứu được</b> nếu khoảng hụt lấp được bằng ③ và D/E ≤ 2; nếu không → <b>D · Nguy cấp</b>.
```
THAY BẰNG:
```
<b>C · Cần hỗ trợ thanh khoản</b> nếu khoảng hụt lấp được bằng ③ và D/E ≤ 2; nếu không → <b>D · Stress cao</b> (có rủi ro không trả đủ nợ đến hạn nếu kịch bản stress xảy ra — không đồng nghĩa mất khả năng thanh toán).
```

### Mục 3
TÌM:
```
không đẩy khách hàng còn cứu được vào vỡ nợ
```
THAY BẰNG:
```
không đẩy khách hàng đang chịu áp lực thanh khoản tạm thời vào tình trạng chậm trả nợ
```

### Mục 4
TÌM:
```
C:{n:'Cứu được',c:C.orange},D:{n:'Nguy cấp',c:C.red}
```
THAY BẰNG:
```
C:{n:'Cần hỗ trợ thanh khoản',c:C.orange},D:{n:'Stress cao',c:C.red}
```

### Mục 5
TÌM:
```
'Gia hạn đúng mức cần (tối đa 80%), có điều kiện: kế hoạch bán tồn kho và tăng vốn theo mốc thời gian.'
```
THAY BẰNG:
```
'Gia hạn đúng mức cần (tối đa 80%), có điều kiện: kế hoạch bán hàng và thu tiền theo mốc quý.'
```

### Mục 6
TÌM:
```
thu hồi dồn dập sẽ biến khoảng hụt có thể lấp thành vỡ nợ.'
```
THAY BẰNG:
```
thu hồi dồn dập sẽ biến khoảng hụt có thể lấp thành nợ quá hạn.'
```

### Mục 7
TÌM:
```
D:{bank:['Đưa vào danh sách theo dõi đặc biệt; định giá lại tài sản bảo đảm theo giá bán thanh lý.','Không cấp hạn mức mới; chỉ cơ cấu lại kỳ hạn khi cổ đông cam kết bơm vốn hoặc bán dự án.','Chuẩn bị phương án xử lý: hoán đổi nợ – tài sản, chuyển nhượng dự án cho nhà đầu tư nhóm A.'],dev:'Tái cấu trúc toàn diện: tăng vốn/hoán đổi nợ thành cổ phần, bán dự án hoặc cổ phần dự án, đàm phán với trái chủ (cần 65% đồng ý theo NĐ 200/2026).'}
```
THAY BẰNG:
```
D:{bank:['Giám sát tăng cường (báo cáo dòng tiền hàng tháng); định giá lại tài sản bảo đảm có chiết khấu.','Ưu tiên cơ cấu lại kỳ hạn có điều kiện — gắn với kế hoạch dòng tiền 13 tuần và mốc bán hàng — thay vì thu hồi trước hạn.','Chỉ giải ngân cho dự án đang mở bán/bàn giao qua tài khoản phong tỏa; không tăng dư nợ để trả nợ cũ.'],dev:'Ưu tiên giữ dòng tiền và kéo dài kỳ hạn nợ trước; tái cấu trúc vốn là phương án dự phòng ở mốc 6–12 tháng, không phải việc làm ngay.'}
```

### Mục 8
TÌM:
```
Ngân hàng gia hạn thêm (đến 80%)</span><span><i style="background:var(--red)"></i>Cổ đông / tái cấu trúc
```
THAY BẰNG:
```
Ngân hàng gia hạn thêm (đến 80%)</span><span><i style="background:var(--red)"></i>Phần còn thiếu: đối tác dự án / cổ đông (6–12 tháng)
```

### Mục 9
TÌM:
```
Doanh nghiệp tự cứu → ngân hàng gia hạn thêm → cổ đông
```
THAY BẰNG:
```
Doanh nghiệp tự xoay → ngân hàng gia hạn thêm → đối tác/cổ đông
```

### Mục 10
TÌM:
```
[['inv',C.teal,'Tự cứu: bán tồn kho'],['bank',C.ochre,'Ngân hàng gia hạn thêm'],['rest',C.red,'Cổ đông / tái cấu trúc']]
```
THAY BẰNG:
```
[['inv',C.teal,'Doanh nghiệp tự xoay: bán tồn kho'],['bank',C.ochre,'Ngân hàng gia hạn thêm'],['rest',C.red,'Phần còn thiếu: đối tác dự án / cổ đông']]
```

### Mục 11
TÌM:
```
— tự cứu ${fmt(vh.bu.inv)}, ngân hàng ${fmt(vh.bu.bank)}, cổ đông ${fmt(vh.bu.rest)}.
```
THAY BẰNG:
```
— tự xoay ${fmt(vh.bu.inv)}, ngân hàng ${fmt(vh.bu.bank)}, còn thiếu ${fmt(vh.bu.rest)}.
```

### Mục 12
TÌM:
```
'phần cổ đông/tái cấu trúc phải gánh'
```
THAY BẰNG:
```
'còn thiếu sau bán tồn kho và gia hạn — cần đối tác/cổ đông trong 6–12 tháng'
```

### Mục 13
TÌM:
```
chỉ cho doanh nghiệp nhóm C có phương án bán hàng và tăng vốn; nhóm D phải kèm cam kết của cổ đông.
```
THAY BẰNG:
```
ưu tiên doanh nghiệp nhóm C có phương án bán hàng khả thi; với nhóm D, cơ cấu kỳ hạn gắn với kế hoạch dòng tiền và cam kết hỗ trợ của cổ đông lớn/công ty mẹ.
```

### Mục 14
TÌM:
```
<b>Trái phiếu: cơ chế đàm phán trái chủ.</b> NĐ 200/2026 yêu cầu 65% trái chủ đồng ý khi sửa điều khoản; cần đầu mối trung gian (đại lý quản lý tài sản bảo đảm, tổ chức xếp hạng) để hoán đổi nợ – tài sản cho nhóm D thay vì để vỡ nợ lan rộng.
```
THAY BẰNG:
```
<b>Trái phiếu: cơ chế đàm phán trái chủ.</b> Sửa điều khoản trái phiếu cần đa số trái chủ đồng ý theo quy định hiện hành; cần đầu mối trung gian (đại lý quản lý tài sản bảo đảm, tổ chức xếp hạng) để giãn kỳ hạn hoặc thanh toán bằng tài sản cho nhóm D, tránh để chậm trả lan rộng.
```

## Phần 2 — Thay khối code trong hàm `recs()`

Trong hàm `recs()`, tìm đoạn bắt đầu bằng:
```
  if(m.gap<0){
   dev.push(`Khoảng hụt
```
và kết thúc **ngay trước** dòng:
```
  }else{
   dev.push(`Dư <b>
```
(tức là toàn bộ nhánh `if(m.gap<0){ ... }`, không gồm `}else{`). Thay đoạn đó bằng:
```js
  if(m.gap<0){
   const fireNeed=-m.gap/(1-P.hc/100),firePct=fireNeed/b.inventory*100;
   if(m.g=='D'){
    dev.push(`<b>0–3 tháng:</b> lập kế hoạch dòng tiền 13 tuần; đàm phán ngân hàng và trái chủ giãn gốc, trả lãi trước — cần gia hạn tối thiểu <b>${fmt(m.rNeed,0)}%</b> nợ ngắn hạn (hiện ${P.roll}%); tạm dừng dự án chưa khởi công.`);
    dev.push(`<b>3–6 tháng:</b> đẩy thu tiền ở dự án đang bàn giao, chiết khấu cho khách thanh toán sớm; bán sỉ/bán chọn lọc ~${fmt(Math.min(fireNeed,b.inventory*0.1))} tỷ tồn kho${firePct>10?` (khoảng hụt <b>${fmt(-m.gap)} tỷ</b> cần tới ${fmt(firePct,0)}% tồn kho — bán lẻ không đủ, nên chuyển nhượng một phần dự án đã đủ pháp lý hoặc tìm đối tác góp vốn dự án)`:''}.`);
    dev.push(`<b>6–12 tháng (dự phòng):</b> ${m.bu.rest>0?`phần còn thiếu ~<b>${fmt(m.bu.rest)} tỷ</b> cần `:''}vay cổ đông lớn/công ty mẹ hoặc phát hành riêng lẻ cho nhà đầu tư chiến lược.`);
    if(b.de>2)dev.push(`D/E ${fmt(b.de,2)} lần: không vay mới để trả nợ cũ; nguồn vốn mới nên là vốn chủ hoặc vốn đối tác dự án.`);
   }else{
    dev.push(`Khoảng hụt <b>${fmt(-m.gap)} tỷ</b>: tự lấp ${fmt(m.bu.inv)} tỷ bằng bán ${fmt(m.bu.inv/(1-P.hc/100)/b.inventory*100,1)}% tồn kho; cần ngân hàng gia hạn tối thiểu <b>${fmt(m.rNeed,0)}%</b> nợ ngắn hạn (hiện ${P.roll}%).`);
    if(m.bu.rest>0)dev.push(`Còn <b>${fmt(m.bu.rest)} tỷ</b> cần vay cổ đông lớn hoặc đối tác góp vốn dự án.`);
    if(b.de>2)dev.push(`D/E ${fmt(b.de,2)} lần: không vay thêm.`);
   }
```
Giữ nguyên nhánh `}else{ ... }` và phần còn lại của hàm.

## Phần 3 — Kiểm tra trước khi trả file

1. Tìm toàn file: không còn chuỗi "Nguy cấp", "Cứu được" hay "vỡ nợ".
2. Chuỗi "NĐ 200/2026" chỉ còn ở thẻ tiêu chí ④ (phần 7). Đây là phần giữ nguyên, không sửa.
3. JavaScript không lỗi cú pháp; mọi dấu backtick (`) và `${...}` trong template string phải đóng mở đúng.
4. Thẻ nhóm D (PDR, VHM, NVL ở kịch bản mặc định) hiển thị 3 mốc "0–3 tháng / 3–6 tháng / 6–12 tháng (dự phòng)".
5. Badge nhóm hiển thị "D · Stress cao" và "C · Cần hỗ trợ thanh khoản".
6. Trả về **toàn bộ file HTML hoàn chỉnh** trong một khối code, không lược bớt.
