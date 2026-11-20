# 06 - Vẽ hình về chất lượng và độ phủ dữ liệu
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap

from common import BASE_Q, BLUE, FIG, GREEN, ORANGE, PROC, QUARTERS, STRESS_Q, get_plt

plt = get_plt()
p = pd.read_csv(PROC + "/panel_quarterly.csv")

# hình 6.1 - mã nào có số liệu ở quý nào
# 0 = không có, 1 = có số liệu quý, 2 = tính được số 12 tháng
p["state"] = np.where(p["cfo_ttm"].isna(), 1, 2)
grid = p.pivot(index="ticker", columns="period", values="state")
grid = grid.reindex(columns=QUARTERS).fillna(0)

fig, ax = plt.subplots(figsize=(9, 3.8))
ax.imshow(grid, cmap=ListedColormap(["#e9ecef", "#9cc3f0", BLUE]), aspect="auto")
ax.set_xticks(range(len(QUARTERS)), QUARTERS, rotation=90)
ax.set_yticks(range(len(grid)), grid.index)
ax.set_title("xám: không có số liệu   xanh nhạt: có số liệu quý   "
             "xanh đậm: tính được số 12 tháng", loc="left", fontsize=9)
fig.tight_layout()
fig.savefig(FIG + "/06_1.png", dpi=110)
n = (grid > 0).sum()
print("quý không có mã nào:", ", ".join(n.index[n == 0]))
print("các quý còn lại đều đủ", n.max(), "mã")

# hình 6.2 - các lỗi đã gắn cờ
names = {"interest_paid_sign": "lãi vay đã trả mang dấu dương",
         "loan_proceeds_sign": "tiền vay mới mang dấu âm",
         "net_sales_sign": "doanh thu thuần âm",
         "loan_repayments_sign": "trả nợ gốc mang dấu dương",
         "interest_paid_from_pl": "lãi vay đã trả lấy từ B02",
         "cash_bs_ne_cf": "tiền B01 khác tiền cuối kỳ B03"}
flags = p["dq_flags"].dropna().str.split(";").explode().map(names).value_counts()

fig, ax = plt.subplots(figsize=(8, 2.8))
ax.barh(flags.index[::-1], flags.values[::-1], color=BLUE)
ax.set_xlabel("số quý bị gắn cờ")
fig.tight_layout()
fig.savefig(FIG + "/06_2.png", dpi=110)
print()
print(flags.to_string())

# hình 6.3 - lãi suất và 2 giai đoạn dùng để đo cú sốc
m = pd.read_csv(PROC + "/macro_quarterly.csv")
x = np.arange(len(m))
i = {q: k for k, q in enumerate(m["period"])}

fig, ax = plt.subplots(figsize=(9, 3.6))
ax.axvspan(i["2021Q3"] - 0.5, i[BASE_Q] + 0.5, color="#dfe7f3", label="trước khủng hoảng")
ax.axvspan(i["2022Q3"] - 0.5, i[STRESS_Q] + 0.5, color="#fbe3d6", label="khủng hoảng")
ax.step(x, m["sbv_refinancing_eoq"], where="mid", color=BLUE, label="tái cấp vốn NHNN")
ax.step(x, m["fed_upper_eoq"], where="mid", color=ORANGE, label="lãi suất Fed")
ax.plot(x, m["ust10y_avg"], color=GREEN, label="UST 10 năm")
ax.set_xticks(x, m["period"], rotation=90)
ax.set_ylabel("%/năm")
ax.legend(frameon=False, ncol=5, fontsize=8, loc="lower center", bbox_to_anchor=(0.5, 1))
fig.tight_layout()
fig.savefig(FIG + "/06_3.png", dpi=110)
print()
print(m[m["period"].isin(["2021Q4", BASE_Q, "2022Q4", STRESS_Q, "2026Q3"])])
