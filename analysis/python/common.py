# Những thứ dùng chung cho các file 00-07. Chạy từ thư mục gốc của dự án.
import os

import pandas as pd

pd.set_option("display.width", 100)
pd.set_option("display.max_columns", 20)
pd.set_option("display.float_format", "{:.2f}".format)

RAW = "data/raw"
PROC = "data/processed"
FIG = "reports/figures/python"

# 9 doanh nghiệp bất động sản; SRC là Cao su Sao Vàng nên chỉ dùng ở phần kiểm tra dữ liệu
RE = ["DIG", "DXG", "HPX", "KDH", "NLG", "NVL", "PDR", "QCG", "VHM"]
LATEST_Q = "2026Q3"
SHOCK = ("2022Q3", "2023Q4")          # giai đoạn lãi suất tăng, bán hàng chậm

BLUE, ORANGE, GREEN, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#9ca3af"


def read(name):
    return pd.read_csv(f"{PROC}/{name}")


def get_plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False})
    os.makedirs(FIG, exist_ok=True)
    return plt
