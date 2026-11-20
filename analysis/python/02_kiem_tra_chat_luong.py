# 02 - Kiểm tra chất lượng dữ liệu
import numpy as np
import pandas as pd

from common import QUARTERS, RAW, PROC, close, load_raw, to_wide

raw = load_raw()
key = ["ticker", "year", "quarter", "field_path"]
print("dòng trùng:", raw.duplicated(key).sum())
print("ô trống:", raw["value"].isna().sum())
print(raw.loc[raw["value"].isna(), ["ticker", "year", "quarter"]])

w = to_wide(raw)
print("\nquý không có số liệu:", [q for q in QUARTERS if q not in set(w["period"])])

# tổng tài sản phải bằng nợ phải trả + vốn chủ
ok = close(w["total_assets"], w["liabilities"] + w["equity"])
print("\ncân đối kế toán khớp:", ok.sum(), "/", len(w))

# tiền cuối kỳ trên B03 phải bằng tiền trên B01
lech = ~close(w["cf_cash_end"], w["cash"])
print("tiền B03 khác B01 (tỷ đồng):")
print(w.loc[lech, ["ticker", "period"]].assign(B01=w["cash"] / 1e9, B03=w["cf_cash_end"] / 1e9))

# số theo quý là riêng từng quý hay lũy kế từ đầu năm?
# riêng quý  -> tiền đầu kỳ quý này = tiền cuối kỳ quý trước
# lũy kế     -> tiền đầu kỳ quý nào cũng = tiền đầu năm
w = w.sort_values(["ticker", "year", "quarter"])
g = w.groupby(["ticker", "year"])
lien_ke = g["quarter"].shift() == w["quarter"] - 1
rieng_quy = close(w["cf_cash_begin"], g["cf_cash_end"].shift())
luy_ke = close(w["cf_cash_begin"], g["cf_cash_begin"].transform("first")) & ~rieng_quy
print("\ncặp quý liền kề:", lien_ke.sum())
print("  khớp kiểu riêng quý:", (rieng_quy & lien_ke).sum())
print("  khớp kiểu lũy kế:", (luy_ke & lien_ke).sum())

# dấu bất thường (theo quy ước FiinQuant, tiền chi ra mang dấu âm)
print("\nlãi vay đã trả > 0:", (w["interest_paid"] > 0).sum(), "quý")
print("trả nợ gốc > 0:", (w["loan_repayments"] > 0).sum(), "quý")
print("vay mới < 0:", (w["loan_proceeds"] < 0).sum(), "quý")
print("doanh thu < 0:", (w["net_sales"] < 0).sum(), "quý")

# file VHM cũ có trùng với file mới không?
old = pd.read_csv(RAW + "/bctc_full_VHM_2026Q3.csv")
m = old.merge(raw, on=key, suffixes=("_cu", "_moi"))
print("\nfile VHM cũ: trùng", len(m), "chỉ tiêu, lệch",
      (~np.isclose(m["value_cu"], m["value_moi"])).sum())

# chuỗi lãi suất NHNN: mức trước đợt sau phải bằng mức sau đợt trước
ev = pd.read_csv(PROC + "/sbv_policy_events.csv")
ev = ev.sort_values(["rate_code", "effective_date"])
ev["sau_dot_truoc"] = ev.groupby("rate_code")["rate_after"].shift()
gap = ev[ev["sau_dot_truoc"].notna() & (ev["rate_before"] != ev["sau_dot_truoc"])]
print("\nchỗ đứt gãy trong chuỗi NHNN:")
print(gap[["rate_code", "effective_date", "sau_dot_truoc", "rate_before"]])
