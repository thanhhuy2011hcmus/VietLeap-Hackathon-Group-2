# 05 - Thống kê mô tả
import pandas as pd

from common import BASE_Q, LATEST_Q, PROC

p = pd.read_csv(PROC + "/panel_quarterly.csv")
shock = pd.read_csv(PROC + "/stress_calibration.csv")
cols = ["liquidity_gap_12m", "liquidity_coverage", "rollover_ratio",
        "implied_rate_pct", "debt_to_equity"]


def mo_ta(df):
    t = df[cols].describe().T
    t["skew"] = df[cols].skew()
    return t.round(2)


now = p[p["period"] == LATEST_Q]
print("quý", LATEST_Q, "-", len(now), "doanh nghiệp")
print(mo_ta(now))

ttm = p.dropna(subset=["cfo_ttm"])
print("\ntất cả các quý có số 12 tháng -", len(ttm), "quan sát")
print(mo_ta(ttm))

# ai không đủ tiền trả nợ vay ngắn hạn nếu không vay thêm được
thieu = now[now["liquidity_gap_12m"] < 0].sort_values("liquidity_gap_12m")
print("\nthiếu tiền tại", LATEST_Q)
print(thieu[["ticker", "liquidity_gap_12m", "liquidity_coverage", "rollover_ratio"]]
      .round(2).to_string(index=False))

# chỉ số này có nhận ra những DN đã chậm trả trái phiếu năm 2022-2023 không?
v = shock[shock["ticker"] != "MEDIAN"]
print("\nthiếu hụt tại", BASE_Q, "so với danh sách chậm trả HNX:")
print(pd.crosstab(v["liquidity_gap_base"] < 0, v["bond_default_flag"].astype(int),
                  rownames=["gap < 0"], colnames=["có tên HNX"], margins=True))
