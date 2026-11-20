# 02 - Kiểm tra chất lượng dữ liệu
import pandas as pd

from common import LATEST_Q, read

p = read("bctc/panel_quarterly_bctc.csv")
print("dòng trùng (ticker, period):", p.duplicated(["ticker", "period"]).sum())

# độ phủ: số quý có kết quả kinh doanh (KQKD) và có cân đối kế toán (CĐKT)
cov = p.groupby("ticker").agg(kqkd=("net_revenue", "count"), cdkt=("total_assets", "count"),
                              tu=("period", "min"), den=("period", "max"))
print(cov)

# quý bị thiếu nằm giữa kỳ đầu và kỳ cuối
print("\nquý thiếu ở giữa:")
for t, g in p.groupby("ticker"):
    q = pd.PeriodIndex(g["period"], freq="Q")
    thieu = [str(x) for x in pd.period_range(q.min(), q.max(), freq="Q") if x not in set(q)]
    print(" ", t, ", ".join(thieu) or "không")

# các đẳng thức kế toán (lệch dưới 0,1 tỷ coi là khớp)
bs = p.dropna(subset=["total_assets"])
ok1 = (bs["current_assets"] + bs["non_current_assets"] - bs["total_assets"]).abs() <= 0.1
ok2 = (bs["total_liabilities"] + bs["owner_equity"] - bs["total_resources"]).abs() <= 0.1
ok3 = (p["net_revenue"] - p["cogs"] - p["gross_profit"]).abs() <= 0.1
print("\ntổng TS = TS ngắn hạn + TS dài hạn:", ok1.sum(), "/", len(bs))
print("tổng NV = nợ phải trả + vốn chủ:", ok2.sum(), "/", len(bs))
print("LN gộp = doanh thu - giá vốn:", ok3.sum(), "/", len(p))

# quy mô vốn điều lệ để nhận diện đúng doanh nghiệp (SRC rất nhỏ so với nhóm BĐS)
now = p[p["period"] == LATEST_Q][["ticker", "paid_in_capital", "total_assets"]]
print()
print(now.sort_values("paid_in_capital").to_string(index=False))
