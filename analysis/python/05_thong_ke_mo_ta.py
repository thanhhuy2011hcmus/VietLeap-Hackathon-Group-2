# 05 - Thống kê mô tả
import numpy as np
import pandas as pd

from common import LATEST_Q, RE, read

f = read("features/bien_moi_quy.csv")
f = f[f["ticker"].isin(RE)]
cols = ["liquidity_gap", "cash_coverage", "inventory_share", "liab_to_equity", "fin_cost_ratio_pct"]

now = f[f["period"] == LATEST_Q]
t = now[cols].describe().T
t["skew"] = now[cols].skew()
print("quý", LATEST_Q, "-", len(now), "doanh nghiệp BĐS")
print(t.round(2))

# cú sốc doanh thu: so cùng kỳ trong năm 2023 với các giai đoạn sau
f["giai_doan"] = np.select([f["period"] <= "2023Q4", f["period"] <= "2025Q3"],
                           ["1. 2023 (khủng hoảng)", "2. 2024-2025Q3"], "3. 2025Q4-2026Q3")
g = f.groupby("giai_doan")["revenue_yoy_pct"]
print("\ndoanh thu quý so cùng kỳ (%):")
print(pd.DataFrame({"n": g.count(), "trung_vi": g.median(), "ty_le_giam": g.apply(lambda s: (s.dropna() < 0).mean())}))

# xếp hạng theo khoảng thiếu hụt thanh khoản tại quý mới nhất
print("\nxếp hạng thiếu hụt tại", LATEST_Q, "(tỷ đồng):")
print(now.sort_values("liquidity_gap")[["ticker", "liquidity_gap", "cash_coverage", "liab_to_equity"]]
      .to_string(index=False))
