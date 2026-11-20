# 03 - Làm sạch: ô trống, ô "-" và ngoại lai
import pandas as pd

from common import RE, read

p = read("bctc/panel_quarterly_bctc.csv")

# ô "-" trong file Vietstock (không phát sinh / không có số) đã được để trống, không thay bằng 0.
# đếm riêng từng bảng để không lẫn với phần CĐKT vốn không có trong nguồn
for name, d in [("KQKD", read("bctc/ket_qua_kinh_doanh_quy.csv")), ("CĐKT", read("bctc/can_doi_ke_toan_quy.csv"))]:
    na = d.isna().sum()
    print(f"ô trống trong {name} ({len(d)} quý):")
    print(na[na > 0].to_string())

# vĩ mô: tháng CPI Mỹ bị thiếu đã được nội suy và gắn cờ
m = read("macro/macro_thang.csv")
print("\nCPI Mỹ nội suy:", m.loc[m["us_cpi_imputed"], ["month", "us_cpi_index"]].to_string(index=False))


# ngoại lai theo quy tắc 1,5 IQR - chỉ đánh dấu, không xóa
def ngoai_lai(s):
    s = s.dropna()
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    return s[(s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)]


# doanh thu quý của từng doanh nghiệp: quý nào cao/thấp bất thường so với chính DN đó
print("\nquý có doanh thu ngoại lai (tỷ đồng):")
for t in RE:
    g = p[p["ticker"] == t].set_index("period")["net_revenue"]
    out = ngoai_lai(g)
    print(f"  {t}: " + (", ".join(f"{k} {v:,.0f}" for k, v in out.items()) or "không có"))

# chỉ số năm 2025 giữa các doanh nghiệp
r = read("bctc/chi_so_tai_chinh_nam.csv")
r = r[(r["year"] == 2025) & r["ticker"].isin(RE)].set_index("ticker")
print("\nngoại lai giữa các DN, năm 2025:")
for col in ["gross_margin_pct", "net_margin_pct", "debt_to_assets", "roea_pct"]:
    out = ngoai_lai(r[col])
    print(f"  {col}: " + (", ".join(f"{k} {v:.2f}" for k, v in out.items()) or "không có"))
