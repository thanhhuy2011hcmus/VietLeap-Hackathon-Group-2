# 07 - Vẽ hình về phân phối và ngoại lai
import numpy as np
import pandas as pd

from common import BLUE, FIG, LATEST_Q, ORANGE, PROC, get_plt

plt = get_plt()
p = pd.read_csv(PROC + "/panel_quarterly.csv")
shock = pd.read_csv(PROC + "/stress_calibration.csv").set_index("ticker").drop("MEDIAN")

# hình 7.1 - hệ số bao phủ nợ vay ngắn hạn tại quý mới nhất
# (tiền + đầu tư ngắn hạn + CFO 12 tháng) / nợ vay ngắn hạn; dưới 1 là không đủ
now = p[p["period"] == LATEST_Q].sort_values("liquidity_coverage")
cov = now["liquidity_coverage"].clip(upper=6)     # DIG 14x, cắt bớt cho dễ nhìn

fig, ax = plt.subplots(figsize=(8, 4.2))
ax.barh(now["ticker"], cov, color=np.where(cov < 1, ORANGE, BLUE))
ax.axvline(1, color="black", lw=1, ls="--")
for k, (c, gap) in enumerate(zip(now["liquidity_coverage"], now["liquidity_gap_12m"])):
    ax.text(max(min(c, 6), 0) + 0.1, k, f"{c:.2f}x  ({gap:,.0f} tỷ)", va="center", fontsize=8)
ax.set_xlim(-1.6, 8.2)
ax.set_xlabel("hệ số bao phủ (lần), cột cắt ở 6")
fig.tight_layout()
fig.savefig(FIG + "/07_1.png", dpi=110)
print(now[["ticker", "liquidity_coverage", "liquidity_gap_12m"]].round(2).to_string(index=False))

# hình 7.2 - cú sốc 2022-2023 của từng DN, ghi tên DN ngoại lai
cols = {"sales_shock_pct": "doanh thu (%)", "adv_shock_pct": "khách trả trước (%)",
        "rate_shock_pp": "lãi suất thực trả (điểm %)", "rollover_stress": "vay mới / trả nợ"}
fig, axes = plt.subplots(4, 1, figsize=(8, 5.2))
print()
for ax, (col, label) in zip(axes, cols.items()):
    s = shock[col].dropna()
    ax.boxplot(s, orientation="horizontal", widths=0.6, patch_artist=True,
               boxprops={"facecolor": "#cfe0f6", "edgecolor": BLUE},
               medianprops={"color": "black"},
               flierprops={"markerfacecolor": ORANGE, "markeredgecolor": "white"})
    q1, q3 = s.quantile([0.25, 0.75])
    out = s[(s < q1 - 1.5 * (q3 - q1)) | (s > q3 + 1.5 * (q3 - q1))].sort_values()
    for k, (t, v) in enumerate(out.items()):
        ax.annotate(t, (v, 1), xytext=(0, 8 if k % 2 == 0 else -15),
                    textcoords="offset points", ha="center", fontsize=8)
    ax.set_yticks([1], [label])
    ds = ", ".join(f"{k} {v:.2f}" for k, v in out.items()) or "không có"
    print(f"{col}: trung vị {s.median():.2f}; ngoại lai {ds}")
fig.tight_layout()
fig.savefig(FIG + "/07_2.png", dpi=110)

# hình 7.3 - lãi suất thực trả trên mọi quan sát có số 12 tháng
r = p.dropna(subset=["implied_rate_pct"])
q1, q3 = r["implied_rate_pct"].quantile([0.25, 0.75])
hi = q3 + 1.5 * (q3 - q1)

fig, ax = plt.subplots(figsize=(8, 3))
ax.hist(r["implied_rate_pct"].clip(upper=30), bins=range(0, 31), color=BLUE, edgecolor="white")
ax.axvline(r["implied_rate_pct"].median(), color="black", ls="--", lw=1)
ax.axvline(hi, color=ORANGE, lw=1)
ax.set_xlabel("lãi vay đã trả 12 tháng / nợ vay bình quân (%), cắt ở 30")
ax.set_ylabel("số quan sát")
fig.tight_layout()
fig.savefig(FIG + "/07_3.png", dpi=110)
print(f"\ntrung vị {r['implied_rate_pct'].median():.2f}%, ngưỡng ngoại lai {hi:.2f}%")
out = r[r["implied_rate_pct"] > hi].sort_values("implied_rate_pct", ascending=False)
print(out[["ticker", "period", "implied_rate_pct", "interest_paid_ttm", "total_debt"]]
      .round(2).to_string(index=False))
