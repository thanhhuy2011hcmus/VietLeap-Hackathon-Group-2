# 07 - Vẽ hình về phân phối và ngoại lai
import numpy as np

from common import BLUE, FIG, GREY, LATEST_Q, ORANGE, RE, get_plt, read

plt = get_plt()
f = read("features/bien_moi_quy.csv")
f = f[f["ticker"].isin(RE)]
now = f[f["period"] == LATEST_Q].sort_values("cash_coverage")

# hình 7.1 - tiền + đầu tư ngắn hạn so với nợ ngắn hạn; dưới 1 là không đủ
fig, ax = plt.subplots(figsize=(8, 4))
ax.barh(now["ticker"], now["cash_coverage"], color=np.where(now["cash_coverage"] < 1, ORANGE, BLUE))
ax.axvline(1, color="black", lw=1, ls="--")
for k, (c, gap) in enumerate(zip(now["cash_coverage"], now["liquidity_gap"])):
    ax.text(c + 0.02, k, f"{c:.2f}x  ({gap:,.0f} tỷ)", va="center", fontsize=8)
ax.set_xlim(0, 1.6)
ax.set_xlabel("(tiền + đầu tư ngắn hạn) / nợ ngắn hạn (lần)")
fig.tight_layout()
fig.savefig(FIG + "/07_1.png", dpi=110)
print(now[["ticker", "cash_coverage", "liquidity_gap"]].to_string(index=False))

# hình 7.2 - doanh thu quý so cùng kỳ theo từng doanh nghiệp (cắt ở ±300% cho dễ nhìn)
d = f.dropna(subset=["revenue_yoy_pct"])
order = d.groupby("ticker")["revenue_yoy_pct"].median().sort_values().index
fig, ax = plt.subplots(figsize=(8, 4.2))
ax.boxplot([d.loc[d["ticker"] == t, "revenue_yoy_pct"].clip(-100, 300) for t in order],
           orientation="horizontal", tick_labels=list(order), widths=0.6, patch_artist=True,
           boxprops={"facecolor": "#cfe0f6", "edgecolor": BLUE}, medianprops={"color": "black"},
           flierprops={"markerfacecolor": ORANGE, "markeredgecolor": "white"})
ax.axvline(0, color=GREY, lw=1)
ax.set_xlabel("doanh thu quý so cùng kỳ năm trước (%), cắt ở -100 và 300")
fig.tight_layout()
fig.savefig(FIG + "/07_2.png", dpi=110)
q1, q3 = d["revenue_yoy_pct"].quantile([0.25, 0.75])
hi = q3 + 1.5 * (q3 - q1)
big = d[d["revenue_yoy_pct"] > hi].sort_values("revenue_yoy_pct", ascending=False)
print(f"\nngưỡng ngoại lai trên {hi:.1f}%, {len(big)} quan sát vượt:")
print(big[["ticker", "period", "revenue_yoy_pct"]].to_string(index=False))

# hình 7.3 - phân phối doanh thu so cùng kỳ: năm 2023 so với các quý sau
crisis = d["period"] <= "2023Q4"
fig, ax = plt.subplots(figsize=(8, 3))
bins = np.arange(-100, 310, 20)
ax.hist(d.loc[~crisis, "revenue_yoy_pct"].clip(-100, 300), bins=bins, color=GREY, label="2024 trở đi")
ax.hist(d.loc[crisis, "revenue_yoy_pct"].clip(-100, 300), bins=bins, color=ORANGE, alpha=0.8, label="năm 2023")
ax.axvline(0, color="black", lw=1)
ax.set_xlabel("doanh thu quý so cùng kỳ (%)")
ax.set_ylabel("số quan sát")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(FIG + "/07_3.png", dpi=110)
print("\ntrung vị năm 2023:", round(d.loc[crisis, "revenue_yoy_pct"].median(), 2),
      "| trung vị từ 2024:", round(d.loc[~crisis, "revenue_yoy_pct"].median(), 2))

# hình 7.4 - đòn bẩy và khả năng trả nợ ngắn hạn (kích thước = khoảng thiếu hụt)
fig, ax = plt.subplots(figsize=(8, 4))
size = 40 + 600 * (now["liquidity_gap"].clip(upper=0).abs() / now["liquidity_gap"].abs().max()) ** 0.5
ax.scatter(now["liab_to_equity"], now["cash_coverage"], s=size, color=ORANGE, alpha=0.6, edgecolor="white")
for _, r in now.iterrows():
    ax.annotate(r["ticker"], (r["liab_to_equity"], r["cash_coverage"]), xytext=(6, 4),
                textcoords="offset points", fontsize=8)
ax.axhline(1, color=GREY, ls="--", lw=1)
ax.set_xlabel("nợ phải trả / vốn chủ sở hữu (lần)")
ax.set_ylabel("(tiền + ĐTNH) / nợ ngắn hạn (lần)")
fig.tight_layout()
fig.savefig(FIG + "/07_4.png", dpi=110)
print("\ntương quan giữa đòn bẩy và khả năng trả nợ ngắn hạn:",
      round(now["liab_to_equity"].corr(now["cash_coverage"]), 2))
