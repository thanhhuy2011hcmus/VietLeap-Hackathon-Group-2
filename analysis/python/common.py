# Những thứ dùng chung cho các file 00-07. Chạy từ thư mục gốc của dự án.
import glob
import os

import numpy as np
import pandas as pd

pd.set_option("display.width", 100)
pd.set_option("display.max_columns", 20)
pd.set_option("display.float_format", "{:.2f}".format)

RAW = "data/raw"
PROC = "data/processed"
FIG = "reports/figures/python"

QUARTERS = list(pd.period_range("2021Q1", "2026Q3", freq="Q").astype(str))
BASE_Q = "2022Q2"     # 4 quý trước khủng hoảng: 2021Q3-2022Q2
STRESS_Q = "2023Q2"   # 4 quý khủng hoảng: 2022Q3-2023Q2
LATEST_Q = "2026Q3"

BLUE, ORANGE, GREEN = "#2a78d6", "#eb6834", "#1baf7a"

# tên ngắn -> đường dẫn chỉ tiêu trong file FiinQuant
BS = "balance_sheet[0]."
IS = "income_statement[0]."
CF = "cash_flow[0]."
FIELDS = {
    "cash": BS + "cash_and_cash_equivalents.total_cash_and_cash_equivalents",
    "st_invest": BS + "short_term_investments.total_short_term_investments",
    "st_debt": BS + "current_liabilities.short_term_borrowings",
    "lt_debt": BS + "long_term_liabilities.long_term_borrowings",
    "adv_st": BS + "current_liabilities.advances_from_customers",
    "adv_lt": BS + "long_term_liabilities.long_term_advances_from_customers",
    "equity": BS + "owner_s_equity",
    "net_sales": IS + "net_sales",
    "cfo": CF + "net_cash_inflows_outflows_from_operating_activities",
    "interest_paid": CF + "operating_profit_loss_before_changes_in_working_capital"
                          ".interest_paid",
    "loan_proceeds": CF + "net_cash_inflows_outflows_from_financing_activities"
                          ".proceeds_from_loans",
    "loan_repayments": CF + "net_cash_inflows_outflows_from_financing_activities"
                            ".repayment_of_loans",
    # 5 chỉ tiêu dưới chỉ để kiểm tra chéo, không đưa vào file sạch
    "total_assets": BS + "total_assets",
    "liabilities": BS + "liabilities",
    "interest_expense": IS + "financial_expenses.in_which_interest_expenses",
    "cf_cash_begin": CF + "cash_and_cash_equivalents_at_the_beginning_o_period",
    "cf_cash_end": CF + "cash_and_cash_equivalents_at_the_end_of_period",
}
FLOWS = ["net_sales", "cfo", "interest_paid", "loan_proceeds", "loan_repayments"]


def load_raw():
    files = sorted(glob.glob(RAW + "/*_bctc_min_raw.csv"))
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


def to_wide(raw):
    """Bảng dài (mỗi dòng 1 chỉ tiêu) -> bảng ngang (mỗi dòng 1 mã x 1 quý)."""
    name = {path: short for short, path in FIELDS.items()}
    df = raw[raw["field_path"].isin(name)].copy()
    df["var"] = df["field_path"].map(name)
    w = df.pivot_table(index=["ticker", "year", "quarter"], columns="var",
                       values="value", aggfunc="first")
    w = w.reindex(columns=list(FIELDS)).reset_index()
    w.columns.name = None
    w["period"] = w["year"].astype(str) + "Q" + w["quarter"].astype(str)
    return w


def close(a, b):
    """Coi 2 số tiền (VND) là bằng nhau nếu lệch dưới 1 triệu đồng hoặc 0,01%."""
    tol = np.maximum(1e6, 1e-4 * np.maximum(a.abs(), b.abs()))
    return (a - b).abs() <= tol


def get_plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False})
    os.makedirs(FIG, exist_ok=True)
    return plt
