# 01 - Nạp dữ liệu và đổi tên biến
import glob

import pandas as pd

from common import FIELDS, RAW, load_raw, to_wide

raw = load_raw()
print("số dòng, số cột:", raw.shape)
print("số mã:", raw["ticker"].nunique(), "| số chỉ tiêu:", raw["field_path"].nunique())
print(raw[["ticker", "year", "quarter", "value"]].head(3))

# chỉ tiêu có trong file nhưng không dùng tới
for path in sorted(set(raw["field_path"]) - set(FIELDS.values())):
    print("bỏ:", path)

# chuyển sang bảng ngang, mỗi dòng là 1 mã trong 1 quý
w = to_wide(raw)
print("\nbảng ngang:", w.shape)

# xem thử VHM 4 quý gần nhất, đơn vị tỷ đồng (dấu giữ nguyên như FiinQuant)
vhm = w[w["ticker"] == "VHM"].set_index("period").tail(4)
print((vhm[list(FIELDS)] / 1e9).round().astype(int).T)

# các file còn lại trong data/raw
for f in sorted(glob.glob(RAW + "/*.csv")):
    if "_bctc_min_raw" not in f:
        print(f, pd.read_csv(f).shape)
