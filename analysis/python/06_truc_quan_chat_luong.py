# 06 - Vẽ hình về chất lượng và độ phủ dữ liệu
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap

from common import BLUE, FIG, GREEN, ORANGE, SHOCK, get_plt, read

plt = get_plt()
p = read("bctc/panel_quarterly_bctc.csv")

# hình 6.1 - mã nào có số liệu ở quý nào: 0 không có, 1 chỉ KQKD, 2 có cả KQKD và CĐKT
quarters = pd.period_range(p["period"].min(), p["period"].max(), freq="Q").astype(str)
p["state"] = np.where(p["total_assets"].notna(), 2, np.where(p["net_revenue"].notna(), 1, 0))
grid = p.pivot(index="ticker", columns="period", values="state").reindex(columns=quarters).fillna(0)

fig, ax = plt.subplots(figsize=(9, 3.8))
ax.imshow(grid, cmap=ListedColormap(["#e9ecef", "#9cc3f0", BLUE]), aspect="auto", vmin=0, vmax=2)
ax.set_xticks(range(len(quarters)), quarters, rotation=90)
ax.set_yticks(range(len(grid)), grid.index)
ax.set_title("xám: không có số liệu   xanh nhạt: chỉ có KQKD   xanh đậm: có cả KQKD và CĐKT",
             loc="left", fontsize=9)
fig.tight_layout()
fig.savefig(FIG + "/06_1.png", dpi=110)
print("số mã có KQKD theo quý:")
print((grid > 0).sum().to_string())

# hình 6.2 - số ô trống theo biến (tính trên các quý có loại báo cáo tương ứng)
is_cols = ["net_revenue", "cogs", "financial_expense", "selling_expense", "associate_profit", "basic_eps_vnd"]
bs = p.dropna(subset=["total_assets"])
miss = pd.concat([p[is_cols].isna().sum(), bs.drop(columns=is_cols).isna().sum()])
miss = miss[miss > 0].sort_values()

fig, ax = plt.subplots(figsize=(8, 3))
ax.barh(miss.index, miss.values, color=ORANGE)
ax.set_xlabel("số ô trống")
fig.tight_layout()
fig.savefig(FIG + "/06_2.png", dpi=110)
print()
print(miss.sort_values(ascending=False).to_string())

# hình 6.3 - lãi suất theo quý và giai đoạn khủng hoảng 2022-2023
m = read("macro/macro_quy.csv")
x = np.arange(len(m))
i = {q: k for k, q in enumerate(m["quarter"])}

fig, ax = plt.subplots(figsize=(9, 3.6))
ax.axvspan(i[SHOCK[0]] - 0.5, i[SHOCK[1]] + 0.5, color="#fbe3d6", label="2022Q3-2023Q4")
ax.step(x, m["sbv_refinancing_eoq_pct"], where="mid", color=BLUE, label="tái cấp vốn NHNN")
ax.step(x, m["fed_upper_eoq_pct"], where="mid", color=ORANGE, label="lãi suất Fed")
ax.plot(x, m["ust10y_avg_pct"], color=GREEN, label="UST 10 năm")
ax.set_xticks(x[::2], m["quarter"][::2], rotation=90)
ax.set_ylabel("%/năm")
ax.legend(frameon=False, ncol=4, fontsize=8, loc="lower center", bbox_to_anchor=(0.5, 1))
fig.tight_layout()
fig.savefig(FIG + "/06_3.png", dpi=110)
print()
print(m[m["quarter"].isin(["2022Q2", "2022Q4", "2023Q4", "2026Q3"])].to_string(index=False))
