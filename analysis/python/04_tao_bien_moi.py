# 04 - Tạo biến mới (chỉ những biến cần cho câu hỏi nghiên cứu)
import numpy as np
import pandas as pd

from common import BASE_Q, FLOWS, LATEST_Q, PROC, QUARTERS, STRESS_Q
from common import load_raw, to_wide

# làm lại các bước của mục 03
w = to_wide(load_raw())
thieu = w["interest_paid"].isna()
w.loc[thieu, "interest_paid"] = w.loc[thieu, "interest_expense"]
w["interest_paid"] = -w["interest_paid"]
w["loan_repayments"] = -w["loan_repayments"]
money = ["cash", "st_invest", "st_debt", "lt_debt", "adv_st", "adv_lt", "equity"] + FLOWS
w[money] = w[money] / 1e9            # đổi sang tỷ đồng

# dựng đủ các quý 2021Q1-2026Q3 cho từng mã, kể cả quý không có số liệu,
# để khi cộng 4 quý không bị nhảy qua khoảng trống 2024-2025
grid = pd.MultiIndex.from_product([w["ticker"].unique(), QUARTERS],
                                  names=["ticker", "period"]).to_frame(index=False)
d = grid.merge(w, on=["ticker", "period"], how="left")

d["liquid_assets"] = d["cash"] + d["st_invest"]
d["total_debt"] = d["st_debt"] + d["lt_debt"]
d["adv_customers"] = d["adv_st"] + d["adv_lt"]

# cộng 4 quý gần nhất -> số 12 tháng
for col in FLOWS:
    d[col + "_ttm"] = d.groupby("ticker")[col].transform(lambda s: s.rolling(4).sum())
avg_debt = d.groupby("ticker")["total_debt"].transform(lambda s: s.rolling(4).mean())

d["implied_rate_pct"] = d["interest_paid_ttm"] / avg_debt.where(avg_debt > 0) * 100
d["rollover_ratio"] = d["loan_proceeds_ttm"] / d["loan_repayments_ttm"].where(
    d["loan_repayments_ttm"] > 0)
d["liquidity_gap_12m"] = d["liquid_assets"] + d["cfo_ttm"] - d["st_debt"]
d["liquidity_coverage"] = (d["liquid_assets"] + d["cfo_ttm"]) / d["st_debt"]
d["debt_to_equity"] = d["total_debt"] / d["equity"]

cols = ["liquid_assets", "st_debt", "cfo_ttm", "liquidity_gap_12m",
        "liquidity_coverage", "rollover_ratio", "implied_rate_pct", "debt_to_equity"]
now = d[d["period"] == LATEST_Q].set_index("ticker").sort_values("liquidity_gap_12m")
print(now[cols[:4]])     # tỷ đồng
print()
print(now[cols[4:]])     # lần, %

# đối chiếu với file sạch do src/clean_raw_data.py tạo ra
saved = pd.read_csv(PROC + "/panel_quarterly.csv").set_index(["ticker", "period"])
mine = d.set_index(["ticker", "period"]).loc[saved.index, cols]
print("\nkhớp với panel_quarterly.csv:",
      np.allclose(mine, saved[cols], atol=1e-3, equal_nan=True))

# cú sốc 2022-2023: 4 quý khủng hoảng so với 4 quý trước đó
b = d[d["period"] == BASE_Q].set_index("ticker")
s = d[d["period"] == STRESS_Q].set_index("ticker")
shock = pd.DataFrame({
    "sales_shock_pct": (s["net_sales_ttm"] / b["net_sales_ttm"] - 1) * 100,
    "adv_shock_pct": (s["adv_customers"] / b["adv_customers"] - 1) * 100,
    "rate_shock_pp": s["implied_rate_pct"] - b["implied_rate_pct"],
    "rollover_stress": s["rollover_ratio"],
})
print()
print(shock)
print("\ntrung vị ngành:")
print(shock.median().to_string())
