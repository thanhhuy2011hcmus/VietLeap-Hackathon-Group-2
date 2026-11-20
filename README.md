# VietLeap Hackathon 2026 – Nhóm 2

**Câu hỏi:** nếu lãi suất tăng và bán hàng chậm lại trong 12 tháng tới như giai đoạn 2022–2023, doanh nghiệp
BĐS dân cư niêm yết nào không đủ tiền trả nợ đến hạn, thiếu bao nhiêu, chịu được cú sốc đến đâu, và doanh nghiệp
cũng như ngân hàng cho vay nên làm gì?

Repo này chứa phần xử lý dữ liệu: từ file thô đến bộ dữ liệu sạch và báo cáo xử lý dữ liệu.
Chỉ những biến phục vụ trực tiếp câu hỏi trên mới được tạo.

## Cấu trúc thư mục

```
.
├── data/
│   ├── raw/                  # dữ liệu thô, không chỉnh sửa tay
│   └── processed/            # dữ liệu sạch (sinh ra bởi src/clean_raw_data.py)
├── src/
│   ├── clean_raw_data.py     # làm sạch, tạo biến, xuất data/processed + data_quality_report.txt
│   └── build_report.py       # chạy code phân tích và dựng báo cáo HTML
├── analysis/
│   ├── python/               # common.py + code từng mục của báo cáo (00–07)
│   └── r/                    # cùng nội dung, bản R
├── reports/
│   ├── bao_cao_xu_ly_du_lieu.html
│   └── figures/              # hình do analysis/ sinh ra (python/, r/)
├── run_pipeline.py           # chạy toàn bộ quy trình
└── requirements.txt
```

## Cách chạy

```bash
pip install -r requirements.txt
python run_pipeline.py            # làm sạch + dựng báo cáo
python run_pipeline.py --clean    # chỉ làm sạch
python run_pipeline.py --report   # chỉ dựng báo cáo
```

Phần R cần R ≥ 4.2 với các gói `dplyr`, `tidyr`, `readr`, `ggplot2`. Mọi lệnh chạy từ thư mục gốc repo; các file
trong `analysis/` cũng chạy riêng được, ví dụ `python analysis/python/04_tao_bien_moi.py` hoặc
`Rscript analysis/r/04_tao_bien_moi.R`.

## Dữ liệu đầu vào (`data/raw/`)

| File | Nguồn | Dùng để |
|---|---|---|
| `<MÃ>_bctc_min_raw.csv` (13 mã) | FiinQuant | Tiền, nợ vay, dòng tiền, doanh thu, khách trả trước theo quý |
| `fred_DFEDTARU_…`, `fred_DGS10_…` | FRED | Xác định thời điểm cú sốc lãi suất |
| `sbv_lai_suat_dieu_hanh_trich_nguon.csv` | NHNN | Lãi suất tái cấp vốn |
| `hnx_54_to_chuc_cham_tra_trich_nguon.csv` | HNX | Nhãn chậm trả trái phiếu 2022–2023 để kiểm chứng |
| `bctc_full_VHM_2026Q3.csv`, `fred_CPIAUCSL_…`, `fred_VNMPCPIPCPPPT_…` | – | Không dùng (trùng nguồn / không phục vụ câu hỏi) |

Thêm mã mới: đặt file `<MÃ>_bctc_min_raw.csv` vào `data/raw/` rồi chạy lại `python run_pipeline.py`.

## Dữ liệu sạch (`data/processed/`)

| File | Nội dung |
|---|---|
| `panel_quarterly.csv` | Mã × quý: nguồn trả nợ, nợ đến hạn, dòng tiền 12 tháng (TTM), thiếu hụt thanh khoản, hệ số bao phủ, tỷ lệ đảo nợ, lãi suất thực trả, nợ/VCSH |
| `stress_calibration.csv` | Cú sốc 2022–2023 của từng DN (TTM 2023Q2 so với TTM 2022Q2) và trung vị ngành |
| `macro_quarterly.csv` | Lãi suất tái cấp vốn NHNN, lãi suất Fed, UST 10 năm theo quý |
| `sbv_policy_events.csv` | Quyết định lãi suất điều hành NHNN đã làm sạch |
| `hnx_default_labels.csv` | Nhãn chậm trả trái phiếu theo mã |
| `data_quality_report.txt` | Nhật ký kiểm tra và xử lý dữ liệu |

Lưu ý: dữ liệu BCTC thiếu 2024Q1–2025Q3 nên chỉ tiêu 12 tháng (TTM) chỉ tính được cho 2021Q4–2023Q4 và 2026Q3.
