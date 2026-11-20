# 03 - Làm sạch: ô trống, dấu, ngoại lai
import pandas as pd

from common import LATEST_Q, PROC, load_raw, to_wide

w = to_wide(load_raw())

# DIG 2021Q3 thiếu lãi vay đã trả -> tạm lấy chi phí lãi vay cùng quý trên B02
thieu = w["interest_paid"].isna()
print(w.loc[thieu, ["ticker", "period", "interest_paid", "interest_expense"]])
w.loc[thieu, "interest_paid"] = w.loc[thieu, "interest_expense"]

# tiền chi ra đang mang dấu âm -> đổi dấu cho dễ đọc.
# không dùng abs(): quý mang dấu ngược là số điều chỉnh, cộng 4 quý thì phải trừ đi.
# so thử lãi vay đã trả cả năm 2023 theo 2 cách (tỷ đồng):
y2023 = w[w["year"] == 2023].groupby("ticker")["interest_paid"]
cmp = pd.DataFrame({"doi_dau": -y2023.sum(),
                    "abs": y2023.apply(lambda s: s.abs().sum())}) / 1e9
print()
print(cmp[cmp["abs"] - cmp["doi_dau"] > 0.01].round(2))


# ngoại lai theo quy tắc 1,5 IQR - chỉ đánh dấu, không xóa
def ngoai_lai(s):
    s = s.dropna()
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    out = s[(s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)]
    return ", ".join(f"{k} {v:.2f}" for k, v in out.items()) or "không có"


p = pd.read_csv(PROC + "/panel_quarterly.csv")
now = p[p["period"] == LATEST_Q].set_index("ticker")
print("\nngoại lai tại", LATEST_Q)
for col in ["liquidity_coverage", "implied_rate_pct", "rollover_ratio", "debt_to_equity"]:
    print(f"  {col}: {ngoai_lai(now[col])}")

shock = pd.read_csv(PROC + "/stress_calibration.csv").set_index("ticker").drop("MEDIAN")
print("\nngoại lai trong cú sốc 2022-2023")
for col in ["sales_shock_pct", "adv_shock_pct", "rate_shock_pp", "rollover_stress"]:
    print(f"  {col}: {ngoai_lai(shock[col])}")
