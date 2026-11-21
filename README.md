# VietLeap Hackathon 2026 – Nhóm 2

Dữ liệu báo cáo tài chính tóm tắt (Vietstock) của 10 doanh nghiệp, dữ liệu vĩ mô (FRED, IMF, NHNN)
và code làm sạch.

## Cấu trúc

```
.
├── data/
│   ├── raw/                          # file gốc, không sửa tay
│   │   ├── vietstock/<MÃ>/           # 4 file *_BCTC_Tom_Tat*.xls mỗi mã (10 mã)
│   │   ├── fred/                     # CPI Mỹ, lãi suất Fed, UST 10 năm, CPI Việt Nam (IMF)
│   │   └── sbv/                      # quyết định lãi suất điều hành NHNN
│   └── processed/                    # sinh ra bởi code, không sửa tay
│       ├── bctc/
│       │   ├── ket_qua_kinh_doanh_quy.csv
│       │   ├── can_doi_ke_toan_quy.csv
│       │   ├── panel_quarterly_bctc.csv
│       │   ├── chi_so_tai_chinh_nam.csv
│       │   └── bao_cao_chat_luong_du_lieu.txt
│       ├── features/bien_moi_quy.csv  # 8 biến mới phục vụ câu hỏi nghiên cứu
│       └── macro/
│           ├── macro_thang.csv
│           ├── macro_quy.csv
│           ├── cpi_viet_nam_nam.csv
│           ├── lai_suat_nhnn_su_kien.csv
│           └── bao_cao_chat_luong_vi_mo.txt
├── src/
│   ├── clean_bctc_data.py            # data/raw/vietstock -> data/processed/bctc
│   ├── clean_macro_data.py           # data/raw/fred, sbv -> data/processed/macro
│   ├── build_features.py             # -> data/processed/features
│   ├── build_report.py               # chạy analysis/, dựng báo cáo HTML
│   ├── build_dashboard_ban_nop.py    # dashboard v3 -> bản nộp gọn, rồi dựng 2 bản tiếng Anh
│   └── translate_dashboard.py        # dịch dashboard sang tiếng Anh (chỉ đổi chữ, giữ số và mô hình)
├── analysis/
│   ├── python/                       # common.py + 00–07, mỗi file là một mục của báo cáo
│   └── r/                            # cùng nội dung, bản R
├── reports/
│   ├── bao_cao_truc_quan_hoa.html    # báo cáo trực quan hóa (mở bằng trình duyệt)
│   ├── dashboard_stress_test_BDS_v3_vnese.html       # dashboard đầy đủ, 10 phần (tiếng Việt)
│   ├── dashboard_stress_test_BDS_v3_eng.html         # như trên, tiếng Anh
│   ├── dashboard_stress_test_BDS_ban_nop_vnese.html  # bản nộp Data Decision, 6 phần (tiếng Việt)
│   ├── dashboard_stress_test_BDS_ban_nop_eng.html    # như trên, tiếng Anh
│   └── figures/python, figures/r
├── .claude/prompts/                  # prompt đặc tả dashboard (v2 -> v3, bản nộp gọn)
├── run_pipeline.py                   # làm sạch -> tạo biến -> báo cáo -> bản nộp dashboard
├── requirements.txt
└── README.md
```

## Cách chạy

```bash
python -m pip install -r requirements.txt
python run_pipeline.py
```

Phần R của báo cáo cần R ≥ 4.2 với `dplyr`, `tidyr`, `readr`, `ggplot2`; Python cần thêm `matplotlib`.

`dashboard_stress_test_BDS_v3_vnese.html` là file gốc (sửa theo `.claude/prompts/PROMPT_cap_nhat_v2_sang_v3.md`).
`python src/build_dashboard_ban_nop.py` dựng bản nộp tiếng Việt từ nó, rồi dịch cả hai sang tiếng Anh (`*_eng.html`).
Sửa chữ trong bản tiếng Việt thì thêm cặp câu tương ứng vào `PAIRS` trong `src/translate_dashboard.py`;
script dừng và in ra chỗ còn sót tiếng Việt nếu thiếu.

Thêm mã mới: tạo `data/raw/vietstock/<MÃ>/`, thả các file `<MÃ>_BCTC_Tom_Tat*.xls` vào rồi chạy lại.
Các đợt tải `(1)`, `(2)`, `(3)` được gộp và khử trùng lặp; nếu hai đợt ghi số khác nhau cho cùng một ô,
code lấy file tải sau cùng và ghi số ô xung đột vào báo cáo.

## Dữ liệu sạch

**BCTC** (đơn vị tỷ đồng; EPS/BVPS nghìn đồng/cp; `period` dạng `2026Q3`)

| File | Nội dung |
|---|---|
| `ket_qua_kinh_doanh_quy.csv` | Kết quả kinh doanh, 16 quý mỗi mã (2022–2026) |
| `can_doi_ke_toan_quy.csv` | Cân đối kế toán, 4 quý gần nhất (2025Q4–2026Q3) |
| `panel_quarterly_bctc.csv` | Ghép hai bảng trên theo `ticker` × `period` |
| `chi_so_tai_chinh_nam.csv` | Chỉ số tài chính theo năm (2022–2025) |

**Vĩ mô** (lãi suất, lạm phát tính bằng %)

| File | Nội dung |
|---|---|
| `macro_thang.csv` | CPI Mỹ (chỉ số và % so cùng kỳ), trần lãi suất Fed cuối tháng, lợi suất UST 10 năm |
| `macro_quy.csv` | Tổng hợp theo quý + lãi suất tái cấp vốn NHNN cuối quý (2019Q1–2026Q3) |
| `cpi_viet_nam_nam.csv` | Lạm phát Việt Nam theo IMF; cột `data_type`: `thuc_te` / `uoc_tinh` / `du_bao` |
| `lai_suat_nhnn_su_kien.csv` | 16 quyết định lãi suất NHNN, mức trước/sau đã tách khỏi câu chữ |

## Lưu ý về dữ liệu

- **`SRC` không phải SCR.** Công ty trong các file `SRC_*` có tổng tài sản 1.236–5.917 tỷ, vốn điều lệ 281–365 tỷ,
  khớp với Cao su Sao Vàng (mã SRC), không phải Địa ốc Sài Gòn Thương Tín (SCR). Nếu cần SCR, tải lại đúng mã.
- **Quý bị thiếu do nguồn:** file Vietstock nhảy cóc kỳ, nên KQKD của DXG, KDH, NLG, NVL, SRC thiếu 2024Q2,
  NVL thiếu thêm 2025Q2. Muốn đủ, tải riêng các kỳ đó.
- Cân đối kế toán chỉ có 4 quý gần nhất vì file tóm tắt chỉ chứa 4 quý. Một ô tổng tài sản trống (SRC 2026Q1)
  được điền bằng tổng nguồn vốn cùng quý (đẳng thức kế toán); mọi ô `-` khác để trống, không thay bằng 0.
- Vĩ mô: CPI Mỹ thiếu 10/2025 được nội suy và gắn cờ `us_cpi_imputed`; tháng 10/2026 của UST 10 năm chưa công
  bố nên bị bỏ; dữ liệu NHNN chỉ có các quyết định 10/2022–06/2023 và thiếu vài đợt giảm năm 2023
  (xem `bao_cao_chat_luong_vi_mo.txt`). Lãi suất chính sách không phải lãi suất vay của doanh nghiệp.
