# 01 - Nạp dữ liệu và đồng bộ tên biến
import glob
import os

import pandas as pd

from common import RAW, read

# file gốc: mỗi mã 4 đợt tải Vietstock, cộng dữ liệu vĩ mô
for t in sorted(os.listdir(RAW + "/vietstock")):
    print(t, len(glob.glob(f"{RAW}/vietstock/{t}/*.xls")), "file .xls")
for f in sorted(glob.glob(RAW + "/fred/*.csv") + glob.glob(RAW + "/sbv/*.csv")):
    print(os.path.basename(f), pd.read_csv(f).shape)

# dữ liệu sạch: tên chỉ tiêu tiếng Việt đã đổi sang tên biến tiếng Anh ngắn
panel = read("bctc/panel_quarterly_bctc.csv")
macro = read("macro/macro_quy.csv")
print("\npanel BCTC:", panel.shape, "| vĩ mô theo quý:", macro.shape)

# đồng bộ khóa thời gian: cả hai bảng dùng kỳ dạng 2026Q3 -> ghép trực tiếp
df = panel.merge(macro, left_on="period", right_on="quarter", how="left")
cols = ["ticker", "period", "net_revenue", "fed_upper_eoq_pct", "sbv_refinancing_eoq_pct"]
print(df.loc[df["ticker"] == "NVL", cols].tail(5).to_string(index=False))
print("\nquý BCTC không ghép được với vĩ mô:",
      sorted(set(panel["period"]) - set(macro["quarter"])))
