# 04 - Tạo biến mới (chỉ những biến cần cho câu hỏi nghiên cứu)
import numpy as np
import pandas as pd

from common import LATEST_Q, RE, read

p = read("bctc/panel_quarterly_bctc.csv")
rows = []
for t, g in p.groupby("ticker"):
    # lưới quý liên tục, để cộng 4 quý / so cùng kỳ không nhảy qua quý bị thiếu
    q = pd.PeriodIndex(g["period"], freq="Q")
    g = g.set_index(q).reindex(pd.period_range(q.min(), q.max(), freq="Q"))
    d = pd.DataFrame(index=g.index)
    d["ticker"] = t
    # nguồn trả nợ sẵn có; đầu tư ngắn hạn ghi "-" coi là 0 trong phép cộng
    d["liquid_assets"] = g["cash_and_equivalents"] + g["short_term_investments"].fillna(0)
    d["liquidity_gap"] = d["liquid_assets"] - g["short_term_liabilities"]
    d["cash_coverage"] = d["liquid_assets"] / g["short_term_liabilities"]
    d["inventory_share"] = g["inventory"] / g["current_assets"]
    d["liab_to_equity"] = g["total_liabilities"] / g["owner_equity"]
    # cú sốc bán hàng và gánh nặng chi phí tài chính
    d["revenue_ttm"] = g["net_revenue"].rolling(4).sum()
    lag = g["net_revenue"].shift(4)
    d["revenue_yoy_pct"] = (g["net_revenue"] - lag) / lag.where(lag > 0) * 100
    d["fin_cost_ratio_pct"] = g["financial_expense"].rolling(4).sum() / d["revenue_ttm"] * 100
    rows.append(d[g["ticker"].notna()])
f = pd.concat(rows).rename_axis("period").reset_index()
f["period"] = f["period"].astype(str)

now = f[(f["period"] == LATEST_Q) & f["ticker"].isin(RE)].set_index("ticker")
print(now[["liquid_assets", "liquidity_gap", "revenue_ttm"]].sort_values("liquidity_gap"))
print()
print(now[["cash_coverage", "inventory_share", "liab_to_equity", "revenue_yoy_pct",
           "fin_cost_ratio_pct"]].sort_values("cash_coverage"))

# đối chiếu với file do src/build_features.py tạo ra
saved = read("features/bien_moi_quy.csv").set_index(["ticker", "period"])
mine = f.set_index(["ticker", "period"]).loc[saved.index]
cols = [c for c in mine.columns]
print("\nkhớp với bien_moi_quy.csv:", np.allclose(mine[cols], saved[cols], atol=1e-3, equal_nan=True))
print("số quan sát có revenue_ttm:", f["revenue_ttm"].notna().sum(),
      "| có revenue_yoy_pct:", f["revenue_yoy_pct"].notna().sum())
