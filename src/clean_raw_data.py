# -*- coding: utf-8 -*-
"""
clean_raw_data.py — VietLeap Hackathon 2026, Nhóm 2

Câu hỏi nghiên cứu: nếu lãi suất tăng và bán hàng chậm lại trong 12 tháng tới như giai đoạn 2022–2023,
doanh nghiệp BĐS dân cư niêm yết nào không đủ tiền trả nợ đến hạn, thiếu bao nhiêu, chịu được cú sốc
đến đâu, và doanh nghiệp/ngân hàng nên làm gì.

Script chỉ tạo những biến phục vụ trực tiếp câu hỏi trên.

Chạy:   python src/clean_raw_data.py            (đọc data/raw, ghi data/processed)

Đầu ra (data/processed/):
  panel_quarterly.csv        mã × quý: biến thanh khoản, nợ, dòng tiền, cộng 4 quý (TTM) và chỉ số rủi ro
  stress_calibration.csv     cú sốc của từng DN giữa giai đoạn nền (TTM 2022Q2) và khủng hoảng (TTM 2023Q2)
  macro_quarterly.csv        lãi suất tái cấp vốn NHNN, lãi suất Fed, lợi suất UST 10 năm theo quý
  sbv_policy_events.csv      các quyết định lãi suất điều hành NHNN đã làm sạch
  hnx_default_labels.csv     nhãn chậm trả trái phiếu HNX 2022–2023 theo mã (để kiểm chứng)
  data_quality_report.txt
"""
from __future__ import annotations

import glob
import os
import re
import sys
import unicodedata

import numpy as np
import pandas as pd

# ════════════════════════════════════ CẤU HÌNH ════════════════════════════════════
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "data", "processed")

FIRST_Q, LAST_Q = "2021Q1", "2026Q3"
BASE_Q, STRESS_Q = "2022Q2", "2023Q2"   # TTM nền: 2021Q3–2022Q2 · TTM khủng hoảng: 2022Q3–2023Q2
UNIT = 1e9                             # mọi số tiền xuất ra tính bằng tỷ VND
CSV_ENC = "utf-8-sig"

BS, IS, CF = "balance_sheet[0].", "income_statement[0].", "cash_flow[0]."
FIELDS = {                             # tên ngắn -> field_path FiinQuant
    "cash":              BS + "cash_and_cash_equivalents.total_cash_and_cash_equivalents",
    "st_invest":         BS + "short_term_investments.total_short_term_investments",
    "st_debt":           BS + "current_liabilities.short_term_borrowings",
    "lt_debt":           BS + "long_term_liabilities.long_term_borrowings",
    "adv_st":            BS + "current_liabilities.advances_from_customers",
    "adv_lt":            BS + "long_term_liabilities.long_term_advances_from_customers",
    "equity":            BS + "owner_s_equity",
    "net_sales":         IS + "net_sales",
    "cfo":               CF + "net_cash_inflows_outflows_from_operating_activities",
    "interest_paid":     CF + "operating_profit_loss_before_changes_in_working_capital.interest_paid",
    "loan_proceeds":     CF + "net_cash_inflows_outflows_from_financing_activities.proceeds_from_loans",
    "loan_repayments":   CF + "net_cash_inflows_outflows_from_financing_activities.repayment_of_loans",
    # chỉ dùng để kiểm tra / điền thiếu, không xuất ra
    "_total_assets":     BS + "total_assets",
    "_liabilities":      BS + "liabilities",
    "_interest_expense": IS + "financial_expenses.in_which_interest_expenses",
    "_cf_cash_begin":    CF + "cash_and_cash_equivalents_at_the_beginning_o_period",
    "_cf_cash_end":      CF + "cash_and_cash_equivalents_at_the_end_of_period",
}
MONEY = ["cash", "st_invest", "st_debt", "lt_debt", "adv_st", "adv_lt", "equity", "net_sales", "cfo",
         "interest_paid", "loan_proceeds", "loan_repayments"]
FLOWS = ["net_sales", "cfo", "interest_paid", "loan_proceeds", "loan_repayments"]


# ════════════════════════════════════ TIỆN ÍCH ════════════════════════════════════
class Report:
    def __init__(self):
        self.lines = []

    def __call__(self, msg=""):
        print(msg)
        self.lines.append(msg)

    def h1(self, t):
        self(f"\n{'═' * 78}\n {t}\n{'═' * 78}")

    def save(self, path):
        open(path, "w", encoding="utf-8").write("\n".join(self.lines) + "\n")


R = Report()


def close(a, b, rel=1e-4, abs_tol=1e6):
    """So sánh hai chuỗi số tiền (VND) với dung sai 1 triệu đồng hoặc 0,01%."""
    return (a - b).abs() <= np.maximum(abs_tol, rel * np.maximum(a.abs(), b.abs()))


def norm_text(s):
    if pd.isna(s):
        return ""
    s = unicodedata.normalize("NFC", str(s)).replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip().strip(" ,.;:")


def parse_vn_date(s):
    return pd.to_datetime(s.astype("string").str.strip(), format="%d/%m/%Y", errors="coerce")


def save(df, name):
    df.to_csv(os.path.join(OUT, name), index=False, encoding=CSV_ENC)
    R(f"  -> {name}: {len(df)} dòng × {df.shape[1]} cột")


# ════════════════════════════ 1. BÁO CÁO TÀI CHÍNH ════════════════════════════
def load_bctc():
    files = sorted(glob.glob(os.path.join(RAW, "*_bctc_min_raw.csv")))
    if not files:
        raise FileNotFoundError("Không thấy data/raw/*_bctc_min_raw.csv")
    raw = pd.concat([pd.read_csv(f, dtype={"ticker": "string", "field_path": "string"}) for f in files],
                    ignore_index=True)
    R(f"Đọc {len(files)} file, {len(raw):,} dòng, {raw['ticker'].nunique()} mã")
    need = {"ticker", "year", "quarter", "reportType", "field_path", "value"}
    if need - set(raw.columns):
        raise ValueError(f"Thiếu cột: {need - set(raw.columns)}")

    raw["ticker"] = raw["ticker"].str.strip().str.upper()
    raw["value"] = pd.to_numeric(raw["value"], errors="coerce")
    raw = raw[raw["reportType"].str.lower().eq("consolidated")]
    dup = raw.duplicated(["ticker", "year", "quarter", "field_path"], keep="last")
    R(f"  Dòng trùng khóa: {int(dup.sum())} | ô trống: {int(raw['value'].isna().sum())}")
    raw = raw[~dup]
    unknown = set(raw["field_path"]) - set(FIELDS.values())
    if unknown:
        R(f"  Bỏ {len(unknown)} chỉ tiêu không dùng: {sorted(unknown)}")

    rev = {v: k for k, v in FIELDS.items()}
    w = (raw[raw["field_path"].isin(rev)].assign(var=lambda d: d["field_path"].map(rev))
         .pivot_table(index=["ticker", "year", "quarter"], columns="var", values="value", aggfunc="first")
         .reindex(columns=list(FIELDS)).reset_index())
    w.columns.name = None
    w["period"] = w["year"].astype(str) + "Q" + w["quarter"].astype(str)
    return w, raw


def cross_check_old(raw):
    """File bctc_full_VHM cũ: chỉ đối chiếu, không đưa vào panel."""
    for f in glob.glob(os.path.join(RAW, "bctc_full_*.csv")):
        old = pd.read_csv(f)
        m = old.merge(raw, on=["ticker", "year", "quarter", "field_path"], suffixes=("_old", ""))
        diff = ~np.isclose(m["value_old"], m["value"], equal_nan=True)
        R(f"  Đối chiếu {os.path.basename(f)}: {len(m)} chỉ tiêu trùng, lệch {int(diff.sum())} -> không dùng (trùng nguồn)")


def quality_checks(w):
    """Kiểm tra chất lượng và sửa lỗi; trả về panel đã làm sạch (VND) kèm cột dq_flags."""
    w = w.copy()
    w["dq_flags"] = ""

    def flag(mask, text):
        w.loc[mask, "dq_flags"] = (w.loc[mask, "dq_flags"] + ";" + text).str.strip(";")
        return int(mask.sum())

    R("Kiểm tra chéo:")
    ok = close(w["_total_assets"], w["_liabilities"] + w["equity"])
    R(f"  Tổng tài sản = Nợ phải trả + VCSH: {int(ok.sum())}/{len(w)}")
    n = flag(~close(w["_cf_cash_end"], w["cash"]), "cash_bs_ne_cf")
    R(f"  Tiền cuối kỳ B03 = tiền B01: {len(w) - n}/{len(w)} (lệch: "
      f"{', '.join(w.loc[w['dq_flags'].str.contains('cash_bs_ne_cf'), 'ticker'] + ' ' + w.loc[w['dq_flags'].str.contains('cash_bs_ne_cf'), 'period'])}; dùng số B01)")

    # số riêng quý hay lũy kế: tiền đầu kỳ quý q so với tiền cuối kỳ quý q-1 cùng năm
    s = w.sort_values(["ticker", "year", "quarter"])
    prev_end = s.groupby(["ticker", "year"])["_cf_cash_end"].shift()
    prev_q = s.groupby(["ticker", "year"])["quarter"].shift()
    q1_begin = s.groupby(["ticker", "year"])["_cf_cash_begin"].transform("first")
    t = s[prev_q.eq(s["quarter"] - 1)]
    standalone = int((close(t["_cf_cash_begin"], prev_end[t.index]) & ~close(t["_cf_cash_begin"], q1_begin[t.index])).sum())
    ytd = int((close(t["_cf_cash_begin"], q1_begin[t.index]) & ~close(t["_cf_cash_begin"], prev_end[t.index])).sum())
    R(f"  Cơ sở số liệu quý: {standalone}/{len(t)} cặp quý liền kề là số riêng quý, {ytd} cặp kiểu lũy kế -> giữ nguyên")

    R("Xử lý thiếu:")
    miss = w["interest_paid"].isna() & w["_interest_expense"].notna()
    w.loc[miss, "interest_paid"] = w.loc[miss, "_interest_expense"]
    R(f"  interest_paid trống {flag(miss, 'interest_paid_from_pl')} quý -> lấy chi phí lãi vay B02 cùng quý: "
      f"{', '.join(w.loc[miss, 'ticker'] + ' ' + w.loc[miss, 'period'])}")
    R(f"  Ô trống còn lại ở biến dùng: {int(w[MONEY].isna().sum().sum())}")

    R("Dấu bất thường (giữ nguyên dấu, gắn cờ; đây là phần hiệu chỉnh khi nhà cung cấp tách số lũy kế):")
    for col, bad, name in [("interest_paid", w["interest_paid"] > 0, "lãi vay đã trả dương"),
                           ("loan_repayments", w["loan_repayments"] > 0, "trả nợ gốc dương"),
                           ("loan_proceeds", w["loan_proceeds"] < 0, "tiền vay mới âm"),
                           ("net_sales", w["net_sales"] < 0, "doanh thu thuần âm")]:
        R(f"  {name:<22} {flag(bad, col + '_sign'):>3} quý")
    # quy ước: dòng tiền ra (lãi vay, trả nợ gốc) đổi sang số dương. Đổi dấu chứ không lấy abs(),
    # để các quý hiệu chỉnh tự trừ đi khi cộng 4 quý.
    w["interest_paid"] = -w["interest_paid"]
    w["loan_repayments"] = -w["loan_repayments"]
    for c in MONEY:
        w[c] = w[c] / UNIT
    return w


def build_features(w):
    """Biến mới — chỉ những biến dùng để trả lời câu hỏi nghiên cứu."""
    grid = pd.MultiIndex.from_product(
        [sorted(w["ticker"].unique()), pd.period_range(FIRST_Q, LAST_Q, freq="Q").astype(str)],
        names=["ticker", "period"]).to_frame(index=False)
    g = grid.merge(w, on=["ticker", "period"], how="left")      # lưới quý đầy đủ: quý thiếu không bị cộng nhầm
    by = g.groupby("ticker")
    g["liquid_assets"] = g["cash"] + g["st_invest"]
    g["total_debt"] = g["st_debt"] + g["lt_debt"]
    g["adv_customers"] = g["adv_st"] + g["adv_lt"]
    for c in FLOWS:
        g[c + "_ttm"] = by[c].transform(lambda s: s.rolling(4, min_periods=4).sum())
    avg_debt = by["total_debt"].transform(lambda s: s.rolling(4, min_periods=4).mean())
    g["implied_rate_pct"] = g["interest_paid_ttm"] / avg_debt.where(avg_debt > 0) * 100
    g["rollover_ratio"] = g["loan_proceeds_ttm"] / g["loan_repayments_ttm"].where(g["loan_repayments_ttm"] > 0)
    g["liquidity_gap_12m"] = g["liquid_assets"] + g["cfo_ttm"] - g["st_debt"]
    g["liquidity_coverage"] = (g["liquid_assets"] + g["cfo_ttm"]) / g["st_debt"].where(g["st_debt"] > 0)
    g["debt_to_equity"] = g["total_debt"] / g["equity"].where(g["equity"] > 0)
    g = g[g["year"].notna()].copy()                               # chỉ giữ quý có số liệu
    g["year"] = g["year"].astype(int)
    g["quarter"] = g["quarter"].astype(int)

    cols = (["ticker", "period", "year", "quarter", "cash", "st_invest", "liquid_assets", "st_debt",
             "lt_debt", "total_debt", "adv_customers", "equity"] + FLOWS + [c + "_ttm" for c in FLOWS]
            + ["implied_rate_pct", "rollover_ratio", "liquidity_gap_12m", "liquidity_coverage", "debt_to_equity",
               "dq_flags"])
    out = g[cols].copy()
    num = out.select_dtypes("number").columns.drop(["year", "quarter"])
    out[num] = out[num].round(4)
    return out


def build_calibration(p, labels):
    """Cú sốc 2022–2023 của từng DN: so TTM khủng hoảng (STRESS_Q) với TTM nền (BASE_Q)."""
    b = p[p["period"] == BASE_Q].set_index("ticker")
    s = p[p["period"] == STRESS_Q].set_index("ticker")
    c = pd.DataFrame(index=b.index)
    c["sales_ttm_base"], c["sales_ttm_stress"] = b["net_sales_ttm"], s["net_sales_ttm"]
    c["sales_shock_pct"] = (s["net_sales_ttm"] / b["net_sales_ttm"].where(b["net_sales_ttm"] > 0) - 1) * 100
    c["adv_base"], c["adv_stress"] = b["adv_customers"], s["adv_customers"]
    c["adv_shock_pct"] = (s["adv_customers"] / b["adv_customers"].where(b["adv_customers"] > 0) - 1) * 100
    c["cfo_ttm_base"], c["cfo_ttm_stress"] = b["cfo_ttm"], s["cfo_ttm"]
    c["cfo_shock"] = s["cfo_ttm"] - b["cfo_ttm"]
    c["rate_base_pct"], c["rate_stress_pct"] = b["implied_rate_pct"], s["implied_rate_pct"]
    c["rate_shock_pp"] = s["implied_rate_pct"] - b["implied_rate_pct"]
    c["rollover_base"], c["rollover_stress"] = b["rollover_ratio"], s["rollover_ratio"]
    c["liquidity_gap_base"] = b["liquidity_gap_12m"]          # cảnh báo sớm, đối chiếu với nhãn HNX
    c = c.reset_index().merge(labels[["ticker", "bond_default_flag"]], on="ticker", how="left")
    shock_cols = ["sales_shock_pct", "adv_shock_pct", "rate_shock_pp", "rollover_stress"]
    med = c[shock_cols].median().to_frame().T.assign(ticker="MEDIAN")
    c = pd.concat([c, med], ignore_index=True)
    num = c.select_dtypes("number").columns
    c[num] = c[num].round(4)
    return c


def run_bctc(labels):
    R.h1("BÁO CÁO TÀI CHÍNH (FiinQuant)")
    w, raw = load_bctc()
    cross_check_old(raw)
    periods = sorted(w["period"].unique())
    full = pd.period_range(FIRST_Q, LAST_Q, freq="Q").astype(str)
    R(f"  Kỳ có số liệu: {len(periods)} quý; thiếu: {', '.join(q for q in full if q not in periods)}")
    w = quality_checks(w)
    p = build_features(w)
    R("Biến mới: TTM chỉ tính khi đủ 4 quý liên tiếp")
    R(f"  Quý tính được TTM: {', '.join(p.loc[p['cfo_ttm'].notna(), 'period'].drop_duplicates())}")
    save(p, "panel_quarterly.csv")
    c = build_calibration(p, labels)
    R(f"Hiệu chỉnh cú sốc ({BASE_Q} -> {STRESS_Q}), trung vị ngành:")
    for k in ["sales_shock_pct", "adv_shock_pct", "rate_shock_pp", "rollover_stress"]:
        R(f"  {k:<18} {c.loc[c['ticker'] == 'MEDIAN', k].iloc[0]:>8.2f}")
    save(c, "stress_calibration.csv")
    return p


# ════════════════════════════ 2. VĨ MÔ ════════════════════════════
RATE_CODES = [(r"tái cấp vốn", "refinancing_rate", "policy"), (r"tái chiết khấu", "rediscount_rate", "policy"),
              (r"qua đêm", "overnight_rate", "policy"),
              (r"tiền gửi.*(không kỳ hạn|dưới 1 tháng)", "deposit_cap_under_1m", "deposit_cap"),
              (r"tiền gửi.*1 tháng đến dưới 6 tháng", "deposit_cap_1m_6m", "deposit_cap"),
              (r"cho vay.*ưu tiên", "priority_lending_cap", "lending_cap")]
DECISION_DATES = {"313/QĐ-NHNN": "2023-03-15", "314/QĐ-NHNN": "2023-03-15"}   # ký 14/03/2023, hiệu lực hôm sau
EFFECTIVE_FILL = {"2023-04-03": ("2023-03-31", {"policy": "574/QĐ-NHNN", "deposit_cap": "575/QĐ-NHNN",
                                                "lending_cap": "576/QĐ-NHNN"})}


def extract_rates(text):
    t = norm_text(text).lower()
    nums = [float(x.replace(",", ".")) for x in re.findall(r"(\d+(?:[.,]\d+)?)\s*%", t)]
    if "giữ nguyên" in t and nums:
        return nums[0], nums[0]
    if len(nums) >= 2 and re.search(r"\btừ\b", t):
        return nums[0], nums[1]
    return (np.nan, nums[0]) if len(nums) == 1 else (np.nan, np.nan)


def clean_sbv():
    df = pd.read_csv(os.path.join(RAW, "sbv_lai_suat_dieu_hanh_trich_nguon.csv"), dtype="string")
    n0 = int(df[["ngay_hieu_luc", "so_quyet_dinh", "ngay_quyet_dinh"]].isna().sum().sum())
    for c in df.columns:
        df[c] = df[c].map(lambda x: norm_text(x) if pd.notna(x) else pd.NA).replace("", pd.NA)
    code = df["loai_lai_suat"].map(lambda s: next(((c, f) for p, c, f in RATE_CODES if re.search(p, s.lower())),
                                                  (None, None)))
    df["rate_code"], df["family"] = code.str[0], code.str[1]
    rates = df["trich_nguyen_van"].map(extract_rates)
    df["rate_before"], df["rate_after"] = rates.str[0].astype(float), rates.str[1].astype(float)
    df["effective_date"] = parse_vn_date(df["ngay_hieu_luc"])
    df["decision_date"] = parse_vn_date(df["ngay_quyet_dinh"])
    df["decision_no"] = df["so_quyet_dinh"]
    df["decision_no"] = df.groupby(["nguon_url", "family"])["decision_no"].transform(lambda s: s.ffill().bfill())
    df["decision_date"] = df.groupby("nguon_url")["decision_date"].transform(lambda s: s.ffill().bfill())
    for dec, eff in DECISION_DATES.items():
        m = df["decision_no"].eq(dec) & df["effective_date"].isna()
        df.loc[m, "effective_date"] = pd.Timestamp(eff)
    for eff, (ddate, decs) in EFFECTIVE_FILL.items():
        m = df["effective_date"].eq(pd.Timestamp(eff))
        df.loc[m & df["decision_date"].isna(), "decision_date"] = pd.Timestamp(ddate)
        for fam, dec in decs.items():
            df.loc[m & df["decision_no"].isna() & df["family"].eq(fam), "decision_no"] = dec
    df = df.sort_values(["rate_code", "effective_date"])
    prev = df.groupby("rate_code")["rate_after"].shift()
    df["rate_before"] = df["rate_before"].fillna(prev)
    gaps = df[prev.notna() & (df["rate_before"] - prev).abs().gt(1e-9)]
    R(f"  NHNN: {len(df)} dòng; ô trống ngày/số QĐ {n0} -> "
      f"{int(df[['effective_date', 'decision_no', 'decision_date']].isna().sum().sum())}; "
      f"đứt gãy chuỗi (nguồn thiếu đợt điều chỉnh): {len(gaps)} -> "
      f"{', '.join(gaps['rate_code'] + ' ' + gaps['effective_date'].dt.strftime('%Y-%m-%d'))}")
    out = df.sort_values(["effective_date", "rate_code"])[
        ["effective_date", "decision_date", "decision_no", "rate_code", "rate_before", "rate_after"]].copy()
    for c in ["effective_date", "decision_date"]:
        out[c] = out[c].dt.strftime("%Y-%m-%d")
    return out, gaps


def run_macro():
    R.h1("VĨ MÔ")
    ev, gaps = clean_sbv()
    save(ev, "sbv_policy_events.csv")
    # tái cấp vốn: forward-fill theo ngày, lấy cuối quý; trước đợt đầu tiên trong nguồn để trống
    refi = ev[ev["rate_code"] == "refinancing_rate"].assign(d=lambda x: pd.to_datetime(x["effective_date"]))
    days = pd.date_range(pd.Period(FIRST_Q).start_time, pd.Period(LAST_Q).end_time.normalize(), freq="D")
    s = refi.set_index("d")["rate_after"].reindex(days).ffill()
    s[s.index < refi["d"].min()] = np.nan
    s.loc[refi["d"].min().to_period("M").start_time:refi["d"].min() - pd.Timedelta(days=1)] = refi["rate_before"].iloc[0]
    q = s.groupby(s.index.to_period("Q")).last().rename("sbv_refinancing_eoq").to_frame()
    gap_refi = gaps[gaps["rate_code"] == "refinancing_rate"]
    q["sbv_uncertain"] = False
    for _, g in gap_refi.iterrows():
        prev_eff = refi.loc[refi["d"] < g["effective_date"], "d"].max()
        q.loc[(q.index >= prev_eff.to_period("Q")) & (q.index < g["effective_date"].to_period("Q")), "sbv_uncertain"] = True

    def fred(fname, col):
        d = pd.read_csv(os.path.join(RAW, fname), parse_dates=["observation_date"])
        d[col] = pd.to_numeric(d[col], errors="coerce")
        n_tail = len(d) - (d[col].last_valid_index() + 1)
        d = d.loc[:d[col].last_valid_index()]                    # bỏ đuôi chưa công bố, không ngoại suy
        return d.set_index("observation_date")[col], n_tail

    fed, n1 = fred("fred_DFEDTARU_thang_cuoiky_2019-2026.csv", "DFEDTARU")
    ust, n2 = fred("fred_DGS10_thang_trungbinh_2019-2026.csv", "DGS10")
    R(f"  FRED: bỏ {n1 + n2} tháng trống cuối chuỗi; dùng DFEDTARU (cuối quý) và DGS10 (trung bình quý)")
    q["fed_upper_eoq"] = fed.groupby(fed.index.to_period("Q")).last()
    q["ust10y_avg"] = ust.groupby(ust.index.to_period("Q")).mean().round(4)
    q = q.loc[FIRST_Q:LAST_Q].reset_index(names="period")
    q["period"] = q["period"].astype(str)
    save(q, "macro_quarterly.csv")


# ════════════════════════════ 3. NHÃN CHẬM TRẢ HNX ════════════════════════════
# (mẫu tên, mã niêm yết, phát hành qua công ty con?) — chỉ cần các pháp nhân thuộc DN BĐS niêm yết
ISSUER_TICKER = [(r"nova final", "NVL", True), (r"no ?va|novaland", "NVL", False), (r"hải phát", "HPX", False),
                 (r"sài gòn thương tín", "SCR", False), (r"\bldg\b|\blgd\b", "LDG", False),
                 (r"danh khôi", "NRC", False), (r"hà an", "DXG", True), (r"đất xanh miền nam", "DXG", True)]


def run_hnx(tickers):
    R.h1("NHÃN CHẬM TRẢ TRÁI PHIẾU (HNX, 16/9/2022 – 31/1/2023)")
    h = pd.read_csv(os.path.join(RAW, "hnx_54_to_chuc_cham_tra_trich_nguon.csv"), dtype="string")
    name = h["ten_to_chuc_phat_hanh_nguyen_van"].map(norm_text).str.replace(r"\s*\(báo cáo bất thường\)", "", regex=True)
    hit = name.map(lambda n: next(((t, sub) for p, t, sub in ISSUER_TICKER if re.search(p, n.lower())), (None, None)))
    h["name"], h["ticker"], h["via_subsidiary"] = name, hit.str[0], hit.str[1]
    m = h[h["ticker"].notna()].drop_duplicates("name")
    R(f"  {len(h)} dòng, {name.nunique()} pháp nhân; {len(m)} pháp nhân gắn được với mã BĐS niêm yết "
      f"(còn lại là DN chưa niêm yết hoặc ngoài ngành, không dùng)")
    lab = (m.groupby("ticker").agg(n_entities=("name", "size"),
                                   n_via_subsidiary=("via_subsidiary", "sum"),
                                   entities=("name", " | ".join)).reset_index())
    lab = pd.DataFrame({"ticker": tickers}).merge(lab, on="ticker", how="left")
    lab["bond_default_flag"] = lab["n_entities"].notna().astype(int)
    lab[["n_entities", "n_via_subsidiary"]] = lab[["n_entities", "n_via_subsidiary"]].fillna(0).astype(int)
    lab["entities"] = lab["entities"].fillna("")
    R(f"  Có tên (1): {', '.join(lab.loc[lab['bond_default_flag'] == 1, 'ticker'])}")
    R(f"  Không có tên trong phần danh sách đã trích (0, chưa chắc chắn): "
      f"{', '.join(lab.loc[lab['bond_default_flag'] == 0, 'ticker'])}")
    save(lab[["ticker", "bond_default_flag", "n_entities", "n_via_subsidiary", "entities"]], "hnx_default_labels.csv")
    return lab


# ════════════════════════════════════ MAIN ════════════════════════════════════
def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    os.makedirs(OUT, exist_ok=True)
    for f in glob.glob(os.path.join(OUT, "*")):                  # xóa đầu ra cũ để không lẫn file lỗi thời
        os.remove(f)
    R(f"DATA QUALITY REPORT — {pd.Timestamp.now():%Y-%m-%d %H:%M} | pandas {pd.__version__}")
    tickers = sorted({os.path.basename(f).split("_")[0] for f in glob.glob(os.path.join(RAW, "*_bctc_min_raw.csv"))})
    labels = run_hnx(tickers)
    run_bctc(labels)
    run_macro()
    R.save(os.path.join(OUT, "data_quality_report.txt"))


if __name__ == "__main__":
    main()
